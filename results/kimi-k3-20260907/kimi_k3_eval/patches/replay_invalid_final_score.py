#!/usr/bin/env python3
"""Read-only replay of a retained answer against a selected source tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--dump", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
data = root / "LLM_ExpGym/data/hpo_tuning"
os.environ.update(HPOBENCH_ROOT=str(data / "HPOBench"), XDG_DATA_HOME=str(data / "hpobench_data"),
                  XDG_CACHE_HOME=str(data / "hpobench_cache"),
                  XDG_CONFIG_HOME=str(root / "kimi_k3_eval/data_runtime/hpobench_config"),
                  PYTHONNOUSERSITE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
sys.path.insert(0, str(args.repo.absolute()))
import ConfigSpace
from expgym.task_tuning import _load_hpobench, evaluate_hpobench_action
from scripts.run_paper_sweep import _score_result

dump = json.loads(args.dump.read_text())
message = dump["response_json"]["choices"][0]["message"]["content"]
assert message.startswith("Answer: ")
answer = message[len("Answer: "):]
config = json.loads(answer)
task = _load_hpobench("hpobench:nasbench101:B")
guard = Mock(side_effect=AssertionError("invalid input must never call backend"))
guarded_task = SimpleNamespace(name=task.name, config_space=task.config_space,
                               fidelity=task.fidelity, benchmark=SimpleNamespace(objective_function=guard))
result = {"answer": answer, "answer_perf": None, "eval_records": [], "api_calls": 2,
          "evaluations": 0, "total_overhead": 0.0, "tool_records": []}
check = _score_result(result, {"evaluate_config": lambda payload: evaluate_hpobench_action(guarded_task, payload)}, None)
print(json.dumps({"classification": "offline retained-answer validation, not a new Kimi-K3 run",
                  "python": sys.version, "configspace": ConfigSpace.__version__,
                  "source_tree": str(args.repo.absolute()), "task": task.name,
                  "source_files": {name: hashlib.sha256((args.repo / name).read_bytes()).hexdigest()
                                   for name in ("expgym/task_tuning.py", "scripts/run_paper_sweep.py")},
                  "dump_path": str(args.dump.absolute()), "dump_sha256": hashlib.sha256(args.dump.read_bytes()).hexdigest(),
                  "request_id": dump["request_id"], "client_id": dump["client_id"], "context": dump["context"],
                  "unknown_keys": sorted(set(config) - {hp.name for hp in task.config_space.get_hyperparameters()}),
                  "score_check": check, "result": result, "backend_objective_calls": guard.call_count},
                 ensure_ascii=False, allow_nan=False, indent=2))
