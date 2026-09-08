import json
import tempfile
import unittest
from pathlib import Path

from expgym.react_loop import FakeLLM, run_react_loop
from expgym.trace_v2 import (
    build_trace_v2,
    load_trace_v2,
    materialize_llm_input,
    validate_trace_v2,
    write_trace_v2,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _runtime():
    return {
        "run": {
            "seed": 1206,
            "backend": {
                "name": "sub2api",
                "base_url": "http://127.0.0.1:8080/v1/chat/completions",
                "auth_configured": True,
                "extra_header_names": [],
            },
            "model": {"id": "gpt-5.4"},
            "generation": {"temperature": 0.0, "top_p": 1.0},
            "prompt_cache": {"key": "test-task-v1", "scope": "run"},
            "transport": {"timeout_seconds": 30, "max_retries": 10},
        },
        "limits": {
            "max_steps": 3,
            "max_evaluations": 2,
            "max_prompt_tokens": None,
            "max_context_tokens": None,
        },
    }


class TraceV2Test(unittest.TestCase):
    def _build(self):
        llm = FakeLLM(
            plan=[("evaluate_config", '{"x": 1}')],
            final_answer='{"x": 1}',
        )
        result = run_react_loop(
            llm=llm,
            tools={"evaluate_config": lambda _argument: (0.8, 12.0)},
            context="Choose x.",
            max_steps=3,
            max_evals=2,
            capture_trace_v2=True,
        )
        result["job"] = {
            "scenario": "tuning",
            "model_alias": "gpt-5.4",
            "model_id": "gpt-5.4",
            "cost_regime": "cost_tight",
            "rep": 0,
            "seed": 1206,
            "tuning_task": "neural_network_training",
            "question_index": 0,
            "data_source": None,
            "cc_split": "cc-large",
            "hypothesis_order": None,
        }
        result["cost_regime_resolved"] = {
            "mode": "time_aware",
            "c_base": 100.0,
            "time_budget": 300.0,
        }
        result["score_check"] = {"ok": True}
        result["wall_time_seconds"] = 0.5
        result["_trace_v2_runtime"] = _runtime()
        return result, build_trace_v2(result, repo_root=REPO_ROOT)

    def test_normalizes_without_legacy_duplicates(self):
        result, trace = self._build()
        validate_trace_v2(trace)
        self.assertEqual(trace["schema"]["version"], "2.0.0")
        for legacy in ("steps", "tool_records", "eval_records", "answer"):
            self.assertNotIn(legacy, trace)
        self.assertEqual(len(trace["llm_calls"]), result["api_calls"])
        self.assertEqual(len(trace["tool_calls"]), result["evaluations"])
        self.assertTrue(
            any("content_ref" in message for message in trace["messages"])
        )
        repository = trace["provenance"]["repository"]
        self.assertIn("source_tree_sha256", repository)
        self.assertIn("environment", trace["provenance"])
        if repository["dirty"]:
            self.assertNotIn("env.example", repository["changed_files"])

    def test_materializes_exact_llm_inputs(self):
        result, trace = self._build()
        captured = result["_trace_v2_capture"]["llm_calls"]
        for index, call in enumerate(trace["llm_calls"]):
            expected = captured[index]["input_messages"]
            actual = materialize_llm_input(trace, call["id"])
            self.assertEqual(actual, expected)

    def test_missing_cache_usage_remains_unreported(self):
        _result, trace = self._build()
        for call in trace["llm_calls"]:
            cache = call["usage"]["cache"]
            self.assertFalse(cache["reported"])
            self.assertIsNone(cache["read_tokens"])
            self.assertIsNone(cache["write_tokens"])

    def test_atomic_write_and_load(self):
        _result, trace = self._build()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            write_trace_v2(path, trace)
            loaded = load_trace_v2(path)
            self.assertEqual(loaded, trace)
            self.assertEqual(json.loads(path.read_text()), trace)

    def test_rejects_dangling_message_reference(self):
        _result, trace = self._build()
        trace["llm_calls"][0]["input_message_ids"] = ["missing"]
        with self.assertRaisesRegex(ValueError, "unknown input message"):
            validate_trace_v2(trace)


if __name__ == "__main__":
    unittest.main()
