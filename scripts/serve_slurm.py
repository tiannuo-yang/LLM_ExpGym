#!/usr/bin/env python3
"""Plan explicit SGLang replica topology; only --submit invokes sbatch.

No model import, checkpoint loading, health request, or credential handling is
performed by the planning path. This is a launcher, not a science/smoke gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import socket
import subprocess
import sys
import time

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs/serving/slurm_tp16.json"
# These options occur in the previously exercised launch profiles or reviewed
# SGLang recipes. Keep them opt-in, never guessed from model names. New runtime
# options still need validation with the selected frozen SGLang executable.
BACKEND_VALUE_FLAGS = {"--moe-runner-backend", "--attention-backend", "--sampling-backend",
                       "--quantization", "--random-seed", "--dist-timeout",
                       "--linear-attn-prefill-backend", "--linear-attn-decode-backend",
                       "--mamba-full-memory-ratio", "--mamba-ssm-dtype",
                       "--max-prefill-tokens", "--page-size", "--chunked-prefill-size"}
BACKEND_SWITCH_FLAGS = {"--enable-deterministic-inference", "--enable-symm-mem"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def positive_int(value, label):
    require(type(value) is int and value > 0, label + " must be a positive integer")


def absolute_path(value, label):
    require(isinstance(value, str) and Path(value).is_absolute() and "\n" not in value,
            label + " must be an absolute path")
    return value


def validate_config(config):
    require(type(config) is dict and set(config) == {"schema_version", "slurm", "topology", "dispatch", "sglang"},
            "unexpected config fields")
    require(type(config["schema_version"]) is int and config["schema_version"] in (1, 2, 3), "unknown schema")
    slurm, topology = config["slurm"], config["topology"]
    require(type(slurm) is dict and set(slurm) == {"account", "partition", "nodes", "gpus_per_node", "cpus_per_task", "time_limit"}, "invalid Slurm config")
    topology_fields = {"replicas", "nodes_per_replica", "tp_size", "http_port_base", "dist_port_base"}
    if config["schema_version"] in (2, 3):
        topology_fields.add("pp_size")
    require(type(topology) is dict and set(topology) == topology_fields, "invalid topology")
    for field in ("nodes", "gpus_per_node", "cpus_per_task"):
        positive_int(slurm[field], field)
    for field, value in topology.items():
        positive_int(value, field)
    require(slurm["nodes"] == topology["replicas"] * topology["nodes_per_replica"], "replica node total mismatch")
    pp_size = topology.get("pp_size", 1)
    require(topology["tp_size"] * pp_size == topology["nodes_per_replica"] * slurm["gpus_per_node"], "TP*PP/GPU total mismatch")
    shape = (slurm["nodes"], slurm["gpus_per_node"], topology["replicas"], topology["nodes_per_replica"], topology["tp_size"], pp_size)
    if config["schema_version"] == 1:
        require(shape == (4, 8, 2, 2, 16, 1), "schema 1 requires 4 nodes, 8 GPUs/node, two TP16 replicas")
    elif config["schema_version"] == 2:
        require(shape == (4, 8, 1, 4, 8, 4), "schema 2 requires 4 nodes, 8 GPUs/node, one TP8*PP4 replica")
    else:
        require(shape == (4, 8, 4, 1, 8, 1), "schema 3 requires 4 nodes, 8 GPUs/node, four single-node TP8 replicas")
    for field in ("account", "partition"):
        require(isinstance(slurm[field], str) and re.fullmatch(r"[A-Za-z0-9_.-]+", slurm[field]), "invalid " + field)
    require(slurm["account"] == "k2p", "this profile requires account k2p")
    require(isinstance(slurm["time_limit"], str) and re.fullmatch(r"(?:\d+-)?\d{1,2}:\d{2}:\d{2}", slurm["time_limit"]), "invalid time limit")
    ports = [topology[name] + replica for name in ("http_port_base", "dist_port_base") for replica in range(topology["replicas"])]
    require(all(1024 <= port <= 65535 for port in ports) and len(set(ports)) == 2 * topology["replicas"], "invalid/overlapping ports")
    require(type(config["dispatch"]) is dict and set(config["dispatch"]) == {"max_workers"}, "invalid dispatch config")
    positive_int(config["dispatch"]["max_workers"], "max_workers")
    require(type(config["sglang"]) is dict and set(config["sglang"]) == {"max_running_requests", "cuda_graph_max_bs_decode"}, "invalid SGLang config")
    for field, value in config["sglang"].items():
        positive_int(value, field)
    return config


def backend_args(value):
    require(type(value) is list and all(type(arg) is str and arg and "\n" not in arg for arg in value), "server args must be a string array")
    seen, index = set(), 0
    while index < len(value):
        flag = value[index]
        require(flag not in seen, "duplicate backend option")
        seen.add(flag)
        if flag in BACKEND_SWITCH_FLAGS:
            index += 1
        else:
            require(flag in BACKEND_VALUE_FLAGS, "unsupported backend option; topology, generation and secrets cannot be overridden here")
            require(index + 1 < len(value) and not value[index + 1].startswith("--"), "backend option needs a value")
            index += 2
    return value


def build_plan(config, *, checkpoint, sglang_bin, model, context_length, mem_fraction_static,
               ep_size, reasoning_parser=None, tool_call_parser=None, server_args=None,
               runtime_env=None, container_image=None, container_mounts=None, trust_remote_code=False):
    config = validate_config(config)
    for label, value in (("checkpoint", checkpoint), ("sglang_bin", sglang_bin)):
        absolute_path(value, label)
    for label, value in (("runtime_env", runtime_env), ("container_image", container_image)):
        if value is not None:
            absolute_path(value, label)
    require(isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", model), "invalid served model name")
    positive_int(context_length, "context_length")
    positive_int(ep_size, "ep_size")
    require(config["topology"]["tp_size"] % ep_size == 0, "ep_size must divide tp_size")
    require(type(mem_fraction_static) in (int, float) and math.isfinite(mem_fraction_static) and 0 < mem_fraction_static < 1, "invalid memory fraction")
    for value in (reasoning_parser, tool_call_parser):
        require(value is None or (isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]+", value)), "invalid parser name")
    mounts = container_mounts or []
    require(type(mounts) is list and all(type(value) is str and value and "\n" not in value for value in mounts), "invalid container mounts")
    require(not mounts or container_image is not None, "mounts require a container image")
    return {"schema_version": config["schema_version"], "config": config, "checkpoint": checkpoint, "sglang_bin": sglang_bin,
            "model": model, "context_length": context_length, "mem_fraction_static": mem_fraction_static,
            "ep_size": ep_size, "reasoning_parser": reasoning_parser, "tool_call_parser": tool_call_parser,
            "server_args": backend_args([] if server_args is None else server_args), "runtime_env": runtime_env,
            "container_image": container_image, "container_mounts": mounts,
            "trust_remote_code": bool(trust_remote_code), "generation_settings": "unchanged; supplied by experiment runner",
            "real_smoke_passed": False, "endpoint_authentication": "none; trusted private network required"}


def node_layout(plan, nodes):
    require(type(nodes) is list and len(nodes) == 4 and len(set(nodes)) == 4, "expected four distinct allocated nodes")
    require(all(type(node) is str and re.fullmatch(r"[A-Za-z0-9_.-]+", node) for node in nodes), "invalid allocated node name")
    topology = plan["config"]["topology"]
    width = topology["nodes_per_replica"]
    return [{"replica": replica, "nodes": nodes[width * replica:width * (replica + 1)], "tp_size": topology["tp_size"],
             **({"pp_size": topology["pp_size"]} if "pp_size" in topology else {}),
             "http_port": topology["http_port_base"] + replica,
             "dist_port": topology["dist_port_base"] + replica,
             "base_url": "http://%s:%d/v1" % (nodes[width * replica], topology["http_port_base"] + replica)}
            for replica in range(topology["replicas"])]


def server_command(plan, replica, rank, head_ip):
    topology = plan["config"]["topology"]
    require(type(rank) is int and 0 <= rank < topology["nodes_per_replica"], "invalid rank")
    require(type(replica["replica"]) is int and 0 <= replica["replica"] < topology["replicas"], "invalid replica")
    cfg = plan["config"]["sglang"]
    parallel_args = ["--tp-size", str(topology["tp_size"])]
    if "pp_size" in topology:
        parallel_args += ["--pp-size", str(topology["pp_size"])]
    command = [plan["sglang_bin"], "serve", "--model-path", plan["checkpoint"],
               "--served-model-name", plan["model"], *parallel_args, "--ep-size", str(plan["ep_size"]),
               "--nnodes", str(topology["nodes_per_replica"]), "--node-rank", str(rank), "--dist-init-addr", "%s:%s" % (head_ip, replica["dist_port"]),
               "--context-length", str(plan["context_length"]), "--mem-fraction-static", str(plan["mem_fraction_static"]),
               "--max-running-requests", str(cfg["max_running_requests"]),
               "--cuda-graph-max-bs-decode", str(cfg["cuda_graph_max_bs_decode"]),
               "--enable-metrics", "--host", "0.0.0.0", "--port", str(replica["http_port"])]
    if plan["trust_remote_code"]:
        command.append("--trust-remote-code")
    for key in ("reasoning_parser", "tool_call_parser"):
        if plan[key] is not None:
            command += ["--" + key.replace("_", "-"), plan[key]]
    return command + plan["server_args"]


def batch_script(plan, directory, launcher, controller_python):
    slurm = plan["config"]["slurm"]
    lines = ["#!/usr/bin/env bash", "#SBATCH --account=" + slurm["account"],
             "#SBATCH --partition=" + slurm["partition"], "#SBATCH --nodes=4", "#SBATCH --ntasks-per-node=1",
             "#SBATCH --cpus-per-task=" + str(slurm["cpus_per_task"]), "#SBATCH --gres=gpu:8",
             "#SBATCH --exclusive", "#SBATCH --no-requeue", "#SBATCH --time=" + slurm["time_limit"],
             "#SBATCH --job-name=expgym-" + plan["model"].replace("/", "-")[:80],
             "#SBATCH --output=" + shlex.quote(str(directory / "slurm-%j.log")),
             "set -euo pipefail", "ulimit -c 0",
             "exec " + shlex.join([controller_python, str(launcher), "--run-allocation", str(directory / "plan.json")])]
    return "\n".join(lines) + "\n"


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def validate_plan(plan):
    """Apply the planning contract again before executing a saved plan.

    A launcher hash alone does not validate editable plan fields. In particular,
    server_args must not bypass topology/secret validation at allocation time.
    """
    require(type(plan) is dict, "invalid serving plan")
    require(type(plan.get("schema_version")) is int, "invalid plan schema")
    require(type(plan.get("trust_remote_code")) is bool, "invalid trust_remote_code")
    parameters = ("checkpoint", "sglang_bin", "model", "context_length", "mem_fraction_static", "ep_size",
                  "reasoning_parser", "tool_call_parser", "server_args", "runtime_env", "container_image",
                  "container_mounts", "trust_remote_code")
    checked = build_plan(plan["config"], **{name: plan[name] for name in parameters})
    require({key: value for key, value in plan.items() if key != "launcher_sha256"} == checked,
            "saved plan does not match planning contract")
    return plan


def run_allocation(plan_path):
    plan_path = Path(plan_path).resolve()
    plan = validate_plan(json.loads(plan_path.read_text()))
    require(plan.get("launcher_sha256") == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "launcher source changed")
    require(os.environ.get("SLURM_JOB_ID", "").isdigit(), "must run inside a Slurm allocation")
    require(os.environ.get("SLURM_JOB_ACCOUNT") == plan["config"]["slurm"]["account"], "allocation account mismatch")
    nodes = subprocess.check_output(["scontrol", "show", "hostnames", os.environ["SLURM_JOB_NODELIST"]], text=True).splitlines()
    replicas = node_layout(plan, nodes)
    directory = plan_path.parent
    commands = []
    for replica in replicas:
        head_ip = socket.gethostbyname(replica["nodes"][0])
        for rank, node in enumerate(replica["nodes"]):
            command = ["srun", "--nodes=1", "--ntasks=1", "--exact", "--exclusive",
                       "--cpus-per-task=" + str(plan["config"]["slurm"]["cpus_per_task"]),
                       "--gres=gpu:8", "--cpu-bind=none", "--kill-on-bad-exit=0", "--nodelist=" + node]
            if plan["container_image"]:
                command += ["--container-image=" + plan["container_image"]]
                if plan["container_mounts"]:
                    command += ["--container-mounts=" + ",".join(plan["container_mounts"])]
            cache_tag = "expgym_%s_replica%d_rank%d" % (os.environ["SLURM_JOB_ID"], replica["replica"], rank)
            command += ["bash", "-c", 'set -euo pipefail; ulimit -c 0; if [[ -n "$1" ]]; then source "$1"; fi; '
                        'export TRITON_CACHE_DIR="/tmp/${2}_triton" HF_MODULES_CACHE="/tmp/${2}_hf" TVM_FFI_CACHE_DIR="/tmp/${2}_tvm"; '
                        'shift 2; exec "$@"', "expgym-rank", plan["runtime_env"] or "", cache_tag,
                        *server_command(plan, replica, rank, head_ip)]
            commands.append({"replica": replica["replica"], "rank": rank, "node": node, "argv": command})
    write_json(directory / "deployment.json", {"schema_version": plan["schema_version"], "job_id": os.environ["SLURM_JOB_ID"],
               "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(), "replicas": replicas,
               "endpoints": [replica["base_url"] for replica in replicas], "rank_commands": commands,
               "real_smoke_passed": False, "status": "launching; endpoint existence is not readiness"})
    children, logs = [], []
    stopped = False

    def request_stop(_signum, _frame):
        nonlocal stopped
        stopped = True

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for record in commands:
            tag = "expgym_%s_replica%d_rank%d" % (os.environ["SLURM_JOB_ID"], record["replica"], record["rank"])
            env = dict(os.environ, TRITON_CACHE_DIR="/tmp/" + tag + "_triton", HF_MODULES_CACHE="/tmp/" + tag + "_hf",
                       TVM_FFI_CACHE_DIR="/tmp/" + tag + "_tvm", OMP_NUM_THREADS="8", PYTHONUNBUFFERED="1")
            log = (directory / ("replica%d-rank%d.log" % (record["replica"], record["rank"]))).open("x")
            logs.append(log)
            children.append(subprocess.Popen(record["argv"], stdout=log, stderr=subprocess.STDOUT, env=env))
        while not stopped and all(child.poll() is None for child in children):
            time.sleep(0.5)
        return 130 if stopped else 1  # A long-lived server rank exited: not a successful experiment.
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=20)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=20)
        for log in logs:
            log.close()
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        write_json(directory / "launcher_exit.json", {"rank_exit_codes": [child.returncode for child in children],
                   "stop_signal_observed": stopped, "server_request_drain_verified": False})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-allocation", help=argparse.SUPPRESS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--checkpoint")
    parser.add_argument("--sglang-bin", help="Absolute executable in the separately prepared/frozen serving runtime")
    parser.add_argument("--model")
    parser.add_argument("--context-length", type=int)
    parser.add_argument("--mem-fraction-static", type=float)
    parser.add_argument("--ep-size", type=int)
    parser.add_argument("--reasoning-parser")
    parser.add_argument("--tool-call-parser")
    parser.add_argument("--server-args-json", default="[]")
    parser.add_argument("--runtime-env", help="Optional nonsecret runtime setup shell script; no automatic environment changes")
    parser.add_argument("--container-image", help="Optional Pyxis image; runtime/data paths must be mounted explicitly")
    parser.add_argument("--container-mount", action="append", default=[])
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--output-dir", type=Path, help="Fresh shared directory: write plan and batch file, still no submission by default")
    parser.add_argument("--dry-run", action="store_true", help="Explicit spelling of the default no-submission behavior")
    parser.add_argument("--submit", action="store_true", help="Submit one exclusive 4-node allocation with sbatch")
    parser.add_argument("--allow-private-unauthenticated", action="store_true", help="Required for submit: operator confirms endpoints restricted to a trusted private network")
    args = parser.parse_args(argv)
    if args.run_allocation:
        return run_allocation(args.run_allocation)
    require(not (args.submit and args.dry_run), "--submit conflicts with --dry-run")
    require(not args.submit or args.output_dir is not None, "--submit requires a fresh --output-dir")
    require(not args.submit or args.allow_private_unauthenticated, "submit requires explicit trusted-private-network acknowledgement")
    plan = build_plan(json.loads(args.config.read_text()), checkpoint=args.checkpoint, sglang_bin=args.sglang_bin,
                      model=args.model, context_length=args.context_length, mem_fraction_static=args.mem_fraction_static,
                      ep_size=args.ep_size, reasoning_parser=args.reasoning_parser, tool_call_parser=args.tool_call_parser,
                      server_args=json.loads(args.server_args_json), runtime_env=args.runtime_env,
                      container_image=args.container_image, container_mounts=args.container_mount,
                      trust_remote_code=args.trust_remote_code)
    if args.output_dir:
        directory = args.output_dir.resolve()
        directory.mkdir(parents=True, exist_ok=False)
        launcher = directory / "serve_slurm.py"
        with launcher.open("xb") as handle:
            handle.write(Path(__file__).read_bytes())
        plan["launcher_sha256"] = hashlib.sha256(launcher.read_bytes()).hexdigest()
        write_json(directory / "plan.json", plan)
        with (directory / "serve.sbatch").open("x") as handle:
            handle.write(batch_script(plan, directory, launcher, sys.executable))
        if args.submit:
            result = subprocess.run(["sbatch", "--parsable", str(directory / "serve.sbatch")], text=True, capture_output=True)
            write_json(directory / "submission.json", {"exit_code": result.returncode, "stdout": result.stdout,
                       "stderr": result.stderr, "automatic_resubmit": False})
            require(result.returncode == 0, "sbatch failed; inspect submission.json, no automatic retry")
            print(result.stdout.strip())
            return 0
    print(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError) as error:
        print("serving plan failed: " + str(error), file=sys.stderr)
        raise SystemExit(2)
