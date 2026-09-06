import os
import unittest
import json

from expgym.task_tuning import (
    build_fake_plan,
    list_hpobench_tasks,
    _load_hpobench,
    _get_hpobench_fidelity_settings,
    _hpobench_evaluate,
    _task_hints,
    evaluate_hpobench_action,
)


def _has_hpobench_deps() -> bool:
    try:
        import ConfigSpace  # noqa: F401
    except Exception:
        return False
    return True


class TestHPOBenchTasks(unittest.TestCase):
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

    def test_nasbench101_hint_matches_paper_constraint(self) -> None:
        hint = _task_hints("hpobench:nasbench101:B")
        self.assertIsNotNone(hint)
        self.assertIn("7-node directed acyclic graph", hint)
        self.assertIn("upper-triangular adjacency matrix", hint)
        self.assertIn("AT MOST 9", hint)
        self.assertIn("will always score 0", hint)
        self.assertNotIn("NASBench101-B", hint)
        self.assertNotIn("selector", hint)

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
        task_name = "hpobench:nasbench201:cifar10-valid"
        plan = build_fake_plan(2, tuning_task=task_name)
        self.assertEqual(len(plan), 2)
        task = _load_hpobench(task_name)
        import ConfigSpace as CS
        for _, payload in plan:
            values = json.loads(payload)
            config = CS.Configuration(task.config_space, values=values)
            self.assertIsNotNone(config)

    @unittest.skipUnless(
        os.environ.get("EXPGYM_ENABLE_HPOBENCH_TESTS") == "1" and _has_hpobench_deps(),
        "HPOBench deps not installed or tests disabled.",
    )
    def test_hpobench_out_of_range_returns_message(self) -> None:
        task = _load_hpobench("hpobench:nasbench201:cifar10-valid")
        config = {
            hp.name: hp.default_value
            for hp in task.config_space.get_hyperparameters()
        }
        config["1<-0"] = "not-an-operation"
        output, overhead = evaluate_hpobench_action(
            task,
            json.dumps(config),
        )
        self.assertIsInstance(output, str)
        self.assertIn("out of range", output)
        self.assertEqual(overhead, 0.0)
