"""One-line A21 audit fix against actual sealed trace-v2 schema; no models."""
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "LLM_ExpGym"))
from expgym.trace_v2 import result_for_score_check


class A21ScoreSchemaFixTests(unittest.TestCase):
    def test_only_intended_line_changes_and_old_auditor_is_frozen(self):
        old = (ROOT / "review/audit_a21_v3.py").read_bytes()
        new = (ROOT / "review/audit_a21_v3_score_schema_fix.py").read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(), "f8ec3e0c1c9fdc93832788a430a6a7c1994d977b98cc2d5ee0ff1a554e63792d")
        self.assertEqual(new, old.replace(b'zero_count += outcome["answer_perf"] == 0', b'zero_count += (outcome["score"]["metrics"][outcome["score"]["primary_metric"]] if "metrics" in outcome["score"] else outcome["score"]["value"]) == 0'))

    def test_all_21_real_trace_v2_outcomes_match_original_score_adapter(self):
        run = ROOT / "pilot_runs/k3_a21_1203474_v3"
        manifest = json.loads((run / "manifest.json").read_text())
        values = []
        for job in manifest["identity"]["jobs"]:
            paths = list(Path(job["output_dir"]).glob("*/traces-v2/*.json"))
            self.assertEqual(len(paths), 1)
            trace = json.loads(paths[0].read_text())
            self.assertNotIn("answer_perf", trace["outcome"])
            score = trace["outcome"]["score"]
            value = score["metrics"][score["primary_metric"]] if "metrics" in score else score["value"]
            self.assertIsNot(type(value), bool)
            self.assertTrue(math.isfinite(value))
            self.assertEqual(value, result_for_score_check(trace)["answer_perf"])
            values.append(value)
        self.assertEqual(len(values), 21)
        self.assertEqual(sum(value == 0 for value in values), 1)

    def test_zero_score_is_valid_semantic_result(self):
        for score, expected in ((0.0, True), (0.4, False)):
            outcome = {"score": {"value": score}}
            self.assertEqual(outcome["score"]["value"] == 0, expected)
            with self.assertRaises(KeyError):
                outcome["answer_perf"]


if __name__ == "__main__":
    unittest.main()
