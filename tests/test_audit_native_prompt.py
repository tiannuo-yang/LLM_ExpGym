"""CPU-only regression for task-owned Audit invocation guidance.

No dataset, model endpoint or score is consulted. Keep the text-protocol prompt
and caller-owned document/hypothesis text intact; native instructions must not
turn the old fixed example into a required first action.
"""
from contextlib import contextmanager, ExitStack
import json
import os
import unittest
from unittest.mock import patch

from expgym import task_evidence_audit as audit
from expgym.llm_clients import OpenAICompatibleLLM
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import run_react_loop
from expgym.tool_protocol import resolve_tool_protocol


OLD_NATIVE_COMMAND = (
    'Call the human_feedback function with arguments '
    '{"nda_id": "nda-11", "evidence_ids": [3, 7]} using a native tool call.'
)
OLD_TEXT_ACTION = 'Action: human_feedback {"nda_id": "nda-11", "evidence_ids": [3, 7]}'
OLD_INPUT = '  Input: {{"nda_id": "...", "evidence_ids": [segment_ids]}}'
LABELS = {
    "hyp-fixture-a": {"short_description": "first", "hypothesis": "First hypothesis."},
    "hyp-fixture-b": {"short_description": "second", "hypothesis": "Second hypothesis."},
}
DOCUMENT = audit.Document(
    91, "synthetic.txt", [{"span_index": 0, "text": "Synthetic document segment."}],
    {name: {"choice": "NotMentioned", "spans": []} for name in LABELS},
)


@contextmanager
def fixture_data(document=DOCUMENT, labels=LABELS):
    with ExitStack() as stack:
        stack.enter_context(patch.object(audit, "_load_example", return_value=document))
        stack.enter_context(patch.object(audit, "_get_doc", return_value=document))
        stack.enter_context(patch.object(audit, "_get_labels", return_value=labels))
        stack.enter_context(patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": ""}))
        yield


class AuditNativePromptTest(unittest.TestCase):
    def assert_native_instructions(self, context):
        instructions = context.split("Document segments:", 1)[0]
        self.assertNotIn(OLD_NATIVE_COMMAND, instructions)
        self.assertNotIn(OLD_TEXT_ACTION, instructions)
        self.assertNotIn(OLD_INPUT, instructions)
        self.assertNotIn('"evidence_ids": [3, 7]', instructions)
        self.assertIn("supplied function schema for nda_id and evidence_ids", instructions)
        self.assertIn("Choose whether and what to verify", instructions)
        self.assertIn("current document and hypotheses", instructions)
        self.assertIn("at most one native tool call per assistant turn", instructions)
        self.assertIn("then wait for its result", instructions)

    def test_native_instructions_do_not_prescribe_fixed_payload(self):
        with fixture_data():
            for overhead in (False, True):
                for split in ("cc-small", "cc-medium", "cc-large"):
                    with self.subTest(overhead=overhead, split=split):
                        context = audit.build_context(
                            overhead, cc_split=split, tool_protocol="native",
                        )
                        self.assert_native_instructions(context)
                        self.assertIn("Your final answer MUST include ALL 2 hypotheses.", context)

    def test_legacy_text_and_answer_format_remain_unchanged(self):
        with fixture_data():
            for overhead in (False, True):
                old = audit.build_context(overhead, tool_protocol="text")
                native = audit.build_context(overhead, tool_protocol="native")
                self.assertEqual(old, audit.build_context(overhead))
                self.assertIn(OLD_INPUT, old)
                self.assertIn(OLD_TEXT_ACTION, old)
                # Reverse precisely the two authorized task-owned line changes.
                restored = native.replace(
                    "  Input: use the supplied function schema for nda_id and evidence_ids.",
                    OLD_INPUT,
                ).replace(
                    "Choose whether and what to verify from the current document and hypotheses. "
                    "Make at most one native tool call per assistant turn, then wait for its result.",
                    OLD_TEXT_ACTION,
                )
                self.assertEqual(old, restored)

    def test_literal_commands_in_document_and_hypotheses_are_not_scrubbed(self):
        literal = OLD_NATIVE_COMMAND + "\n" + OLD_TEXT_ACTION + "\n" + OLD_INPUT
        document = audit.Document(
            91, "synthetic.txt", [{"span_index": 0, "text": literal}],
            DOCUMENT.annotations,
        )
        labels = {
            "hyp-fixture-a": {"short_description": "first", "hypothesis": literal},
            "hyp-fixture-b": LABELS["hyp-fixture-b"],
        }
        with fixture_data(document, labels):
            for order in (list(labels), list(reversed(labels))):
                old = audit.build_context(False, hypothesis_order=order, tool_protocol="text")
                native = audit.build_context(False, hypothesis_order=order, tool_protocol="native")
                self.assert_native_instructions(native)
                old_data = old.split("Document segments:", 1)[1]
                new_data = native.split("Document segments:", 1)[1]
                self.assertEqual(old_data, new_data)
                self.assertEqual(new_data.count(OLD_NATIVE_COMMAND), 2)

    def test_native_schema_contains_real_hypotheses_not_example_ids(self):
        with fixture_data():
            schema = audit.build_tools()["human_feedback"].__expgym_tool_schema__
            self.assertEqual(schema["parameters"]["properties"]["nda_id"]["enum"], list(LABELS))
            self.assertEqual(schema["parameters"]["required"], ["nda_id", "evidence_ids"])
            self.assertNotIn("nda-11", json.dumps(schema))

    def test_mock_wire_is_model_independent_for_native_and_auto(self):
        observed_contexts = []
        for model in ("unfamiliar-provider/alpha-91", "other-vendor/beta-17"):
            for requested in ("native", "auto"):
                with self.subTest(model=model, requested=requested), fixture_data():
                    requests = []

                    def transport(request, timeout):
                        payload = json.loads(request.data.decode("utf-8"))
                        requests.append(payload)
                        if len(requests) > 1:
                            raise AssertionError("No repair or extra request is expected")
                        return json.dumps({"choices": [{
                            "message": {"role": "assistant", "content": 'Answer: {}'},
                            "finish_reason": "stop",
                        }], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}).encode()

                    client = OpenAICompatibleLLM(
                        api_key="offline-placeholder", model=model,
                        base_url="http://offline.invalid/v1", transport=transport,
                        max_retries=0,
                    )
                    resolved = resolve_tool_protocol(client, requested)
                    context = audit.build_context(False, tool_protocol=resolved)
                    result = run_react_loop(
                        llm=client, tools=audit.build_tools(), context=context,
                        system_prompt=audit.build_system_prompt(False),
                        tool_protocol=resolved, max_steps=1,
                    )
                    self.assertEqual(result["answer"], "{}")
                    self.assertEqual(len(requests), 1)
                    request = requests[0]
                    self.assertEqual(request["model"], model)
                    self.assertEqual(request["tool_choice"], "auto")
                    self.assertIs(request["parallel_tool_calls"], False)
                    self.assert_native_instructions(request["messages"][1]["content"])
                    observed_contexts.append(request["messages"])
        self.assertTrue(all(messages == observed_contexts[0] for messages in observed_contexts))

    def test_pool_graph_preserves_pending_action_without_fixed_task_command(self):
        with fixture_data():
            coordinator = PoolActCoordinator(n_agents=2)
            runtime = coordinator.bind_tools(audit.build_tools(), 1)
            payload = json.dumps({"nda_id": "hyp-fixture-a", "evidence_ids": []})
            coordinator.graph.record_claim("human_feedback", payload, 0, start_time=0.0)
            context = runtime.observation_augmenter(
                audit.build_context(False, tool_protocol="native"),
            )
            self.assert_native_instructions(context)
            self.assertIn("verify nda:hyp-fixture-a ev:[] [agent 0]", context)
            self.assertIn("Select an action not listed above.", context)
            self.assertNotIn(OLD_NATIVE_COMMAND, context)


if __name__ == "__main__":
    unittest.main()
