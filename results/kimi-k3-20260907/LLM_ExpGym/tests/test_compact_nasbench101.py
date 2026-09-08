import pickle
import tempfile
import unittest
from pathlib import Path

from expgym.compact_nasbench101 import (
    SCHEMA,
    CompactNasBench101Benchmark,
    configuration_hash,
)


OFFICIAL_ROW_CONFIG_A = {
    "edge_0": 1,
    "edge_1": 0,
    "edge_2": 0,
    "edge_3": 1,
    "edge_4": 1,
    "edge_5": 0,
    "edge_6": 1,
    "edge_7": 0,
    "edge_8": 0,
    "edge_9": 0,
    "edge_10": 0,
    "edge_11": 1,
    "edge_12": 0,
    "edge_13": 0,
    "edge_14": 1,
    "edge_15": 0,
    "edge_16": 1,
    "edge_17": 0,
    "edge_18": 1,
    "edge_19": 0,
    "edge_20": 1,
    "op_node_0": "conv3x3-bn-relu",
    "op_node_1": "maxpool3x3",
    "op_node_2": "conv3x3-bn-relu",
    "op_node_3": "conv3x3-bn-relu",
    "op_node_4": "conv1x1-bn-relu",
}
OFFICIAL_ROW_HASH = "00005c142e6f48ac74fdcf73e3439874"


class CompactNasBench101Test(unittest.TestCase):
    def test_hash_matches_official_tfrecord_row(self) -> None:
        self.assertEqual(configuration_hash(OFFICIAL_ROW_CONFIG_A, "A"), OFFICIAL_ROW_HASH)

    def test_lookup_and_test_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "compact.pkl"
            payload = {
                "schema": SCHEMA,
                "architectures_count": 1,
                "architectures": {OFFICIAL_ROW_HASH: (0.1, 0.2, 30.0)},
            }
            with path.open("wb") as handle:
                pickle.dump(payload, handle, protocol=4)

            benchmark = CompactNasBench101Benchmark("A", data_path=path)
            validation = benchmark.objective_function(
                OFFICIAL_ROW_CONFIG_A,
                fidelity={"budget": 108},
            )
            test = benchmark.objective_function_test(
                OFFICIAL_ROW_CONFIG_A,
                fidelity={"budget": 108},
            )

            self.assertEqual(validation["function_value"], 0.1)
            self.assertEqual(validation["cost"], 30.0)
            self.assertEqual(test["function_value"], 0.2)
            with self.assertRaisesRegex(ValueError, "only budget=108"):
                benchmark.objective_function(
                    OFFICIAL_ROW_CONFIG_A,
                    fidelity={"budget": 36},
                )

    def test_disconnected_graph_is_invalid(self) -> None:
        config = dict(OFFICIAL_ROW_CONFIG_A)
        for index in range(21):
            config[f"edge_{index}"] = 0
        self.assertIsNone(configuration_hash(config, "A"))


if __name__ == "__main__":
    unittest.main()
