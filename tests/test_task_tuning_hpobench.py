import os
import unittest
import json
import threading
from types import SimpleNamespace
from unittest.mock import patch

from expgym.task_tuning import (
    build_fake_plan,
    list_hpobench_tasks,
    _load_hpobench,
    _get_hpobench_fidelity_settings,
    _hpobench_evaluate,
    _task_hints,
    _nasbench101_edge_pairs,
    evaluate_hpobench_action,
    InvalidConfigurationError,
)


def _has_hpobench_deps() -> bool:
    try:
        import ConfigSpace  # noqa: F401
    except Exception:
        return False
    return True


class TestHPOBenchTasks(unittest.TestCase):
    def test_fake_plan_serializes_numpy_choices_as_json_primitives(self) -> None:
        import numpy as np

        values = {
            "edge": np.int64(1),
            "rate": np.float32(0.25),
            "enabled": np.bool_(True),
            "operation": np.str_("conv1x1-bn-relu"),
        }
        config_space = SimpleNamespace(sample_configuration=lambda: dict(values))
        task = SimpleNamespace(name="numpy-choices", config_space=config_space)
        with patch("expgym.task_tuning._load_hpobench", return_value=task), patch.dict(
            "expgym.task_tuning._HPOBENCH_EVAL_LOCKS",
            {task.name: threading.Lock()},
        ):
            plan = build_fake_plan(1, tuning_task="hpobench:nasbench101:A")
        self.assertEqual(plan[0][0], "evaluate_config")
        parsed = json.loads(plan[0][1])
        self.assertEqual(parsed, {"edge": 1, "rate": 0.25, "enabled": True, "operation": "conv1x1-bn-relu"})
        self.assertIs(type(parsed["edge"]), int)
        self.assertIs(type(parsed["rate"]), float)
        self.assertIs(type(parsed["enabled"]), bool)

    def test_hpobench_evaluate_returns_numeric_perf(self) -> None:
        class _DummyBenchmark:
            def objective_function(self, configuration, fidelity):
                del configuration, fidelity
                return {"function_value": 1.0, "cost": 0.0}

        class _DummyTask:
            benchmark = _DummyBenchmark()
            fidelity = {}

        perf, cost = _hpobench_evaluate(_DummyTask(), {})
        self.assertIsInstance(perf, float)
        self.assertEqual(perf, 0.0)
        self.assertEqual(cost, 0.0)

    def test_list_includes_nasbench101(self) -> None:
        tasks = list_hpobench_tasks()
        self.assertEqual(len(tasks), 9)
        for variant in ["A", "B", "C"]:
            self.assertIn(f"hpobench:nasbench101:{variant}", tasks)

    def test_nasbench101_hints_describe_distinct_encodings(self) -> None:
        hints = {v: _task_hints("hpobench:nasbench101:" + v) for v in "ABC"}
        for variant, hint in hints.items():
            self.assertNotIn("NASBench", hint)
            self.assertIn("neural architecture search task", hint)
            self.assertIn("7-node directed acyclic graph", hint)
            self.assertIn("AT MOST 9", hint)
            self.assertIn("will always score 0", hint)
            self.assertIn("ALL parameters", hint)
        self.assertIn("0=absent, 1=present", hints["A"])
        self.assertIn("edge-ID selectors", hints["B"])
        self.assertIn("ID 0 is a real edge (5->6)", hints["B"])
        self.assertIn("Repeated IDs select that edge only once", hints["B"])
        self.assertNotIn("set unused edges to 0", hints["B"].lower())
        self.assertIn("priorities in [0,1]", hints["C"])
        self.assertIn("num_edges", hints["C"])
        self.assertIn("top-k", hints["C"])
        self.assertIn("distinct priorities", hints["C"])

    def test_every_documented_nas101_edge_matches_decoder(self) -> None:
        from expgym.compact_nasbench101 import _matrix_for_variant

        for variant in "ABC":
            hint = _task_hints("hpobench:nasbench101:" + variant)
            pairs = _nasbench101_edge_pairs(variant)
            self.assertEqual(len(pairs), 21)
            self.assertEqual(len(set(pairs)), 21)
            for index, pair in enumerate(pairs):
                with self.subTest(variant=variant, edge=index):
                    if variant == "B":
                        config = {"edge_{}".format(i): index for i in range(9)}
                        fragment = "{}={}->{}".format(index, *pair)
                    else:
                        config = {"edge_{}".format(i): 0 for i in range(21)}
                        config["edge_{}".format(index)] = 1
                        if variant == "C":
                            config["num_edges"] = 1
                        fragment = "edge_{}={}->{}".format(index, *pair)
                    matrix = _matrix_for_variant(config, variant)
                    selected = [(r, c) for r in range(7) for c in range(7) if matrix[r][c]]
                    self.assertEqual(selected, [pair])
                    self.assertIn(fragment, hint)
        self.assertEqual(_nasbench101_edge_pairs("A")[0], (0, 1))
        self.assertEqual(_nasbench101_edge_pairs("B")[0], (5, 6))
        self.assertEqual(_nasbench101_edge_pairs("B")[20], (0, 1))

    def test_nas101_c_hint_top_k_and_zero_edges_match_decoder(self) -> None:
        from expgym.compact_nasbench101 import _matrix_for_variant

        config = {"edge_{}".format(i): i / 20.0 for i in range(21)}
        config["num_edges"] = 3
        matrix = _matrix_for_variant(config, "C")
        selected = {(r, c) for r in range(7) for c in range(7) if matrix[r][c]}
        self.assertEqual(selected, set(_nasbench101_edge_pairs("C")[-3:]))
        config["num_edges"] = 0
        self.assertEqual(sum(map(sum, _matrix_for_variant(config, "C"))), 0)

    def test_hpobench_zero_perf_returns_numeric_score_with_message(self) -> None:
        class _Hyperparameter:
            name = "x"
            lower = 0
            upper = 1

        class _ConfigSpace:
            def get_hyperparameters(self):
                return [_Hyperparameter()]

        class _Benchmark:
            def objective_function(self, configuration, fidelity):
                del configuration, fidelity
                return {"function_value": 1.0, "cost": 12.5}

        class _Task:
            benchmark = _Benchmark()
            config_space = _ConfigSpace()
            fidelity = {}

        output, perf, overhead = evaluate_hpobench_action(_Task(), json.dumps({"x": 0}))
        self.assertIn("invalid or degenerate", output)
        self.assertEqual(perf, 0.0)
        self.assertEqual(overhead, 12.5)

    def test_hpobench_fidelity_config_svm(self) -> None:
        fidelity, tips = _get_hpobench_fidelity_settings("hpobench:svm_surrogate")
        self.assertIn("dataset_fraction", fidelity)
        self.assertEqual(fidelity["dataset_fraction"], 1.0)
        self.assertTrue(any("dataset_fraction" in tip for tip in tips))

    def test_hpobench_fidelity_config_paramnet(self) -> None:
        fidelity, tips = _get_hpobench_fidelity_settings("hpobench:paramnet:adult:steps")
        self.assertEqual(fidelity.get("step"), 50)
        self.assertTrue(any("step" in tip for tip in tips))

    @unittest.skipUnless(
        os.environ.get("EXPGYM_ENABLE_HPOBENCH_TESTS") == "1" and _has_hpobench_deps(),
        "HPOBench ConfigSpace dependency not installed or tests disabled.",
    )
    def test_nasbench101_config_space_has_ops(self) -> None:
        cs = _load_hpobench("hpobench:nasbench101:A").config_space
        names = {hp.name for hp in cs.get_hyperparameters()}
        self.assertIn("op_node_0", names)
        self.assertTrue(any(name.startswith("edge_") for name in names))

    @unittest.skipUnless(
        os.environ.get("EXPGYM_ENABLE_HPOBENCH_TESTS") == "1" and _has_hpobench_deps(),
        "HPOBench deps not installed or tests disabled.",
    )
    def test_fake_plan_matches_hpobench_space(self) -> None:
        import ConfigSpace as CS

        for task_name in [
            "hpobench:nasbench101:A",
            "hpobench:nasbench101:B",
            "hpobench:nasbench101:C",
            "hpobench:nasbench201:cifar10-valid",
        ]:
            with self.subTest(task=task_name):
                plan = build_fake_plan(2, tuning_task=task_name, seed=1206)
                self.assertEqual(len(plan), 2)
                task = _load_hpobench(task_name)
                for _, payload in plan:
                    values = json.loads(payload)
                    config = CS.Configuration(task.config_space, values=values)
                    self.assertIsNotNone(config)

    @unittest.skipUnless(
        os.environ.get("EXPGYM_ENABLE_HPOBENCH_TESTS") == "1" and _has_hpobench_deps(),
        "HPOBench deps not installed or tests disabled.",
    )
    def test_hpobench_out_of_range_is_a_typed_input_error(self) -> None:
        task = _load_hpobench("hpobench:nasbench201:cifar10-valid")
        config = {
            hp.name: hp.default_value
            for hp in task.config_space.get_hyperparameters()
        }
        config["1<-0"] = "not-an-operation"
        with self.assertRaisesRegex(InvalidConfigurationError, "out of range"):
            evaluate_hpobench_action(task, json.dumps(config))
