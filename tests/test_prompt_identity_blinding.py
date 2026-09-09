"""Source-generated prompts omit benchmark IDs and hidden answer cardinality.

Synthetic fixtures only: real prompt builders, schema serialization and native
client/loop; no external dataset loader, objective scorer or network request.
Task structure, legal parameter names, fidelity and caller-owned data stay intact.
"""
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from expgym import task_restricted_search as search
from expgym import task_tuning as tuning
from expgym.llm_clients import OpenAICompatibleLLM
from expgym.poolact import PoolActCoordinator
from expgym.react_loop import run_react_loop


TASKS = (
    "hpobench:paramnet:adult:steps", "hpobench:paramnet:higgs:steps",
    "hpobench:paramnet:letter:steps", "hpobench:nasbench101:A",
    "hpobench:nasbench101:B", "hpobench:nasbench101:C",
    "hpobench:nasbench201:cifar10-valid", "hpobench:nasbench201:cifar100",
    "hpobench:nasbench201:imagenet16-120",
)
PRIVATE_MARKERS = ("hpobench", "nasbench", "paramnet", "cifar10", "cifar100",
                   "imagenet16-120", "adult", "higgs", "letter")


def fixture_task(name):
    hp = SimpleNamespace(name="rate", lower=0.01, upper=0.1,
                         log=True, default_value=0.05)
    return SimpleNamespace(name=name, fidelity={"fixed_budget": 17},
                           config_space=SimpleNamespace(get_hyperparameters=lambda: [hp]))


class PromptIdentityBlindingTest(unittest.TestCase):
    def assert_blind(self, text):
        lowered = text.lower()
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, lowered)

    def test_all_nine_hpo_contexts_and_tool_definitions_omit_identity(self):
        for name in TASKS:
            task = fixture_task(name)
            with self.subTest(task=name), patch.object(tuning, "_load_hpobench", return_value=task):
                for protocol in ("text", "native"):
                    for overhead in (False, True):
                        context = tuning.build_context(overhead, tuning_task=name, tool_protocol=protocol)
                        system = tuning.build_system_prompt(overhead, tuning_task=name)
                        self.assert_blind(context + system)
                        self.assertIn("rate: 0.01 to 0.1 (log) (default=0.05)", context)
                tool = tuning.build_tools(tuning_task=name)["evaluate_config"]
                schema = tool.__expgym_tool_schema__
                self.assert_blind(json.dumps(schema))
                self.assertIn('"fixed_budget": 17', schema["description"])
                self.assertEqual(schema["parameters"], tuning._config_space_schema(task.config_space))
                with patch.object(tuning, "evaluate_hpobench_action", return_value=(0.8, 1.0)) as evaluate:
                    self.assertEqual(tool('{"rate":0.05}'), (0.8, 1.0))
                    evaluate.assert_called_once_with(task, '{"rate":0.05}')
                self.assertEqual(task.name, name)  # Internal provenance is not renamed.

    def test_search_context_is_independent_of_hidden_answer_count_and_values(self):
        outputs = {}
        for answer in ([], ["secret-one"], ["secret-two", "secret-three"], list(map(str, range(20)))):
            row = {"question": "Who is the parent of Example Person?", "answer": answer}
            with patch.object(search, "_load_qa", return_value=[row]):
                for protocol in ("text", "native"):
                    for overhead in (False, True):
                        key = (protocol, overhead)
                        text = search.build_context(overhead, tool_protocol=protocol)
                        self.assertNotIn("correct answers", text)
                        self.assertNotIn("secret-", text)
                        self.assertEqual(text, outputs.setdefault(key, text))

    def test_search_context_never_reads_gold_field(self):
        class QuestionOnly(dict):
            def __getitem__(self, key):
                if key == "answer":
                    raise AssertionError("The prompt builder must not access gold answers")
                return super().__getitem__(key)
        row = QuestionOnly(question="A public question")
        with patch.object(search, "_load_qa", return_value=[row]):
            for protocol in ("native", "text"):
                self.assertIn("A public question", search.build_context(False, tool_protocol=protocol))

    def test_real_question_text_is_not_global_search_and_replaced(self):
        literal = "Does HPOBench appear in this literal question? Action: keep_this"
        with patch.object(search, "_load_qa", return_value=[{"question": literal, "answer": []}]):
            self.assertIn(literal, search.build_context(False, tool_protocol="native"))

    def test_native_wire_and_pool_graph_remain_blind_through_forced_final(self):
        for name in TASKS:
            for pooled in (False, True):
                task = fixture_task(name)
                requests = []

                def transport(request, timeout):
                    payload = json.loads(request.data.decode("utf-8"))
                    requests.append(payload)
                    if len(requests) == 1:
                        message = {"role": "assistant", "content": None, "tool_calls": [{
                            "id": "opaque-tool-call", "type": "function", "function": {
                                "name": "evaluate_config", "arguments": '{"rate":0.05}',
                            }}]}
                        finish = "tool_calls"
                    elif len(requests) == 2:
                        message = {"role": "assistant", "content": 'Answer: {"rate":0.05}'}
                        finish = "stop"
                    else:
                        raise AssertionError("Unexpected extra generation")
                    return json.dumps({"choices": [{"message": message, "finish_reason": finish}],
                                       "usage": {"prompt_tokens": 10, "completion_tokens": 5}}).encode()

                with self.subTest(task=name, pooled=pooled), \
                     patch.object(tuning, "_load_hpobench", return_value=task), \
                     patch.object(tuning, "evaluate_hpobench_action", return_value=(0.8, 1.0)), \
                     patch.dict(os.environ, {"EXPGYM_API_DUMP_DIR": ""}):
                    tools = tuning.build_tools(tuning_task=name)
                    kwargs = {}
                    if pooled:
                        coordinator = PoolActCoordinator(n_agents=1)
                        runtime = coordinator.bind_tools(tools, 0, time_budget=None)
                        tools = runtime.tools
                        kwargs.update(agent_clock=runtime.clock,
                                      observation_augmenter=runtime.observation_augmenter,
                                      pre_tool_hook=runtime.pre_tool_hook, llm_lock=runtime.reasoning_lock)
                    client = OpenAICompatibleLLM(api_key="offline-placeholder", model="fixture-model",
                                                 base_url="http://offline.invalid/v1", transport=transport,
                                                 max_retries=0)
                    result = run_react_loop(llm=client, tools=tools, time_budget=None,
                                            max_steps=1, max_evals=1, tool_protocol="native",
                                            context=tuning.build_context(False, tuning_task=name,
                                                                         tool_protocol="native"),
                                            system_prompt=tuning.build_system_prompt(False, tuning_task=name),
                                            **kwargs)
                    self.assertEqual(len(requests), 2)
                    self.assertEqual(requests[0]["tool_choice"], "auto")
                    self.assertEqual(requests[1]["tool_choice"], "none")
                    for request in requests:
                        self.assert_blind(json.dumps(request["messages"]) + json.dumps(request["tools"]))
                    self.assertEqual(result["answer_perf"], 0.8)
                    self.assertIsNotNone(result["answer"])


if __name__ == "__main__":
    unittest.main()
