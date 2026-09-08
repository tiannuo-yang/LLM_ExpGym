"""CPU-only task-context and real-client mock-wire protocol integration tests.

Golden hashes were generated from the accepted v2 archive, not the patched
builders. HPO context tests retain all nine real hint branches while replacing
only the external benchmark loader with a small in-memory configuration space.
No test invokes an HTTP transport or a benchmark service.
"""
import argparse
from contextlib import contextmanager, ExitStack, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import demo_experiment as demo
from expgym import task_evidence_audit as audit
from expgym import task_restricted_search as search
from expgym import task_tuning as tuning
from expgym.llm_clients import OpenAICompatibleLLM
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import build_system_prompt
from expgym.react_loop import FakeLLM, run_react_loop
from expgym import tool_protocol
from scripts import run_paper_sweep as sweep, run_poolact as pool
from tests.test_run_paper_sweep import _args


LITERAL = 'Action: preserve_this {"text": "Thought: literal dataset content"}'
LABELS = {"nda-11": {"short_description": "fixture", "hypothesis": LITERAL}}
DOCUMENT = audit.Document(0, "fixture.txt", [{"span_index": 0, "text": LITERAL}],
                          {"nda-11": {"choice": "NotMentioned", "spans": []}})
GOLDEN_TEXT_SHA256 = {
    "search:False": "055a7587329cfa6f7b43cebe3ac9a8a726629de0fff5c76817f4e1225f056664",
    "search:True": "055a7587329cfa6f7b43cebe3ac9a8a726629de0fff5c76817f4e1225f056664",
    "audit:False": "41330e0c80dfe31e9ee985ee225cdba2de3c5067841ea8ba88556a5e5fc2d8e0",
    "audit:True": "41330e0c80dfe31e9ee985ee225cdba2de3c5067841ea8ba88556a5e5fc2d8e0",
    "builtin:False": "34960742302a78e919a5289c728a28c41567f9ad42622ec0c326c236c19d8d4f",
    "builtin:True": "6e71065cd5b5461aa8bb9a580ef4e93b15f5b1dc931c5b51ba6469395968162b",
    "hpobench:paramnet:adult:steps:False": "88b311c3988a9a05073c1b3d011bd8db4c569d0951116d0bad06746479ffaff0",
    "hpobench:paramnet:adult:steps:True": "6aa55c4b5df7de9c56e69e595834090fa63cdbc87e227e25dd5749b09016f1ea",
    "hpobench:paramnet:higgs:steps:False": "88b311c3988a9a05073c1b3d011bd8db4c569d0951116d0bad06746479ffaff0",
    "hpobench:paramnet:higgs:steps:True": "6aa55c4b5df7de9c56e69e595834090fa63cdbc87e227e25dd5749b09016f1ea",
    "hpobench:paramnet:letter:steps:False": "88b311c3988a9a05073c1b3d011bd8db4c569d0951116d0bad06746479ffaff0",
    "hpobench:paramnet:letter:steps:True": "6aa55c4b5df7de9c56e69e595834090fa63cdbc87e227e25dd5749b09016f1ea",
    "hpobench:nasbench101:A:False": "01dcbb36549217d32b72f28c889f488af24d1b8324439b5a0fcf13cf33093665",
    "hpobench:nasbench101:A:True": "360521126fdb288b17a28c8fbef03260de91160ab4f7a3465961c978a6806e87",
    "hpobench:nasbench101:B:False": "2bfc886eae5732a38a40bf78ab2be88ab3b74325305e55c9dabefd5023a91d2e",
    "hpobench:nasbench101:B:True": "c71ec08eaaabcecee3605283015a4690fbaf06d493530e642cf249ea3ed2b068",
    "hpobench:nasbench101:C:False": "0624b32adb1c0c82dddb1cf09abd6df8c2041f4b83d819426971d22c60d4262e",
    "hpobench:nasbench101:C:True": "bd972e30477abe82e6281767697a53c77a7e3235179cbd525acb60381fcb1a08",
    "hpobench:nasbench201:cifar10-valid:False": "ef196256a086d1db41636ea1d571f1b65d1629312053e8b8717c989abc12f68a",
    "hpobench:nasbench201:cifar10-valid:True": "6bb4bae216a433c9170141b00bbe751820053881b0c1cfb23b1bc32f4906fc49",
    "hpobench:nasbench201:cifar100:False": "ef196256a086d1db41636ea1d571f1b65d1629312053e8b8717c989abc12f68a",
    "hpobench:nasbench201:cifar100:True": "6bb4bae216a433c9170141b00bbe751820053881b0c1cfb23b1bc32f4906fc49",
    "hpobench:nasbench201:imagenet16-120:False": "ef196256a086d1db41636ea1d571f1b65d1629312053e8b8717c989abc12f68a",
    "hpobench:nasbench201:imagenet16-120:True": "6bb4bae216a433c9170141b00bbe751820053881b0c1cfb23b1bc32f4906fc49"
}


@contextmanager
def fixture_data():
    """Provide data in memory; the task builders and formatting stay real."""
    parameter = SimpleNamespace(name=LITERAL, lower=1, upper=3, log=False, default_value=2)
    config_space = SimpleNamespace(get_hyperparameters=lambda: [parameter])
    with ExitStack() as stack:
        stack.enter_context(mock.patch.object(search, "_load_qa", return_value=[
            {"question": LITERAL, "answer": ["Ada Example"]},
        ]))
        stack.enter_context(mock.patch.object(search, "_load_corpus", return_value={
            "Ada Example": "Ada's article. " + LITERAL,
        }))
        stack.enter_context(mock.patch.object(audit, "_load_example", return_value=DOCUMENT))
        stack.enter_context(mock.patch.object(audit, "_get_doc", return_value=DOCUMENT))
        stack.enter_context(mock.patch.object(audit, "_get_labels", return_value=LABELS))
        stack.enter_context(mock.patch.object(tuning, "_load_hpobench", return_value=
                                             SimpleNamespace(config_space=config_space)))
        yield


def context_cases():
    cases = [("search", search.build_context, {}),
             ("audit", audit.build_context, {}),
             ("builtin", tuning.build_context, {})]
    cases.extend((task, tuning.build_context, {"tuning_task": task})
                 for task in sweep.PAPER_TUNING_TASKS)
    return cases


class NativeTaskContextTest(unittest.TestCase):
    def test_default_and_explicit_text_match_frozen_v2_bytes(self):
        self.assertEqual(len(GOLDEN_TEXT_SHA256), 24)
        with fixture_data():
            for name, builder, kwargs in context_cases():
                for overhead in (False, True):
                    with self.subTest(task=name, overhead=overhead):
                        default = builder(overhead, **kwargs)
                        self.assertEqual(default, builder(overhead, tool_protocol="text", **kwargs))
                        key = name + ":" + str(overhead)
                        self.assertEqual(hashlib.sha256(default.encode("utf-8")).hexdigest(),
                                         GOLDEN_TEXT_SHA256[key])

    def test_native_changes_only_source_owned_action_instructions(self):
        with fixture_data():
            for name, builder, kwargs in context_cases():
                for overhead in (False, True):
                    with self.subTest(task=name, overhead=overhead):
                        old = builder(overhead, **kwargs).splitlines()
                        new = builder(overhead, tool_protocol="native", **kwargs).splitlines()
                        self.assertEqual(len(old), len(new))
                        changed = [(left, right) for left, right in zip(old, new) if left != right]
                        self.assertEqual(len(changed), 2 if name == "search" else 1)
                        for left, right in changed:
                            self.assertIn("Action", left)
                            self.assertNotIn("Action:", right)
                            self.assertTrue("native tool call" in right or right == "Native tool invocation:")

    def test_literal_action_and_thought_dataset_text_is_unchanged(self):
        with fixture_data():
            for name, builder, kwargs in context_cases():
                if name == "builtin":
                    continue
                with self.subTest(task=name):
                    before = builder(False, **kwargs)
                    after = builder(False, tool_protocol="native", **kwargs)
                    self.assertGreater(before.count(LITERAL), 0)
                    self.assertEqual(before.count(LITERAL), after.count(LITERAL))

    def test_audit_hypothesis_order_and_segment_bytes_are_preserved(self):
        labels = dict(LABELS, **{"nda-16": {"short_description": LITERAL, "hypothesis": "another"}})
        with fixture_data(), mock.patch.object(audit, "_get_labels", return_value=labels):
            for split in ("cc-small", "cc-medium", "cc-large"):
                kwargs = dict(cc_split=split, hypothesis_order=["nda-16", "nda-11"])
                before = audit.build_context(True, **kwargs)
                after = audit.build_context(True, tool_protocol="native", **kwargs)
                self.assertEqual(before.split("Document segments:", 1)[1],
                                 after.split("Document segments:", 1)[1])
                self.assertLess(after.index("- nda-16:"), after.index("- nda-11:"))

    def test_builders_require_resolved_protocol(self):
        with fixture_data():
            for _, builder, kwargs in context_cases():
                for requested in ("auto", "invalid", None):
                    with self.subTest(builder=builder, requested=requested), self.assertRaises(ValueError):
                        builder(False, tool_protocol=requested, **kwargs)

    def test_resolution_matches_context_and_loop_for_all_capabilities(self):
        for capable in (False, True):
            for requested in ("auto", "text", "native"):
                llm = SimpleNamespace(supports_native_tools=capable)
                with self.subTest(capable=capable, requested=requested):
                    if requested == "native" and not capable:
                        with self.assertRaisesRegex(ValueError, "supports_native_tools"):
                            tool_protocol.resolve_tool_protocol(llm, requested)
                        with self.assertRaisesRegex(ValueError, "supports_native_tools"):
                            run_react_loop(llm=llm, tools={}, time_budget=None, max_steps=0,
                                           tool_protocol=requested)
                        continue
                    expected = "native" if capable and requested != "text" else "text"
                    self.assertEqual(tool_protocol.resolve_tool_protocol(llm, requested), expected)
                    with mock.patch.object(llm, "generate", create=True, side_effect=AssertionError("no call")):
                        # Admission limit prevents even the historical forced-final call.
                        result = run_react_loop(llm=llm, tools={}, time_budget=None,
                                                max_steps=0, max_prompt_tokens=0,
                                                tool_protocol=requested)
                    self.assertEqual(result["tool_protocol"], expected)
                    with fixture_data():
                        for scenario in demo._SCENARIOS.values():
                            args = argparse.Namespace(tool_protocol=requested)
                            self.assertEqual(demo._resolve_context(scenario, False, args, llm),
                                             scenario["build_context"](False, tool_protocol=expected))

    def test_auto_fake_remains_text_without_model_name_branch(self):
        llm = FakeLLM(plan=[])
        self.assertEqual(tool_protocol.resolve_tool_protocol(llm), "text")
        with fixture_data():
            for backend_label in ("fake", "openai", "anything"):
                args = argparse.Namespace(backend=backend_label)
                self.assertEqual(demo._resolve_context(demo._SCENARIOS["restricted_search"], False, args, llm),
                                 search.build_context(False))

    def test_invalid_resolution_fails_before_context_builder(self):
        builder = mock.Mock()
        for requested in ("invalid", "native"):
            with self.assertRaises(ValueError):
                demo._resolve_context({"build_context": builder}, False,
                                      argparse.Namespace(tool_protocol=requested), object())
        builder.assert_not_called()

    def test_scenario_dispatch_does_not_leak_namespace_protocol(self):
        args = argparse.Namespace(tool_protocol="native")
        hook = lambda primary, **kwargs: kwargs
        self.assertNotIn("tool_protocol", demo._call_scenario(hook, False, args))
        self.assertEqual(demo._call_scenario(hook, False, args, tool_protocol="text")["tool_protocol"], "text")
        self.assertEqual(demo._call_scenario(lambda primary: "legacy-custom-hook", False,
                                             args, tool_protocol="native"), "legacy-custom-hook")

    def test_custom_context_is_not_rewritten(self):
        context = LITERAL + "\nAction: supplied_by_user\nThought: preserve"
        args = argparse.Namespace(tool_protocol="native")
        capable = SimpleNamespace(supports_native_tools=True)
        scenario = {"build_context": lambda include_overhead: context}
        self.assertEqual(demo._resolve_context(scenario, False, args, capable), context)

    def test_execution_contract_precedes_backend_capability_property(self):
        class CountedBackend:
            def __init__(self):
                self.capability_reads = 0
                self.generate_calls = 0

            @property
            def supports_native_tools(self):
                self.capability_reads += 1
                return True

            def generate(self, messages, **kwargs):
                self.generate_calls += 1
                raise AssertionError("Backend must not run")

        runtime = PoolActCoordinator(1).bind_tools({}, 0, time_budget=None)
        for requested in ("auto", "native", "text"):
            backend = CountedBackend()
            with self.subTest(requested=requested), self.assertRaisesRegex(ValueError, "Execution contract"):
                run_react_loop(llm=backend, tools=runtime.tools, agent_clock=runtime.clock,
                               observation_augmenter=runtime.observation_augmenter,
                               pre_tool_hook=runtime.pre_tool_hook, time_budget=10.,
                               max_steps=0, tool_protocol=requested)
            self.assertEqual(backend.capability_reads, 0)
            self.assertEqual(backend.generate_calls, 0)


class NativeRunnerWireTest(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.stack.enter_context(fixture_data())
        self.stack.enter_context(mock.patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": ""}))
        self.directory = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.clients = []

    def tearDown(self):
        self.stack.close()

    def factory(self, scenario_name, native=True):
        final = {
            "restricted_search": "Ada Example",
            "evidence_audit": json.dumps({"nda-11": {"label": "NotMentioned", "evidence_ids": []}}),
            "tuning": tuning.format_config(tuning.REFERENCE_CONFIGS[0]),
        }[scenario_name]
        name, arguments = {
            "restricted_search": ("search", {"query": "Ada Example"}),
            "evidence_audit": ("human_feedback", {"nda_id": "nda-11", "evidence_ids": []}),
            "tuning": ("evaluate_config", tuning.REFERENCE_CONFIGS[0]),
        }[scenario_name]

        def build(*args, **kwargs):
            requests = []
            call = {"id": "opaque:fixture:1", "type": "function", "function": {
                "name": name, "arguments": json.dumps(arguments),
            }}
            assistant = {"role": "assistant", "content": None,
                         "reasoning_content": "Preserve fixture reasoning.", "tool_calls": [call]}
            if not native:
                assistant = {"role": "assistant", "content": "Action: " + name + " " + json.dumps(arguments)}

            def transport(request, timeout):
                payload = json.loads(request.data.decode("utf-8"))
                requests.append(payload)
                if len(requests) > 2:
                    raise AssertionError("Unexpected semantic retry")
                message = assistant if len(requests) == 1 else {"role": "assistant", "content": "Answer: " + final}
                return json.dumps({"choices": [{"message": message,
                    "finish_reason": "tool_calls" if native and len(requests) == 1 else "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5}}).encode("utf-8")

            client = OpenAICompatibleLLM(api_key="offline-placeholder", model="unrelated-portable-model",
                                         base_url="http://mock.invalid/v1/chat/completions",
                                         transport=transport, max_retries=0)
            self.clients.append((requests, assistant))
            return client
        return build

    def assert_wire(self, scenario_name, expected_clients):
        self.assertEqual(len(self.clients), expected_clients)
        function = {"tuning": "evaluate_config", "restricted_search": "search",
                    "evidence_audit": "human_feedback"}[scenario_name]
        for requests, assistant in self.clients:
            self.assertEqual(len(requests), 2)
            first, second = requests
            self.assertEqual(first["tool_choice"], "auto")
            self.assertIs(first["parallel_tool_calls"], False)
            self.assertEqual(first["tools"][0]["function"]["name"], function)
            context = first["messages"][1]["content"]
            self.assertIn("Call the " + function + " function", context)
            self.assertIn("native tool call", context)
            self.assertNotIn("Action format:", context)
            self.assertNotIn("Action: " + function + " ", context)
            if scenario_name != "tuning":
                self.assertIn(LITERAL, context)
            self.assertIn(assistant, second["messages"])
            tool_messages = [m for m in second["messages"] if m["role"] == "tool"]
            self.assertEqual(len(tool_messages), 1)
            self.assertEqual(tool_messages[0]["tool_call_id"], "opaque:fixture:1")

    def test_demo_native_wire_all_three_scenarios(self):
        for requested in ("auto", "native"):
            for scenario_name in demo._SCENARIOS:
                with self.subTest(scenario=scenario_name, requested=requested):
                    self.clients = []
                    argv = ["demo_experiment.py", "--backend", "openai", "--scenario", scenario_name,
                            "--cost-regime", "cost_free", "--max-steps", "2", "--max-evals", "2",
                            "--tool-protocol", requested]
                    with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), \
                         mock.patch.object(demo, "build_llm", side_effect=self.factory(scenario_name)):
                        demo.main()
                    self.assert_wire(scenario_name, 1)

    def test_direct_loop_does_not_rewrite_arbitrary_context(self):
        client = self.factory("restricted_search")()
        context = LITERAL + '\nAction: search {"query": "caller-owned text"}'
        result = run_react_loop(
            llm=client, tools=search.build_tools(), time_budget=None, max_steps=2,
            context=context, tool_protocol="native",
            answer_evaluator=search.build_answer_evaluator(0),
        )
        self.assertEqual(result["tool_protocol"], "native")
        self.assertEqual(self.clients[0][0][0]["messages"][1]["content"], context)

    def test_direct_library_caller_can_share_resolver_with_builder(self):
        client = self.factory("restricted_search")()
        resolved = tool_protocol.resolve_tool_protocol(client, "auto")
        context = search.build_context(False, tool_protocol=resolved)
        run_react_loop(llm=client, tools=search.build_tools(), time_budget=None,
                       max_steps=2, context=context, tool_protocol=resolved,
                       answer_evaluator=search.build_answer_evaluator(0))
        self.assert_wire("restricted_search", 1)

    def test_native_preserves_nonprotocol_custom_system_and_instruction_notes(self):
        custom = ('Dataset field "Action:" and "Thought:" are literal labels.\n'
                  'Preserve this nonprotocol requirement: résumé / 中文 / {"flag": true}.')
        cases = [
            (None, [custom], build_system_prompt(instruction_notes=[custom])),
            (custom, [], custom),
            (build_system_prompt(instruction_notes=[custom]), [], build_system_prompt(instruction_notes=[custom])),
        ]
        for system_prompt, notes, original in cases:
            with self.subTest(system_prompt=system_prompt):
                self.clients = []
                client = self.factory("restricted_search")()
                before_notes = list(notes)
                context = search.build_context(False, tool_protocol="native")
                run_react_loop(llm=client, tools=search.build_tools(), time_budget=None,
                               max_steps=2, context=context, tool_protocol="native",
                               system_prompt=system_prompt, instruction_notes=notes,
                               answer_evaluator=search.build_answer_evaluator(0))
                actual = self.clients[0][0][0]["messages"][0]["content"]
                self.assertIn(custom, actual)
                self.assertEqual(actual, tool_protocol.native_system_prompt(original))
                self.assertEqual(notes, before_notes)
                self.assert_wire("restricted_search", 1)

    def test_sweep_native_wire_all_three_scenarios(self):
        for requested in ("auto", "native"):
            for scenario_name in demo._SCENARIOS:
                with self.subTest(scenario=scenario_name, requested=requested):
                    self.clients = []
                    args = _args(backend="openai", models="fixture", scenarios=scenario_name,
                                 output_dir=Path(self.directory), cost_regimes="cost_free",
                                 max_steps=2, max_evals=2, tool_protocol=requested)
                    job = sweep._build_jobs(args)[0]
                    # Source/data identity itself is tested separately; fixtures intentionally
                    # have no benchmark files on disk. Keep this test CPU-only and portable.
                    with mock.patch.object(sweep, "evaluation_identity", return_value={"sha256": "fixture"}), \
                         mock.patch.object(sweep, "bind_evaluation_identity"), \
                         mock.patch.object(sweep, "build_llm", side_effect=self.factory(scenario_name)):
                        result = sweep._run_job(args, job, "offline-placeholder")
                    self.assertTrue(result["score_check"]["ok"])
                    self.assertEqual(result["tool_protocol"], "native")
                    self.assert_wire(scenario_name, 1)

    def test_pool_native_wire_all_scenarios_and_three_strategies(self):
        for requested in ("auto", "native"):
            for scenario_name in demo._SCENARIOS:
                for strategy in pool.STRATEGIES:
                    with self.subTest(scenario=scenario_name, strategy=strategy, requested=requested):
                        self.clients = []
                        argv = ["run_poolact.py", "--backend", "openai", "--model", "fixture",
                                "--scenario", scenario_name, "--agents", "2", "--max-steps", "2",
                                "--question-index", "0",
                                "--max-evals", "2", "--tool-protocol", requested,
                                "--output-dir", self.directory]
                        with mock.patch.object(sys, "argv", argv):
                            args = pool.parse_args()
                        with mock.patch.object(pool, "build_llm", side_effect=self.factory(scenario_name)):
                            result = pool._run_strategy(args, strategy, "offline-placeholder", None, "no_budget")
                        self.assertTrue(all(agent["score_check"]["ok"] for agent in result["agent_results"]))
                        self.assertTrue(all(agent["tool_protocol"] == "native" for agent in result["agent_results"]))
                        self.assert_wire(scenario_name, 2)

    def test_capable_client_explicit_text_wire_through_all_entrypoints(self):
        for entrypoint in ("demo", "sweep", "naive", "cached", "poolact"):
            with self.subTest(entrypoint=entrypoint):
                self.clients = []
                factory = self.factory("tuning", native=False)
                if entrypoint == "demo":
                    argv = ["demo_experiment.py", "--backend", "openai", "--scenario", "tuning",
                            "--cost-regime", "cost_free", "--max-steps", "2", "--max-evals", "2",
                            "--tool-protocol", "text"]
                    with mock.patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()), \
                         mock.patch.object(demo, "build_llm", side_effect=factory):
                        demo.main()
                elif entrypoint == "sweep":
                    args = _args(backend="openai", models="fixture", scenarios="tuning",
                                 output_dir=Path(self.directory), cost_regimes="cost_free",
                                 max_steps=2, max_evals=2, tool_protocol="text")
                    job = sweep._build_jobs(args)[0]
                    with mock.patch.object(sweep, "evaluation_identity", return_value={"sha256": "fixture"}), \
                         mock.patch.object(sweep, "bind_evaluation_identity"), \
                         mock.patch.object(sweep, "build_llm", side_effect=factory):
                        result = sweep._run_job(args, job, "offline-placeholder")
                    self.assertEqual(result["tool_protocol"], "text")
                else:
                    argv = ["run_poolact.py", "--backend", "openai", "--model", "fixture",
                            "--scenario", "tuning", "--agents", "2", "--max-steps", "2",
                            "--max-evals", "2", "--tool-protocol", "text", "--output-dir", self.directory]
                    with mock.patch.object(sys, "argv", argv):
                        args = pool.parse_args()
                    with mock.patch.object(pool, "build_llm", side_effect=factory):
                        result = pool._run_strategy(args, entrypoint, "offline-placeholder", None, "no_budget")
                    self.assertTrue(all(agent["tool_protocol"] == "text" for agent in result["agent_results"]))
                self.assertEqual(len(self.clients), 1 if entrypoint in ("demo", "sweep") else 2)
                for requests, _ in self.clients:
                    self.assertEqual(len(requests), 2)
                    for payload in requests:
                        for name in ("tools", "tool_choice", "parallel_tool_calls"):
                            self.assertNotIn(name, payload)
                    context = requests[0]["messages"][1]["content"]
                    task_context = tuning.build_context(False)
                    if entrypoint == "poolact":
                        # The unchanged coordinator appends its graph guidance.
                        self.assertTrue(context == task_context or
                                        context.startswith(task_context + "\n\n[Parallel Exploration"))
                    else:
                        self.assertEqual(context, task_context)
                    self.assertIn("Action format: Action: evaluate_config", context)
                    self.assertFalse(any(m["role"] == "tool" for m in requests[1]["messages"]))


if __name__ == "__main__":
    unittest.main()
