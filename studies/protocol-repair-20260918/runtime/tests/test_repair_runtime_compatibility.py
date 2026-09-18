"""No-network checks for the merged historical transports and repaired parser."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from demo_experiment import build_llm
from expgym.llm_clients import OpenAICompatibleLLM
from expgym.react_loop import LLMOutput, run_react_loop
from scripts import run_paper_sweep as sweep, run_poolact as pool
from scripts.run_study_queue import make_plan


class RepairRuntimeCompatibilityTest(unittest.TestCase):
    def test_historical_cache_field_changes_only_selected_wire_field(self):
        for field in ("prompt_cache_key", "cache_salt"):
            for key in (None, "invocation-isolation"):
                with self.subTest(field=field, key=key):
                    requests = []

                    def transport(request, timeout):
                        requests.append(json.loads(request.data))
                        return json.dumps({"choices": [{"message": {"role": "assistant", "content": "Answer: done"}, "finish_reason": "stop"}]}).encode()

                    client = OpenAICompatibleLLM(api_key="test-only", model="model", prompt_cache_key=key,
                                                 prompt_cache_key_field=field, transport=transport)
                    client.generate("test")
                    body = requests[0]
                    if key is None:
                        self.assertNotIn("prompt_cache_key", body)
                        self.assertNotIn("cache_salt", body)
                    else:
                        self.assertEqual(body[field], key)
                        self.assertNotIn("cache_salt" if field == "prompt_cache_key" else "prompt_cache_key", body)

    def test_cache_field_survives_both_runners_and_resume_identity(self):
        args = sweep.parse_args(["--backend", "openai", "--models", "model", "--prompt-cache-key-field", "cache_salt"])
        job = sweep._build_jobs(args)[0]
        namespace = sweep._namespace_for_job(args, job, "test-only")
        self.assertEqual(build_llm("openai", [], namespace).config.prompt_cache_key_field, "cache_salt")
        old_key = sweep._resume_key(args, job, evaluation={"sha256": "fixture"})
        args.prompt_cache_key_field = "prompt_cache_key"
        self.assertNotEqual(old_key, sweep._resume_key(args, job, evaluation={"sha256": "fixture"}))
        args = pool.parse_args(["--backend", "openai", "--model", "model", "--prompt-cache-key-field", "cache_salt"])
        namespace = pool._agent_namespace(args, "poolact", 0, "test-only")
        client = build_llm("openai", [], namespace)
        self.assertEqual(client.config.prompt_cache_key_field, "cache_salt")
        self.assertIsNone(client.config.prompt_cache_key)
        self.assertEqual(pool._resolved_config(args, None)["prompt_cache_key_field"], "cache_salt")

    def test_queue_provider_override_keeps_historical_no_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = make_plan({"stages": [{"label": "fixture", "runner": "poolact", "args": [
                "--backend", "fake", "--model", "fake", "--scenario", "tuning",
                "--tuning-task", "neural_network_training", "--strategies", "poolact",
            ]}]}, study_id="compatibility", output_root=Path(tmp), default_python=sys.executable)
            job = plan["jobs"][0]
            self.assertTrue(job["args"]["prompt_cache_key"].startswith("queue-"))
            self.assertIsNone(job["identity"]["args"]["prompt_cache_key"])
            job["args"]["prompt_cache_key"] = None
            # Worker reconstructs Namespace from these explicit job arguments.
            import argparse
            namespace = argparse.Namespace(**copy.deepcopy(job["args"]))
            agent = pool._agent_namespace(namespace, "poolact", 0, "test-only")
            self.assertIsNone(agent.prompt_cache_key)

    def test_all_final_entrypoints_share_repaired_parser(self):
        from expgym.tool_protocol import ANSWER_PROTOCOL_VERSION, parse_final_answer
        answer = 'Here is my final answer:\n\n**Answer:** {"x":1}'

        class Replay:
            def __init__(self, native, forced):
                self.supports_native_tools = native
                self.outputs = iter(([LLMOutput("", finish_reason="length")] if forced else []) + [LLMOutput(answer, finish_reason="stop")])

            def generate(self, messages, **kwargs):
                return next(self.outputs)

        for native in (False, True):
            for forced in (False, True):
                with self.subTest(native=native, forced=forced):
                    result = run_react_loop(Replay(native, forced), {}, max_steps=1,
                                            answer_evaluator=lambda text: float(json.loads(text)["x"]),
                                            capture_trace_v2=True)
                    self.assertEqual(result["answer"], parse_final_answer(answer))
                    self.assertEqual(result["answer_perf"], 1.)
                    self.assertEqual(result["answer_protocol_version"], ANSWER_PROTOCOL_VERSION)
                    self.assertEqual(result["answer_source"], "forced_model_answer" if forced else "natural_model_answer")


if __name__ == "__main__":
    unittest.main()
