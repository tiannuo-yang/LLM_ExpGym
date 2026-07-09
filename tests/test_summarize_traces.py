import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


_SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "summarize_traces.py",
)
_spec = importlib.util.spec_from_file_location("summarize_traces", _SCRIPT_PATH)
summarize_traces = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(summarize_traces)


class SummarizeTracesTest(unittest.TestCase):
    def test_summarizes_tuning_trace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            path.write_text(
                json.dumps(
                    {
                        "job": {
                            "scenario": "tuning",
                            "tuning_task": "neural_network_training",
                            "model_id": "openai/gpt-4.1-nano",
                            "cost_regime": "cost_tight",
                        },
                        "answer_perf": 0.812345678,
                        "score_check": {"ok": True},
                        "evaluations": 2,
                        "api_calls": 3,
                        "aborted": False,
                        "wall_time_seconds": 12.34,
                    }
                ),
                encoding="utf-8",
            )

            row = summarize_traces.summarize_trace(path)

            self.assertEqual(row["scenario"], "tuning")
            self.assertEqual(row["item"], "neural_network_training")
            self.assertEqual(row["model"], "openai/gpt-4.1-nano")
            self.assertEqual(row["score_check"], "ok")
            self.assertEqual(summarize_traces.format_value(row["answer_perf"]), "0.812346")

    def test_iter_trace_files_recurses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            trace = nested / "trace.json"
            trace.write_text("{}", encoding="utf-8")
            (nested / "not_trace.txt").write_text("x", encoding="utf-8")

            files = summarize_traces.iter_trace_files([root])

            self.assertEqual(files, [trace])

    def test_summarizes_audit_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit.json"
            path.write_text(
                json.dumps(
                    {
                        "job": {
                            "scenario": "evidence_audit",
                            "cc_split": "cc-large",
                            "question_index": 9,
                            "model_id": "openai/gpt-4.1-nano",
                            "cost_regime": "cost_tight",
                        },
                        "answer_perf": 0.35294117647058826,
                        "answer_metrics": {
                            "label_acc": 0.35294117647058826,
                            "evidence_acc": 0.23529411764705882,
                            "verification_eff": 0.0,
                        },
                        "score_check": {"ok": True},
                    }
                ),
                encoding="utf-8",
            )

            row = summarize_traces.summarize_trace(path)

            self.assertEqual(row["item"], "cc-large[9]")
            self.assertEqual(summarize_traces.format_value(row["label_acc"]), "0.352941")
            self.assertEqual(summarize_traces.format_value(row["evidence_acc"]), "0.235294")
            self.assertEqual(summarize_traces.format_value(row["verification_eff"]), "0.000000")


if __name__ == "__main__":
    unittest.main()
