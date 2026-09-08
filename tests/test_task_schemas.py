"""Native schemas describe, but do not change, existing flat tool payloads."""
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from expgym import task_restricted_search as search
from expgym import task_tuning as tuning
from expgym.errors import ToolInputError

try:
    import ConfigSpace as CS
except ImportError:
    CS = None


class ToolSchemaTest(unittest.TestCase):
    def assert_definition(self, function, name):
        definition = function.__expgym_tool_schema__
        self.assertEqual(definition["name"], name)
        self.assertTrue(definition["description"])
        self.assertEqual(json.loads(json.dumps(definition, allow_nan=False)), definition)
        schema = definition["parameters"]
        self.assertEqual(schema["type"], "object")
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["required"]), set(schema["properties"]))
        self.assertNotIn("config", schema["properties"])
        return schema

    def test_synthetic_schema_has_all_ten_integer_ranges_and_flat_dispatch(self):
        function = tuning.build_tools()["evaluate_config"]
        schema = self.assert_definition(function, "evaluate_config")
        self.assertEqual(len(schema["properties"]), 10)
        for bounds in tuning.PARAMETER_RANGES:
            self.assertEqual(schema["properties"][bounds.name],
                             {"type": "integer", "minimum": bounds.low, "maximum": bounds.high})
        payload = tuning.format_config(tuning.REFERENCE_CONFIGS[0])
        self.assertEqual(function(payload), tuning.evaluate_config_action(payload))
        with patch.object(tuning, "evaluate_config_action", return_value=(0.3, 7.0)) as evaluate:
            self.assertEqual(function(payload), (0.3, 7.0))
            evaluate.assert_called_once_with(payload)

    def test_search_schema_and_per_instance_cache_preserve_flat_dispatch(self):
        with patch.object(search, "_load_corpus", return_value={"Alice Example": "Alice's article"}):
            first = search.build_tools(data_source="phantom_seed1")["search"]
            second = search.build_tools(data_source="phantom_seed2")["search"]
        schema = self.assert_definition(first, "search")
        self.assertEqual(schema["required"], ["query"])
        self.assertEqual(schema["properties"]["query"]["type"], "string")
        payload = '{"query":"Alice Example"}'
        observed, cost = first(payload)
        self.assertIn("Alice's article", observed)
        self.assertGreater(cost, 0)
        self.assertEqual(first(payload), (observed, 0.0))
        self.assertEqual(second(payload), (observed, cost))
        schema["properties"]["query"]["description"] = "changed only on first instance"
        self.assertNotEqual(schema, second.__expgym_tool_schema__["parameters"])

    def test_search_payload_errors_are_typed_but_corpus_failures_are_not(self):
        for payload in (None, "bad JSON", "[]", "null"):
            with self.subTest(payload=payload), self.assertRaises(ToolInputError):
                search._parse_payload(payload)
        failure = FileNotFoundError("Missing corpus")
        with patch.object(search, "_load_corpus", side_effect=failure):
            with self.assertRaises(FileNotFoundError) as caught:
                search.build_tools()
        self.assertIs(caught.exception, failure)

    @unittest.skipUnless(CS is not None, "ConfigSpace unavailable")
    def test_mixed_configspace_schema_preserves_real_types_and_ranges(self):
        cs = CS.ConfigurationSpace(seed=1)
        cs.add_hyperparameters([
            CS.UniformIntegerHyperparameter("layers", lower=1, upper=5),
            CS.UniformFloatHyperparameter("rate", lower=0.001, upper=0.1, log=True),
            CS.CategoricalHyperparameter("edge", choices=[0, 1, 2]),
            CS.CategoricalHyperparameter("operation", choices=["skip", "conv"]),
            CS.OrdinalHyperparameter("ordered", sequence=[1, 2, 4]),
            CS.Constant("fixed", value="x"),
        ])
        properties = tuning._config_space_schema(cs)["properties"]
        self.assertEqual(properties["layers"], {"type": "integer", "minimum": 1, "maximum": 5})
        self.assertEqual(properties["rate"]["type"], "number")
        self.assertEqual(properties["rate"]["minimum"], 0.001)
        self.assertEqual(properties["rate"]["maximum"], 0.1)
        self.assertIn("Log-scaled", properties["rate"]["description"])
        self.assertEqual(properties["edge"], {"type": "integer", "enum": [0, 1, 2]})
        self.assertEqual(properties["operation"], {"type": "string", "enum": ["skip", "conv"]})
        self.assertEqual(properties["ordered"], {"type": "integer", "enum": [1, 2, 4]})
        self.assertEqual(properties["fixed"], {"type": "string", "enum": ["x"]})
        json.dumps(properties, allow_nan=False)
        valid = {"layers": 2, "rate": 0.01, "edge": 1, "operation": "conv", "ordered": 2, "fixed": "x"}
        self.assertIsNone(tuning._validate_hpobench_config(cs, dict(valid)))
        for field, value in (("ordered", 3), ("fixed", "y")):
            self.assertIn("out of range", tuning._validate_hpobench_config(cs, dict(valid, **{field: value})))

    @unittest.skipUnless(CS is not None, "ConfigSpace unavailable")
    def test_conditional_and_forbidden_spaces_fail_explicitly(self):
        conditional = CS.ConfigurationSpace()
        mode = CS.CategoricalHyperparameter("mode", ["off", "on"])
        layers = CS.UniformIntegerHyperparameter("layers", 1, 5)
        conditional.add_hyperparameters([mode, layers])
        conditional.add_condition(CS.EqualsCondition(layers, mode, "on"))
        forbidden = CS.ConfigurationSpace()
        choice = CS.CategoricalHyperparameter("choice", [0, 1])
        forbidden.add_hyperparameter(choice)
        forbidden.add_forbidden_clause(CS.ForbiddenEqualsClause(choice, 1))
        for cs, label in ((conditional, "conditional"), (forbidden, "forbidden-clause")):
            for operation in (tuning._config_space_schema,
                              lambda space: tuning._validate_hpobench_config(space, {})):
                with self.subTest(label=label), self.assertRaisesRegex(ValueError, "Unsupported " + label) as caught:
                    operation(cs)
                self.assertNotIsInstance(caught.exception, ToolInputError)

    def test_unsupported_quantized_bool_null_and_nonfinite_definitions_fail(self):
        for hp in (SimpleNamespace(name="x", lower=0, upper=1, q=0.1),
                   SimpleNamespace(name="x", choices=[False, True]),
                   SimpleNamespace(name="x", choices=[None, "x"]),
                   SimpleNamespace(name="x", choices=[float("nan")]),
                   SimpleNamespace(name="x", choices=[float("inf")]),
                   SimpleNamespace(name="x", lower=float("nan"), upper=1),
                   SimpleNamespace(name="x", lower=False, upper=1),
                   SimpleNamespace(name="x", lower=2, upper=1)):
            cs = SimpleNamespace(get_hyperparameters=lambda hp=hp: [hp])
            with self.subTest(hp=hp), self.assertRaises((ValueError, TypeError)) as caught:
                tuning._config_space_schema(cs)
            self.assertNotIsInstance(caught.exception, ToolInputError)

    @unittest.skipUnless(CS is not None, "ConfigSpace unavailable")
    def test_nas_schema_matches_all_six_actual_spaces_without_loading_tables(self):
        from expgym.compact_nasbench101 import CompactNasBench101Benchmark
        from expgym.compact_nasbench201 import CompactNasBench201Benchmark

        for name in tuning.list_hpobench_tasks()[3:]:
            with self.subTest(task=name):
                if ":nasbench101:" in name:
                    benchmark = CompactNasBench101Benchmark.__new__(CompactNasBench101Benchmark)
                    benchmark.variant = name.rsplit(":", 1)[-1]
                    cs = benchmark.get_configuration_space(seed=1)
                    fidelity = {"budget": 108}
                else:
                    cs = CompactNasBench201Benchmark.get_configuration_space(seed=1)
                    fidelity = {"epoch": 200}
                task = SimpleNamespace(config_space=cs, fidelity=fidelity)
                with patch.object(tuning, "_load_hpobench", return_value=task):
                    function = tuning.build_tools(tuning_task=name)["evaluate_config"]
                schema = self.assert_definition(function, "evaluate_config")
                self.assertEqual(set(schema["properties"]), {hp.name for hp in cs.get_hyperparameters()})
                self.assertFalse(set(fidelity) & set(schema["properties"]))
                values = {hp.name: tuning._schema_scalar(hp.default_value) for hp in cs.get_hyperparameters()}
                self.assertIsNone(tuning._validate_hpobench_config(cs, dict(values)))
                for hp in cs.get_hyperparameters():
                    prop = schema["properties"][hp.name]
                    if hasattr(hp, "choices"):
                        self.assertEqual(prop["enum"], [tuning._schema_scalar(v) for v in hp.choices])
                    else:
                        self.assertEqual((prop["minimum"], prop["maximum"]), (hp.lower, hp.upper))
                payload = json.dumps(values)
                with patch.object(tuning, "evaluate_hpobench_action", return_value=(0.8, 12.0)) as evaluate:
                    self.assertEqual(function(payload), (0.8, 12.0))
                    evaluate.assert_called_once_with(task, payload)

    @unittest.skipUnless(CS is not None, "ConfigSpace unavailable")
    def test_nas_b_selectors_and_c_priorities_do_not_inherit_binary_schema(self):
        from expgym.compact_nasbench101 import CompactNasBench101Benchmark

        for variant in "ABC":
            benchmark = CompactNasBench101Benchmark.__new__(CompactNasBench101Benchmark)
            benchmark.variant = variant
            schema = tuning._config_space_schema(benchmark.get_configuration_space())
            prop = schema["properties"]["edge_0"]
            if variant == "A":
                self.assertEqual(prop, {"type": "integer", "enum": [0, 1]})
                self.assertEqual(len(schema["required"]), 26)
            elif variant == "B":
                self.assertEqual(prop, {"type": "integer", "enum": list(range(21))})
                self.assertEqual(len(schema["required"]), 14)
                self.assertNotIn("edge_9", schema["properties"])
            else:
                self.assertEqual(prop, {"type": "number", "minimum": 0.0, "maximum": 1.0})
                self.assertEqual(schema["properties"]["num_edges"], {"type": "integer", "minimum": 0, "maximum": 9})
                self.assertEqual(len(schema["required"]), 27)

    @unittest.skipUnless(os.environ.get("EXPGYM_ENABLE_PARAMNET_SCHEMA_TESTS") == "1", "Requires isolated legacy ParamNet environment")
    def test_three_real_paramnet_schemas(self):
        for name in tuning.list_hpobench_tasks()[:3]:
            with self.subTest(task=name):
                function = tuning.build_tools(tuning_task=name)["evaluate_config"]
                schema = self.assert_definition(function, "evaluate_config")
                self.assertEqual(len(schema["required"]), 8)
                self.assertEqual(schema["properties"]["num_layers"], {"type": "integer", "minimum": 1, "maximum": 5})
                self.assertEqual(schema["properties"]["initial_lr_log10"], {"type": "number", "minimum": -6.0, "maximum": -2.0})


if __name__ == "__main__":
    unittest.main()
