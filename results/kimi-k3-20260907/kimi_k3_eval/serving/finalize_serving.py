"""Summarize already completed serving evidence without generating new tokens."""
import datetime
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
deployment = json.loads((BASE / "deployment.json").read_text())
run_dir = BASE / "runs" / deployment["job_id"]
summary = json.loads((run_dir / "smoke/summary.json").read_text())
long_probe = json.loads((run_dir / "smoke/long_context_100000.json").read_text())
padding = json.loads((BASE / "manifests/padding-tests-passed.json").read_text())
native = [item for item in summary if item["name"].startswith("replica")]
assert len(native) == 4 and all(item["answer_42"] and item["finish_reason"] == "stop" for item in native)
assert long_probe["passcode_retrieved"] and not long_probe["content_has_pad_storm"]
assert long_probe["finish_reason"] == "stop" and long_probe["prompt_tokens"] >= 90000
assert padding["tests"] == 340 and padding["failures"] == padding["errors"] == 0
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open(deployment["router_url"] + "/health", timeout=10) as response:
    health = json.load(response)
assert health["healthy_replicas"] == 4
with opener.open(deployment["base_url"] + "/models", timeout=10) as response:
    models = json.load(response)
(run_dir / "models.json").write_text(json.dumps(models, indent=2) + "\n")
frozen = subprocess.check_output([
    "/lustrefs/users/chufan.shi/.local/bin/uv", "pip", "freeze", "--python",
    str(BASE / "independent/.venv/bin/python")], text=True)
(BASE / "manifests/final-uv-freeze.txt").write_text(frozen)
record = {
    "accepted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "ready_for_benchmark": True,
    "job_id": deployment["job_id"],
    "base_url": deployment["base_url"],
    "gpu_count": 64,
    "nodes": deployment["nodes"],
    "replicas": 4,
    "parallelism_per_replica": {"nodes": 2, "tp": 16, "ep": 16},
    "sglang_version": "0.5.16+pr32477",
    "python_environment": str(BASE / "independent/.venv"),
    "python_package_inheritance": False,
    "distribution_count": 311,
    "final_freeze_sha256": hashlib.sha256(frozen.encode()).hexdigest(),
    "padding_regression": {"passed": 340, "failures": 0, "seconds": 144.85},
    "native_replica_probes_passed": 4,
    "total_short_probes": 7,
    "long_context": {key: long_probe[key] for key in ["prompt_tokens", "elapsed_seconds", "passcode_retrieved", "content_has_pad_storm", "finish_reason"]},
    "extra_llm_probes_active": False,
    "router_health": "Fixed five-second interval after each round; idle /health emits one token, busy probes ignored and not logged as request metrics",
    "model_protocol": "Server native default is thinking enabled; native multi-turn requests preserve complete assistant messages including reasoning_content and tool_calls",
    "benchmark_request_policy": {
        "chat_template_kwargs": {"thinking": False},
        "intent": "Align ExpGym/PoolAct benchmark requests with the paper's non-thinking setting",
        "deviation_from_k3_recommendation": True,
        "deviation": "Per-request thinking=false differs from K3's recommended always-thinking trained usage; the server's native default remains unchanged",
    },
    "thinking_false_probe": "Low-level thinking=false produced valid content without reasoning. This per-request mode is selected for the benchmark; the server's native request default remains thinking enabled",
    "evidence_directory": str(run_dir / "smoke"),
}
(BASE / "ACCEPTANCE.json").write_text(json.dumps(record, indent=2) + "\n")
(run_dir / "acceptance.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
