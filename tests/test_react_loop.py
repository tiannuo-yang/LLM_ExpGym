import unittest
from typing import Tuple

from expgym.react_loop import FakeLLM, LLMBackend, LLMOutput, run_react_loop
from expgym.tools_experiment import CONFIGS, run_config


class RunReactLoopTest(unittest.TestCase):
    def test_fake_llm_produces_answer_and_observations(self) -> None:
        config_ids = list(CONFIGS.keys())[:3]
        llm = FakeLLM(config_ids=config_ids, probes=2)
        result = run_react_loop(
            llm=llm,
            tools={"run_config": run_config},
            time_budget=5.0,
            max_steps=5,
        )
        self.assertFalse(result["aborted"])
        self.assertIn("Answer:", "\n".join(result["steps"]))
        self.assertIsInstance(result["answer"], str)
        self.assertIsNotNone(result["answer_perf"])
        self.assertAlmostEqual(
            result["answer_perf"], CONFIGS[config_ids[1]]["perf"], places=6
        )
        self.assertAlmostEqual(
            result["answer_overhead"], CONFIGS[config_ids[1]]["overhead"], places=6
        )
        self.assertGreater(result["total_overhead"], 0.0)
        self.assertEqual(result["evaluations"], 2)
        self.assertEqual(result["api_calls"], 3)
        self.assertEqual(result["instruction_tokens"], 0)
        self.assertEqual(result["cached_prompt_tokens"], 0)
        # total_overhead >= eval_time (includes API latency)
        self.assertGreaterEqual(result["total_overhead"], result["eval_time"])

    def test_time_budget_abort(self) -> None:
        class SingleActionLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: checking\nAction: run_config cfg_custom"
                    )
                return LLMOutput(text="Answer: cfg_custom")

        def heavy_tool(_: str) -> Tuple[float, float]:
            return 0.1, 2.0

        result = run_react_loop(
            llm=SingleActionLLM(),
            tools={"run_config": heavy_tool},
            time_budget=1.0,
            max_steps=3,
        )
        self.assertTrue(result["aborted"])
        self.assertEqual(result["answer"], "cfg_custom")
        # Over-budget eval is excluded from eval_records — its result
        # is withheld, so answer_perf is None.
        self.assertIsNone(result["answer_perf"])
        # total_overhead >= 2.0 (tool cost) + tiny API latency
        self.assertGreaterEqual(result["total_overhead"], 2.0)
        self.assertEqual(result["evaluations"], 1)
        self.assertEqual(result["api_calls"], 2)
        self.assertEqual(result["eval_time"], 2.0)

    def test_missing_tool_aborts_execution(self) -> None:
        class MissingToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._called = False

            def generate(self, messages) -> LLMOutput:
                if not self._called:
                    self._called = True
                    return LLMOutput(
                        text="Thought: try tool\nAction: unknown_tool arg"
                    )
                return LLMOutput(text="Answer: fallback")

        result = run_react_loop(
            llm=MissingToolLLM(),
            tools={"run_config": run_config},
            max_steps=2,
        )
        self.assertTrue(result["aborted"])
        self.assertEqual(result["answer"], "fallback")
        self.assertIsNone(result["answer_perf"])
        self.assertIsNone(result["answer_overhead"])
        # total_overhead includes API latency even with no tool calls
        self.assertGreaterEqual(result["total_overhead"], 0.0)
        self.assertEqual(result["evaluations"], 0)
        self.assertEqual(result["api_calls"], 2)
        self.assertEqual(result["eval_time"], 0.0)

    def test_max_evals_enforced(self) -> None:
        plan = [("evaluate_config", "{\"x\": 1}") for _ in range(3)]
        llm = FakeLLM(plan=plan)

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 0.5

        result = run_react_loop(
            llm=llm,
            tools={"evaluate_config": tool},
            max_steps=5,
            max_evals=1,
            context="Test context",
        )
        self.assertTrue(result["aborted"])
        self.assertEqual(result["evaluations"], 1)
        self.assertTrue(any("Test context" in s for s in result["steps"]))
        self.assertGreaterEqual(result["total_overhead"], result["eval_time"])
        self.assertIsInstance(result["answer"], str)
        self.assertEqual(result["api_calls"], 2)
        self.assertEqual(result["answer_perf"], 0.5)
        self.assertEqual(result["answer_overhead"], 0.5)

    def test_forced_answer_selects_prior_action_metrics(self) -> None:
        class TwoActionLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: first\nAction: run_config first_cfg"
                    )
                if self._calls == 2:
                    return LLMOutput(
                        text="Thought: second\nAction: run_config second_cfg"
                    )
                return LLMOutput(text="Answer: first_cfg")

        def tool(argument: str) -> Tuple[float, float]:
            if argument == "first_cfg":
                return 0.91, 11.0
            if argument == "second_cfg":
                return 0.82, 9.0
            raise ValueError(argument)

        result = run_react_loop(
            llm=TwoActionLLM(),
            tools={"run_config": tool},
            max_steps=4,
            max_evals=2,
        )
        self.assertTrue(result["aborted"])
        self.assertEqual(result["evaluations"], 2)
        self.assertEqual(result["answer"], "first_cfg")
        self.assertEqual(result["answer_perf"], 0.91)
        self.assertEqual(result["answer_overhead"], 11.0)

    def test_markdown_wrapped_action_parsed(self) -> None:
        class MarkdownLLM(LLMBackend):
            def __init__(self) -> None:
                self._called = False

            def generate(self, messages) -> LLMOutput:
                if not self._called:
                    self._called = True
                    text = (
                        "**Thought:** checking\n"
                        "**Action:** evaluate_config {\"x\": 1}"
                    )
                    return LLMOutput(text=text)
                return LLMOutput(text="Answer: {\"x\": 1}")

        def tool(payload: str) -> Tuple[float, float]:
            self.assertEqual(payload, '{"x": 1}')
            return 0.2, 0.3

        result = run_react_loop(
            llm=MarkdownLLM(),
            tools={"evaluate_config": tool},
            max_steps=3,
        )
        self.assertFalse(result["aborted"])
        self.assertEqual(result["evaluations"], 1)
        self.assertEqual(result["answer_perf"], 0.2)
        self.assertEqual(result["answer_overhead"], 0.3)

    def test_multiline_action_payload_supported(self) -> None:
        class MultiLineLLM(LLMBackend):
            def __init__(self) -> None:
                self._called = False

            def generate(self, messages) -> LLMOutput:
                if self._called:
                    return LLMOutput(text="Thought: done\nAnswer: ok")
                self._called = True
                text = (
                    "Thought: testing multiline\n"
                    "Action: run_config\n"
                    "cfg_01\n"
                )
                return LLMOutput(text=text)

        result = run_react_loop(
            llm=MultiLineLLM(),
            tools={"run_config": run_config},
            max_steps=2,
        )
        self.assertEqual(result["evaluations"], 1)
        # Agent answered "ok" which doesn't match eval_record for cfg_01.
        # Fallback activates: answer is replaced with best eval (cfg_01, perf=0.42).
        self.assertAlmostEqual(result["answer_perf"], 0.42, places=2)

    def test_fallback_preserves_zero_score_when_all_evals_invalid(self) -> None:
        class ZeroOnlyLLM(LLMBackend):
            def __init__(self) -> None:
                self._called = False

            def generate(self, messages) -> LLMOutput:
                if self._called:
                    return LLMOutput(text='Answer: {"x": 999}')
                self._called = True
                return LLMOutput(text='Thought: try\nAction: evaluate_config {"x": 1}')

        def tool(_: str) -> Tuple[float, float]:
            return 0.0, 1.0

        result = run_react_loop(
            llm=ZeroOnlyLLM(),
            tools={"evaluate_config": tool},
            max_steps=2,
        )

        self.assertEqual(result["answer_perf"], 0.0)
        self.assertEqual(result["answer"], '{"x": 1}')

    def test_tool_error_returns_observation_instead_of_crash(self) -> None:
        """Tool exceptions should be caught and returned as observations."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: bad_tool arg"
                    )
                return LLMOutput(text="Answer: fallback")

        def crashing_tool(_: str):
            raise ValueError("bad JSON or whatever")

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"bad_tool": crashing_tool},
            max_steps=3,
        )
        # Should NOT crash — the error becomes an observation
        self.assertFalse(result["aborted"])
        self.assertEqual(result["answer"], "fallback")
        self.assertEqual(result["evaluations"], 1)
        # The observation should contain the error text
        obs = [s for s in result["steps"] if "Tool error" in s]
        self.assertTrue(len(obs) > 0, "Expected a 'Tool error' observation")


class CallScenarioTest(unittest.TestCase):
    """Tests for _call_scenario kwarg introspection."""

    def test_passes_only_accepted_kwargs(self) -> None:
        """Should pass data_source but NOT cc_split to a function
        that only accepts data_source."""
        import argparse
        from demo_experiment import _call_scenario

        def fn(primary, *, row_index=0, data_source=None):
            return (row_index, data_source)

        args = argparse.Namespace(
            question_index=42, data_source="hotpotqa",
            tuning_task="x", seed=1, cc_split="cc-large",
        )
        result = _call_scenario(fn, True, args)
        self.assertEqual(result, (42, "hotpotqa"))

    def test_passes_cc_split_to_audit(self) -> None:
        """Should pass cc_split but NOT data_source to a function
        that only accepts cc_split."""
        import argparse
        from demo_experiment import _call_scenario

        def fn(primary, *, row_index=0, cc_split="cc-large"):
            return (row_index, cc_split)

        args = argparse.Namespace(
            question_index=7, data_source=None,
            tuning_task="x", seed=1, cc_split="cc-small",
        )
        result = _call_scenario(fn, True, args)
        self.assertEqual(result, (7, "cc-small"))

    def test_passes_tuning_task_and_seed(self) -> None:
        """Tuning build_context accepts tuning_task but not data_source/cc_split."""
        import argparse
        from demo_experiment import _call_scenario

        def fn(primary, *, tuning_task="default", seed=0):
            return (tuning_task, seed)

        args = argparse.Namespace(
            question_index=0, data_source="hotpotqa",
            tuning_task="hpobench:paramnet:poker:steps",
            seed=1206, cc_split="cc-large",
        )
        result = _call_scenario(fn, True, args)
        self.assertEqual(result, ("hpobench:paramnet:poker:steps", 1206))

    def test_no_kwargs_function(self) -> None:
        """Function with no kwargs should still work."""
        import argparse
        from demo_experiment import _call_scenario

        def fn(primary):
            return primary * 2

        args = argparse.Namespace(
            question_index=0, data_source=None,
            tuning_task="x", seed=1, cc_split="cc-large",
        )
        result = _call_scenario(fn, 5, args)
        self.assertEqual(result, 10)


class TuningJsonErrorTest(unittest.TestCase):
    """Tests for JSON error handling in tuning tool functions."""

    def test_evaluate_config_action_bad_json(self) -> None:
        from expgym.task_tuning import evaluate_config_action
        result = evaluate_config_action("not valid json{{{")
        # Should return error string, not crash
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn("Invalid JSON", str(result[0]))
        self.assertEqual(result[1], 0.0)


class ExtractAnswerTest(unittest.TestCase):
    """Tests for the _extract_answer() multi-line fix (Change 1)."""

    def setUp(self) -> None:
        from expgym.react_loop import _extract_answer
        self._extract = _extract_answer

    def test_single_line_answer(self) -> None:
        """Single-line answer after Thought should return just the answer."""
        block = "Thought: I have enough info.\nAnswer: hello"
        self.assertEqual(self._extract(block), "hello")

    def test_single_line_answer_no_thought(self) -> None:
        """Answer line alone should still be extracted."""
        block = "Answer: some_config_id"
        self.assertEqual(self._extract(block), "some_config_id")

    def test_multiline_json_answer(self) -> None:
        """Multi-line JSON answer should capture all lines after Answer:."""
        block = 'Answer: {\n  "key": "value"\n}'
        result = self._extract(block)
        self.assertIsNotNone(result)
        self.assertIn('"key"', result)
        self.assertIn('"value"', result)
        # Verify it's valid JSON
        import json
        parsed = json.loads(result)
        self.assertEqual(parsed, {"key": "value"})

    def test_answer_brace_on_first_line_rest_follows(self) -> None:
        """Answer: { followed by JSON body on subsequent lines."""
        block = 'Answer: {\n  "x": 1,\n  "y": 2\n}'
        result = self._extract(block)
        self.assertIsNotNone(result)
        import json
        parsed = json.loads(result)
        self.assertEqual(parsed, {"x": 1, "y": 2})

    def test_no_answer_returns_none(self) -> None:
        """Block with no Answer: line should return None."""
        block = "Thought: still thinking\nAction: run_config cfg_01"
        self.assertIsNone(self._extract(block))

    def test_empty_string_returns_none(self) -> None:
        """Empty string should return None."""
        self.assertIsNone(self._extract(""))

    def test_single_line_preserved_with_trailing_whitespace(self) -> None:
        """Single-line answer with no subsequent lines (no trailing newline)."""
        block = "Answer: cfg_best"
        self.assertEqual(self._extract(block), "cfg_best")

    def test_multiline_answer_with_thought_prefix(self) -> None:
        """Multi-line answer after Thought line should capture everything."""
        block = (
            "Thought: Based on my analysis.\n"
            'Answer: {"learning_rate": 0.01,\n'
            '"batch_size": 32}'
        )
        result = self._extract(block)
        self.assertIsNotNone(result)
        import json
        parsed = json.loads(result)
        self.assertEqual(parsed["learning_rate"], 0.01)
        self.assertEqual(parsed["batch_size"], 32)

    def test_markdown_answer_single_line(self) -> None:
        """Markdown-wrapped Answer label is detected. Note: _normalize_label
        only strips leading markup, so trailing ** on the label remains in
        the extracted value."""
        block = "**Answer:** hello_world"
        result = self._extract(block)
        # _normalize_label strips leading ** -> "Answer:** hello_world"
        # split("Answer:",1) -> "** hello_world"
        self.assertIsNotNone(result)
        self.assertIn("hello_world", result)

    def test_answer_with_leading_dash(self) -> None:
        """Answer prefixed with dash/bullet should be detected."""
        block = "- Answer: my_answer"
        self.assertEqual(self._extract(block), "my_answer")


class BudgetOvershootTest(unittest.TestCase):
    """Tests for the budget overshoot fix (Change 2).

    When a tool call pushes total_overhead past time_budget, the observation
    should NOT be appended to the LLM's messages, and the steps should
    contain the '[over-budget, result withheld]' marker.
    """

    def test_second_eval_over_budget_withholds_observation(self) -> None:
        """Two tool calls; second exceeds budget. Verify observation withheld."""

        class TwoCallLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: first eval\n"
                             "Action: eval_tool {\"x\": 1}"
                    )
                if self._calls == 2:
                    return LLMOutput(
                        text="Thought: second eval\n"
                             "Action: eval_tool {\"x\": 2}"
                    )
                # Forced answer after abort
                return LLMOutput(text="Answer: {\"x\": 1}")

        call_count = 0

        def eval_tool(arg: str) -> Tuple[float, float]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 0.5, 3.0  # 3s overhead, within budget
            return 0.7, 8.0  # 8s overhead, pushes total to 11s (>10s budget)

        result = run_react_loop(
            llm=TwoCallLLM(),
            tools={"eval_tool": eval_tool},
            time_budget=10.0,
            max_steps=5,
        )

        # Should be aborted
        self.assertTrue(result["aborted"])

        # Steps should contain the withheld marker
        withheld_steps = [
            s for s in result["steps"]
            if "over-budget, result withheld" in s
        ]
        self.assertEqual(len(withheld_steps), 1,
                         "Expected exactly one '[over-budget, result withheld]' step")

        # The LLM messages should NOT contain the second tool's raw
        # observation (perf=0.7) — only the first observation should have it.
        user_messages = [
            m["content"] for m in result["messages"] if m["role"] == "user"
        ]
        # First observation (perf=0.5) should be present as a standalone msg
        obs_first = [m for m in user_messages if "0.5" in m and "Observation" in m
                      and "over-budget" not in m]
        self.assertTrue(len(obs_first) > 0,
                        "First observation should be in messages")
        # Second tool's raw observation (perf=0.7) should NOT appear as a
        # standalone observation — only in the forced-answer eval summary.
        obs_second = [m for m in user_messages
                      if "0.7" in m and "Observation:" in m
                      and "over-budget" not in m and "Loop aborted" not in m]
        self.assertEqual(len(obs_second), 0,
                         "Second observation should NOT be in messages (withheld)")

        # The assistant message (Thought+Action) that led to the over-budget
        # eval should be KEPT in messages (so agent can reference the config
        # it tried), but the observation result should be withheld.
        assistant_messages = [
            m["content"] for m in result["messages"] if m["role"] == "assistant"
        ]
        second_thought = [m for m in assistant_messages if "second eval" in m]
        self.assertEqual(len(second_thought), 1,
                         "Thought/Action for over-budget eval should be kept in messages")
        # The over-budget observation and forced-answer prompt should be
        # combined in a single user message to maintain role alternation.
        combined_msg = [
            m["content"] for m in result["messages"]
            if m["role"] == "user" and "over-budget" in m["content"]
            and "Loop aborted" in m["content"]
        ]
        self.assertEqual(len(combined_msg), 1,
                         "Over-budget note + forced-answer should be one combined message")

    def test_over_budget_sets_correct_abort_reason(self) -> None:
        """Verify the forced answer step references budget exceeded."""

        class SingleCallLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: fallback")

        def expensive_tool(_: str) -> Tuple[float, float]:
            return 0.9, 100.0  # way over any budget

        result = run_react_loop(
            llm=SingleCallLLM(),
            tools={"tool": expensive_tool},
            time_budget=1.0,
            max_steps=3,
        )
        self.assertTrue(result["aborted"])
        # The forced-answer system note should mention "Time budget exceeded"
        budget_notes = [
            s for s in result["steps"]
            if "Time budget exceeded" in s
        ]
        self.assertTrue(len(budget_notes) > 0,
                        "Expected 'Time budget exceeded' in steps")

    def test_under_budget_observation_shown_normally(self) -> None:
        """When still under budget, observation IS shown to the LLM."""

        class SingleCallLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: arg")

        def cheap_tool(_: str) -> Tuple[float, float]:
            return 0.5, 1.0  # under budget of 10.0

        result = run_react_loop(
            llm=SingleCallLLM(),
            tools={"tool": cheap_tool},
            time_budget=10.0,
            max_steps=3,
        )
        self.assertFalse(result["aborted"])
        # Observation should be in messages
        user_messages = [
            m["content"] for m in result["messages"] if m["role"] == "user"
        ]
        obs = [m for m in user_messages if "Observation" in m]
        self.assertTrue(len(obs) > 0,
                        "Observation should be in messages when under budget")
        # No withheld marker
        withheld = [s for s in result["steps"]
                    if "over-budget, result withheld" in s]
        self.assertEqual(len(withheld), 0)


class ContextTokenAbortTest(unittest.TestCase):
    """Test graceful abort when conversation approaches context token limit."""

    def test_aborts_when_context_exceeds_limit(self):
        """Agent should be aborted and forced to answer when context is full."""

        class VerboseLLM(LLMBackend):
            """LLM that produces long outputs to fill context quickly."""
            def __init__(self):
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                # Check if this is the forced-answer call (abort message)
                last = messages[-1].get("content", "")
                if "Loop aborted" in last:
                    return LLMOutput(text="Answer: {\"x\": 1}")
                # Normal action calls
                return LLMOutput(
                    text="Thought: " + "x" * 500 + "\n"
                         "Action: eval_tool {\"x\": " + str(self._calls) + "}"
                )

        def eval_tool(arg):
            # Return long observation text to fill context
            return ("result " + "y" * 500, 1.0)

        result = run_react_loop(
            llm=VerboseLLM(),
            tools={"eval_tool": eval_tool},
            time_budget=99999.0,
            max_steps=50,
            max_context_tokens=800,  # Low limit to trigger after a few rounds
        )

        self.assertTrue(result["aborted"])
        # Should have the forced answer
        self.assertEqual(result["answer"], '{"x": 1}')
        # Should NOT have run all 50 steps
        self.assertLess(result["api_calls"], 10)
        # Steps should contain the abort note
        abort_notes = [s for s in result["steps"]
                       if "Context token budget exceeded" in s]
        self.assertEqual(len(abort_notes), 1)

    def test_no_abort_when_under_limit(self):
        """Agent should run normally when context stays under limit."""
        llm = FakeLLM(plan=[("eval_tool", '{"x": 1}')])

        def eval_tool(arg):
            return (0.5, 1.0)

        result = run_react_loop(
            llm=llm,
            tools={"eval_tool": eval_tool},
            time_budget=99999.0,
            max_steps=5,
            max_context_tokens=40000,  # Generous limit
        )

        self.assertFalse(result["aborted"])

    def test_no_abort_when_limit_not_set(self):
        """No context abort when max_context_tokens is None."""
        llm = FakeLLM(plan=[("eval_tool", '{"x": 1}')])

        def eval_tool(arg):
            return (0.5, 1.0)

        result = run_react_loop(
            llm=llm,
            tools={"eval_tool": eval_tool},
            time_budget=99999.0,
            max_steps=5,
            max_context_tokens=None,
        )

        self.assertFalse(result["aborted"])


class HTTP500RetryTest(unittest.TestCase):
    """Tests for HTTP 500 being included in the retry list (Change 3)."""

    def test_retry_codes_include_500(self) -> None:
        """Verify that HTTP 500 is in the retryable status codes.

        We inspect the source code of llm_clients.py to confirm the tuple
        includes 500. This is a static analysis test since actually triggering
        HTTP 500 retries would require mocking network calls.
        """
        import inspect
        from expgym import llm_clients
        source = inspect.getsource(llm_clients.OpenAICompatibleLLM.generate)
        # The retry condition should include 500
        self.assertIn("500", source,
                      "HTTP 500 should be in the retry status codes")
        # Verify the exact tuple pattern
        self.assertIn("429, 500, 502, 503", source,
                      "Retry codes should be (429, 500, 502, 503)")

    def test_http_500_triggers_retry(self) -> None:
        """Simulate an HTTP 500 followed by a successful response.

        Uses a fake transport to confirm that 500 errors cause retries
        rather than immediate failure.
        """
        import urllib.error
        import urllib.request
        from expgym.llm_clients import OpenAICompatibleLLM

        call_count = 0

        def mock_transport(request: urllib.request.Request, timeout: float) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call: HTTP 500
                raise urllib.error.HTTPError(
                    url="http://fake",
                    code=500,
                    msg="Internal Server Error",
                    hdrs=None,  # type: ignore[arg-type]
                    fp=__import__("io").BytesIO(b'{"error": "server error"}'),
                )
            # Second call: success
            return json.dumps({
                "choices": [{"message": {"content": "Answer: hello"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }).encode("utf-8")

        import json
        # Patch time.sleep to avoid actual waiting during test
        import unittest.mock
        with unittest.mock.patch("time.sleep"):
            client = OpenAICompatibleLLM(
                api_key="test-key",
                model="test-model",
                transport=mock_transport,
            )
            output = client.generate([{"role": "user", "content": "test"}])

        self.assertEqual(call_count, 2, "Should have retried once after HTTP 500")
        self.assertEqual(output.text, "Answer: hello")
        self.assertEqual(output.request_attempts, 2)

    def test_http_429_still_retries(self) -> None:
        """Confirm that 429 (rate limit) still triggers retries as before."""
        import urllib.error
        import urllib.request
        from expgym.llm_clients import OpenAICompatibleLLM

        call_count = 0

        def mock_transport(request: urllib.request.Request, timeout: float) -> bytes:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise urllib.error.HTTPError(
                    url="http://fake",
                    code=429,
                    msg="Too Many Requests",
                    hdrs=None,  # type: ignore[arg-type]
                    fp=__import__("io").BytesIO(b'{"error": "rate limited"}'),
                )
            return json.dumps({
                "choices": [{"message": {"content": "ok"}}],
                "usage": {},
            }).encode("utf-8")

        import json
        import unittest.mock
        with unittest.mock.patch("time.sleep"):
            client = OpenAICompatibleLLM(
                api_key="test-key",
                model="test-model",
                transport=mock_transport,
            )
            output = client.generate("test")

        self.assertEqual(call_count, 2)
        self.assertEqual(output.text, "ok")
        self.assertEqual(output.request_attempts, 2)

    def test_http_400_does_not_retry(self) -> None:
        """Non-retryable codes like 400 should raise immediately."""
        import urllib.error
        import urllib.request
        from expgym.llm_clients import OpenAICompatibleLLM

        call_count = 0

        def mock_transport(request: urllib.request.Request, timeout: float) -> bytes:
            nonlocal call_count
            call_count += 1
            raise urllib.error.HTTPError(
                url="http://fake",
                code=400,
                msg="Bad Request",
                hdrs=None,  # type: ignore[arg-type]
                fp=__import__("io").BytesIO(b'{"error": "bad request"}'),
            )

        from expgym.llm_clients import OpenAICompatibleLLM
        import unittest.mock
        with unittest.mock.patch("time.sleep"):
            client = OpenAICompatibleLLM(
                api_key="test-key",
                model="test-model",
                transport=mock_transport,
            )
            with self.assertRaises(RuntimeError):
                client.generate("test")

        self.assertEqual(call_count, 1,
                         "HTTP 400 should NOT trigger retries")


class TimeAwareBaselineTest(unittest.TestCase):
    """Tests for the time_aware baseline mode.

    time_aware shows cost + budget status in observations but does NOT
    change the system prompt or context (unlike time_focus).
    """

    def test_cost_and_budget_in_observation(self) -> None:
        """Observation should include cost=Xs and [time_left=..., step ..., context_len=...]."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: arg")

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 3.0  # perf=0.5, overhead=3.0

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            time_budget=10.0,
            max_steps=5,
            include_cost_in_observation=True,
        )
        self.assertFalse(result["aborted"])
        # Find the observation in steps
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 1)
        self.assertIn("cost=3s", obs[0])
        # time_left <= 7s due to API latency
        self.assertRegex(obs[0], r"time_left=[67]s")
        self.assertIn("perf=0.500000", obs[0])
        # Step and context_len no longer shown in time_aware observations
        self.assertNotIn("step", obs[0])
        self.assertNotIn("context_len", obs[0])

    def test_cost_shown_for_text_tool_output(self) -> None:
        """When tool returns (text, overhead), cost + budget appear."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: done")

        def tool(_: str) -> Tuple[str, float]:
            return "some result text", 5.0

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            time_budget=20.0,
            max_steps=10,
            include_cost_in_observation=True,
        )
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 1)
        self.assertIn("some result text", obs[0])
        self.assertIn("cost=5s", obs[0])
        # time_left <= 15s due to API latency
        self.assertRegex(obs[0], r"time_left=1[45]s")
        # Step and context_len not shown
        self.assertNotIn("step", obs[0])
        self.assertNotIn("context_len", obs[0])

    def test_context_len_not_shown_in_observations(self) -> None:
        """Context len is an internal limit and not shown to the model."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg",
                    )
                return LLMOutput(text="Answer: arg")

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 1.0

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            time_budget=10.0,
            max_steps=5,
            max_context_tokens=14000,
            include_cost_in_observation=True,
        )
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 1)
        # context_len is no longer shown to the model
        self.assertNotIn("context_len", obs[0])
        # But cost and time_left should still be there
        self.assertIn("cost=1s", obs[0])
        self.assertRegex(obs[0], r"time_left=")

    def test_no_time_budget_omits_time_left(self) -> None:
        """Without time_budget, time_left should not appear."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: arg")

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 2.0

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            max_steps=5,
            include_cost_in_observation=True,
        )
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 1)
        self.assertNotIn("time_left", obs[0])
        self.assertIn("cost=2s", obs[0])
        # Step count not shown
        self.assertNotIn("step", obs[0])

    def test_time_aware_does_not_modify_system_prompt(self) -> None:
        """time_aware should NOT inject budget hints into system prompt."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: arg")

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 1.0

        sys_prompt = "You are a helpful assistant."
        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            time_budget=10.0,
            max_steps=5,
            system_prompt=sys_prompt,
            include_cost_in_observation=True,
        )
        # System prompt in messages should be exactly what we passed
        sys_msg = result["messages"][0]
        self.assertEqual(sys_msg["role"], "system")
        self.assertEqual(sys_msg["content"], sys_prompt)
        # No budget/overhead hints in system prompt
        self.assertNotIn("overhead", sys_msg["content"].lower())
        self.assertNotIn("budget", sys_msg["content"].lower())

    def test_time_aware_vs_no_budget_vs_time_focus_observations(self) -> None:
        """Compare observation format across all three baseline modes."""

        def make_llm():
            class TLlm(LLMBackend):
                def __init__(self):
                    self._calls = 0
                def generate(self, messages) -> LLMOutput:
                    self._calls += 1
                    if self._calls == 1:
                        return LLMOutput(
                            text="Thought: try\nAction: tool arg"
                        )
                    return LLMOutput(text="Answer: arg")
            return TLlm()

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 3.0

        kwargs = dict(tools={"tool": tool}, time_budget=10.0, max_steps=5)

        # no_budget
        r_nb = run_react_loop(llm=make_llm(), **kwargs)
        obs_nb = [s for s in r_nb["steps"] if s.startswith("Observation:")][0]

        # time_aware
        r_ta = run_react_loop(
            llm=make_llm(), include_cost_in_observation=True, **kwargs
        )
        obs_ta = [s for s in r_ta["steps"] if s.startswith("Observation:")][0]

        # time_focus
        r_tf = run_react_loop(
            llm=make_llm(), include_overhead_in_observation=True, **kwargs
        )
        obs_tf = [s for s in r_tf["steps"] if s.startswith("Observation:")][0]

        # no_budget: just perf, no cost/overhead
        self.assertIn("perf=0.500000", obs_nb)
        self.assertNotIn("cost", obs_nb)
        self.assertNotIn("overhead", obs_nb)

        # time_aware: perf + cost + time_left (no step count or context_len)
        self.assertIn("perf=0.500000", obs_ta)
        self.assertIn("cost=3s", obs_ta)
        self.assertRegex(obs_ta, r"time_left=[67]s")
        self.assertNotIn("step", obs_ta)
        self.assertNotIn("context_len", obs_ta)

        # time_focus: perf + overhead (old format)
        self.assertIn("perf=0.500000", obs_tf)
        self.assertIn("overhead=3.00", obs_tf)
        self.assertNotIn("time_left", obs_tf)

    def test_near_zero_overhead_hides_cost(self) -> None:
        """When overhead < 0.5s (e.g. search_meta), cost is not shown."""

        class SingleToolLLM(LLMBackend):
            def __init__(self) -> None:
                self._calls = 0

            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls == 1:
                    return LLMOutput(
                        text="Thought: try\nAction: tool arg"
                    )
                return LLMOutput(text="Answer: done")

        def tool(_: str) -> Tuple[str, float]:
            return "meta search results", 0.1  # near-zero overhead

        result = run_react_loop(
            llm=SingleToolLLM(),
            tools={"tool": tool},
            time_budget=20.0,
            max_steps=10,
            include_cost_in_observation=True,
        )
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 1)
        self.assertIn("meta search results", obs[0])
        # cost and time_left should NOT be shown for near-zero overhead
        self.assertNotIn("cost=", obs[0])
        self.assertNotIn("time_left=", obs[0])

    def test_multiple_evals_budget_decreases(self) -> None:
        """Budget hint should update across multiple tool calls."""

        class MultiLLM(LLMBackend):
            def __init__(self):
                self._calls = 0
            def generate(self, messages) -> LLMOutput:
                self._calls += 1
                if self._calls <= 2:
                    return LLMOutput(
                        text="Thought: eval {}\nAction: tool arg".format(self._calls)
                    )
                return LLMOutput(text="Answer: arg")

        def tool(_: str) -> Tuple[float, float]:
            return 0.5, 4.0

        result = run_react_loop(
            llm=MultiLLM(),
            tools={"tool": tool},
            time_budget=20.0,
            max_steps=5,
            include_cost_in_observation=True,
        )
        obs = [s for s in result["steps"] if s.startswith("Observation:")]
        self.assertEqual(len(obs), 2)
        # First: 4s tool + tiny API latency used; ~16s left
        self.assertRegex(obs[0], r"time_left=1[56]s")
        # Second: 8s tool + API latency used; ~12s left
        self.assertRegex(obs[1], r"time_left=1[12]s")
        # Step count not shown in observations
        self.assertNotIn("step", obs[0])
        self.assertNotIn("step", obs[1])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
