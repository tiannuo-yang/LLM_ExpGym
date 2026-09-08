#!/usr/bin/env python3
"""One-shot A21 config/log/Slurm recheck; router metadata only, no generation."""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import httpx

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[1]
RUN = BASE / "runs/1203474"
A21 = BASE / "reports/a21_router_rawjoin_v3/final_20260908T0555Z"
FIELDS = "model_path tp_size ep_size pp_size nnodes node_rank attention_backend moe_runner_backend sampling_backend enable_deterministic_inference random_seed max_running_requests context_length disable_cuda_graph enable_dp_attention dp_size dist_init_addr chunked_prefill_size mem_fraction_static reasoning_parser tool_call_parser enable_metrics".split()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ref(path):
    return {"path": str(path), "sha256": sha(path.read_bytes())}


def describe(values):
    return {"min": min(values), "median": statistics.median(values),
            "mean": statistics.mean(values), "max": max(values), "sum": sum(values)} if values else None


def main():
    observed_start = datetime.now(timezone.utc).isoformat()
    deployment = json.loads((RUN / "deployment.json").read_text())
    capacity_path = BASE / "reports/capacity_snapshot_v2/capacity_receipt.json"
    capacity = json.loads(capacity_path.read_text())
    receipt = json.loads((A21 / "receipt.json").read_text())
    inventory_path = A21 / "response_inventory.jsonl"
    assert sha(inventory_path.read_bytes()) == receipt["artifacts"]["inventory"]["sha256"]
    rows = [json.loads(line) for line in inventory_path.read_text().splitlines()]
    usage = json.loads((A21 / "usage_runtime_receipt.json").read_text())
    start = datetime.fromisoformat(usage["first_client_attempt_started_utc"]).strftime("%Y-%m-%d %H:%M:%S")
    end = datetime.fromisoformat(usage["last_client_attempt_finished_utc"]).strftime("%Y-%m-%d %H:%M:%S")
    issues, nodes, all_uuids = [], [], []
    source_matches = {}
    for name, expected in deployment["source_sha256"].items():
        actual = sha((BASE / name).read_bytes())
        source_matches[name] = {"expected": expected, "actual": actual, "matches": actual == expected}
        if actual != expected:
            issues.append("source mismatch: " + name)
    for replica in range(4):
        for rank in range(2):
            tag = f"replica{replica}-rank{rank}"
            launch_path, hardware_path, log_path = [RUN / (tag + suffix) for suffix in ("-launch.json", "-hardware.json", ".log")]
            launch, hardware = json.loads(launch_path.read_text()), json.loads(hardware_path.read_text())
            raw_log = log_path.read_bytes()
            lines = raw_log.decode(errors="replace").splitlines()
            found = [(number, line) for number, line in enumerate(lines, 1) if "server_args=ServerArgs(" in line]
            if len(found) != 1:
                issues.append(f"{tag} expected one startup ServerArgs, got {len(found)}")
            number, line = found[0]
            call = ast.parse(line.split("server_args=", 1)[1], mode="eval").body
            args = {x.arg: ast.literal_eval(x.value) for x in call.keywords if x.arg in FIELDS}
            expected = {"model_path": deployment["profile"]["checkpoint"], "tp_size": 16, "ep_size": 16,
                        "pp_size": 1, "nnodes": 2, "node_rank": rank, "attention_backend": "fa3",
                        "moe_runner_backend": "marlin", "sampling_backend": "pytorch",
                        "enable_deterministic_inference": True, "random_seed": 42,
                        "max_running_requests": 64, "context_length": 524288,
                        "disable_cuda_graph": False, "dp_size": 1, "enable_dp_attention": False,
                        "reasoning_parser": "kimi_k3", "tool_call_parser": "kimi_k3"}
            mismatches = {k: {"expected": v, "actual": args.get(k)} for k, v in expected.items() if args.get(k) != v}
            if mismatches:
                issues.append(f"{tag} ServerArgs mismatch")
            gpus = hardware["nvidia_smi"]["gpus"]
            uuids = [g["uuid"] for g in gpus]
            all_uuids.extend(uuids)
            hardware_ok = hardware["passed"] and len(uuids) == 8 and len(set(uuids)) == 8 and all(g["name"] == "NVIDIA H200" for g in gpus)
            if not hardware_ok:
                issues.append(f"{tag} hardware gate failure")
            tp_ranks = sorted({int(x) for x in re.findall(r"\bTP(\d+)", "\n".join(lines))})
            if tp_ranks != list(range(rank * 8, rank * 8 + 8)):
                issues.append(f"{tag} TP log rank coverage mismatch")
            cap_lines = [{"line": n, "text": text} for n, text in enumerate(lines, 1) if "max_total_num_tokens=" in text and "TP0 EP0" in text]
            samples, prefill_samples = [], []
            for n, text in enumerate(lines, 1):
                m = re.search(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) TP0 EP0\] Decode batch, #running-req: (\d+).*gen throughput \(token/s\): ([\d.]+), #queue-req: (\d+)", text)
                if m and start <= m[1] <= end:
                    samples.append({"line": n, "utc": m[1], "running": int(m[2]), "tokens_per_second": float(m[3]), "queued": int(m[4])})
                m = re.search(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) TP0 EP0\] Prefill batch, #new-seq: (\d+), #new-token: (\d+), #cached-token: (\d+)", text)
                if m and start <= m[1] <= end:
                    prefill_samples.append({"line": n, "utc": m[1], "sequences": int(m[2]), "new_tokens": int(m[3]), "cached_tokens": int(m[4])})
            error_lines = [{"line": n, "text": text[:700]} for n, text in enumerate(lines, 1)
                           if re.search(r"Traceback|CUDA out of memory|\bERROR\b|NCCL.*[Ee]rror", text)]
            if error_lines:
                issues.append(f"{tag} error-like log lines require review")
            nodes.append({"replica": replica, "node_rank": rank, "node": hardware["node"],
                          "launch": ref(launch_path), "hardware": ref(hardware_path),
                          "log_snapshot": {"path": str(log_path), "sha256": sha(raw_log), "bytes": len(raw_log)},
                          "launch_command": launch["command"], "server_args_line": number,
                          "server_args_line_sha256": sha(line.encode()), "selected_server_args": args,
                          "expected_parameter_mismatches": mismatches, "logged_tp_rank_coverage": tp_ranks,
                          "startup_hardware_gate_pass": hardware_ok, "gpu_uuids": uuids,
                          "gpu_names": dict(Counter(g["name"] for g in gpus)),
                          "gpu_memory_mib": sorted({g["memory_total_mib"] for g in gpus}),
                          "driver_versions": sorted({g["driver_version"] for g in gpus}),
                          "startup_capacity_lines": cap_lines,
                          "a21_decode_log_sample_count": len(samples),
                          "a21_sampled_running_counts": dict(Counter(s["running"] for s in samples)),
                          "a21_sampled_queue_max": max((s["queued"] for s in samples), default=None),
                          "a21_logged_decode_throughput_samples": describe([s["tokens_per_second"] for s in samples]),
                          "a21_prefill_log_sample_count": len(prefill_samples),
                          "a21_prefill_samples_with_cached_tokens": sum(s["cached_tokens"] > 0 for s in prefill_samples),
                          "error_like_lines": error_lines})
    if len(all_uuids) != 64 or len(set(all_uuids)) != 64:
        issues.append("physical GPU UUID coverage is not exactly 64 distinct startup-measured GPUs")
    per_replica = []
    for replica in range(4):
        subset = [r for r in rows if r["router_receipt"]["replica"] == replica]
        client_times, router_times, prompts, completions, reasonings = [], [], [], [], []
        for row in subset:
            p = Path(row["dump"])
            assert sha(p.read_bytes()) == row["dump_sha256"]
            d = json.loads(p.read_text())
            client_times.append(d["wall_time_seconds"])
            router_times.append(row["router_receipt"]["elapsed_seconds"])
            prompts.append(d["response_json"]["usage"]["prompt_tokens"])
            completions.append(d["response_json"]["usage"]["completion_tokens"])
            reasonings.append(d["response_json"]["usage"]["reasoning_tokens"])
        per_replica.append({"replica": replica, "requests": len(subset), "prompt_tokens": sum(prompts),
                            "completion_tokens": sum(completions), "reasoning_tokens": sum(reasonings),
                            "client_http_wall_seconds": describe(client_times), "router_wall_seconds": describe(router_times),
                            "completion_tokens_divided_by_http_wall_sum": sum(completions) / sum(client_times),
                            "peak_completed_router_interval_concurrency": receipt["completed_router_interval_peak_per_replica"][str(replica)]})
    slurm = {}
    for name, command in {"job": ["scontrol", "show", "job", "1203474"], "steps": ["scontrol", "show", "step", "1203474"]}.items():
        r = subprocess.run(command, capture_output=True, text=True, timeout=20)
        slurm[name] = {"command": command, "exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    step_blocks = slurm["steps"]["stdout"].split("\n\n")
    model_steps = [block for block in step_blocks if re.search(r"replica\d-rank\d\.log", block)]
    if len(model_steps) != 8 or not all("State=RUNNING" in b and "gres/gpu=8" in b for b in model_steps):
        issues.append("Slurm did not report eight running eight-GPU model steps")
    # The only HTTP request made by this collector is the router metadata path.
    response = httpx.get(deployment["router_url"] + "/health", timeout=10, trust_env=False,
                         headers={"Authorization": "Bearer " + Path(deployment["router_api_key_file"]).read_text().strip()})
    health = response.json()
    selected_health = {"observed_utc": datetime.now(timezone.utc).isoformat(), "http_status": response.status_code,
                       "healthy_replicas": health.get("healthy_replicas"),
                       "backends": [{k: b.get(k) for k in ("replica", "inflight", "health_error", "cleanup_quarantined")} for b in health["backends"]]}
    if response.status_code != 200 or health.get("healthy_replicas") != 4:
        issues.append("router metadata is not 4/4 healthy")
    report = {"schema_version": "portable_eval.a21_serving_config_recheck.v1", "observed_start_utc": observed_start,
              "observed_end_utc": datetime.now(timezone.utc).isoformat(), "job_id": "1203474",
              "status": "NO_OBVIOUS_CONFIG_MISMATCH_IN_CHECKED_SCOPE" if not issues else "REVIEW_REQUIRED",
              "issues": issues, "generation_requests": 0, "new_slurm_steps_or_allocations": 0,
              "bound_sources": {"deployment": ref(RUN / "deployment.json"), "ready_metadata": ref(RUN / "ready_metadata_20260908T031954Z.json"),
                                "capacity": ref(capacity_path), "a21_byte_join": ref(A21 / "receipt.json"),
                                "a21_inventory": ref(inventory_path), "a21_usage": ref(A21 / "usage_runtime_receipt.json"),
                                "collector": ref(Path(__file__))},
              "source_matches_original_deployment": source_matches, "allocation_nodes": deployment["nodes"],
              "startup_measured_unique_gpu_uuids": len(set(all_uuids)), "node_reports": nodes,
              "current_slurm": slurm, "current_router_metadata": selected_health,
              "a21_window_utc": [start, end], "a21_per_replica": per_replica,
              "a21_usage_totals": usage["response_reported_token_sums"], "a21_harness_seconds": usage["harness_elapsed_seconds"],
              "a21_peak_concurrency": receipt["completed_router_interval_peak_concurrency"],
              "reasoning_fraction_of_completion": usage["response_reported_token_sums"]["reasoning_tokens"] / usage["response_reported_token_sums"]["completion_tokens"],
              "capacity_reference": {"configuration": capacity["configuration"], "measured_per_replica": capacity["measured_per_replica"]},
              "limits": [
                  "Eight nodes / 64 GPUs are four independent replicas, each TP16/EP16/PP1 across two nodes. One sequential request does not use all 64 GPUs; four replicas principally provide concurrency capacity.",
                  "Current Slurm running-step evidence, startup ServerArgs/TP-rank logs, hardware receipts, frozen-source hashes and current router metadata were cross-checked. Direct current GPU worker PID/command-line inspection was not obtained: login-node scontrol listpids reported no job on that node and SSH host-key verification rejected access. No security check was bypassed and no extra srun step was created.",
                  "The 64 H200 UUIDs are startup physical/CUDA measurements. No fresh GPU utilization or hardware probe was issued; drained-state utilization would not describe A21 execution utilization.",
                  "Router metadata readiness and successful transport do not prove optimal kernels, topology or throughput. Exact deterministic output repeatability previously failed; this run uses seed_labels_only.",
                  "A21 completed-interval peak was four requests globally and one per replica. This workload did not test replica batching or saturated capacity. Backend effective running-request cap 47 is not the active-request count.",
                  "HTTP wall includes queuing, tokenization/input prefill, decoding and networking. Response usage contains no TTFT or per-request pure-decode timer. Ratios of completion tokens to HTTP wall are end-to-end rates, not pure decode speed.",
                  "Decode/prefill log samples are coarse periodic server observations with no unique per-request attribution. They cannot provide an exact request-level time decomposition or quantify communication/kernel overhead.",
                  "Long reasoning is observed output workload, not a measured counterfactual slowdown: its fraction must not be converted directly into a promised speedup from disabling thinking.",
                  "The accepted FA3/Marlin/PyTorch deterministic candidate was not compared against alternate attention/quantization/topology configurations under a controlled performance benchmark. No claim of optimal serving configuration is made.",
              ]}
    output = OUT / "receipt.json"
    with output.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"path": str(output), "sha256": sha(output.read_bytes()), "status": report["status"],
                      "issues": issues, "per_replica": per_replica, "health": selected_health}, indent=2))


if __name__ == "__main__":
    main()
