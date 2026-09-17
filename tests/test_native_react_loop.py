"""Provider-shaped decision lifecycle, budget and failure-boundary regressions."""
import copy
import json
import unittest

from expgym.errors import ToolInputError
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import (
    LLMOutput, FakeLLM, run_react_loop, _estimate_tokens, _trim_messages,
    _finalize_answer, _parse_tool_return,
    _trace_argument, _unpack_perf,
)


def call(arguments='{"x":1}', name="evaluate_config", call_id="call_1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def native(*calls, content=None, finish_reason="tool_calls"):
    message = {"role": "assistant", "content": content,
               "reasoning_content": "Retain this reasoning.", "tool_calls": list(calls)}
    return LLMOutput(
        text=content or "", prompt_tokens=11, completion_tokens=7,
        tool_calls=list(calls), assistant_message=message, finish_reason=finish_reason,
        attempt_usage=[{"attempt": 1, "state": "success", "http_status": 200,
                        "usage": {"prompt_tokens": 11, "completion_tokens": 7}}],
    )


class NativeReplay:
    supports_native_tools = True

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.requests = []

    def generate(self, messages, **kwargs):
        self.requests.append((copy.deepcopy(messages), copy.deepcopy(kwargs)))
        return next(self.outputs)


class NativeLoopTest(unittest.TestCase):
    def test_tool_only_response_and_complete_history(self):
        first = native(call())
        llm = NativeReplay([first, LLMOutput('Answer: {"x":1}')])
        result = run_react_loop(llm, {"evaluate_config": lambda _: (.4, 2.)},
                                context="Tune x.", max_steps=3, capture_trace_v2=True)
        self.assertEqual(result["tool_protocol"], "native")
        self.assertEqual(result["answer_perf"], .4)
        self.assertEqual((result["agent_steps"], result["evaluations"], result["total_overhead"]), (2, 1, 2.))
        second, options = llm.requests[1]
        self.assertEqual(second[-2], first.assistant_message)
        self.assertEqual(second[-1]["role"], "tool")
        self.assertEqual(second[-1]["tool_call_id"], "call_1")
        self.assertEqual(options["tool_choice"], "auto")
        self.assertTrue(options["tools"])
        self.assertNotIn("MUST output BOTH", second[0]["content"])
        capture = result["_trace_v2_capture"]
        self.assertEqual(capture["llm_calls"][0]["output_message"], first.assistant_message)
        self.assertEqual(capture["tool_calls"][0]["raw_arguments"], '{"x":1}')
        self.assertTrue(capture["tool_calls"][0]["included_in_eval_records"])
        self.assertEqual(result["usage_attempts"][0]["attempts"], first.attempt_usage)

    def test_invalid_native_arguments_consume_repair_step_not_tool_evaluation(self):
        for arguments in ('{', '[]', '{"x":NaN}', '{"x":1e999}', '[' * 1500 + '0' + ']' * 1500):
            with self.subTest(arguments=arguments):
                llm = NativeReplay([native(call(arguments)), native(call(call_id="call_2")),
                                    LLMOutput('Answer: {"x":1}')])
                seen = []
                result = run_react_loop(llm, {"evaluate_config": lambda p: seen.append(p) or (.5, 1.)},
                                        max_steps=2, max_protocol_retries=1)
                self.assertEqual(seen, ['{"x":1}'])
                self.assertEqual(result["agent_steps"], 2)
                self.assertEqual(result["api_calls"], 3)  # two steps plus one forced final
                self.assertEqual(result["protocol_retries"], 1)
                self.assertEqual(result["evaluations"], 1)
                self.assertEqual(llm.requests[1][0][-1]["role"], "tool")
                self.assertIn("No tool was executed", llm.requests[1][0][-1]["content"])
                self.assertEqual(llm.requests[-1][1]["tool_choice"], "none")

    def test_multiple_calls_rejected_as_a_whole_and_all_ids_paired(self):
        llm = NativeReplay([native(call(call_id="a"), call(call_id="b")), LLMOutput("Answer: done")])
        seen = []
        result = run_react_loop(llm, {"evaluate_config": lambda p: seen.append(p) or (.5, 1.)}, max_steps=1)
        self.assertEqual(seen, [])
        self.assertEqual(result["evaluations"], 0)
        tool_messages = [m for m in llm.requests[-1][0] if m["role"] == "tool"]
        self.assertEqual([m["tool_call_id"] for m in tool_messages], ["a", "b"])

    def test_forced_final_never_executes_tools(self):
        llm = NativeReplay([native(call())])
        seen = []
        result = run_react_loop(llm, {"evaluate_config": lambda p: seen.append(p) or (.5, 1.)}, max_steps=0)
        self.assertEqual(seen, [])
        self.assertIsNone(result["answer"])
        self.assertTrue(result["protocol_failures"][0]["forced"])
        self.assertEqual(llm.requests[0][1]["tool_choice"], "none")

    def test_invalid_call_envelope_is_rejected_before_side_effects(self):
        for call_id in (None, "", "  "):
            llm = NativeReplay([native(call(call_id=call_id))])
            seen = []
            with self.subTest(call_id=call_id), self.assertRaisesRegex(ValueError, "call IDs"):
                run_react_loop(llm, {"evaluate_config": lambda p: seen.append(p) or (.5, 1.)}, max_steps=1)
            self.assertEqual(seen, [])

    def test_length_stop_is_recorded_and_not_executed(self):
        llm = NativeReplay([native(call(), finish_reason="length"), LLMOutput("Answer: done")])
        result = run_react_loop(llm, {"evaluate_config": lambda _: (.5, 1.)}, max_steps=1)
        self.assertEqual(result["evaluations"], 0)
        self.assertEqual(result["protocol_failures"][0]["finish_reason"], "length")

    def test_budget_withheld_notice_pairs_call_without_leaking_score(self):
        coordinator = PoolActCoordinator(1)
        runtime = coordinator.bind_tools({"evaluate_config": lambda _: (.765432, 10.)}, 0, time_budget=10.)
        llm = NativeReplay([native(call()), LLMOutput('Answer: {"x":1}')])
        result = run_react_loop(llm, runtime.tools, context="Tune x.", time_budget=10., max_steps=3,
                                observation_augmenter=runtime.observation_augmenter,
                                agent_clock=runtime.clock, pre_tool_hook=runtime.pre_tool_hook,
                                llm_lock=runtime.reasoning_lock, capture_trace_v2=True)
        last_request = llm.requests[-1][0]
        notice = [m for m in last_request if m["role"] == "tool"][0]
        self.assertIn("withheld", notice["content"])
        self.assertNotIn("765432", str(last_request))
        record = result["_trace_v2_capture"]["tool_calls"][0]
        self.assertFalse(record["visible_to_model"])
        self.assertEqual(record["response_kind"], "withheld_notice")
        self.assertEqual(result["eval_records"], [])
        self.assertEqual(runtime.clock.now, 10.)
        self.assertEqual(coordinator.graph.stats()["pending_claims"], 0)

    def test_submitted_policy_never_replaces_unobserved_final(self):
        for policy, expected in (("legacy", '{"x":1}'), ("submitted", '{"x":2}')):
            llm = NativeReplay([native(call()), LLMOutput('Answer: {"x":2}')])
            result = run_react_loop(llm, {"evaluate_config": lambda _: (.9, 1.)},
                                    max_steps=3, tuning_final_policy=policy)
            self.assertEqual(result["answer"], expected)
            self.assertEqual(result["evaluations"], 1)
            self.assertEqual(result["total_overhead"], 1.)
            if policy == "submitted":
                self.assertIsNone(result["answer_perf"])


class BoundaryTest(unittest.TestCase):
    def test_invalid_model_json_can_still_be_saved_as_strict_trace(self):
        for payload in ('{"x":NaN}', '{"x":1e999}', '{'):
            encoded = _trace_argument(payload)
            self.assertEqual(encoded, {"raw": payload, "encoding": "text"})
            json.dumps(encoded, allow_nan=False)

    def test_invalid_primary_metric_is_not_a_score(self):
        for result in ({"label_acc": True}, {"label_acc": "0.9"}, {}, {"count": float('nan')}, "0.7", True):
            with self.subTest(result=result), self.assertRaises((ValueError, TypeError)):
                _unpack_perf(result)

    def test_environment_failures_are_not_model_errors(self):
        for error in (FileNotFoundError("snapshot missing"), ValueError("backend bug"), TypeError("backend bug")):
            def fail(_):
                raise error
            with self.subTest(error=type(error).__name__), self.assertRaises(type(error)):
                run_react_loop(FakeLLM(plan=[("t", "{}")]), {"t": fail}, max_steps=2)

    def test_internal_evaluator_typeerror_is_not_retried(self):
        calls = []
        def evaluator(answer, records=None):
            calls.append(records)
            if records is not None:
                raise TypeError("internal evaluator bug")
            return .99
        with self.assertRaisesRegex(TypeError, "internal evaluator bug"):
            _finalize_answer("{}", [], evaluator, [], 0.)
        self.assertEqual(calls, [[]])

    def test_zero_eval_budget_never_executes_a_tool(self):
        seen = []
        result = run_react_loop(FakeLLM(plan=[("t", "{}")], final_answer="{}"),
                                {"t": lambda p: seen.append(p) or (.1, 1.)}, max_evals=0)
        self.assertEqual(seen, [])
        self.assertEqual(result["agent_steps"], 0)
        self.assertEqual(result["api_calls"], 1)

    def test_invalid_tool_values_raise_before_accounting(self):
        for value in ((.5, -1.), (.5, float('nan')), (.5, float('inf')),
                      (float('nan'), 1.), (.5, True), (True, 1.)):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                _parse_tool_return(value)

    def test_initial_task_cannot_be_trimmed_to_make_request_fit(self):
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "task" * 300}]
        trimmed = _trim_messages(messages, 10)
        self.assertEqual(trimmed, messages)
        self.assertGreater(_estimate_tokens(trimmed), 10)
        llm = NativeReplay([])
        result = run_react_loop(llm, {}, context="task" * 300, max_context_tokens=10)
        self.assertEqual(llm.requests, [])
        self.assertTrue(result["aborted"])

    def test_context_trimming_preserves_complete_native_groups(self):
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "task"}]
        for i in range(8):
            messages.extend([{"role": "assistant", "content": None, "tool_calls": [call(call_id=str(i))]},
                             {"role": "tool", "tool_call_id": str(i), "content": "observation" * 300}])
        trimmed = _trim_messages(messages, 700)
        ids = [c["id"] for m in trimmed for c in m.get("tool_calls", [])]
        results = [m["tool_call_id"] for m in trimmed if m["role"] == "tool"]
        self.assertEqual(ids, results)
        self.assertEqual(trimmed[:2], messages[:2])
        self.assertEqual(messages[-1]["content"], "observation" * 300)

    def test_native_schema_is_reserved_in_context_budget(self):
        def tool(_):
            return .5, 1.
        tool.__expgym_tool_schema__ = {
            "name": "evaluate_config", "description": "X" * 6000,
            "parameters": {"type": "object", "properties": {}},
        }
        llm = NativeReplay([])
        result = run_react_loop(llm, {"evaluate_config": tool}, context="task", max_context_tokens=500)
        self.assertEqual(llm.requests, [])
        self.assertEqual(result["termination_reason"], "Context token budget exceeded")


if __name__ == "__main__":
    unittest.main()
