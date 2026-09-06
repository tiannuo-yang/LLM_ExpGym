import pickle
import tempfile
import unittest
from itertools import product
from pathlib import Path

from expgym.compact_nasbench201 import (
    DATASET_FILES,
    EDGES,
    SCHEMA,
    CompactNasBench201Benchmark,
    configuration_id,
)


class CompactNasBench201Test(unittest.TestCase):
    def test_configuration_id_uses_canonical_edge_order(self) -> None:
        config = {
            "1<-0": "none",
            "2<-0": "skip_connect",
            "2<-1": "nor_conv_1x1",
            "3<-0": "nor_conv_3x3",
            "3<-1": "avg_pool_3x3",
            "3<-2": "none",
        }
        self.assertEqual(configuration_id(config), "012340")

    def test_max_fidelity_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            table = {
                "".join(digits): (12.5, 34.0)
                for digits in product("01234", repeat=6)
            }
            payload = {
                "schema": SCHEMA,
                "dataset": "cifar10-valid",
                "architectures": table,
            }
            with (data_dir / DATASET_FILES["cifar10-valid"]).open("wb") as handle:
                pickle.dump(payload, handle, protocol=4)

            benchmark = CompactNasBench201Benchmark(
                dataset="cifar10-valid",
                data_dir=data_dir,
            )
            config = {edge: "none" for edge in EDGES}
            result = benchmark.objective_function(config, fidelity={"epoch": 200})

            self.assertEqual(result["function_value"], 12.5)
            self.assertEqual(result["cost"], 34.0)
            self.assertEqual(result["info"]["configuration_id"], "000000")
            with self.assertRaisesRegex(ValueError, "only epoch=200"):
                benchmark.objective_function(config, fidelity={"epoch": 199})

    def test_rejects_unknown_operation(self) -> None:
        config = {edge: "none" for edge in EDGES}
        config["1<-0"] = "bad_operation"
        with self.assertRaisesRegex(ValueError, "invalid NASBench201 operation"):
            configuration_id(config)


if __name__ == "__main__":
    unittest.main()
