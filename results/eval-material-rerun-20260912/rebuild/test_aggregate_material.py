"""Synthetic, standard-library-only report checks; never read study results."""
import copy
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest

import aggregate_material as a


ORACLE = {"tasks": {"hpobench:nasbench101:A": {"mean_perf": 0.5, "best_perf": 0.9},
                    "hpobench:nasbench101:B": {"mean_perf": 0.5, "best_perf": 0.9}}}


def terminal(complete=True, missing=0, n=1):
    return dict(execution_complete=True, score_complete=complete, policy_version="task-abstention-v1",
                terminal_classification="model_no_answer" if missing else "completed_scored",
                model_no_answer_count=missing, expected_model_terminals=n, reported_model_terminals=n)


def saved(perfs=(0.4, 0.6, 0.8, 1.0), scenario="tuning", strategy="poolact"):
    agents = []
    for i, perf in enumerate(perfs):
        missing = perf is None
        scored = not missing or scenario != "tuning"
        value = perf if not missing else (None if scenario == "tuning" else 0.0)
        agents.append(dict(agent_id=i, answer=None if missing else "synthetic",
                           answer_perf=value, answer_metrics=None if scenario == "tuning" else {
                               "evidence_acc": value, "label_acc": value},
                           scoring_input=None if missing and scenario == "tuning" else "synthetic",
                           score_status="unscorable_missing_configuration" if not scored else "scored_final_answer",
                           terminal_origin="normal_loop_return", terminal_status=terminal(scored, int(missing))))
    all_scored = all(x["terminal_status"]["score_complete"] for x in agents)
    values = [x["answer_perf"] for x in agents]
    agg = dict(answer_perf=max(values) if all_scored else None,
               mean_individual_perf=a.full_mean(values), terminal_status=terminal(all_scored, sum(x is None for x in perfs), len(perfs)),
               answer_metrics=None if scenario == "tuning" else {"evidence_acc": 0.7, "label_acc": 0.8})
    return dict(agent_results=agents, aggregate=agg, terminal_status=agg["terminal_status"], agents=4, strategy=strategy)


def plan(scenario="tuning", items=("hpobench:nasbench101:A",), seeds=(2200,)):
    jobs = []
    for item in items:
        for seed in seeds:
            for strategy in a.STRATEGIES:
                job_id = f"job_{item}_{seed}_{strategy}"
                args = dict(agents=4, scenario=scenario, model="fixture-unfamiliar-model", cc_split="fixture",
                            data_source="fixture", question_index=0, tuning_task=item, cost_regime="cost_tight",
                            seed=seed, strategies=[strategy], repeats=1, max_steps=30, max_evals=30,
                            max_context_tokens=131072, missing_final_policy="task-abstention-v1",
                            temperature=1.0, reasoning_effort="max", api_key=None, api_key_file=None,
                            output_dir="/fixture/"+job_id, base_url="http://fixture.invalid", prompt_cache_key=job_id)
                jobs.append(dict(job_id=job_id, args=args, runner="poolact", selection={}))
    return dict(schema="expgym.study-queue-plan.v1", jobs=jobs, source_tree_sha256="synthetic-source", study_id="fixture")


def historical_fixtures(tie=False):
    budget, rankings = [], []
    for scenario, metric in (("Search", "f1"), ("Audit", "evidence_acc"), ("HPO/NAS", "gap0")):
        for model in a.HISTORICAL_MODELS:
            free = 110 if metric == "gap0" else 70
            tight = free + 5 if model == "deepseek-v4-flash-0731" and metric == "gap0" else free - 10
            budget.append(dict(scenario=scenario, model=model, metric=metric,
                               unit="Gap0点" if metric == "gap0" else "分 (0–100)",
                               free=free, moderate=free-2, tight=tight, free_minus_tight=free-tight))
    for i, family in enumerate(a.HISTORICAL_FAMILIES):
        metric = "f1" if family.startswith("Search") else "evidence_acc" if family == "Audit" else "gap0"
        free_winners = {i % 5}
        if tie and i == 0:
            free_winners.add((i+1) % 5)
        tight_winners = {(i+1) % 5} if i % 2 == 0 else free_winners
        changed = free_winners != tight_winners
        for regime in ("cost_free", "cost_moderate", "cost_tight"):
            selected = tight_winners if regime == "cost_tight" else free_winners
            for j, model in enumerate(a.HISTORICAL_MODELS):
                rankings.append(dict(family=family, model=model, regime=regime, metric=metric,
                                     value=90 if j in selected else 70+j, winner=j in selected,
                                     winner_set=";".join(a.HISTORICAL_MODELS[k] for k in sorted(selected)),
                                     candidate_count=5, first_second_margin=0 if len(selected) > 1 else 16,
                                     unit="Gap0点" if metric == "gap0" else "分 (0–100)",
                                     free_to_tight_winner_changed=changed))
    return budget, rankings


class EndpointTests(unittest.TestCase):
    def row(self, scenario="tuning"):
        return dict(scenario=scenario, item="hpobench:nasbench101:A", N=4, strategy="poolact")

    def test_gap_lower_clip_before_mean_no_upper_clip(self):
        values, _ = a.endpoints(saved(), self.row(), ORACLE)
        self.assertAlmostEqual(values["gap_mi"], 56.25)
        self.assertAlmostEqual(values["gap_bon"], 125)
        self.assertNotAlmostEqual(values["gap_mi"], a.gap(0.7, self.row()["item"], ORACLE))

    def test_partial_missing_preserves_strict_unknown(self):
        values, counts = a.endpoints(saved((0.4, 0.6, 0.8, None)), self.row(), ORACLE)
        self.assertIsNone(values["gap_mi"])
        self.assertIsNone(values["gap_bon"])
        self.assertAlmostEqual(values["gap0_mi"], 25)
        self.assertAlmostEqual(values["gap0_bon"], 75)
        self.assertEqual(counts["missing_configuration_agents"], 1)

    def test_all_normal_missing_is_gap0_zero_only(self):
        values, _ = a.endpoints(saved((None,)*4), self.row(), ORACLE)
        self.assertEqual(values["gap0_mi"], 0)
        self.assertEqual(values["gap0_bon"], 0)
        self.assertIsNone(values["raw_perf_mi"])

    def test_infrastructure_error_cannot_be_gap0(self):
        result = saved((None,)*4)
        result["agent_results"][0]["terminal_origin"] = "provider_exception"
        with self.assertRaisesRegex(ValueError, "failure cannot become Gap0"):
            a.endpoints(result, self.row(), ORACLE)

    def test_search_missing_prediction_remains_evaluator_score(self):
        values, counts = a.endpoints(saved((0.4, 0.6, 0.8, None), "restricted_search"), self.row("restricted_search"), ORACLE)
        self.assertAlmostEqual(values["f1_mi"], 0.45)
        self.assertEqual(counts["scored_agents"], 4)
        self.assertEqual(counts["missing_answer_agents"], 1)

    def test_audit_ea_is_not_primary_answer_perf(self):
        result = saved((0.4, 0.6, 0.8, 1.0), "evidence_audit")
        values, _ = a.endpoints(result, self.row("evidence_audit"), ORACLE)
        self.assertEqual(values["evidence_acc_mv"], 0.7)
        self.assertEqual(values["label_acc_mv"], 0.8)

    def test_wrong_saved_strict_aggregate_rejected(self):
        result = saved()
        result["aggregate"]["answer_perf"] = 0.7
        with self.assertRaisesRegex(ValueError, "BoN mismatch"):
            a.endpoints(result, self.row(), ORACLE)

    def test_nonfinite_and_boolean_rejected(self):
        for value in (float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                a.number(value)


class AggregationTests(unittest.TestCase):
    def metric(self, item, seed, value, strategy="naive"):
        return dict(job_id=f"{item}-{seed}-{strategy}", model="m", scenario="tuning", regime="cost_tight",
                    strategy=strategy, metric="gap_mi", unit="Gap points", item=item, seed=str(seed), value=value)

    def test_fold_repeats_then_task_equal_weight(self):
        rows = [self.metric(item, seed, val) for item, vals in (("A", [10, 20, 30]), ("B", [40, 50, 60])) for seed, val in enumerate(vals)]
        result = a.grouped_metrics(rows)[0]
        self.assertEqual(result["full_mean"], 35)
        self.assertEqual(result["expected_items"], 2)
        self.assertEqual(result["repeats_per_item"], 3)

    def test_missing_pool_makes_full_setting_unknown(self):
        rows = [self.metric("A", 0, 10), self.metric("A", 1, None), self.metric("B", 0, 40), self.metric("B", 1, 60)]
        result = a.grouped_metrics(rows)[0]
        self.assertIsNone(result["full_mean"])
        self.assertEqual(result["known_subset_item_weighted_mean"], 30)
        self.assertEqual(result["known_pools"], 3)

    def test_negative_effect_and_no_complete_case_intersection(self):
        rows = [self.metric("A", 0, val, strategy) for strategy, val in zip(a.STRATEGIES, [80, 90, 70])]
        _, effects = a.comparisons(rows)
        values = {r["strategy"]: r["full_mean"] for r in effects}
        self.assertEqual(values["poolact_minus_cached"], -20)
        with self.assertRaisesRegex(ValueError, "intersect"):
            a.comparisons(rows[:2])

    def test_matrix_rejects_setting_mismatch_or_missing_arm(self):
        p = plan()
        self.assertEqual(len(a.validate_matrix(a.plan_rows(p), 3, 1)), 1)
        p["jobs"][0]["args"]["reasoning_effort"] = "low"
        with self.assertRaisesRegex(ValueError, "scientific args"):
            a.validate_matrix(a.plan_rows(p))
        p = plan()
        p["jobs"].pop()
        with self.assertRaisesRegex(ValueError, "comparison arm"):
            a.validate_matrix(a.plan_rows(p))

    def test_result_summary_keeps_old_counterexample_new_negative_and_unknown(self):
        rows = []
        for model, old, new in (("negative", [80, 90, 70], [90, 91, 89]),
                                ("positive", [80, 90, 95], [80, 90, None])):
            for strategy, before, after in zip(a.STRATEGIES, old, new):
                rows.append(dict(model=model, scenario="tuning", regime="cost_tight", metric="gap0_mi",
                                 strategy=strategy, historical_value=before, rerun_value=after))
        text = a.result_summary(rows)
        self.assertIn("旧负差共 1 个单元：低于至少一臂 1 个", text)
        self.assertIn("旧非负对照共 1 个单元：本轮未知 1 个", text)
        self.assertIn("-10.00 | -1.00", text)
        statuses = [dict(model=model, scenario="tuning", regime="cost_tight", execution_status="completed",
                         missing_answer_agents=0 if model == "negative" else 1)
                    for model in ("negative", "positive") for strategy in a.STRATEGIES]
        text = a.result_summary(rows, statuses)
        self.assertIn("残余负差单元（negative / NAS101 / tight）的三臂均无缺最终回答", text)
        self.assertNotIn("全部计划成员", text)

    def test_primary_direction_summary_keeps_unknown_in_denominator(self):
        rows = []
        for model, values in (("up", [10, 15, 20]), ("unknown", [None, 15, 20]), ("tie", [20, 20, 20])):
            for strategy, value in zip(a.STRATEGIES, values):
                rows.append(dict(model=model, scenario="tuning", regime="cost_tight", strategy=strategy,
                                 metric="gap_mi", full_mean=value))
        text = a.overall_primary_summary(rows)
        self.assertIn("高于 naive 1/3，高于 cached 2/3", text)
        self.assertIn("未知单元分别为 1、0", text)
        self.assertIn("Tight 单元中 1/3 高于两臂，未知 1", text)


class HistoricalDisplayTests(unittest.TestCase):
    def test_budget_uses_existing_display_units_and_preserves_improvement(self):
        budget, _ = historical_fixtures()
        parsed = a.historical_budget_data(a.csv_bytes(budget))
        text = a.historical_budget_display(parsed)
        self.assertIn("70.00 → 60.00", text)
        self.assertNotIn("7000.00", text)
        self.assertIn("110.00 → 115.00 | -5.00", text)
        self.assertIn("HPO/NAS 有 4/5 个模型", text)
        self.assertIn("DeepSeek 的 HPO/NAS 反而改善 5.00 点", text)

    def test_budget_rejects_missing_model_or_wrong_delta(self):
        budget, _ = historical_fixtures()
        with self.assertRaisesRegex(ValueError, "five-model"):
            a.historical_budget_data(a.csv_bytes(budget[:-1]))
        budget[0]["free_minus_tight"] = -10
        with self.assertRaisesRegex(ValueError, "Free-minus-Tight differs"):
            a.historical_budget_data(a.csv_bytes(budget))

    def test_ranking_preserves_tied_winners_and_known_transitions(self):
        _, rankings = historical_fixtures(tie=True)
        _, winners = a.historical_ranking_data(a.csv_bytes(rankings))
        text = a.historical_ranking_display(winners)
        self.assertIn("Kimi (90.00) / GLM (90.00)", text)
        self.assertIn("6 个家族中，3 个", text)
        self.assertIn("不存在横跨所有家族的同一最优模型", text)

    def test_ranking_rejects_candidate_or_winner_drift(self):
        _, rankings = historical_fixtures()
        rankings[0]["candidate_count"] = 4
        with self.assertRaisesRegex(ValueError, "candidate set changed"):
            a.historical_ranking_data(a.csv_bytes(rankings))
        _, rankings = historical_fixtures()
        rankings[0]["winner"] = False
        with self.assertRaisesRegex(ValueError, "winner flag/set mismatch"):
            a.historical_ranking_data(a.csv_bytes(rankings))


class EndToEndTests(unittest.TestCase):
    def fixture(self, root, failed=False):
        def put(name, obj, raw=False):
            data = obj if raw else a.jb(obj)
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return dict(path=name, bytes=len(data), sha256=a.sha(data))
        p = plan()
        p_entry = put("plan.json", p)
        records = []
        for i, job in enumerate(p["jobs"]):
            result = saved(strategy=job["args"]["strategies"][0])
            result.update(config=job["args"], implementation_sha256={"source_tree": p["source_tree_sha256"]})
            summary = dict(config=result["config"], implementation_sha256=result["implementation_sha256"],
                           strategies={result["strategy"]: result["aggregate"]})
            record = dict(logical_job_id=job["job_id"], execution_status="completed", cohort="synthetic-formal",
                          effective_plan=p_entry, effective_job_id=job["job_id"], identity_score_verification_passed=True,
                          result=put(f"pool{i}/result.json", result), summary=put(f"pool{i}/summary.json", summary),
                          verification_receipt=put(f"pool{i}/verification.json", {"passed": True}))
            if i == 0 and failed:
                record = dict(logical_job_id=job["job_id"], execution_status="failed", cohort="synthetic-failed",
                              reason="Connection refused; no model response")
            records.append(record)
        old, old0 = [], []
        for strategy in a.STRATEGIES:
            for metric in a.METRICS["tuning"]:
                r = dict(model="fixture-unfamiliar-model", system="poolact", scenario="tuning", regime="cost_tight",
                         strategy=strategy, metric=metric, slice_kind="all", slice="all")
                if metric.startswith("gap0"):
                    old0.append(dict(r, value=0))
                else:
                    old.append(dict(r, full_mean=0))
        old_budget, old_rankings = historical_fixtures()
        spec = dict(schema="expgym.material-report-inputs.v1", study_id="fixture", expected_jobs=3, expected_cells=1,
                    plans=[p_entry], execution_index=put("executions.json", dict(schema="expgym.material-execution-index.v1", jobs=records)),
                    oracle=put("oracle.json", ORACLE), historical_absolute=put("old.csv", a.csv_bytes(old), True),
                    historical_gap0=put("old0.csv", a.csv_bytes(old0), True),
                    historical_expgym_summary=put("old_budget.csv", a.csv_bytes(old_budget), True),
                    historical_family_rankings=put("old_rankings.csv", a.csv_bytes(old_rankings), True),
                    resources_by_setting=put("resources.csv", b"scope,value\nfixture,unknown\n", True),
                    all_attempts_index=put("attempts.json", {"fixture_only": True}))
        put("spec.json", spec)
        return root / "spec.json"

    def test_deterministic_complete_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = self.fixture(Path(tmp))
            first, second = a.generate(spec), a.generate(spec)
            self.assertEqual(first, second)
            self.assertIn("Gap=0", first["README.zh.md"].decode())
            self.assertIn("本轮未重跑单体矩阵", first["README.zh.md"].decode())
            self.assertIn("Search F1：Free→Tight", first["README.zh.md"].decode())
            self.assertIn("任务家族 / 指标", first["README.zh.md"].decode())
            self.assertIn("EXECUTION_NOTES.zh.md", first["README.zh.md"].decode())
            self.assertIn("原 legacy 评分可能回退自身 best", first["DETAILS.zh.md"].decode())
            self.assertIn("未事后把轨迹最优配置填给无回答成员", first["DETAILS.zh.md"].decode())
            self.assertEqual(first["historical_expgym_summary.csv"], (Path(tmp)/"old_budget.csv").read_bytes())
            self.assertEqual(first["historical_family_rankings.csv"], (Path(tmp)/"old_rankings.csv").read_bytes())
            counts = json.loads(first["CHECKS.json"])
            self.assertEqual(counts["expected_pools"], 3)
            self.assertEqual(counts["aggregate_rows"], 18)

    def test_failed_pool_stays_unknown_even_gap0(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = a.generate(self.fixture(Path(tmp), failed=True))
            rows = list(csv.DictReader(io.StringIO(outputs["pool_metrics.csv"].decode())))
            self.assertTrue(all(r["value"] == "" for r in rows if r["strategy"] == "naive"))
            self.assertEqual(json.loads(outputs["CHECKS.json"])["execution_status_counts"]["failed"], 1)

    def test_tampered_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = self.fixture(Path(tmp))
            (Path(tmp)/"pool0/result.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "input identity mismatch"):
                a.generate(spec)

    def test_recovery_cannot_change_reasoning_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = self.fixture(root)
            execution = json.loads((root/"executions.json").read_bytes())
            changed = json.loads((root/"plan.json").read_bytes())
            changed["jobs"][0]["args"]["reasoning_effort"] = "low"
            raw = a.jb(changed)
            (root/"recovery-plan.json").write_bytes(raw)
            execution["jobs"][0]["effective_plan"] = dict(path="recovery-plan.json", bytes=len(raw), sha256=a.sha(raw))
            raw = a.jb(execution)
            (root/"executions.json").write_bytes(raw)
            config = json.loads(spec.read_bytes())
            config["execution_index"].update(bytes=len(raw), sha256=a.sha(raw))
            spec.write_bytes(a.jb(config))
            with self.assertRaisesRegex(ValueError, "recovery changed model/scientific args"):
                a.generate(spec)


if __name__ == "__main__":
    unittest.main()
