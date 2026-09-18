import copy
import json
import tempfile
import unittest
from pathlib import Path

from expgym.react_loop import FakeLLM, LLMOutput, run_react_loop
from expgym.trace_v2 import (
    build_trace_v2,
    load_trace_v2,
    materialize_llm_input,
    materialize_message,
    result_for_score_check,
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

    def test_rejects_malformed_root_and_every_record_container(self):
        _result, baseline = self._build()
        for value in (None, [], "trace", True, 12):
            with self.subTest(root=value), self.assertRaises(ValueError):
                validate_trace_v2(value)
        for field in ("schema", "provenance", "run", "task", "outcome", "timing"):
            for value in (None, [], ["not-an-outcome-object"], "object", True):
                trace = copy.deepcopy(baseline)
                trace[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_trace_v2(trace)
        for field in ("messages", "llm_calls", "tool_calls"):
            for value in (None, {}, "array", True, [None], [42], [[]]):
                trace = copy.deepcopy(baseline)
                trace[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    validate_trace_v2(trace)

    def test_rejects_nested_container_corruption(self):
        _result, baseline = self._build()
        paths = [("outcome", "score"), ("outcome", "validation"),
                 ("llm_calls", 0, "usage"), ("llm_calls", 0, "usage", "cache"),
                 ("run", "backend"), ("run", "model"), ("task", "budget"),
                 ("task", "limits"), ("provenance", "repository")]
        for path in paths:
            for value in (None, [], "container", True):
                trace = copy.deepcopy(baseline)
                parent = trace
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                with self.subTest(path=path, value=value), self.assertRaises(ValueError):
                    validate_trace_v2(trace)

    def test_rejects_wrong_scalar_domains_and_validation_claims(self):
        _result, baseline = self._build()
        cases = [
            (("trace_id",), True), (("trace_id",), ""),
            (("outcome", "status"), "success"), (("outcome", "termination_reason"), "invented"),
            (("outcome", "answer_source"), "invented"),
            (("outcome", "validation", "passed"), "false"),
            (("outcome", "validation", "passed"), 1),
            (("outcome", "validation", "passed"), False),
            (("outcome", "validation", "method"), "trust_me"),
            (("outcome", "score", "value"), True),
            (("outcome", "score", "value"), float("nan")),
            (("timing", "wall_time_seconds"), -1),
            (("llm_calls", 0, "input_message_ids"), ""),
            (("llm_calls", 0, "request_attempts"), True),
            (("llm_calls", 0, "request_attempts"), 0),
            (("llm_calls", 0, "latency_seconds"), float("inf")),
            (("llm_calls", 0, "forced"), 1),
            (("llm_calls", 0, "usage", "input_tokens"), True),
            (("llm_calls", 0, "usage", "output_tokens"), 2.5),
            (("llm_calls", 0, "usage", "cache", "reported"), "false"),
            (("llm_calls", 0, "usage", "cache", "read_tokens"), -1),
            (("tool_calls", 0, "visible_to_model"), "false"),
            (("tool_calls", 0, "simulated_cost_seconds"), -1),
        ]
        for path, value in cases:
            trace = copy.deepcopy(baseline)
            parent = trace
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            with self.subTest(path=path, value=value), self.assertRaises(ValueError):
                validate_trace_v2(trace)
        for field in ("score", "validation", "status", "termination_reason"):
            trace = copy.deepcopy(baseline)
            del trace["outcome"][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                validate_trace_v2(trace)
        trace = copy.deepcopy(baseline)
        trace["run"]["protocol"] = {"tool_protocol": ["native"]}
        with self.assertRaises(ValueError):
            validate_trace_v2(trace)

    def test_reference_requires_actual_matching_observation(self):
        _result, baseline = self._build()
        for field in ("observation", "result_message_id"):
            trace = copy.deepcopy(baseline)
            if field == "observation":
                del trace["tool_calls"][0][field]
            else:
                trace["tool_calls"][0][field] = trace["messages"][0]["id"]
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_trace_v2(trace)

    def test_graph_augmented_observation_round_trips_exactly(self):
        result, _trace = self._build()
        captured = result["_trace_v2_capture"]
        message_index = captured["tool_calls"][0]["result_message_index"]
        result["messages"][message_index]["content"] += "\nGRAPH: another agent explored y."
        captured["llm_calls"][1]["input_messages"][message_index] = copy.deepcopy(result["messages"][message_index])
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertNotIn("content_ref", trace["messages"][message_index])
        self.assertEqual(materialize_llm_input(trace, "llm0002"), captured["llm_calls"][1]["input_messages"])
        self.assertIn("GRAPH:", materialize_message(trace, trace["messages"][message_index]["id"])["content"])

    def test_full_native_wire_objects_and_request_only_interning(self):
        result, _trace = self._build()
        tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "evaluate_config", "arguments": '{"x":1}'}}]
        native = {"role": "assistant", "content": None, "reasoning_content": "private reason",
                  "reasoning": {"signature": "opaque"}, "tool_calls": tool_calls}
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "question"},
                    native, {"role": "tool", "content": "Observation", "tool_call_id": "call_1", "name": "evaluate_config"},
                    {"role": "assistant", "content": '{"x":1}', "reasoning_content": None}]
        result["messages"] = copy.deepcopy(messages)
        first, second = result["_trace_v2_capture"]["llm_calls"]
        first.update(input_messages=copy.deepcopy(messages[:2]), output_message_index=2, output_message=copy.deepcopy(native))
        second.update(input_messages=copy.deepcopy(messages[:4]), output_message_index=4, output_message=copy.deepcopy(messages[4]))
        # Same role/content, different reasoning and call ID: both must become
        # complete request-only objects, not aliases of the history record.
        second["input_messages"][2]["reasoning_content"] = "different reason"
        second["input_messages"][2]["tool_calls"][0]["id"] = "call_2"
        second["input_messages"][3]["tool_call_id"] = "call_2"
        captured_tool = result["_trace_v2_capture"]["tool_calls"][0]
        captured_tool.update(request_message_index=2, result_message_index=3, observation="Observation")
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual([materialize_message(trace, "m%04d" % (index + 1)) for index in range(5)], messages)
        self.assertEqual(materialize_llm_input(trace, "llm0002"), second["input_messages"])
        self.assertTrue(all(mid.startswith("x") for mid in trace["llm_calls"][1]["input_message_ids"][2:]))
        self.assertIsNone(trace["messages"][2]["content"])
        self.assertEqual(trace["llm_calls"][0]["output_message"], native)
        second["input_messages"][2]["tool_calls"][0]["id"] = "later-mutation"
        self.assertEqual(materialize_llm_input(trace, "llm0002")[2]["tool_calls"][0]["id"], "call_2")

    def test_raw_native_invalid_arguments_are_evidence_not_artifact_failure(self):
        result, _trace = self._build()
        output = {"role": "assistant", "content": None, "reasoning_content": "reason",
                  "tool_calls": [{"id": "bad", "type": "function", "function": {"name": "evaluate_config", "arguments": "not JSON"}}]}
        result["_trace_v2_capture"]["llm_calls"][0]["output_message"] = output
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual(trace["llm_calls"][0]["output_message"], output)
        output["tool_calls"][0]["function"]["arguments"] = "changed"
        self.assertEqual(trace["llm_calls"][0]["output_message"]["tool_calls"][0]["function"]["arguments"], "not JSON")

    def test_attempt_usage_preserves_missing_and_checks_partial_records(self):
        result, _trace = self._build()
        captured = result["_trace_v2_capture"]["llm_calls"][0]
        attempts = [{"attempt": 1, "state": "error", "http_status": 503, "usage": None},
                    {"attempt": 2, "state": "success", "http_status": 200, "usage": {"prompt_tokens": 9, "provider_detail": {"unknown": True}}}]
        captured.update(request_attempts=2, attempt_usage=copy.deepcopy(attempts))
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual(trace["llm_calls"][0]["attempt_usage"], attempts)
        self.assertIsNone(trace["llm_calls"][0]["attempt_usage"][0]["usage"])
        trace["llm_calls"][0]["attempt_usage"].pop()
        with self.assertRaisesRegex(ValueError, "every request attempt"):
            validate_trace_v2(trace)

    def test_offline_score_source_is_not_matching_tool_call(self):
        result, _trace = self._build()
        self.assertTrue(result["eval_records"])
        result.update(answer='{"x":99}', answer_perf=0.4, answer_score_source="offline_final_answer", tuning_final_policy="submitted")
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual(trace["outcome"]["answer_score_source"], "offline_final_answer")
        self.assertEqual(trace["outcome"]["score_cost_basis"], "offline_final_answer")
        restored = result_for_score_check(trace)
        for field in ("answer", "answer_perf", "tool_records", "eval_records", "total_overhead", "tuning_final_policy"):
            self.assertEqual(restored[field], result[field])

    def test_historical_optional_fields_remain_readable_but_not_rescorable(self):
        _result, trace = self._build()
        for call in trace["llm_calls"]:
            for field in ("output_message", "attempt_usage", "finish_reason"):
                call.pop(field, None)
        for tool in trace["tool_calls"]:
            for field in ("raw_arguments", "tool_result", "canonical_argument", "included_in_eval_records"):
                tool.pop(field, None)
        for field in ("answer", "answer_overhead", "answer_score_source", "tool_protocol", "tuning_final_policy", "protocol_failures", "protocol_retries", "agent_steps", "http_request_attempts"):
            trace["outcome"].pop(field, None)
        validate_trace_v2(trace)
        with self.assertRaisesRegex(ValueError, "exact historical tool_records"):
            result_for_score_check(trace)

    def test_native_final_answer_is_not_reparsed(self):
        result, _trace = self._build()
        result.update(answer='{"x":23}', tool_protocol="native")
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual(result_for_score_check(trace)["answer"], '{"x":23}')
        del trace["outcome"]["answer"]
        with self.assertRaisesRegex(ValueError, "native final answer"):
            result_for_score_check(trace)

    def test_native_withheld_tool_notice_and_raw_result_round_trip(self):
        baseline, _trace = self._build()
        call = {"id": "call_withheld", "type": "function", "function": {"name": "evaluate_config", "arguments": '{"x":1}'}}

        class NativeFixture:
            supports_native_tools = True

            def __init__(self):
                self.requests = []

            def generate(self, messages, **options):
                self.requests.append((copy.deepcopy(messages), copy.deepcopy(options)))
                if len(self.requests) == 1:
                    return LLMOutput(text="", tool_calls=[copy.deepcopy(call)], finish_reason="tool_calls",
                                     assistant_message={"role": "assistant", "content": None,
                                                        "reasoning_content": "retain this reason", "tool_calls": [copy.deepcopy(call)]})
                return LLMOutput(text='{"x":2}', assistant_message={"role": "assistant", "content": '{"x":2}'}, finish_reason="stop")

        llm = NativeFixture()
        hidden = {"secret-feedback": [1, 2, 3]}
        result = run_react_loop(llm=llm, tools={"evaluate_config": lambda _arg: (copy.deepcopy(hidden), 0.9, 4)},
                                context="Task", time_budget=1, max_steps=3, tool_protocol="native",
                                capture_trace_v2=True, answer_evaluator=lambda _answer, _records: 0.7)
        for key in ("job", "cost_regime_resolved", "score_check", "wall_time_seconds", "_trace_v2_runtime"):
            result[key] = copy.deepcopy(baseline[key])
        trace = build_trace_v2(result, repo_root=REPO_ROOT)
        self.assertEqual(len(trace["tool_calls"]), 1)
        tool = trace["tool_calls"][0]
        self.assertFalse(tool["visible_to_model"])
        self.assertEqual(tool["response_kind"], "withheld_notice")
        self.assertIsNotNone(tool["result_message_id"])
        for index, request in enumerate(llm.requests):
            self.assertEqual(materialize_llm_input(trace, "llm%04d" % (index + 1)), request[0])
        self.assertEqual(llm.requests[1][1]["tool_choice"], "none")
        self.assertNotIn("secret-feedback", json.dumps(llm.requests[1][0]))
        self.assertEqual(result_for_score_check(trace)["tool_records"], result["tool_records"])
        self.assertEqual(result_for_score_check(trace)["eval_records"], [])
        tool["observation"] = "Observation: hidden performance=0.9"
        with self.assertRaisesRegex(ValueError, "fixed withheld observation"):
            validate_trace_v2(trace)

    def test_missing_content_and_content_parts_remain_distinct(self):
        result, _trace = self._build()
        messages = [{"role": "assistant", "reasoning_content": "reason only"},
                    {"role": "assistant", "content": [{"type": "text", "text": "part one"}, {"type": "text", "text": "part two"}]}]
        for message in messages:
            with self.subTest(message=message):
                changed = copy.deepcopy(result)
                changed["messages"].append(copy.deepcopy(message))
                trace = build_trace_v2(changed, repo_root=REPO_ROOT)
                materialized = materialize_message(trace, "m%04d" % len(changed["messages"]))
                self.assertEqual(materialized, message)

    def test_builder_does_not_turn_truthy_values_into_validated_booleans(self):
        baseline, _trace = self._build()
        for value in ("false", 1, [], None):
            result = copy.deepcopy(baseline)
            result["score_check"]["ok"] = value
            with self.subTest(passed=value), self.assertRaises(ValueError):
                build_trace_v2(result, repo_root=REPO_ROOT)
        for field in ("aborted", "forced"):
            result = copy.deepcopy(baseline)
            target = result if field == "aborted" else result["_trace_v2_capture"]["llm_calls"][0]
            target[field] = "false"
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_trace_v2(result, repo_root=REPO_ROOT)

    def test_restoring_cost_requires_explicit_retained_total(self):
        _result, trace = self._build()
        del trace["timing"]["total_simulated_cost_seconds"]
        validate_trace_v2(trace)
        with self.assertRaisesRegex(ValueError, "Cannot restore exact cost"):
            result_for_score_check(trace)


if __name__ == "__main__":
    unittest.main()
