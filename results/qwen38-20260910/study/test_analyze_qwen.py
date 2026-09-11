"""Synthetic CPU fixtures only; never open the formal study's output tree."""
import copy
from contextlib import ExitStack
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import analyze_qwen as a
from analyze_qwen_metrics import aggregate, collapse


def meta(system="poolact", scenario="tuning", strategy="naive", regime="cost_tight", outer=0, item="task-A", order="none"):
    return dict(execution_id="job-%s-%s-%s-%s-%s-%s" % (system, item, regime, strategy, outer, order),
                model="model-cedar", system=system, scenario=scenario, item=item, family="family-x",
                regime=regime, strategy="single" if system == "expgym" else strategy,
                N=1 if system == "expgym" else 4, outerrep=outer, order=order, seed=2200 + 4 * outer)


def agent(value=.6, unknown=False):
    return dict(answer=None if unknown else "answer", answer_perf=None if unknown else value,
                answer_metrics=None, score_status="unscorable_missing_configuration" if unknown else "scored_final_answer",
                score_check={"ok": not unknown}, terminal_status={"execution_complete": True, "score_complete": not unknown},
                total_overhead=600, evaluations=2, api_calls=2, protocol_failures=[],
                wall_time_seconds=7, tool_records=[("tool", "same"), ("tool", "different")])


def metric(meta_row, value, name="gap"):
    return {**meta_row, "metric": name, "value": value,
            "unit": "Gap points" if name == "gap" else "fraction", "higher_is_better": True}


def write(path, value, raw=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if raw else json.dumps(value, sort_keys=True).encode())
    return {"bytes": path.stat().st_size, "sha256": a.sha(path.read_bytes())}


class ProjectionTests(unittest.TestCase):
    def test_per_agent_gap_clip_before_mi_and_unknown_bon(self):
        oracle = {"mean_perf": .5, "best_perf": .9}
        members = [agent(.1), agent(.9), agent(.5), agent(.7)]
        voted = agent(.9)
        rows, raw = a.project(meta(), members, voted, True, oracle, [], budget=900)
        values = {r["metric"]: r["value"] for r in rows}
        self.assertAlmostEqual(values["gap_mi"], 37.5)
        self.assertAlmostEqual(values["gap_bon"], 100)
        self.assertEqual(values["feedback_attempts"], 8)
        self.assertEqual(values["duplicate_action_attempts"], 6)
        self.assertAlmostEqual(values["budget_utilization"], 2 / 3)
        self.assertIsNone(values["wall_time_seconds"])
        members[0] = agent(unknown=True)
        rows, raw = a.project(meta(), members, {}, True, oracle, [], budget=900)
        values = {r["metric"]: r["value"] for r in rows}
        self.assertIsNone(values["gap_mi"])
        self.assertIsNone(values["gap_bon"])
        self.assertFalse(raw[0]["score_complete"])

    def test_valid_search_empty_zero_not_missing(self):
        member = agent(0)
        member["answer"] = None
        rows, _ = a.project(meta("expgym", "restricted_search"), [member], None, True, None, [])
        self.assertEqual(next(r["value"] for r in rows if r["metric"] == "f1"), 0)

    def test_failed_results_never_promote_scores(self):
        rows, raw = a.project(meta(), [agent()] * 4, agent(), False, {"mean_perf": .5, "best_perf": .9}, [])
        self.assertTrue(all(r["value"] is None for r in rows))
        self.assertTrue(all(not r["score_complete"] for r in raw))

    def test_complete_score_missing_value_rejected(self):
        member = agent()
        member["answer_perf"] = None
        with self.assertRaises(ValueError):
            a.project(meta("expgym"), [member], None, True, {"mean_perf": .5, "best_perf": .9}, [])

    def test_complete_pool_aggregate_missing_value_rejected(self):
        with self.assertRaises(ValueError):
            a.project(meta(), [agent()] * 4, {"terminal_status": {"score_complete": True}}, True,
                      {"mean_perf": .5, "best_perf": .9}, [])

    def test_chat_usage_keeps_reasoning_in_output_and_request_settings(self):
        record = {"schema_version": "expgym.api_attempt.v1", "run_id": "job-x", "state": "success",
                  "request_id": "r1", "request_payload": {"reasoning_effort": "xhigh", "chat_template_kwargs": {"preserve_thinking": True}},
                  "response_json": {"usage": {"prompt_tokens": 10, "completion_tokens": 20,
                                              "completion_tokens_details": {"reasoning_tokens": 15}},
                                    "choices": [{"finish_reason": "length"}]}, "wall_time_seconds": 3}
        row = a.chat_usage(record, "job-x", True, Path("attempt.json"))
        self.assertEqual(row["total_tokens"], 30)
        self.assertEqual(row["reasoning_tokens_included_in_output"], 15)
        self.assertEqual(row["finish_reasons"], ["length"])
        self.assertEqual(row["effective_request_parameters"], record["request_payload"])
        record["state"] = "in_progress"
        row = a.chat_usage(record, "job-x", True, Path("attempt.json"))
        self.assertIsNone(row["total_tokens"])
        self.assertIsNone(row["request_wall_seconds"])
        record["state"] = "invented"
        with self.assertRaises(ValueError):
            a.chat_usage(record, "job-x", True, Path("attempt.json"))

    def test_wrong_owner_and_reasoning_count_rejected(self):
        record = {"schema_version": "expgym.api_attempt.v1", "run_id": "job-x", "state": "success",
                  "response_json": {"usage": {"completion_tokens": 10, "completion_tokens_details": {"reasoning_tokens": 11}}}}
        with self.assertRaises(ValueError):
            a.chat_usage(record, "wrong", True, Path("attempt.json"))
        with self.assertRaises(ValueError):
            a.chat_usage(record, "job-x", True, Path("attempt.json"))


    def test_top_level_reasoning_fallback_missing_zero_and_conflicts(self):
        record = {"schema_version": "expgym.api_attempt.v1", "run_id": "job-x", "state": "success",
                  "response_json": {"usage": {"prompt_tokens": 10, "completion_tokens": 20}}}
        cases = [({}, None), ({"reasoning_tokens": None}, None),
                 ({"reasoning_tokens": 0}, 0), ({"reasoning_tokens": 12}, 12),
                 ({"completion_tokens_details": {"reasoning_tokens": 12}}, 12),
                 ({"reasoning_tokens": 12, "completion_tokens_details": {"reasoning_tokens": None}}, 12),
                 ({"reasoning_tokens": None, "completion_tokens_details": {"reasoning_tokens": 12}}, 12),
                 ({"reasoning_tokens": 12, "completion_tokens_details": {"reasoning_tokens": 12}}, 12)]
        for extra, expected in cases:
            with self.subTest(extra=extra):
                sample = copy.deepcopy(record)
                sample["response_json"]["usage"].update(extra)
                row = a.chat_usage(sample, "job-x", True, Path("attempt.json"))
                self.assertEqual(row["reasoning_tokens_included_in_output"], expected)
                self.assertEqual(row["output_tokens"], 20)
                self.assertEqual(row["total_tokens"], 30)
        invalid = [{"reasoning_tokens": value} for value in (-1, True, 1.5, "12", 21)]
        invalid += [{"reasoning_tokens": 12, "completion_tokens_details": {"reasoning_tokens": 13}},
                    {"reasoning_tokens": 0, "completion_tokens_details": {"reasoning_tokens": 12}},
                    {"reasoning_tokens": 12, "completion_tokens_details": {"reasoning_tokens": -1}}]
        for extra in invalid:
            with self.subTest(invalid=extra), self.assertRaises(ValueError):
                sample = copy.deepcopy(record)
                sample["response_json"]["usage"].update(extra)
                a.chat_usage(sample, "job-x", True, Path("attempt.json"))
        record["state"] = "in_progress"
        record["response_json"]["usage"]["reasoning_tokens"] = 12
        row = a.chat_usage(record, "job-x", True, Path("attempt.json"))
        self.assertIsNone(row["reasoning_tokens_included_in_output"])
        self.assertIsNone(row["total_tokens"])


class NumericTests(unittest.TestCase):
    def test_audit_mean_once_unknown_and_no_repeat_sd(self):
        rows = [metric(meta("expgym", "evidence_audit", item="doc-1", order=i), v, "evidence_acc")
                for i, v in enumerate((.3, .6, .9))]
        folded = collapse(rows)
        self.assertEqual(len(folded), 1)
        self.assertAlmostEqual(folded[0]["value"], .6)
        absolute, repeats, _ = aggregate(folded)
        self.assertEqual(len(repeats), 2)  # all and family, each one outerrep
        self.assertTrue(all(r["descriptive_repeat_sd"] is None for r in absolute))
        rows[1]["value"] = None
        folded = collapse(rows)
        self.assertIsNone(folded[0]["value"])
        self.assertAlmostEqual(folded[0]["known_component_subset_mean"], .6)
        with self.assertRaises(ValueError):
            collapse(rows[:2])

    def test_three_r1_stages_preserve_all_outerreps_and_negative_effects(self):
        rows = [metric(meta(outer=outer, strategy=strategy), base + outer)
                for outer in range(3) for strategy, base in (("naive", 10), ("cached", 8), ("poolact", 9))]
        absolute, repeats, contrasts = aggregate(collapse(rows))
        self.assertEqual(len([r for r in repeats if r["slice_kind"] == "all"]), 9)
        effects = sorted(r["effect"] for r in contrasts if r["slice_kind"] == "all")
        self.assertEqual(effects, [-2, -1, 1])
        self.assertTrue(all(r["descriptive_repeat_sd"] == 1 for r in absolute))

    def test_missing_cached_full_contrasts_unknown_not_intersection(self):
        rows = [metric(meta(outer=outer, strategy=strategy), None if strategy == "cached" and outer == 1 else 1)
                for outer in range(3) for strategy in ("naive", "cached", "poolact")]
        _, _, contrasts = aggregate(collapse(rows))
        all_rows = [r for r in contrasts if r["slice_kind"] == "all"]
        self.assertEqual(sum(r["effect"] is None for r in all_rows), 2)
        self.assertEqual(sum(r["effect"] == 0 for r in all_rows), 1)
        with self.assertRaises(ValueError):
            aggregate(collapse(rows[:-1]))

    def test_duplicate_metric_and_component_replacement_rejected(self):
        row = metric(meta(), 1)
        with self.assertRaises(ValueError):
            collapse([row, row])
        other = {**row, "metric": "raw_perf", "execution_id": "replacement"}
        with self.assertRaises(ValueError):
            collapse([row, other])

    def test_full_synthetic_matrix_783_705_1881(self):
        rows = []
        for regime in ("cost_free", "cost_moderate", "cost_tight"):
            for item in range(73):
                rows.append(metric(meta("expgym", "restricted_search", regime=regime, item="search-%d" % item), 0, "f1"))
            for item in range(13):
                for order in range(3):
                    rows.append(metric(meta("expgym", "evidence_audit", regime=regime, item="doc-%d" % item, order=order), 0, "evidence_acc"))
            for item in range(9):
                for outer in range(3):
                    rows.append(metric(meta("expgym", regime=regime, item="task-%d" % item, outer=outer), 0))
        for regime in ("cost_moderate", "cost_tight"):
            for strategy in ("naive", "cached", "poolact"):
                for scenario, count in (("restricted_search", 39), ("evidence_audit", 13), ("tuning", 3)):
                    for item in range(count):
                        for outer in range(3 if scenario == "tuning" else 1):
                            rows.append(metric(meta(scenario=scenario, strategy=strategy, regime=regime, outer=outer,
                                                    item="%s-%d" % (scenario, item), order="default" if scenario == "evidence_audit" else "none"), 0))
        self.assertEqual(len(rows), 783)
        self.assertEqual(sum(row["N"] for row in rows), 1881)
        folded = collapse(rows)
        self.assertEqual(len({r["analysis_id"] for r in folded}), 705)
        absolute, _, contrasts = aggregate(folded)
        self.assertEqual(len([r for r in absolute if r["slice_kind"] == "all"]), 27)
        self.assertTrue(all(r["effect"] == 0 for r in contrasts))


class InputAndStateTests(unittest.TestCase):
    def setup_state(self, base):
        identity = {"study_id": "fixture", "source_tree_sha256": "f" * 64}
        job_id = "job_" + a.digest(identity)
        output = base / "invocations" / job_id
        job = {"job_id": job_id, "identity": identity, "args": {"output_dir": str(output / "result")}}
        root = base / "queue"
        write(root / "controller.lock", b"", raw=True)
        write(root / "definition.json", {"schema": "expgym.queue-definition.v1", "jobs": [{"id": job_id, "identity": identity, "output": str(output)}]})
        write(root / "sessions" / "session-1" / "summary.json", {"schema": "expgym.study-queue-summary.v1", "planned": 1, "finished": 0, "reports": [], "unstarted": [job_id]})
        write(root / "sessions" / "session-1" / "events.jsonl", b'{"event":"drained","active":0,"unstarted":1}\n', raw=True)
        spec = {"schema": "qwen38.analysis-states.v1", "roots": [{"path": str(root), "sessions": ["session-1"]}]}
        return {"jobs": [job]}, spec, root, job_id

    def test_input_pin_tamper_and_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = write(root / "a.json", {"x": 1})
            inputs = a.Inputs()
            inputs.json(root / "a.json", "fixture", pin=pin)
            write(root / "a.json", {"x": 200})
            with self.assertRaises(ValueError):
                inputs.finish()
            (root / "link.json").symlink_to(root / "a.json")
            with self.assertRaises(ValueError):
                a.Inputs().read(root / "link.json", "fixture")

    def test_correct_lock_and_explicit_sessions(self):
        with tempfile.TemporaryDirectory() as temporary:
            plan, spec, root, job_id = self.setup_state(Path(temporary))
            with ExitStack() as stack:
                state = a.states(plan, spec, a.Inputs(), stack)
                self.assertTrue(state[job_id][0]["effective"])
            with (root / "controller.lock").open("rb") as owner:
                fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with ExitStack() as stack, self.assertRaises(BlockingIOError):
                    a.states(plan, spec, a.Inputs(), stack)
            spec["roots"][0]["sessions"] = []
            with ExitStack() as stack, self.assertRaises(ValueError):
                a.states(plan, spec, a.Inputs(), stack)

    def test_multiple_attempts_require_explicit_authorized_winner(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            plan, spec, root, job_id = self.setup_state(base)
            _, extra, root2, _ = self.setup_state(base / "epoch2")
            spec["roots"] += extra["roots"]
            for state_root in (root, root2):
                write(state_root / "jobs" / job_id / "started.json", {"identity_sha256": a.digest(plan["jobs"][0]["identity"])})
            with ExitStack() as stack, self.assertRaises(ValueError):
                a.states(plan, spec, a.Inputs(), stack)
            authorization = base / "authorization.json"
            pin = write(authorization, {"reason": "fixture-approved-fixed-slot-recovery"})
            spec["effective_attempt"] = {job_id: {"state_root": str(root2), "authorization": {"path": str(authorization), **pin}}}
            with ExitStack() as stack:
                state = a.states(plan, spec, a.Inputs(), stack)
            self.assertEqual([r["effective"] for r in state[job_id]], [False, True])


class InputMetadataTests(unittest.TestCase):
    def test_shared_parent_metadata_call_reduction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "shared"
            paths = [root / ("fixture-%d.json" % i) for i in range(12)]
            pins = {path: write(path, {"fixture": i}) for i, path in enumerate(paths)}
            original_stat = Path.stat
            calls = []
            def counted(path, *args, **kwargs):
                calls.append(str(path))
                return original_stat(path, *args, **kwargs)
            inputs = a.Inputs()
            with patch.object(Path, "stat", counted):
                for path in paths:
                    inputs.register(path, "inventory", pins[path])
                for path in paths:
                    inputs.json(path, "used_content", pin=pins[path])
                actual = inputs.finish()
            optimized = len(calls)
            expected_parents = {str(parent) for path in paths for parent in path.parents}
            self.assertEqual(set(inputs.directories), expected_parents)
            self.assertEqual(optimized, 4 * len(paths) + 2 * len(expected_parents))
            self.assertTrue(all(calls.count(parent) == 2 for parent in expected_parents))
            self.assertTrue(all(row["sha256"] == pins[Path(row["path"])]["sha256"]
                                and row["evidence"] == "content_SHA256_verified" for row in actual))
            # Count the exact former metadata sequence on the same small files.
            def former_register(path):
                self.assertTrue(path.is_file() and not path.is_symlink()
                                and not any(parent.is_symlink() for parent in path.parents))
                return path.stat()
            calls.clear()
            with patch.object(Path, "stat", counted):
                for path in paths:
                    former_register(path)  # Inventory registration.
                for path in paths:
                    former_register(path)
                    path.read_bytes()
                    former_register(path)
                for path in paths:
                    former_register(path)  # Final change check.
            legacy = len(calls)
            self.assertEqual(legacy, 4 * sum(3 + len(path.parents) for path in paths))
            self.assertLess(optimized, legacy)
            type(self).metadata_counts = {"files": len(paths), "unique_parents": len(expected_parents),
                                          "former_metadata_calls": legacy, "optimized_metadata_calls": optimized}

    def test_cached_ancestor_symlink_and_directory_identity_swap_rejected(self):
        for replacement in ("symlink", "directory", "higher_ancestor"):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary)
                original = base / "original"
                path = original / "nested" / "file.json"
                pin = write(path, {"same": "content"})
                substitute = base / "substitute"
                if replacement == "directory":
                    (substitute / "nested").mkdir(parents=True)
                    # Pre-link before recording the file's ctime. Only rename
                    # directories after reading, so file identity stays equal.
                    (substitute / "nested" / "file.json").hardlink_to(path)
                elif replacement == "higher_ancestor":
                    substitute.mkdir()
                inputs = a.Inputs()
                inputs.json(path, "fixture", pin=pin)
                original.rename(base / "saved")
                if replacement == "symlink":
                    original.symlink_to(base / "saved", target_is_directory=True)
                else:
                    if replacement == "higher_ancestor":
                        # Preserve the immediate parent's inode as well: only
                        # a higher ancestor's directory identity changes.
                        (base / "saved" / "nested").rename(substitute / "nested")
                    substitute.rename(original)
                # The final-file guard alone cannot catch these path swaps.
                info = path.lstat()
                self.assertEqual(inputs.files[str(path)]["signature"],
                                 (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
                if replacement == "higher_ancestor":
                    info = path.parent.lstat()
                    self.assertEqual(inputs.directories[str(path.parent)][:2], (info.st_dev, info.st_ino))
                with self.assertRaisesRegex(ValueError, "input parent"):
                    inputs.finish()

    def test_file_replacement_and_mutation_during_read_rejected(self):
        for mutation in ("replace", "during_read"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                path = root / "file.json"
                pin = write(path, {"same": "content"})
                inputs = a.Inputs()
                if mutation == "replace":
                    replacement = root / "replacement.json"
                    write(replacement, {"same": "content"})
                    inputs.json(path, "fixture", pin=pin)
                    replacement.replace(path)
                    with self.assertRaisesRegex(ValueError, "input changed"):
                        inputs.finish()
                else:
                    original_read = Path.read_bytes
                    def changed_after_read(selected):
                        raw = original_read(selected)
                        selected.write_bytes(b'{"changed":"larger replacement data"}')
                        return raw
                    with patch.object(Path, "read_bytes", changed_after_read), self.assertRaisesRegex(ValueError, "input changed"):
                        inputs.json(path, "fixture", pin=pin)

    def test_parent_metadata_changes_without_identity_change_are_allowed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = write(root / "file.json", {"same": "content"})
            inputs = a.Inputs()
            inputs.json(root / "file.json", "fixture", pin=pin)
            write(root / "unrelated.json", {"new": "file"})
            self.assertEqual(len(inputs.finish()), 1)


class ArtifactFixtures(unittest.TestCase):
    """Two tiny explicit result inventories; no real experiment files."""
    def fixture(self, root, system="expgym"):
        m = meta(system, "restricted_search", strategy="poolact")
        m["execution_id"] = "job-fixture"
        job = {"job_id": m["execution_id"], "runner": system,
               "identity": {"source_tree_sha256": "f" * 64},
               "args": {"repeats": 1},
               "selection": {"strategy": "poolact", "repeat_index": 0, "scenario": "restricted_search",
                             "data_source": "fixture", "question_index": 2, "model_alias": "cedar",
                             "cost_regime": "cost_tight", "rep": 0, "seed": 2200}}
        inventory = {}
        def save(path, value, raw=False):
            inventory[path.relative_to(root).as_posix()] = write(path, value, raw)
        result_path = a.planned_result(job, root)
        agents = []
        for index in range(m["N"]):
            request = "request-%d" % index
            member = agent(.6)
            member.update(agent_id=index, http_request_attempts=1,
                          usage_attempts=[{"attempts": [{"request_id": request}]}])
            agents.append(member)
            save(root / "api_dump" / (request + ".json"),
                 {"schema_version": "expgym.api_attempt.v1", "run_id": job["job_id"],
                  "request_id": request, "state": "success", "wall_time_seconds": 3,
                  "request_payload": {"model": m["model"], "cache_salt": "unique-fixture-salt-%d" % index},
                  "response_json": {"usage": {"prompt_tokens": 10, "completion_tokens": 20}}})
        if system == "expgym":
            data = {"schema": {"name": "expgym.trace", "version": "2.1.0"},
                    "provenance": {"repository": {"source_tree_sha256": "f" * 64}},
                    "run": {"model": {"id": m["model"]}}, "task": {"budget": {"limit_seconds": 900}},
                    "timing": {"wall_time_seconds": 7, "total_simulated_cost_seconds": 0},
                    "tool_calls": [], "llm_calls": [{"attempt_usage": [{"request_id": "request-0"}]}],
                    "outcome": {"answer": "fixture-answer", "score": {"primary_metric": "f1", "metrics": {"f1": .6}},
                                "validation": {"passed": True}, "http_request_attempts": 1,
                                "terminal_status": {"execution_complete": True, "score_complete": True},
                                "protocol_failures": []}}
        else:
            data = {"agents": 4, "strategy": "poolact", "implementation_sha256": {"source_tree": "f" * 64},
                    "config": {"model": m["model"], "time_budget": 900}, "agent_results": agents,
                    "aggregate": agent(.6)}
            for member in agents:
                save(result_path.parent / "agents" / ("agent_%d.json" % member["agent_id"]), member)
        save(result_path, data)
        attempt = {"artifact_root": root, "receipt": {"artifacts": inventory},
                   "started": {"identity_sha256": "fixture"}, "effective": True}
        return job, m, attempt, data, result_path

    def test_completed_expgym_and_pool_artifact_projection(self):
        for system in ("expgym", "poolact"):
            with self.subTest(system=system), tempfile.TemporaryDirectory() as directory:
                job, m, attempt, _, _ = self.fixture(Path(directory), system)
                inputs = a.Inputs()
                rows, raw, costs = a.collect(job, m, attempt, inputs, {}, None)
                values = {r["metric"]: r["value"] for r in rows}
                self.assertAlmostEqual(values["f1" if system == "expgym" else "f1_mv"], .6)
                self.assertEqual(values["input_tokens"], 10 * m["N"])
                self.assertEqual(values["output_tokens"], 20 * m["N"])
                self.assertEqual(len(raw), m["N"])
                self.assertEqual(len(costs), m["N"])
                self.assertIn("cache_salt", costs[0]["effective_request_parameters"])
                self.assertTrue(all(row["score_complete"] for row in raw))
                self.assertTrue(all(f["evidence"] == "content_SHA256_verified" for f in inputs.finish()))

    def test_failed_truncated_result_is_unknown_but_costs_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            job, m, attempt, _, result_path = self.fixture(root)
            inventory = attempt["receipt"]["artifacts"]
            inventory[result_path.relative_to(root).as_posix()] = write(result_path, b'{"partial":', raw=True)
            attempt["receipt"] = None
            inputs = a.Inputs()
            rows, raw, costs = a.collect(job, m, attempt, inputs,
                                         {"unreceipted_artifacts": {str(root): inventory}}, None)
            self.assertTrue(all(row["value"] is None for row in rows))
            self.assertFalse(raw[0]["score_complete"])
            self.assertEqual(costs[0]["total_tokens"], 30)
            registered = {f["path"]: f for f in inputs.finish()}
            self.assertEqual(registered[str(result_path)]["evidence"], "inherited_inventory_pin_size_checked")

    def test_complete_result_corruption_and_ledger_omission_rejected(self):
        for problem in ("source", "ledger", "aggregate"):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                job, m, attempt, data, result_path = self.fixture(root, "poolact")
                inventory = attempt["receipt"]["artifacts"]
                if problem == "source":
                    data["implementation_sha256"]["source_tree"] = "wrong"
                elif problem == "ledger":
                    inventory.pop("api_dump/request-0.json")
                else:
                    data["aggregate"]["answer_perf"] = None
                inventory[result_path.relative_to(root).as_posix()] = write(result_path, data)
                with self.assertRaises(ValueError):
                    a.collect(job, m, attempt, a.Inputs(), {}, None)


if __name__ == "__main__":
    unittest.main()
