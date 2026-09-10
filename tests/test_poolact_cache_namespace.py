"""No-provider checks for independent PoolAct prompt-cache routing keys."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

from scripts import run_poolact


class PoolActCacheNamespaceTests(unittest.TestCase):
    def make_args(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(sys, "argv", [
            "run_poolact.py", "--backend", "openai", "--model", "generic-model",
            "--prompt-cache-key", "study", "--question-index", "0",
        ]):
            return run_poolact.parse_args()

    def key(self, args, strategy="poolact", agent_id=0):
        return run_poolact._agent_namespace(args, strategy, agent_id, None).prompt_cache_key

    def test_full_invocation_identity_separates_keys(self):
        args = self.make_args()
        baseline = self.key(args)
        changes = {
            "prompt_cache_key": "another-study",
            "backend": "sub2api",
            "model": "another-generic-model",
            "scenario": "restricted_search",
            "tuning_task": "hpobench:nasbench101:B",
            "question_index": 1,
            "data_source": "phantom_seed2",
            "cc_split": "cc-small",
            "cost_regime": "cost_free",
            "agents": args.agents + 1,
            "seed": args.seed + 1,
            "base_seed": args.seed + 20,
            "repeat_index": 1,
            "temperature": 0.25,
            "max_steps": args.max_steps + 1,
            "max_evals": args.max_evals + 1,
            "max_context_tokens": 2048,
            "probes": args.probes + 1,
            "max_tokens": 1024,
            "top_p": 0.5,
            "top_k": 10,
            "chat_template_kwargs": {"enable_thinking": False},
            "reasoning_effort": "high",
            "tool_protocol": "text",
            "max_protocol_retries": 0,
            "tuning_final_policy": "submitted",
            "missing_final_policy": "task-abstention-v1",
            "_evaluation_identity": {"sha256": "a" * 64},
        }
        keys = {baseline}
        for name, value in changes.items():
            with self.subTest(field=name):
                changed = copy.deepcopy(args)
                setattr(changed, name, value)
                key = self.key(changed)
                self.assertNotEqual(baseline, key)
                self.assertNotIn(key, keys)
                keys.add(key)

    def test_single_repeat_processes_keep_repeat_identity(self):
        args = self.make_args()
        self.assertEqual(args.repeats, 1)
        args.repeat_index = 0
        first = self.key(args)
        args.repeat_index = 1
        self.assertNotEqual(first, self.key(args))

    def test_agents_strategies_and_items_have_distinct_bounded_keys(self):
        args = self.make_args()
        args.prompt_cache_key = "命名空间/" + "x" * 200
        keys = set()
        for item in range(3):
            args.question_index = item
            for strategy in run_poolact.STRATEGIES:
                for agent in range(4):
                    key = self.key(args, strategy, agent)
                    self.assertLessEqual(len(key), 64)
                    self.assertRegex(key, r"^[A-Za-z0-9_.-]+$")
                    keys.add(key)
        self.assertEqual(len(keys), 36)

    def test_generation_mapping_order_and_output_relocation_are_stable(self):
        args = self.make_args()
        args.chat_template_kwargs = {"enable_thinking": False, "nested": {"a": 1, "b": 2}}
        first = self.key(args)
        args.chat_template_kwargs = {"nested": {"b": 2, "a": 1}, "enable_thinking": False}
        args.output_dir = Path("/different/output/location")
        args.terminal_evidence_dir = Path("/different/evidence/location")
        self.assertEqual(first, self.key(args))

    def test_credentials_and_unrelated_namespace_fields_are_not_serialized(self):
        args = self.make_args()
        first = self.key(args)
        args.api_key = "test-secret-not-a-real-key"
        args.api_key_file = Path("/credentials/secret-file")
        args.base_url = "https://private-user:private-password@example.invalid/v1"
        args.extra_private_field = "private-metadata"
        original_dumps = json.dumps
        serialized = []

        def record(value, **kwargs):
            encoded = original_dumps(value, **kwargs)
            serialized.append(encoded)
            return encoded

        with mock.patch.object(run_poolact.json, "dumps", side_effect=record):
            self.assertEqual(first, self.key(args))
        self.assertEqual(len(serialized), 1)
        for forbidden in ("api_key", "secret-file", "private-user", "private-password", "private-metadata"):
            self.assertNotIn(forbidden, serialized[0])

    def test_disabled_namespace_is_not_enabled_implicitly(self):
        args = self.make_args()
        for base in (None, ""):
            args.prompt_cache_key = base
            self.assertIsNone(self.key(args))

    def test_vllm_effective_thinking_control_is_part_of_identity(self):
        args = self.make_args()
        args.backend = "vllm"
        first = self.key(args)
        args.vllm_disable_thinking = True
        second = self.key(args)
        self.assertNotEqual(first, second)
        args.vllm_disable_thinking = False
        args.chat_template_kwargs = {"enable_thinking": False}
        self.assertEqual(second, self.key(args))

    def test_input_namespace_is_unchanged_and_same_invocation_is_stable(self):
        args = self.make_args()
        before = copy.deepcopy(vars(args))
        self.assertEqual(self.key(args), self.key(args))
        self.assertEqual(before, vars(args))


if __name__ == "__main__":
    unittest.main()
