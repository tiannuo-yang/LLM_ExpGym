"""Report contract tests using synthetic inputs only, never the formal outputs."""
import copy
import csv
from functools import lru_cache
import hashlib
import itertools
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import build_report as report
from analyze_deepseek_metrics import aggregate, collapse


COMMIT = "1" * 40
REVIEWED_SOURCE_COMMIT = "5aabf7f6b568a1281fb677a94c19cfb2e8ce98b8"
SOURCE = "2" * 64
MODEL = "unfamiliar-model-fixture"
STUDY = "report-fixture-study"
BASE_URL = "https://github.com/fixture-owner/fixture-repo/blob/" + COMMIT + "/fixture/"
FILES = {
    "INPUTS.json", "COSTS.json", "SOURCE_INDEX.json", "normalized.csv",
    "metrics_execution.csv", "metrics.csv", "absolute_settings.csv",
    "contrasts.csv", "by_outerseed.csv", "raw_terminals.csv", "all_attempt_costs.csv",
}
READ_FILES = {"INPUTS.json", "COSTS.json", "normalized.csv", "absolute_settings.csv",
              "contrasts.csv", "by_outerseed.csv"}
OUTPUTS = {"README.zh.md", "TABLES.md", "REPEATS.md"}
QUALITY = {
    ("expgym", "restricted_search"): ("f1",),
    ("expgym", "evidence_audit"): ("evidence_acc", "label_acc"),
    ("expgym", "tuning"): ("gap", "raw_perf"),
    ("poolact", "restricted_search"): ("f1_mi", "f1_mv"),
    ("poolact", "evidence_audit"): ("evidence_acc_mi", "evidence_acc_mv", "label_acc_mi", "label_acc_mv"),
    ("poolact", "tuning"): ("gap_mi", "gap_bon", "raw_perf_mi", "raw_perf_bon"),
}
RESOURCES = ("input_tokens", "output_tokens", "feedback_attempts", "feedback_visible",
             "duplicate_action_attempts", "feedback_cost_seconds", "wall_time_seconds",
             "protocol_failure_rate", "budget_utilization")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def checksum(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: canonical(value) if isinstance(value, (dict, list, tuple)) else value
                             for key, value in row.items()})


@lru_cache(maxsize=4)
def synthetic_tables(unknown=False, escaped=False):
    """Mirror counts/units, not the real study's measurements or raw artifacts."""
    jobs, normalized, executions = [], [], []
    regimes = ("cost_free", "cost_moderate", "cost_tight")
    strategies = ("naive", "cached", "poolact")
    whois = [("phantom_seed2", i, "whois") for i in range(20)] + [("phantom_seed3", i, "whois") for i in range(19)]
    whatis = [("phantom_seed2", i, "whatis") for i in range(20, 37)] + [("phantom_seed3", i, "whatis") for i in range(19, 36)]
    nas = ["hpobench:nasbench101:" + name for name in ("A", "B", "C")]
    if escaped:
        nas[0] += " | <unsafe>\nnext"
    tasks = [(item, "nasbench101") for item in nas]
    tasks += [("hpobench:paramnet:" + name, "paramnet") for name in ("adult", "higgs", "jasmine")]
    tasks += [("hpobench:fcnet:" + name, "fcnet") for name in ("naval", "protein", "parkinsons")]

    def add(system, scenario, item, family, regime, strategy, outerrep, order, source=None, question=None):
        job_id = "job_%064x" % len(jobs)
        n = 1 if system == "expgym" else 4
        seed = 2200 + 4 * outerrep + (order if type(order) is int else 0)
        meta = dict(execution_id=job_id, model=MODEL, system=system, scenario=scenario,
                    item=item, family=family, regime=regime, strategy=strategy, N=n,
                    outerrep=outerrep, order=order, seed=seed)
        args = dict(model=MODEL, backend="openai", api_protocol="chat", scenario=scenario,
                    cost_regime=regime, seed=seed, agents=n, repeats=1, max_steps=30,
                    max_evals=30, max_tokens=32768, temperature=1, temperature_tuning=1,
                    temperature_eval=1, top_p=.95, top_k=None, tool_protocol="native",
                    max_protocol_retries=1, max_retries=2, reasoning_effort="max", request_timeout=7200,
                    chat_template_kwargs={"thinking": True},
                    tuning_final_policy="legacy", missing_final_policy="task-abstention-v1",
                    max_context_tokens=131072, probes=4)
        selection = dict(scenario=scenario, cost_regime=regime, model_id=MODEL,
                         model_alias=MODEL, seed=seed, rep=order if type(order) is int else 0,
                         repeat_index=0, strategy=strategy, question_index=question or 0)
        if scenario == "tuning":
            args["tuning_task"] = selection["tuning_task"] = item
        elif scenario == "restricted_search":
            args["data_source"] = selection["data_source"] = source
            args["question_index"] = question
        else:
            args["cc_split"] = selection["cc_split"] = "cc-large"
        jobs.append(dict(job_id=job_id, runner=system, args=args, selection=selection))
        normalized.append({**meta, "execution_complete": True,
                           "state_root": "/synthetic/queue", "artifact_root": "/synthetic/" + job_id})
        base = {"cost_free": .8, "cost_moderate": .6, "cost_tight": .4}[regime] if system == "expgym" else {"naive": .45, "cached": .65, "poolact": .55}[strategy]
        base += outerrep * .01 + (order * .001 if type(order) is int else 0)
        missing_pool = (unknown and system == "poolact" and scenario == "tuning"
                        and item == nas[0] and regime == "cost_moderate" and strategy == "cached" and outerrep == 1)
        for metric in QUALITY[system, scenario]:
            value = None if missing_pool else base * (100 if metric.startswith("gap") else 1)
            executions.append({**meta, "metric": metric, "value": value,
                               "unit": "Gap points" if metric.startswith("gap") else "fraction",
                               "higher_is_better": True, "scope": "quality"})
        for metric in RESOURCES:
            if metric == "budget_utilization" and regime == "cost_free":
                continue
            value = {"input_tokens": 100 * n, "output_tokens": 10 * n,
                     "feedback_attempts": 2 * n, "feedback_visible": 2 * n,
                     "duplicate_action_attempts": 0, "feedback_cost_seconds": 2 * n,
                     "wall_time_seconds": 1 if n == 1 else None,
                     "protocol_failure_rate": 0, "budget_utilization": .5}[metric]
            unit = ("tokens" if metric in {"input_tokens", "output_tokens"} else "seconds" if metric.endswith("seconds")
                    else "fraction" if metric in {"protocol_failure_rate", "budget_utilization"} else "count")
            executions.append({**meta, "metric": metric, "value": value, "unit": unit,
                               "higher_is_better": None, "scope": "resource"})

    for regime, (source, question, family) in itertools.product(regimes, whois + whatis):
        add("expgym", "restricted_search", "%s:%s" % (source, question), family, regime, "single", 0, "none", source, question)
    for regime, question, order in itertools.product(regimes, range(13), range(3)):
        add("expgym", "evidence_audit", "doc-%02d" % question, "evidence_audit", regime, "single", 0, order, question=question)
    for regime, (item, family), outerrep in itertools.product(regimes, tasks, range(3)):
        add("expgym", "tuning", item, family, regime, "single", outerrep, "none")
    for regime, strategy, (source, question, family) in itertools.product(regimes[1:], strategies, whois):
        add("poolact", "restricted_search", "%s:%s" % (source, question), family, regime, strategy, 0, "none", source, question)
    for regime, strategy, question in itertools.product(regimes[1:], strategies, range(13)):
        add("poolact", "evidence_audit", "doc-%02d" % question, "evidence_audit", regime, strategy, 0, "default", question=question)
    for regime, strategy, item, outerrep in itertools.product(regimes[1:], strategies, nas, range(3)):
        add("poolact", "tuning", item, "nasbench101", regime, strategy, outerrep, "none")
    scientific = collapse(executions)
    absolute, repeats, contrasts = aggregate(scientific)
    assert len(jobs) == len(normalized) == 783
    assert sum(row["N"] for row in normalized) == 1881
    assert len({row["analysis_id"] for row in scientific}) == 705
    return jobs, normalized, executions, scientific, absolute, repeats, contrasts


class Fixture:
    def __init__(self, root, *, unknown=False, escaped=False):
        self.root = Path(root)
        self.analysis = self.root / "analysis"
        self.context_dir = self.root / "context"
        self.analysis.mkdir()
        self.context_dir.mkdir()
        profile = {"schema": "deepseek-flash.model-profile.v1", "model": MODEL,
                   "reasoning_effort": "max", "chat_template_kwargs": {"thinking": True}}
        profile_path = self.context_dir / "model_profile.json"
        write_json(profile_path, profile)
        profile_pin = {key: value for key, value in self.pin(profile_path).items() if key != "url"}

        jobs, normalized, executions, scientific, absolute, repeats, contrasts = synthetic_tables(unknown, escaped)
        tuning_items = sorted({row["item"] for row in normalized if row["scenario"] == "tuning"})
        self.context = {
            "plan": {"schema": "expgym.study-queue-plan.v1", "study_id": STUDY,
                     "source_tree_sha256": SOURCE, "jobs": copy.deepcopy(jobs)},
            "coverage": {"schema_version": "deepseek-flash-fixed-matrix-coverage-v1", "model": MODEL,
                         "queue_jobs": 783, "logical_outcomes": 783, "agent_traces": 1881,
                         "model_profile": {**profile_pin, "value": profile},
                         "full_canonical_identity_matches": True, "deployment_pending": False,
                         "origin_manifest": {"publication_commit": COMMIT, "sha256": "3" * 64},
                         "search_filter": {"types": ["whois", "whatis"], "max_answer_count": 10,
                                           "stable_sort": ["type", "difficulty"]}},
            "serving_plan": {"schema_version": 3, "model": MODEL, "checkpoint": "/synthetic/checkpoint",
                             "config": {"slurm": {"nodes": 4, "gpus_per_node": 8},
                                        "topology": {"replicas": 4, "tp_size": 8, "pp_size": 1, "nodes_per_replica": 1}},
                             "context_length": 262144, "reasoning_parser": "fixture-reasoning",
                             "tool_call_parser": "fixture-tools", "ep_size": 1},
            "oracle": {"tasks": {item: {"best_cost": 12.5 + 3 * index}
                                  for index, item in enumerate(tuning_items)}},
        }
        self.context_paths = {name: self.context_dir / (name + ".json")
                              for name in ("plan", "coverage", "run_inputs", "serving_plan", "oracle")}
        for name, data in self.context.items():
            write_json(self.context_paths[name], data)
        self.context["run_inputs"] = {
            "schema": "deepseek-flash.run-inputs.v1", "study_id": STUDY,
            "source_tree_sha256": SOURCE, "source_commit": REVIEWED_SOURCE_COMMIT,
            "inputs": [{key: value for key, value in self.pin(self.context_paths[name]).items() if key != "url"}
                       for name in ("plan", "coverage", "serving_plan", "oracle")] + [profile_pin],
            "runtime_encoding_files": [{"path": "/synthetic/runtime/encoding_dsv4.py", "bytes": 1234, "sha256": "7" * 64}],
        }
        write_json(self.context_paths["run_inputs"], self.context["run_inputs"])
        self.context_paths["provider_contract"] = self.context_dir / "provider_contract.json"
        self.context["provider_contract"] = {
            "schema": "deepseek-flash.provider-contract.v1", "model": MODEL,
            "source_commit": REVIEWED_SOURCE_COMMIT,
            "serving_plan_sha256": self.pin(self.context_paths["serving_plan"])["sha256"],
            "model_profile_sha256": profile_pin["sha256"],
            "runtime_encoding_files": copy.deepcopy(self.context["run_inputs"]["runtime_encoding_files"]),
            "precision": {"weights": "FP4 experts (mixed checkpoint)", "dense_weights": "FP8",
                          "backend": "Marlin", "arithmetic": "W4A16 MoE"},
            "vendor_recommended_max_output_label": "384K", "speculative_decoding": False, "mtp_used": False,
            "validation": {"status": "passed",
                "scope": "Synthetic fixture representing real wire dump plus actual encoder CPU replay, not a real model test",
                "evidence": {
                    name: {"path": "/synthetic/" + name + ".json", "bytes": 123, "sha256": "8" * 64,
                           "url": BASE_URL + name + ".json"}
                    for name in ("native_wire", "cpu_encoder_replay")}},
            "forced_final": {
                "wire_tools_retained": {"value": True, "evidence": ["native_wire"]},
                "rendered_tool_definitions_retained": {"value": True, "evidence": ["cpu_encoder_replay"]},
                "assistant_reasoning_history_retained": {"value": True, "evidence": ["native_wire", "cpu_encoder_replay"]},
                "tool_history_retained": {"value": True, "evidence": ["native_wire", "cpu_encoder_replay"]}},
        }
        write_json(self.context_paths["provider_contract"], self.context["provider_contract"])
        analyzer_inputs = {"schema": "deepseek-flash.analysis.v1", "input_pins": {
            "plan": self.pin(self.context_paths["plan"])["sha256"],
            "coverage": self.pin(self.context_paths["coverage"])["sha256"],
            "reference_manifest": "3" * 64,
            "oracle": self.pin(self.context_paths["oracle"])["sha256"], "states": "5" * 64},
            "python": "3.11.fixture", "execution_slots": 783, "analysis_units": 705,
            "agent_slots": 1881, "score_recomputation": False, "model_calls": 0,
            "independent_postdraft_review": "not performed by generator", "archive_content_verification": False}
        write_json(self.analysis / "INPUTS.json", analyzer_inputs)
        amounts = {"input_tokens": 188100, "output_tokens": 18810,
                   "reasoning_tokens_included_in_output": 9405, "total_tokens": 206910,
                   "request_wall_seconds": 1881}
        costs = {scope: {name: {"complete_total": value, "known_subset_total": value,
                               "known": 1881, "expected": 1881} for name, value in amounts.items()}
                 for scope in ("all_physical_attempts", "effective_slots")}
        write_json(self.analysis / "COSTS.json", costs)
        for name, rows in (("normalized.csv", normalized), ("metrics_execution.csv", executions),
                           ("metrics.csv", scientific), ("absolute_settings.csv", absolute),
                           ("by_outerseed.csv", repeats), ("contrasts.csv", contrasts)):
            write_csv(self.analysis / name, rows)
        # These are valid but deliberately minimal opaque exports, not raw logs.
        write_csv(self.analysis / "raw_terminals.csv", [{"execution_id": "synthetic-opaque", "raw_answer": None}])
        write_csv(self.analysis / "all_attempt_costs.csv", [{"request_id": "synthetic-opaque", "input_tokens": None}])
        write_json(self.analysis / "SOURCE_INDEX.json", {"schema": "deepseek-flash.analysis.v1", "files": []})
        self.descriptor = {"schema": "deepseek-flash.report-inputs.v1",
                           "files": {name: self.pin(self.analysis / name) for name in sorted(FILES)},
                           "context": {name: self.pin(path) for name, path in self.context_paths.items()}}
        self.inputs_path = self.root / "REPORT_INPUTS.json"
        self.refresh_descriptor()
        self.output = self.root / "report"
        self.links = {"archive_index": BASE_URL + "ARCHIVE_INDEX.md",
                      "archive_index_json": BASE_URL + "ARCHIVE_INDEX.json",
                      "previous_report": BASE_URL + "previous/README.zh.md"}

    def pin(self, path):
        raw = path.read_bytes()
        return {"path": str(path), "bytes": len(raw), "sha256": checksum(raw),
                "url": BASE_URL + path.name}

    def refresh_descriptor(self):
        write_json(self.inputs_path, self.descriptor)
        self.inputs_sha256 = checksum(self.inputs_path.read_bytes())

    def repin_context(self, name, *, bind_run=True, bind_analyzer=True):
        """Keep unrelated pins valid so mutations reach their semantic check."""
        path = self.context_paths[name]
        write_json(path, self.context[name])
        pin = self.pin(path)
        self.descriptor["context"][name] = pin
        if bind_run and name != "run_inputs":
            entries = self.context["run_inputs"]["inputs"]
            replacement = {key: value for key, value in pin.items() if key != "url"}
            for index, entry in enumerate(entries):
                if entry["path"] == str(path):
                    entries[index] = replacement
                    break
            else:
                raise AssertionError("fixture lacks context binding: " + name)
            run_path = self.context_paths["run_inputs"]
            write_json(run_path, self.context["run_inputs"])
            self.descriptor["context"]["run_inputs"] = self.pin(run_path)
        if bind_analyzer and name in {"plan", "coverage", "oracle"}:
            inputs_path = self.analysis / "INPUTS.json"
            inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
            inputs["input_pins"][name] = pin["sha256"]
            write_json(inputs_path, inputs)
            self.descriptor["files"]["INPUTS.json"] = self.pin(inputs_path)
        self.refresh_descriptor()

    def generate(self, *, check=False, links=None, output=None):
        return report.generate(self.inputs_path, self.inputs_sha256,
                               output or self.output, links or self.links, check=check)

    def read_output(self):
        return {name: (self.output / name).read_text(encoding="utf-8") for name in sorted(OUTPUTS)}


class BuildReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="deepseek-report-fixture-")
        self.addCleanup(self.temporary.cleanup)

    def fixture(self, **kwargs):
        return Fixture(self.temporary.name, **kwargs)

    def test_full_synthetic_report_preserves_inputs_and_only_three_outputs(self):
        fixture = self.fixture()
        before = {path: checksum(path.read_bytes()) for path in fixture.root.rglob("*") if path.is_file()}
        fixture.generate()
        self.assertEqual({path.name for path in fixture.output.iterdir()}, OUTPUTS)
        self.assertEqual(before, {path: checksum(path.read_bytes()) for path in before})
        text = "\n".join(fixture.read_output().values())
        for count in ("783", "1881", "705"):
            self.assertIn(count, text.replace(",", ""))
        for link in fixture.links.values():
            self.assertIn(link, text)
        self.assertIn(MODEL, text)

    def test_moderate_cached_and_all_effect_directions_are_visible(self):
        fixture = self.fixture()
        fixture.generate()
        output = fixture.read_output()
        text = "\n".join(output.values())
        for token in ("cached", "naive", "poolact", "f1_mv", "gap_mi", "gap_bon", "label_acc_mv"):
            self.assertIn(token, text)
        self.assertRegex(text, r"(?i)moderate|中等|适中")
        self.assertRegex(text, r"-0\.1(?:0+)?(?:\D|$)")
        self.assertRegex(text, r"0\.2(?:0+)?(?:\D|$)")

    def test_r3_seeds_and_audit_are_not_repeated_twice(self):
        fixture = self.fixture()
        fixture.generate()
        output = fixture.read_output()
        for seed in ("2200", "2204", "2208"):
            self.assertIn(seed, output["REPEATS.md"])
        text = "\n".join(output.values())
        self.assertIn("117", text)
        self.assertIn("39", text)
        self.assertRegex(text, r"SD|标准差|standard deviation")

    def test_finite_budgets_use_frozen_oracle_not_default_100(self):
        fixture = self.fixture()
        fixture.generate()
        text = "\n".join(fixture.read_output().values())
        lines = text.splitlines()

        def has_budget_line(label, amounts):
            return any(re.search(label, line, re.IGNORECASE)
                       and all(re.search(r"(?<![\d.])" + re.escape(str(amount))
                                         + r"(?:\.0+)?(?![\d.])", line)
                               for amount in amounts) for line in lines)

        for label in (r"Search|restricted_search", r"Audit|evidence_audit"):
            self.assertTrue(has_budget_line(label, (300, 3000, 900)),
                            "Search/Audit must show c_base=300, M=3000, T=900")
        first_item = sorted(fixture.context["oracle"]["tasks"])[0]
        self.assertTrue(has_budget_line(re.escape(first_item), (12.5, 125, 37.5)),
                        "Tuning budget must use its non-default frozen best_cost")

    def test_missing_full_pool_stays_unknown_in_report(self):
        fixture = self.fixture(unknown=True)
        fixture.generate()
        text = "\n".join(fixture.read_output().values())
        self.assertIn("unknown", text.lower())
        self.assertRegex(text, r"已知|known")
        self.assertIn("gap_mi", text)
        self.assertRegex(text, r"-0\.1(?:0+)?(?:\D|$)")

    def test_markdown_task_labels_escape_pipe_newline_and_html(self):
        fixture = self.fixture(escaped=True)
        fixture.generate()
        text = "\n".join(fixture.read_output().values())
        self.assertNotIn("A | <unsafe>\nnext", text)
        self.assertNotIn("<unsafe>", text)
        self.assertTrue("\\|" in text or "&#124;" in text,
                        "Markdown pipe must be safely escaped")
        self.assertIn("&lt;unsafe&gt;", text)

    def test_check_is_byte_deterministic_and_read_only(self):
        fixture = self.fixture()
        fixture.generate()
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in fixture.output.iterdir()}
        original_open = Path.open

        def forbid_write(path, mode="r", *args, **kwargs):
            self.assertFalse(any(flag in mode for flag in "wax+"), "check attempted a file write")
            return original_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", forbid_write), patch.object(Path, "mkdir", side_effect=AssertionError("check attempted mkdir")):
            fixture.generate(check=True)
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in before})

    def test_check_detects_changed_report_without_rewriting(self):
        fixture = self.fixture()
        fixture.generate()
        target = fixture.output / "TABLES.md"
        target.write_text(target.read_text() + "\nsynthetic tamper\n")
        before = target.read_bytes()
        with self.assertRaises((ValueError, AssertionError)):
            fixture.generate(check=True)
        self.assertEqual(target.read_bytes(), before)

    def test_existing_output_and_check_missing_output_rejected(self):
        fixture = self.fixture()
        with self.assertRaises((ValueError, FileNotFoundError)):
            fixture.generate(check=True)
        self.assertFalse(fixture.output.exists())
        fixture.output.mkdir()
        with self.assertRaises((ValueError, FileExistsError)):
            fixture.generate()
        self.assertEqual(list(fixture.output.iterdir()), [])

    def test_opaque_five_exports_are_not_read_again(self):
        fixture = self.fixture()
        opaque = {fixture.analysis / name for name in FILES - READ_FILES}
        original_open, original_read = Path.open, Path.read_bytes

        def guarded_open(path, mode="r", *args, **kwargs):
            self.assertNotIn(path.absolute(), opaque, "metadata-only export was opened")
            return original_open(path, mode, *args, **kwargs)

        def guarded_read(path, *args, **kwargs):
            self.assertNotIn(path.absolute(), opaque, "metadata-only export was read")
            return original_read(path, *args, **kwargs)

        with patch.object(Path, "open", guarded_open), patch.object(Path, "read_bytes", guarded_read):
            fixture.generate()

    def test_moving_or_non_github_urls_rejected(self):
        fixture = self.fixture()
        invalid = [BASE_URL.replace(COMMIT, "main") + "ARCHIVE_INDEX.md",
                   BASE_URL.replace(COMMIT, COMMIT[:8]) + "ARCHIVE_INDEX.md",
                   BASE_URL.replace("https://", "http://") + "ARCHIVE_INDEX.md",
                   BASE_URL.replace("github.com", "github.com.evil.invalid") + "ARCHIVE_INDEX.md",
                   BASE_URL + "ARCHIVE_INDEX.md?token=not-a-secret"]
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                fixture.generate(links={**fixture.links, "archive_index": url})
            self.assertFalse(fixture.output.exists())

    def test_descriptor_and_consumed_input_sha_mismatches_rejected(self):
        fixture = self.fixture()
        with self.assertRaises(ValueError):
            report.generate(fixture.inputs_path, "0" * 64, fixture.output, fixture.links)
        target = fixture.analysis / "COSTS.json"
        target.write_text(target.read_text().replace("188100", "188101"))
        with self.assertRaises(ValueError):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_exact_sibling_indexes_generate_and_check_without_self_commit(self):
        fixture = self.fixture()
        links = {**fixture.links, "archive_index": "ARCHIVE_INDEX.md",
                 "archive_index_json": "ARCHIVE_INDEX.json"}
        fixture.generate(links=links)
        text = fixture.read_output()["README.zh.md"]
        self.assertIn("[原始 dump 存档索引](ARCHIVE_INDEX.md)", text)
        self.assertIn("[机器可读存档索引](ARCHIVE_INDEX.json)", text)
        self.assertIn(fixture.links["previous_report"], text)
        fixture.generate(links=links, check=True)

    def test_relative_navigation_is_exact_name_and_role_whitelisted(self):
        invalid = [("archive_index", value) for value in
                   ("../ARCHIVE_INDEX.md", "./ARCHIVE_INDEX.md", "ARCHIVE_INDEX.json",
                    "/ARCHIVE_INDEX.md", "ARCHIVE_INDEX.md?x=1", "ARCHIVE_INDEX.md#anchor")]
        invalid += [("archive_index_json", "ARCHIVE_INDEX.md"),
                    ("previous_report", "ARCHIVE_INDEX.md")]
        for name, value in invalid:
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                report.navigation_link(name, value)

    def test_immutable_urls_required_for_each_input_not_only_navigation(self):
        fixture = self.fixture()
        original = copy.deepcopy(fixture.descriptor)
        invalid = [("files", "metrics.csv", BASE_URL.replace(COMMIT, "main") + "metrics.csv"),
                   ("files", "metrics.csv", "ARCHIVE_INDEX.md"),
                   ("context", "oracle", "ARCHIVE_INDEX.json"),
                   ("context", "provider_contract", "ARCHIVE_INDEX.md")]
        for section, name, value in invalid:
            fixture.descriptor = copy.deepcopy(original)
            fixture.descriptor[section][name]["url"] = value
            fixture.refresh_descriptor()
            with self.subTest(section=section, name=name, value=value), self.assertRaises(ValueError):
                fixture.generate()
            self.assertFalse(fixture.output.exists())

    def test_exact_eleven_file_inventory_required(self):
        fixture = self.fixture()
        fixture.descriptor["files"].pop("metrics_execution.csv")
        fixture.refresh_descriptor()
        with self.assertRaises(ValueError):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_run_source_binding_mismatch_rejected(self):
        fixture = self.fixture()
        fixture.context["run_inputs"]["source_tree_sha256"] = "9" * 64
        path = fixture.context_paths["run_inputs"]
        write_json(path, fixture.context["run_inputs"])
        fixture.descriptor["context"]["run_inputs"] = fixture.pin(path)
        fixture.refresh_descriptor()
        with self.assertRaises(ValueError):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_missing_run_input_binding_rejected(self):
        fixture = self.fixture()
        fixture.context["run_inputs"]["inputs"].pop()
        path = fixture.context_paths["run_inputs"]
        write_json(path, fixture.context["run_inputs"])
        fixture.descriptor["context"]["run_inputs"] = fixture.pin(path)
        fixture.refresh_descriptor()
        with self.assertRaises(ValueError):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_oracle_run_input_binding_mismatch_rejected(self):
        fixture = self.fixture()
        item = next(iter(fixture.context["oracle"]["tasks"]))
        fixture.context["oracle"]["tasks"][item]["best_cost"] += 1
        fixture.repin_context("oracle", bind_run=False)
        with self.assertRaisesRegex(ValueError, r"(?i)oracle|context not bound by RUN_INPUTS"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_oracle_analyzer_input_binding_mismatch_rejected(self):
        fixture = self.fixture()
        item = next(iter(fixture.context["oracle"]["tasks"]))
        fixture.context["oracle"]["tasks"][item]["best_cost"] += 1
        fixture.repin_context("oracle", bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, r"(?i)oracle|analysis/context pin mismatch"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_oracle_missing_task_rejected_after_all_bindings_repin(self):
        fixture = self.fixture()
        fixture.context["oracle"]["tasks"].pop(next(iter(fixture.context["oracle"]["tasks"])))
        fixture.repin_context("oracle")
        with self.assertRaisesRegex(ValueError, r"(?i)oracle|best_cost|tuning.*task"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_oracle_best_cost_must_be_positive_numeric(self):
        fixture = self.fixture()
        item = next(iter(fixture.context["oracle"]["tasks"]))
        for value in (0, -1, True, None, "12.5"):
            with self.subTest(best_cost=value):
                fixture.context["oracle"]["tasks"][item]["best_cost"] = value
                fixture.repin_context("oracle")
                with self.assertRaisesRegex(ValueError, r"(?i)oracle|best_cost|budget"):
                    fixture.generate()
                self.assertFalse(fixture.output.exists())

    def test_budget_overrides_rejected_after_all_plan_bindings_repin(self):
        fixture = self.fixture()
        original_jobs = copy.deepcopy(fixture.context["plan"]["jobs"])
        cases = (("cost_regime", "custom"), ("beta", 1.5), ("time_budget", 123))
        for key, value in cases:
            with self.subTest(option=key):
                fixture.context["plan"]["jobs"] = copy.deepcopy(original_jobs)
                job = next(job for job in fixture.context["plan"]["jobs"]
                           if job["args"]["cost_regime"] == "cost_moderate")
                job["args"][key] = value
                fixture.repin_context("plan")
                with self.assertRaisesRegex(ValueError, r"(?i)budget|regime|beta|override|custom"):
                    fixture.generate()
                self.assertFalse(fixture.output.exists())

    def test_unreviewed_budget_source_commit_rejected(self):
        fixture = self.fixture()
        fixture.context["run_inputs"]["source_commit"] = "9" * 40
        fixture.repin_context("run_inputs")
        fixture.context["provider_contract"]["source_commit"] = "9" * 40
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, r"(?i)source|commit|budget"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_provider_settings_and_mixed_precision_are_visible(self):
        fixture = self.fixture()
        # This deployment needs no invented failed startup or Qwen accounting
        # sidecar. Allocation IDs are recorded separately from replica count.
        self.assertNotIn("accounting", fixture.descriptor["context"])
        fixture.generate()
        text = fixture.read_output()["README.zh.md"]
        for value in ("384K", "32768", "262144", "FP4 experts", "FP8", "Marlin", "W4A16 MoE",
                      "7200", "最大 thinking", "四个独立的单节点 TP8", "不使用 MTP"):
            self.assertIn(value, text)
        self.assertNotIn("qwen", text.lower())
        for name, pin in fixture.context["provider_contract"]["validation"]["evidence"].items():
            self.assertIn(name, text)
            self.assertIn(pin["url"], text)
        self.assertIn("allocation GPU-hours", text)
        self.assertIn("不从请求、agent 时长、当前时间", text)
        self.assertIn("4 × 8", text)
        self.assertTrue("&#91;4,8,1,1&#93;" in text, "replicas/TP/PP/EP row must render 4/8/1/1")
        self.assertNotIn("startup_attempt", text)
        self.assertIn("未提供该账本时，本报告中这些量均为 unknown", text)

    def test_profile_or_timeout_cannot_drift_from_max_setting(self):
        fixture = self.fixture()
        original = copy.deepcopy(fixture.context["plan"]["jobs"])
        cases = (("top_k", 20), ("reasoning_effort", "high"),
                 ("chat_template_kwargs", {"thinking": False}), ("request_timeout", 3600),
                 ("max_tokens", 393216), ("temperature_eval", 0), ("max_retries", 3))
        for key, value in cases:
            with self.subTest(key=key):
                fixture.context["plan"]["jobs"] = copy.deepcopy(original)
                fixture.context["plan"]["jobs"][0]["args"][key] = value
                fixture.repin_context("plan")
                with self.assertRaisesRegex(ValueError, "profile|transport|temperature"):
                    fixture.generate()
                self.assertFalse(fixture.output.exists())

    def test_provider_topology_and_encoder_identity_must_match(self):
        fixture = self.fixture()
        provider = fixture.context["provider_contract"]
        provider["runtime_encoding_files"][0]["sha256"] = "9" * 64
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, "encoder identity"):
            fixture.generate()
        provider["runtime_encoding_files"] = copy.deepcopy(fixture.context["run_inputs"]["runtime_encoding_files"])
        fixture.context["serving_plan"]["config"]["topology"]["replicas"] = 2
        fixture.repin_context("serving_plan")
        provider["serving_plan_sha256"] = fixture.descriptor["context"]["serving_plan"]["sha256"]
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, "topology"):
            fixture.generate()

    def test_native_million_token_context_is_read_from_serving_plan(self):
        fixture = self.fixture()
        fixture.context["serving_plan"]["context_length"] = 1048576
        fixture.repin_context("serving_plan")
        provider = fixture.context["provider_contract"]
        provider["serving_plan_sha256"] = fixture.descriptor["context"]["serving_plan"]["sha256"]
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        fixture.generate()
        text = fixture.read_output()["README.zh.md"]
        self.assertIn("context_length=1048576", text)
        self.assertNotIn("context_length=262144", text)
        self.assertIn("32768", text)
        self.assertIn("131072", text)

    def test_boolean_retention_claim_without_corresponding_evidence_rejected(self):
        fixture = self.fixture()
        provider = fixture.context["provider_contract"]
        provider["forced_final"]["rendered_tool_definitions_retained"]["evidence"] = ["native_wire"]
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, "lacks actual wire/encoder evidence"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_unverified_provider_properties_remain_unknown(self):
        fixture = self.fixture()
        provider = fixture.context["provider_contract"]
        provider["validation"].update(status="unverified", scope="No actual native or encoder evidence supplied", evidence={})
        for value in provider["forced_final"].values():
            value.update(value=None, evidence=[])
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        fixture.generate()
        text = fixture.read_output()["README.zh.md"]
        self.assertIn("unverified", text)
        self.assertIn('"observed":null', text)
        self.assertIn("尚未提供实际 wire/encoder 证据", text)

    def test_provider_evidence_pin_requires_immutable_url(self):
        fixture = self.fixture()
        pin = fixture.context["provider_contract"]["validation"]["evidence"]["cpu_encoder_replay"]
        pin["url"] = pin["url"].replace(COMMIT, "main")
        fixture.repin_context("provider_contract", bind_run=False, bind_analyzer=False)
        with self.assertRaisesRegex(ValueError, "immutable"):
            fixture.generate()

    def test_provider_contract_is_required_and_hash_bound(self):
        fixture = self.fixture()
        fixture.context["provider_contract"]["precision"]["backend"] = "marlin"
        write_json(fixture.context_paths["provider_contract"], fixture.context["provider_contract"])
        with self.assertRaisesRegex(ValueError, "SHA"):
            fixture.generate()
        fixture.descriptor["context"].pop("provider_contract")
        fixture.refresh_descriptor()
        with self.assertRaisesRegex(ValueError, "complete.*inventory"):
            fixture.generate()

    def test_missing_task_row_rejected_after_valid_input_repin(self):
        fixture = self.fixture()
        path = fixture.analysis / "absolute_settings.csv"
        rows = report.read_csv(path.read_bytes())
        omitted = next(row for row in rows if row["slice_kind"] == "task" and row["metric"] == "gap")
        rows.remove(omitted)
        write_csv(path, rows)
        fixture.descriptor["files"][path.name] = fixture.pin(path)
        fixture.refresh_descriptor()
        with self.assertRaisesRegex(ValueError, "omit planned"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())

    def test_reversed_negative_effect_rejected_not_silently_corrected(self):
        fixture = self.fixture()
        path = fixture.analysis / "contrasts.csv"
        rows = report.read_csv(path.read_bytes())
        selected = next(row for row in rows if row["system"] == "poolact" and row["effect"] is not None and row["effect"] < 0)
        selected["effect"] *= -1
        write_csv(path, rows)
        fixture.descriptor["files"][path.name] = fixture.pin(path)
        fixture.refresh_descriptor()
        with self.assertRaisesRegex(ValueError, "arithmetic differs"):
            fixture.generate()
        self.assertFalse(fixture.output.exists())


if __name__ == "__main__":
    unittest.main()
