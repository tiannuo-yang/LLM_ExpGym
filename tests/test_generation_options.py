import argparse
import io
import os
import sys
import unittest
from unittest import mock

import demo_experiment
from scripts import run_paper_sweep, run_poolact


class GenerationOptionsTest(unittest.TestCase):
    PARSERS = (demo_experiment, run_paper_sweep, run_poolact)
    FACTORIES = {
        "openai": "OpenAICompatibleLLM",
        "gemini": "build_gemini_client",
        "openrouter": "build_openrouter_client",
        "sub2api": "build_sub2api_client",
        "vllm": "build_vllm_client",
    }

    def _parse(self, module, options):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(sys, "argv", [module.__name__, *options]):
                return module.parse_args()

    def test_all_cli_generation_options_default_to_none(self):
        for module in self.PARSERS:
            with self.subTest(cli=module.__name__):
                args = self._parse(module, [])
                self.assertIsNone(args.max_tokens)
                self.assertIsNone(args.chat_template_kwargs)
                self.assertIsNone(args.reasoning_effort)
                self.assertEqual(args.max_steps, 30)
                self.assertEqual(args.tool_protocol, "auto")
                self.assertEqual(args.max_protocol_retries, 1)
                self.assertEqual(args.tuning_final_policy, "legacy")

    def test_all_cli_accept_portable_protocol_options(self):
        for module in self.PARSERS:
            with self.subTest(cli=module.__name__):
                args = self._parse(module, [
                    "--tool-protocol", "text", "--max-protocol-retries", "0",
                    "--reasoning-effort", "high", "--tuning-final-policy", "legacy",
                ])
                self.assertEqual(demo_experiment._loop_options(args), {
                    "tool_protocol": "text", "max_protocol_retries": 0,
                    "tuning_final_policy": "legacy",
                })
                self.assertEqual(demo_experiment._generation_options(args)["reasoning_effort"], "high")

    def test_all_cli_reject_invalid_protocol_options(self):
        for module in self.PARSERS:
            for option, value in (
                ("--tool-protocol", "guess"), ("--max-protocol-retries", "-1"),
                ("--max-protocol-retries", "1.5"), ("--tuning-final-policy", "best"),
            ):
                with self.subTest(cli=module.__name__, option=option, value=value):
                    with mock.patch.object(sys, "stderr", io.StringIO()):
                        with self.assertRaises(SystemExit):
                            self._parse(module, [option, value])

    def test_all_cli_accept_positive_tokens_and_json_object(self):
        for module in self.PARSERS:
            with self.subTest(cli=module.__name__):
                args = self._parse(
                    module,
                    [
                        "--max-tokens", "4096",
                        "--chat-template-kwargs",
                        '{"enable_thinking":false,"nested":{"label":"中文","values":[1,null]}}',
                    ],
                )
                self.assertEqual(args.max_tokens, 4096)
                self.assertEqual(
                    args.chat_template_kwargs,
                    {"enable_thinking": False, "nested": {"label": "中文", "values": [1, None]}},
                )

    def test_all_cli_reject_invalid_token_limits(self):
        for module in self.PARSERS:
            for value in ("0", "-1", "1.5", "true"):
                with self.subTest(cli=module.__name__, value=value):
                    with mock.patch.object(sys, "stderr", io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            self._parse(module, ["--max-tokens", value])
                    self.assertEqual(raised.exception.code, 2)

    def test_all_cli_require_strict_json_object(self):
        invalid_values = (
            "[]", "null", "true", "1", '"text"', "{broken}",
            '{"value":NaN}', '{"value":Infinity}', '{"nested":[-Infinity]}',
            '{"value":1e309}',
        )
        for module in self.PARSERS:
            for value in invalid_values:
                with self.subTest(cli=module.__name__, value=value):
                    with mock.patch.object(sys, "stderr", io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            self._parse(module, ["--chat-template-kwargs", value])
                    self.assertEqual(raised.exception.code, 2)

    def test_build_llm_passes_generation_options_to_every_real_backend(self):
        args = self._parse(
            demo_experiment,
            [
                "--model", "Kimi-K3", "--max-tokens", "4096",
                "--chat-template-kwargs", '{"enable_thinking":false}',
                "--reasoning-effort", "high",
            ],
        )
        for backend, factory in self.FACTORIES.items():
            with self.subTest(backend=backend):
                with mock.patch(f"expgym.llm_clients.{factory}") as build:
                    client = demo_experiment.build_llm(backend, [], args)
                self.assertIs(client, build.return_value)
                self.assertEqual(build.call_args[1]["max_tokens"], 4096)
                self.assertEqual(build.call_args[1]["reasoning_effort"], "high")
                self.assertEqual(
                    build.call_args[1]["chat_template_kwargs"],
                    {"enable_thinking": False},
                )

    def test_vllm_disable_thinking_merges_without_mutating_explicit_options(self):
        for explicit in (None, {"custom_option": "preserved"}, {"enable_thinking": False}):
            with self.subTest(explicit=explicit):
                args = argparse.Namespace(
                    max_tokens=None,
                    chat_template_kwargs=explicit,
                    vllm_disable_thinking=True,
                )
                original = None if explicit is None else dict(explicit)
                resolved = demo_experiment._generation_options(args)
                self.assertEqual(
                    resolved["chat_template_kwargs"],
                    {**(explicit or {}), "enable_thinking": False},
                )
                self.assertEqual(args.chat_template_kwargs, original)

    def test_vllm_disable_thinking_rejects_explicit_conflicting_option(self):
        args = self._parse(
            demo_experiment,
            [
                "--vllm-disable-thinking",
                "--chat-template-kwargs", '{"enable_thinking":true}',
            ],
        )
        with mock.patch("expgym.llm_clients.build_vllm_client") as build:
            with self.assertRaisesRegex(ValueError, "enable_thinking"):
                demo_experiment.build_llm("vllm", [], args)
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
