"""CPU-only synthetic transport fixtures; never invokes the model or runner."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


class Collectors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="a21-collector-cpu-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "synthetic-a21"
        self.manifest = json.loads((STUDY / "pilot_runs/k3_a21_1203474_v3/manifest.json").read_text())
        self.jobs = self.manifest["identity"]["jobs"]
        self.completion = {
            "executed": True, "passed": True, "unstarted": [],
            "validated_trace_count": 21, "elapsed_seconds_including_preflight_resume": 25,
            "results": [{"job_id": j["id"], "passed": True, "run": {"exit_code": 0}} for j in self.jobs],
        }
        self.dumps, self.rows = [], []
        for i, job in enumerate(self.jobs):
            payload = {"model": "synthetic-no-network", "unique_job": i, "max_tokens": 32768}
            response = {"choices": [{"finish_reason": "stop"}], "usage": {
                "prompt_tokens": 10, "completion_tokens": 4, "reasoning_tokens": 3,
                "total_tokens": 14, "prompt_tokens_details": None,
            }}
            raw = json.dumps(response)
            record = {
                "schema_version": "expgym.api_attempt.v1", "request_id": "request-%d" % i,
                "generation_id": "generation-%d" % i, "state": "success", "attempt": 1,
                "will_retry": False, "http_status": None, "request_payload": payload,
                "response_raw": raw, "response_json": response, "wall_time_seconds": 1,
                "started_at_utc": "2026-09-08T00:00:%02d+00:00" % i,
                "finished_at_utc": "2026-09-08T00:00:%02d+00:00" % (i + 1),
            }
            self.dumps.append((self.run / "dumps" / job["id"] / (record["request_id"] + ".json"), record))
            self.rows.append({
                "payload_sha256": hashlib.sha256(json.dumps(payload).encode()).hexdigest(),
                "response_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "replica": i % 4, "complete": True, "upstream_close_started": True,
                "upstream_close_completed": True, "upstream_close_error": None,
                "http_status": 200, "started_unix": 1788825600 + i, "elapsed_seconds": 1,
            })

    def collect(self):
        write_json(self.run / "manifest.json", self.manifest)
        write_json(self.run / "execution.json", self.completion)
        for path, data in self.dumps:
            write_json(path, data)
        router = self.root / "router.jsonl"
        router.write_text("".join(json.dumps(row) + "\n" for row in self.rows))
        source = STUDY.parent / "LLM_ExpGym/expgym/llm_clients.py"
        self.out = self.root / "final"
        command = [sys.executable, "-B", str(HERE / "join.py"),
                   "--scenario-root", str(self.run), "--router-jsonl", str(router),
                   "--completion-receipt", str(self.run / "execution.json"),
                   "--static-acceptance", str(STUDY / "validation/static_acceptance_v3.json"),
                   "--client-source", str(source), "--router-source", str(STUDY / "serving/router.py"),
                   "--capacity-receipt", str(STUDY / "serving/reports/capacity_snapshot_v2/capacity_receipt.json"),
                   "--out", str(self.out)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertTrue((self.out / "receipt.json").is_file(), result.stderr)
        return result, json.loads((self.out / "receipt.json").read_text())

    def test_full_byte_join_and_a21_elapsed_key(self):
        result, receipt = self.collect()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(receipt["matched_router_count"], 21)
        usage = subprocess.run([sys.executable, "-B", str(HERE / "summarize_usage.py"), "--final", str(self.out)], capture_output=True, text=True)
        self.assertEqual(usage.returncode, 0, usage.stderr)
        data = json.loads((self.out / "usage_runtime_receipt.json").read_text())
        self.assertEqual(data["response_reported_token_sums"]["total_tokens"], 294)
        self.assertEqual(data["harness_elapsed_seconds"], 25)

    def test_missing_completion_job_fails(self):
        self.completion["results"].pop()
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_boolean_exit_code_rejected(self):
        self.completion["results"][0]["run"]["exit_code"] = False
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_boolean_attempt_index_rejected(self):
        self.dumps[0][1]["attempt"] = True
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_changed_harness_hash_fails(self):
        hashes = self.manifest["identity"]["harness_files"]
        hashes[next(iter(hashes))] = "0" * 64
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_changed_acceptance_hash_fails(self):
        self.manifest["identity"]["static_acceptance"]["sha256"] = "0" * 64
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_ambiguous_router_pair_fails(self):
        self.rows.append(copy.deepcopy(self.rows[0]))
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_unclosed_http_response_fails(self):
        self.rows[0]["upstream_close_completed"] = False
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_missing_dump_job_fails(self):
        self.dumps.pop()
        self.assertNotEqual(self.collect()[0].returncode, 0)

    def test_unknown_usage_does_not_become_zero(self):
        self.dumps[0][1]["response_json"]["usage"]["reasoning_tokens"] = None
        raw = json.dumps(self.dumps[0][1]["response_json"])
        self.dumps[0][1]["response_raw"] = raw
        self.rows[0]["response_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
        self.assertEqual(self.collect()[0].returncode, 0)
        usage = subprocess.run([sys.executable, "-B", str(HERE / "summarize_usage.py"), "--final", str(self.out)], capture_output=True, text=True)
        self.assertNotEqual(usage.returncode, 0)
        self.assertFalse((self.out / "usage_runtime_receipt.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
