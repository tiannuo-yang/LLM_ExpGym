"""No-model-call contracts for the independent 21-trace v3 coordinator."""
from __future__ import annotations

import copy
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


HARNESSES = Path(__file__).resolve().parents[1]
STATIC = HARNESSES.parent / "validation/static_acceptance_v3.json"
SPEC = importlib.util.spec_from_file_location("scenario_smoke_v3_tests_subject", HARNESSES / "scenario_smoke_v3.py")
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class HarnessCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="expgym_scenario_v3_test_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def args(self, *extra):
        with contextlib.redirect_stderr(io.StringIO()):
            return subject.parse_args([
                "--output-dir", str(self.root / "output"),
                "--static-acceptance", str(STATIC), *extra,
            ])

    def write_profile(self, **changes):
        profile = copy.deepcopy(subject.profiles().DEFAULT_PROFILE)
        profile["randomness_contract"] = "seed_labels_only"
        profile.update(changes)
        path = self.root / "profile.json"
        path.write_text(json.dumps(profile), encoding="utf-8")
        return path


class PlanningTests(HarnessCase):
    def test_six_jobs_twenty_one_traces_twelve_skips(self):
        jobs = subject.build_jobs(self.args())
        self.assertEqual(len(jobs), 6)
        self.assertEqual(sum(job["expected_traces"] for job in jobs), 21)
        self.assertEqual(sum(1 if job["system"] == "expgym" else 3 for job in jobs), 12)
        self.assertEqual(subject.COUNTS["child_jobs"], 6)
        self.assertEqual(subject.COUNTS["all_agent_traces"], 21)
        self.assertEqual(subject.COUNTS["guarded_resume_skips"], 12)
        self.assertEqual(subject.COUNTS["native_coverage_cells"], 12)
        self.assertEqual(
            {(job["system"], job["scenario"], job["regime"]) for job in jobs},
            {(system, scenario, "cost_moderate") for system in ("expgym", "poolact")
             for scenario in ("tuning", "restricted_search", "evidence_audit")},
        )

    def test_commands_only_change_two_legacy_budget_values(self):
        args = self.args()
        original = {job["id"]: job for job in subject.helpers().build_jobs(args)}
        for job in subject.build_jobs(args):
            before, after = original[job["id"]]["command"], job["command"]
            self.assertEqual(len(before), len(after))
            expected_changes = {before.index("--max-steps") + 1, before.index("--max-evals") + 1}
            self.assertEqual({i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]}, expected_changes)
            self.assertEqual(after[after.index("--max-steps") + 1], "3")
            self.assertEqual(after[after.index("--max-evals") + 1], "2")

    def test_duplicate_legacy_budget_flag_is_rejected(self):
        args = self.args()
        jobs = subject.helpers().build_jobs(args)
        jobs[1]["command"] += ["--max-steps", "6"]
        with mock.patch.object(subject.helpers(), "build_jobs", return_value=jobs):
            with self.assertRaises(RuntimeError):
                subject.build_jobs(args)

    def test_changed_legacy_default_is_rejected(self):
        args = self.args()
        jobs = subject.helpers().build_jobs(args)
        job = next(job for job in jobs if job["regime"] == "cost_moderate")
        job["command"][job["command"].index("--max-evals") + 1] = "99"
        with mock.patch.object(subject.helpers(), "build_jobs", return_value=jobs):
            with self.assertRaises(RuntimeError):
                subject.build_jobs(args)

    def test_settings_have_no_stale_six_five_declaration(self):
        config = subject.settings(self.args())
        self.assertEqual((config["max_steps"], config["max_evals"]), (3, 2))
        self.assertEqual(config["regimes"], ["cost_moderate"])
        self.assertEqual(config["randomness_contract"], "seed_labels_only")
        self.assertEqual(config["logical_generation_upper_bound_per_agent"], 4)
        self.assertEqual(config["concurrency_bound"]["conservative_request_upper_bound"], 7)
        self.assertNotIn("6 steps", " ".join(config["deviations_from_paper"]))
        self.assertNotIn("5 evaluations", " ".join(config["deviations_from_paper"]))

    def test_fake_is_explicitly_not_native_coverage(self):
        args = self.args()
        self.assertEqual(subject.settings(args)["tool_protocol"], "auto")
        coverage = subject.classify_native_coverage(subject.build_jobs(args)[0], self.root / "absent", args)
        self.assertEqual(coverage["classification"], "fake_text_not_native")
        self.assertFalse(coverage["promotion_eligible"])
        self.assertFalse(coverage["coverage_complete"])

    def test_real_plan_uses_native_without_execution(self):
        args = self.args("--backend", "openai", "--base-url", "http://localhost:8080/v1")
        self.assertFalse(args.execute)
        self.assertEqual(subject.settings(args)["tool_protocol"], "native")
        self.assertEqual(subject.settings(args)["max_protocol_retries"], 1)

    def test_explicit_static_acceptance_is_required(self):
        with self.assertRaises(SystemExit):
            subject.parse_args(["--output-dir", str(self.root / "unused")])

    def test_real_execution_without_authority_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.args("--backend", "openai", "--base-url", "http://localhost:8080/v1", "--execute")

    def test_fake_cannot_carry_real_endpoint(self):
        with self.assertRaises(SystemExit):
            self.args("--base-url", "http://localhost:8080/v1")

    def test_fake_rejects_real_permission_parameters(self):
        for argv in (("--allow-real",), ("--authorization", str(self.root / "auth.json")),
                     ("--serving-binding", str(self.root / "serving.json"))):
            with self.assertRaises(SystemExit):
                self.args(*argv)

    def test_hostile_backend_environment_cannot_change_fake_commands(self):
        with mock.patch.dict("os.environ", {"EXPGYM_BACKEND": "openai", "OPENAI_BASE_URL": "http://localhost:1/v1",
                                            "OPENAI_API_KEY": "unit-test-placeholder-not-a-real-key"}):
            for job in subject.build_jobs(self.args()):
                command = job["command"]
                self.assertEqual(command.count("--backend"), 1)
                self.assertEqual(command[command.index("--backend") + 1], "fake")
                self.assertNotIn("--base-url", command)
                self.assertNotIn("unit-test-placeholder-not-a-real-key", command)

    def test_endpoint_rejects_credentials_and_query(self):
        for endpoint in ("http://user:secret@localhost/v1", "http://localhost/v1?api_key=secret", "http://localhost/v1#fragment"):
            with self.subTest(endpoint_kind=endpoint.split(":", 1)[0]):
                with self.assertRaises(SystemExit):
                    self.args("--backend", "openai", "--base-url", endpoint)

    def test_default_profile_is_seed_labels_without_mutating_library(self):
        args = self.args()
        selected = subject.generation_profile(args)
        self.assertEqual(selected["randomness_contract"], "seed_labels_only")
        self.assertEqual(subject.profiles().DEFAULT_PROFILE["randomness_contract"], "strict")
        self.assertEqual(selected["model"], "kimi-k3")
        self.assertEqual(selected["top_p"], 1.0)
        self.assertIsNone(selected["top_k"])

    def test_current_scope_rejects_unverified_model_and_strict_profile(self):
        for changes in ({"model": "unverified-model"}, {"top_p": 0.95}, {"randomness_contract": "strict"}):
            with self.subTest(fields=sorted(changes)):
                path = self.write_profile(**changes)
                with self.assertRaises(SystemExit):
                    self.args("--request-profile", str(path))

    def test_explicit_profile_raw_bytes_are_bound(self):
        path = self.write_profile()
        args = self.args("--request-profile", str(path))
        identity = subject.profiles().identity(args)
        self.assertEqual(identity["source"]["file_sha256"], subject.sha256(path))
        self.assertTrue(subject.profiles().unchanged(args))
        path.write_text(path.read_text() + "\n", encoding="utf-8")
        self.assertFalse(subject.profiles().unchanged(args))

    def test_resume_command_points_to_new_entrypoint(self):
        for job in subject.build_jobs(self.args()):
            command = subject.resume_command(job)
            self.assertEqual(command[2], str(subject.HERE))
            self.assertEqual(command[3], "--_resume-guard")
            self.assertEqual(command.count("--resume"), 1)
            self.assertNotIn(str(subject.LEGACY_PATH), command)
            self.assertEqual(command[-1], "--resume")

    def test_selected_output_must_not_be_inside_frozen_repo(self):
        with self.assertRaises(SystemExit):
            subject.parse_args(["--output-dir", str(HARNESSES.parents[1] / "LLM_ExpGym/runs/forbidden"),
                                "--static-acceptance", str(STATIC)])


class StaticBindingTests(HarnessCase):
    def receipt_args(self, mutate=None):
        args = self.args()
        receipt = json.loads(STATIC.read_text())
        if mutate:
            mutate(receipt)
        args.static_acceptance = self.root / "acceptance.json"
        args.static_acceptance.write_text(json.dumps(receipt), encoding="utf-8")
        return args

    def test_current_static_acceptance_is_usable(self):
        args = self.args()
        result = subject.validate_static_acceptance(args)
        self.assertEqual(result["sha256"], subject.sha256(STATIC))
        self.assertGreater(result["file_count"], 0)
        self.assertEqual(result["source_tree_sha256"], json.loads(STATIC.read_text())["source_tree_sha256"])

    def test_static_rejects_failed_check_and_boolean_exit(self):
        for code in (1, False):
            with self.subTest(exit_code=code):
                args = self.receipt_args(lambda r: r["checks"]["full_check"].update(exit_code=code))
                with self.assertRaises(ValueError):
                    subject.validate_static_acceptance(args)

    def test_static_rejects_escaping_inventory(self):
        args = self.receipt_args(lambda r: r.update(files={"../escape": "0" * 64}))
        with self.assertRaises(ValueError):
            subject.validate_static_acceptance(args)

    def test_static_rejects_incomplete_inventory(self):
        args = self.receipt_args(lambda r: r["files"].pop("demo_experiment.py"))
        with self.assertRaises(ValueError):
            subject.validate_static_acceptance(args)

    def test_static_rejects_wrong_source_hash(self):
        args = self.receipt_args(lambda r: r.update(source_tree_sha256="0" * 64))
        with self.assertRaises(ValueError):
            subject.validate_static_acceptance(args)

    def test_receipt_json_rejects_duplicate_keys_and_nonfinite(self):
        for content in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.subTest(content=content):
                path = self.root / "bad.json"
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(ValueError):
                    subject.read_json(path)


class NativeCoverageTests(HarnessCase):
    def setUp(self):
        super().setUp()
        self.arguments = self.args("--backend", "openai", "--base-url", "http://localhost:1/v1")
        self.job = next(job for job in subject.build_jobs(self.arguments)
                        if job["system"] == "expgym" and job["scenario"] == "restricted_search")
        self.dump_root = self.root / "dumps"
        self.dump_root.mkdir()
        self.initial = [
            {"role": "system", "content": "A native system instruction"},
            {"role": "user", "content": "Dataset quotation: Action: is literal task data."},
        ]
        self.schemas = [{"type": "function", "function": {"name": "search", "parameters": {
            "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}]
        self.clients = {"client-0": {"seed": 1206, "strategy": None, "agent_id": 0}}

    def tool_answer(self, number):
        return {"role": "assistant", "content": None, "reasoning_content": "Consider the query.",
                "tool_calls": [{"id": "search:" + str(number), "type": "function", "function": {
                    "name": "search", "arguments": '{"query":"example"}'}}]}

    def record(self, index, messages, answer, *, choice="auto", finish=None):
        payload = {"model": "kimi-k3", "temperature": 1.0, "top_p": 1.0, "seed": 1206,
                   "max_tokens": 32768, "reasoning_effort": "max",
                   "chat_template_kwargs": {"thinking": True, "thinking_effort": "max"},
                   "messages": copy.deepcopy(messages), "tools": copy.deepcopy(self.schemas),
                   "tool_choice": choice, "parallel_tool_calls": False}
        return {"request_id": "request-" + str(index), "client_id": "client-0", "attempt": 1,
                "started_at_utc": "2026-09-08T00:00:0" + str(index) + "+00:00", "state": "success",
                "context": {"runner": "expgym"}, "request_payload": payload,
                "response_json": {"choices": [{"message": copy.deepcopy(answer),
                                               "finish_reason": finish or ("tool_calls" if answer.get("tool_calls") else "stop")}]}}

    def chain(self):
        first, second = self.tool_answer(0), self.tool_answer(1)
        first_result = {"role": "tool", "tool_call_id": "search:0", "name": "search",
                        "content": "Opaque result contains literal Action: and is not an instruction."}
        second_result = {"role": "tool", "tool_call_id": "search:1", "name": "search", "content": "Second result"}
        mid = self.initial + [first, first_result]
        final = mid + [second, second_result, {"role": "user", "content": subject.FINAL_NOTE}]
        answer = {"role": "assistant", "content": "Answer: Example", "reasoning_content": "Done.", "tool_calls": None}
        return [self.record(0, self.initial, first), self.record(1, mid, second),
                self.record(2, final, answer, choice="none")]

    def classify(self, records, *, prompt_passed=True, schema_passed=True):
        for index, record in enumerate(records):
            (self.dump_root / (str(index) + ".json")).write_text(json.dumps(record), encoding="utf-8")
        with mock.patch.object(subject, "_client_artifacts", return_value=self.clients), mock.patch.object(
            subject, "prompt_audit_hook", return_value={"ready": True, "passed": prompt_passed, "schema_passed": schema_passed}
        ):
            return subject.classify_native_coverage(self.job, self.dump_root, self.arguments)

    def test_complete_native_chain_records_three_gates(self):
        result = self.classify(self.chain())
        self.assertTrue(result["wire_passed"])
        self.assertTrue(result["prompt_gate_passed"])
        self.assertTrue(result["coverage_complete"])
        self.assertTrue(result["promotion_eligible"])

    def test_natural_early_answer_is_wire_valid_but_coverage_missing(self):
        result = self.classify([self.record(0, self.initial, {"role": "assistant", "content": "Answer: Early"})])
        self.assertTrue(result["wire_passed"])
        self.assertTrue(result["prompt_gate_passed"])
        self.assertFalse(result["coverage_complete"])
        self.assertFalse(result["promotion_eligible"])
        self.assertTrue(any("native_continuation" in item for item in result["missing"]))

    def test_context_prompt_failure_is_not_hidden_by_full_path_coverage(self):
        result = self.classify(self.chain(), prompt_passed=False)
        self.assertTrue(result["coverage_complete"])
        self.assertFalse(result["prompt_gate_passed"])
        self.assertFalse(result["promotion_eligible"])

    def test_wrong_profile_is_wire_failure(self):
        records = self.chain()
        records[0]["request_payload"]["top_p"] = 0.95
        result = self.classify(records)
        self.assertFalse(result["wire_passed"])
        self.assertTrue(any("top_p" in item for item in result["wire_errors"]))

    def test_joint_artifact_and_dump_seed_drift_is_rejected(self):
        records = self.chain()
        self.clients["client-0"]["seed"] = 9999
        for record in records:
            record["request_payload"]["seed"] = 9999
        result = self.classify(records)
        self.assertFalse(result["wire_passed"])
        self.assertTrue(any("immutable plan" in error for error in result["wire_errors"]))

    def test_boolean_agent_id_is_not_an_integer_identity(self):
        self.clients["client-0"]["agent_id"] = False
        result = self.classify(self.chain())
        self.assertFalse(result["wire_passed"])

    def test_dropped_or_changed_native_history_is_wire_failure(self):
        records = self.chain()
        records[1]["request_payload"]["messages"][2]["reasoning_content"] = "Changed history"
        result = self.classify(records)
        self.assertFalse(result["wire_passed"])

    def test_dropped_prior_assistant_and_tool_pair_is_wire_failure(self):
        records = self.chain()
        original = records[2]["request_payload"]["messages"]
        records[2]["request_payload"]["messages"] = original[:2] + original[4:]
        self.assertFalse(self.classify(records)["wire_passed"])

    def test_reordered_prior_complete_pairs_are_wire_failure(self):
        records = self.chain()
        original = records[2]["request_payload"]["messages"]
        records[2]["request_payload"]["messages"] = original[:2] + original[4:6] + original[2:4] + original[6:]
        self.assertFalse(self.classify(records)["wire_passed"])

    def test_duplicated_prior_complete_pair_is_wire_failure(self):
        records = self.chain()
        original = records[2]["request_payload"]["messages"]
        records[2]["request_payload"]["messages"] = original[:4] + original[2:4] + original[4:]
        self.assertFalse(self.classify(records)["wire_passed"])

    def test_changed_previously_delivered_tool_feedback_is_wire_failure(self):
        records = self.chain()
        records[2]["request_payload"]["messages"][3]["content"] = "Silently replaced old tool feedback"
        self.assertFalse(self.classify(records)["wire_passed"])

    def test_unpaired_tool_result_is_wire_failure(self):
        records = self.chain()
        records[1]["request_payload"]["messages"][3]["tool_call_id"] = "wrong-id"
        result = self.classify(records)
        self.assertFalse(result["wire_passed"])

    def test_wrong_actual_schema_is_wire_failure(self):
        result = self.classify(self.chain(), schema_passed=False)
        self.assertFalse(result["wire_passed"])

    def test_forced_none_requires_actual_final_note(self):
        records = self.chain()
        records[2]["request_payload"]["messages"][-1]["content"] = "Unrelated data"
        result = self.classify(records)
        self.assertFalse(result["coverage_complete"])

    def test_coverage_gap_does_not_stop_bounded_fixed_plan(self):
        jobs = subject.build_jobs(self.arguments)
        completed = []
        def worker(job):
            completed.append(job["id"])
            return {"job_id": job["id"], "passed": True, "native_coverage": {"coverage_complete": False}}
        result = subject.helpers().run_bounded(jobs, worker, 2)
        self.assertEqual(len(completed), 6)
        self.assertFalse(result["failed"])
        self.assertFalse(result["unstarted"])

    def pool_records(self, *, omit_strategy=None):
        self.job = next(job for job in subject.build_jobs(self.arguments)
                        if job["system"] == "poolact" and job["scenario"] == "restricted_search")
        self.clients, all_records = {}, []
        for strategy in ("naive", "cached", "poolact"):
            for agent_id in (0, 1):
                client_id = strategy + "-" + str(agent_id)
                self.clients[client_id] = {"seed": 1206 + agent_id, "strategy": strategy, "agent_id": agent_id}
                records = self.chain()
                if strategy == omit_strategy:
                    records = [self.record(0, self.initial, {"role": "assistant", "content": "Answer: Early"})]
                elif agent_id == 0:
                    # This client covers continuation but answers naturally before forced-none.
                    records = records[:2]
                    records[-1]["response_json"]["choices"][0] = {
                        "message": {"role": "assistant", "content": "Answer: Natural"}, "finish_reason": "stop"}
                else:
                    # Its peer covers forced-none but no normal-auto continuation.
                    records = [records[0], records[2]]
                    messages = records[-1]["request_payload"]["messages"]
                    records[-1]["request_payload"]["messages"] = messages[:4] + messages[6:]
                for index, record in enumerate(records):
                    record["client_id"] = client_id
                    record["request_id"] = client_id + "-" + str(index)
                    record["request_payload"]["seed"] = 1206 + agent_id
                    record["context"] = {"runner": "poolact", **self.clients[client_id]}
                all_records.extend(records)
        return all_records

    def classify_pool(self, records, *, graph_missing_client=None):
        for index, record in enumerate(records):
            (self.dump_root / (str(index) + ".json")).write_text(json.dumps(record), encoding="utf-8")
        def prompt(job, record, args):
            return {"ready": True, "passed": True, "schema_passed": True,
                    "graph_context_verified": record["client_id"] != graph_missing_client}
        with mock.patch.object(subject, "_client_artifacts", return_value=self.clients), \
             mock.patch.object(subject, "prompt_audit_hook", side_effect=prompt):
            return subject.classify_native_coverage(self.job, self.dump_root, self.arguments)

    def test_pool_branch_coverage_can_be_shared_only_within_strategy_cell(self):
        result = self.classify_pool(self.pool_records())
        self.assertTrue(result["wire_passed"], result)
        self.assertTrue(result["coverage_complete"], result)
        self.assertEqual(result["cell_count"], 3)
        self.assertTrue(all(len(cell["clients"]) == 2 for cell in result["cells"].values()))
        for client in result["clients"].values():
            self.assertFalse(client["forced_none"] and client["native_continuation"])

    def test_pool_missing_strategy_cannot_borrow_other_strategy_paths(self):
        result = self.classify_pool(self.pool_records(omit_strategy="naive"))
        self.assertTrue(result["wire_passed"])
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any("naive" in value for value in result["missing"]))

    def test_coordinated_graph_must_cover_every_client(self):
        result = self.classify_pool(self.pool_records(), graph_missing_client="poolact-1")
        self.assertTrue(result["wire_passed"])
        self.assertFalse(result["coverage_complete"])
        self.assertTrue(any("poolact-1" in value and "graph_context" in value for value in result["missing"]))


class NativePromptTests(HarnessCase):
    def setUp(self):
        super().setUp()
        self.arguments = self.args("--backend", "openai", "--base-url", "http://localhost:1/v1")

    def request(self, job, *, tool_protocol="native", strategy=None, agent_id=0):
        args = self.arguments
        demo = subject.helpers().repository_module(args.repo_root, "demo_experiment")
        protocol = subject.helpers().repository_module(args.repo_root, "expgym.tool_protocol")
        order = None
        if job["system"] == "expgym" and job["scenario"] == "evidence_audit":
            order = subject.read_json(args.repo_root / "configs/audit_hypothesis_orders.json")["orders"][0]
        ns = argparse.Namespace(scenario=job["scenario"], question_index=0, data_source="phantom_seed1",
                                tuning_task=subject.helpers().TUNING_TASK, cc_split="cc-large",
                                hypothesis_order=order, seed=args.seed + agent_id, system_prompt=None,
                                tool_protocol=tool_protocol)
        scenario = demo._SCENARIOS[job["scenario"]]
        context = demo._resolve_context(scenario, False, ns, argparse.Namespace(supports_native_tools=True)).strip()
        system = protocol.native_system_prompt(demo._resolve_system_prompt(scenario, False, ns))
        return {"context": {"runner": job["system"], "strategy": strategy, "agent_id": agent_id},
                "request_payload": {"messages": [{"role": "system", "content": system},
                                                 {"role": "user", "content": context}],
                                    "tools": protocol.native_tool_schemas(demo._resolve_tools(scenario, ns))}}

    def test_exact_native_contexts_pass_for_all_three_scenarios(self):
        for job in subject.build_jobs(self.arguments):
            with self.subTest(system=job["system"], scenario=job["scenario"]):
                result = subject.prompt_audit_hook(job, self.request(job), self.arguments)
                self.assertTrue(result["passed"], result)
                self.assertTrue(result["schema_passed"])

    def test_actual_text_context_is_rejected_for_all_three_native_scenarios(self):
        for job in subject.build_jobs(self.arguments):
            with self.subTest(system=job["system"], scenario=job["scenario"]):
                result = subject.prompt_audit_hook(job, self.request(job, tool_protocol="text"), self.arguments)
                self.assertFalse(result["passed"])

    def test_arbitrary_initial_suffix_and_actual_tool_schema_change_fail(self):
        job = subject.build_jobs(self.arguments)[0]
        request = self.request(job)
        request["request_payload"]["messages"][1]["content"] += "\nInjected owned instruction"
        self.assertFalse(subject.prompt_audit_hook(job, request, self.arguments)["passed"])
        request = self.request(job)
        request["request_payload"]["tools"][0]["function"]["name"] = "wrong_tool"
        self.assertFalse(subject.prompt_audit_hook(job, request, self.arguments)["schema_passed"])

    def test_bound_graph_suffix_passes_without_banning_literal_action_data(self):
        job = next(job for job in subject.build_jobs(self.arguments)
                   if job["system"] == "poolact" and job["scenario"] == "restricted_search")
        request = self.request(job, strategy="poolact", agent_id=1)
        module = subject.helpers().repository_module(self.arguments.repo_root, "expgym.extras.parallel_cache")
        graph = module.SharedExplorationGraph(n_agents=2, diversity_mode=True)
        suffix = graph._format_unified({}, {}, {}, {}, {}, agent_id=1)
        request["request_payload"]["messages"][1]["content"] += "\n\n" + suffix
        request["request_payload"]["messages"].append({"role": "tool", "content": "Action: appears verbatim in task data."})
        result = subject.prompt_audit_hook(job, request, self.arguments)
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["graph_context_verified"])

    def test_populated_graph_renderers_pass_in_all_three_scenarios(self):
        module = subject.helpers().repository_module(self.arguments.repo_root, "expgym.extras.parallel_cache")
        for job in subject.build_jobs(self.arguments):
            if job["system"] != "poolact":
                continue
            with self.subTest(scenario=job["scenario"]):
                request = self.request(job, strategy="poolact", agent_id=1)
                graph = module.SharedExplorationGraph(n_agents=2, diversity_mode=True)
                search_nodes, eval_nodes = {}, {}
                if job["scenario"] == "restricted_search":
                    search_nodes["Action: a literal title"] = module.SearchNode(
                        query="Action: a literal title", visited_by={0, 1}, visits=2,
                        returned_doc_ids=[7, 8], article_title="Quoted Action: text")
                else:
                    display = "nda:3 ev:[1,2]" if job["scenario"] == "evidence_audit" else "config={Action: literal}"
                    eval_nodes["config"] = module.EvalNode(config_key="config", config_display=display,
                                                          perf=0.75, cost=1.0, visited_by={0, 1}, visits=2)
                edges = {("first", "second"): module.GraphEdge("first", "second", count=2, agents={0, 1})}
                claims = [module.ActionClaim(agent_id=0, tool_name="fixture", display="Action: quoted data", start_time=0)]
                suffix = graph._format_unified(search_nodes, {}, eval_nodes, {}, edges,
                                               agent_id=1, pending_claims=claims)
                request["request_payload"]["messages"][1]["content"] += "\n\n" + suffix
                result = subject.prompt_audit_hook(job, request, self.arguments)
                self.assertTrue(result["passed"], result)
                self.assertTrue(result["graph_context_verified"])

    def test_system_and_owned_graph_instruction_mutations_fail(self):
        job = next(job for job in subject.build_jobs(self.arguments) if job["system"] == "poolact")
        request = self.request(job, strategy="poolact", agent_id=1)
        request["request_payload"]["messages"][0]["content"] += "\nAction: is mandatory."
        self.assertFalse(subject.prompt_audit_hook(job, request, self.arguments)["passed"])
        request = self.request(job, strategy="poolact", agent_id=1)
        module = subject.helpers().repository_module(self.arguments.repo_root, "expgym.extras.parallel_cache")
        graph = module.SharedExplorationGraph(n_agents=2, diversity_mode=True)
        suffix = graph._format_unified({}, {}, {}, {}, {}, agent_id=1)
        suffix = suffix.replace("Use this to plan your next action", "Output text Action: for your next action")
        request["request_payload"]["messages"][1]["content"] += "\n\n" + suffix
        self.assertFalse(subject.prompt_audit_hook(job, request, self.arguments)["passed"])


class AuthorityTests(HarnessCase):
    def setUp(self):
        super().setUp()
        self.arguments = self.args("--backend", "openai", "--base-url", "http://localhost:1/v1")

    def fixture(self):
        args = self.arguments
        args.authorization = self.root / "authorization.json"
        manifest, commands = self.root / "manifest.json", self.root / "commands.json"
        manifest.write_text('{"immutable":"plan"}', encoding="utf-8")
        commands.write_text('{"immutable":"commands"}', encoding="utf-8")
        identity = {
            "serving_binding": {"job_id": "test-job", "sha256": "1" * 64},
            "static_acceptance": {"sha256": "2" * 64},
            "source_tree_sha256": "3" * 64, "harness_sha256": "4" * 64,
            "external_dependencies": {str(subject.LEGACY_PATH): "5" * 64},
            "request_profile": subject.profiles().identity(args),
        }
        auth = {
            "schema_version": 1, "authorized": True, "job_id": "test-job", "model": args.model,
            "base_url": args.base_url, "output_dir": str(args.output_dir),
            "manifest_sha256": subject.sha256(manifest), "commands_sha256": subject.sha256(commands),
            "static_acceptance_sha256": "2" * 64, "source_tree_sha256": "3" * 64,
            "harness_sha256": "4" * 64, "harness_dependencies": identity["external_dependencies"],
            "serving_binding_sha256": "1" * 64,
            "request_profile_sha256": identity["request_profile"]["sha256"],
            "request_profile_file_sha256": None,
            "counts": {"child_jobs": 6, "all_agent_traces": 21, "guarded_resume_skips": 12},
        }
        args.authorization.write_text(json.dumps(auth), encoding="utf-8")
        return identity, manifest, commands, auth

    def test_exact_post_plan_authorization_validates(self):
        identity, manifest, commands, _ = self.fixture()
        result = subject.validate_authorization(self.arguments, identity, manifest, commands)
        self.assertTrue(result["authorized"])
        self.assertEqual(result["sha256"], subject.sha256(self.arguments.authorization))

    def test_authorization_rejects_bool_counts_and_false_permission(self):
        for change in (lambda a: a.update(authorized=False),
                       lambda a: a.update(schema_version=True),
                       lambda a: a["counts"].update(child_jobs=True),
                       lambda a: a.update(request_profile_file_sha256="not-the-raw-profile"),
                       lambda a: a.update(harness_dependencies={})):
            identity, manifest, commands, auth = self.fixture()
            change(auth)
            self.arguments.authorization.write_text(json.dumps(auth), encoding="utf-8")
            with self.assertRaises(ValueError):
                subject.validate_authorization(self.arguments, identity, manifest, commands)

    def test_plan_byte_changes_invalidate_authorization(self):
        for key in ("manifest", "commands"):
            identity, manifest, commands, _ = self.fixture()
            path = manifest if key == "manifest" else commands
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                subject.validate_authorization(self.arguments, identity, manifest, commands)

    def serving_fixture(self):
        args = self.arguments
        args.serving_binding = self.root / "serving.json"
        evidence = {}
        for label in ("deployment", "profile", "capacity_source_receipt", "transport_receipt"):
            path = self.root / (label + ".json")
            path.write_text(json.dumps({"fixture": label}), encoding="utf-8")
            evidence[label] = {"path": str(path), "sha256": subject.sha256(path)}
        record = {"schema_version": 1, "observed_transport_pass": True, "job_id": "test-job",
                  "model": args.model, "base_url": args.base_url, "observed_completed_interval_peak": 8,
                  "planned_maximum_inflight_upper_bound": 7, "effective_slots_per_replica": 47,
                  "file_bindings": evidence}
        args.serving_binding.write_text(json.dumps(record), encoding="utf-8")
        return record

    def test_serving_evidence_is_not_a_blanket_capacity_guarantee(self):
        self.serving_fixture()
        result = subject.serving_binding(self.arguments)
        self.assertFalse(result["metadata_verified_by_harness"])
        self.assertIn("no saturation-throughput", result["interpretation"])
        self.assertNotIn("capacity_verified", result)

    def test_serving_evidence_byte_mutation_is_rejected(self):
        record = self.serving_fixture()
        path = Path(record["file_bindings"]["transport_receipt"]["path"])
        path.write_text(path.read_text() + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            subject.serving_binding(self.arguments)

    def test_serving_evidence_rejects_wrong_concurrency_and_boolean_peak(self):
        for changes in ({"planned_maximum_inflight_upper_bound": 8}, {"observed_completed_interval_peak": True},
                        {"effective_slots_per_replica": 0}, {"observed_transport_pass": False}):
            record = self.serving_fixture()
            record.update(changes)
            self.arguments.serving_binding.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaises(ValueError):
                subject.serving_binding(self.arguments)


class OneShotTests(HarnessCase):
    def test_symlinked_output_subtree_is_rejected_before_child(self):
        for directory in ("results", "dumps", "logs"):
            args = self.args("--execute")
            args.output_dir = self.root / ("symlink_" + directory)
            args.output_dir.mkdir()
            external = self.root / ("external_" + directory)
            external.mkdir()
            (args.output_dir / directory).symlink_to(external, target_is_directory=True)
            with mock.patch.object(subject, "parse_args", return_value=args), \
                 mock.patch.object(subject, "binding_identity", return_value={"jobs": []}), \
                 mock.patch.object(subject.helpers(), "run_child") as child:
                with self.assertRaises(RuntimeError):
                    subject.main([])
                child.assert_not_called()
            self.assertEqual(list(external.iterdir()), [])

    def test_started_or_completed_attempt_is_never_replayed(self):
        for marker in ("execution_started.json", "execution.json", "launch_receipt.json"):
            args = self.args()
            args.output_dir = self.root / marker.replace(".", "_")
            args.output_dir.mkdir()
            (args.output_dir / marker).write_text("{}", encoding="utf-8")
            with mock.patch.object(subject, "parse_args", return_value=args), \
                 mock.patch.object(subject, "binding_identity", return_value={"jobs": []}), \
                 mock.patch.object(subject.helpers(), "run_child") as child:
                with self.assertRaisesRegex(RuntimeError, "already started"):
                    subject.main([])
                child.assert_not_called()

    def test_preexisting_results_or_dumps_prevent_execution(self):
        for directory in ("results", "dumps"):
            args = self.args("--execute")
            args.output_dir = self.root / directory
            existing = args.output_dir / directory / "retained.json"
            existing.parent.mkdir(parents=True)
            existing.write_text("{}", encoding="utf-8")
            with mock.patch.object(subject, "parse_args", return_value=args), \
                 mock.patch.object(subject, "binding_identity", return_value={"jobs": []}), \
                 mock.patch.object(subject.helpers(), "run_child") as child:
                with self.assertRaisesRegex(RuntimeError, "Pre-existing"):
                    subject.main([])
                child.assert_not_called()
            self.assertEqual(existing.read_text(), "{}")


class ResumeGuardTests(HarnessCase):
    def fixture(self, *, backend="fake"):
        args = self.args()
        args.output_dir.mkdir(exist_ok=True)
        jobs = subject.build_jobs(args)
        identity = {"settings": {"backend": backend}, "repo_root": str(args.repo_root), "jobs": jobs,
                    "harness_sha256": subject.sha256(subject.HERE),
                    "external_dependencies": {str(path): subject.sha256(path) for path in subject.PINNED_HELPERS},
                    "source_tree_sha256": "fixture-source"}
        manifest = args.output_dir / "manifest.json"
        commands = args.output_dir / "commands.json"
        launch = args.output_dir / "launch_receipt.json"
        manifest.write_text(json.dumps({"identity": identity}), encoding="utf-8")
        commands.write_text(json.dumps(subject.command_receipts(jobs)), encoding="utf-8")
        launch.write_text(json.dumps({"manifest_sha256": subject.sha256(manifest),
                                     "commands_sha256": subject.sha256(commands), "authorization": None}), encoding="utf-8")
        return jobs[0]["command"][2:] + ["--resume"], manifest, commands, launch

    def test_exact_guard_delegates_only_to_existing_no_model_guard(self):
        argv, _, _, _ = self.fixture()
        with mock.patch.object(subject.helpers(), "source_fingerprint", return_value="fixture-source"), \
             mock.patch.object(subject.helpers(), "resume_guard") as protected:
            subject._resume_guard(argv)
            protected.assert_called_once_with(argv)

    def test_guard_rejects_manifest_and_command_byte_changes(self):
        for target in ("manifest", "commands"):
            argv, manifest, commands, _ = self.fixture()
            path = manifest if target == "manifest" else commands
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            with mock.patch.object(subject.helpers(), "resume_guard") as protected:
                with self.assertRaisesRegex(RuntimeError, "launch receipt"):
                    subject._resume_guard(argv)
                protected.assert_not_called()

    def test_guard_rejects_changed_runner_argument(self):
        argv, _, _, _ = self.fixture()
        argv[argv.index("--max-steps") + 1] = "4"
        with mock.patch.object(subject.helpers(), "resume_guard") as protected:
            with self.assertRaisesRegex(RuntimeError, "runner/argv"):
                subject._resume_guard(argv)
            protected.assert_not_called()

    def test_guard_rejects_source_drift(self):
        argv, _, _, _ = self.fixture()
        with mock.patch.object(subject.helpers(), "source_fingerprint", return_value="changed-source"), \
             mock.patch.object(subject.helpers(), "resume_guard") as protected:
            with self.assertRaisesRegex(RuntimeError, "source changed"):
                subject._resume_guard(argv)
            protected.assert_not_called()

    def test_real_guard_cannot_omit_launch_authorization(self):
        argv, _, _, _ = self.fixture(backend="openai")
        with mock.patch.object(subject.helpers(), "resume_guard") as protected:
            with self.assertRaisesRegex(RuntimeError, "no launch authorization"):
                subject._resume_guard(argv)
            protected.assert_not_called()


if __name__ == "__main__":
    unittest.main()
