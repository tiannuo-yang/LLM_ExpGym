"""Persist the actual eight allocated nodes and four replica endpoints."""
import datetime
import json
import os
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
nodes = sys.argv[2:]
assert len(nodes) == 8
record = {
    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "job_id": os.environ["SLURM_JOB_ID"],
    "account": "k2p",
    "partition": "higherprio",
    "nodes": nodes,
    "gpu_count": 64,
    "model": "kimi-k3",
    "checkpoint": "/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3",
    "python_environment": str(Path(__file__).resolve().parent / "independent/.venv"),
    "sglang_version": "0.5.16+pr32477",
    "python_package_inheritance": False,
    "base_url": f"http://{nodes[0]}:30141/v1",
    "router_url": f"http://{nodes[0]}:30141",
    "replicas": [
        {"replica": i, "nodes": nodes[2*i:2*i+2], "tp": 16, "ep": 16,
         "url": f"http://{nodes[2*i]}:30140"} for i in range(4)
    ],
}
(run_dir / "deployment.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
