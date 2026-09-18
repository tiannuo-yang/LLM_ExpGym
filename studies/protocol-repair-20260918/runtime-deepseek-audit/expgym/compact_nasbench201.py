"""Low-memory, max-fidelity NASBench201 adapter for the paper sweep."""
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, Optional


SCHEMA = "expgym.nasbench201-maxfidelity.v2"
OPERATIONS = (
    "none",
    "skip_connect",
    "nor_conv_1x1",
    "nor_conv_3x3",
    "avg_pool_3x3",
)
EDGES = ("1<-0", "2<-0", "2<-1", "3<-0", "3<-1", "3<-2")
DATASET_FILES = {
    "cifar10-valid": "cifar10-valid.pkl",
    "cifar100": "cifar100.pkl",
    "imagenet16-120": "imagenet16-120.pkl",
}


def default_data_dir() -> Path:
    repo_data = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "hpo_tuning"
        / "hpobench_data"
    )
    return Path(os.environ.get("XDG_DATA_HOME", str(repo_data))) / "nasbench_201_compact"


def configuration_id(configuration: Any) -> str:
    """Map HPOBench's six named edges to the canonical base-5 ID."""
    indices = []
    for edge in EDGES:
        operation = str(configuration[edge])
        try:
            indices.append(str(OPERATIONS.index(operation)))
        except ValueError as exc:
            raise ValueError(f"invalid NASBench201 operation for {edge}: {operation}") from exc
    return "".join(indices)


class CompactNasBench201Benchmark:
    """HPOBench-compatible access to the paper's fixed epoch-200 slice.

    The original HPOBench downloader loads multi-gigabyte per-epoch JSON into
    memory even though this repository fixes fidelity to epoch 200. The setup
    script derives this small table from the official NATS-Bench simple archive.
    """

    def __init__(
        self,
        dataset: str,
        rng: Optional[int] = None,
        data_dir: Optional[Path] = None,
    ) -> None:
        del rng
        if dataset not in DATASET_FILES:
            raise ValueError(f"unknown NASBench201 dataset: {dataset}")
        path = (data_dir or default_data_dir()) / DATASET_FILES[dataset]
        try:
            with path.open("rb") as handle:
                payload = pickle.load(handle)
        except OSError as exc:
            raise FileNotFoundError(
                f"compact NASBench201 data is missing at {path}; "
                "run `python scripts/download_data.py --only hpobench`"
            ) from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SCHEMA
            or payload.get("dataset") != dataset
            or not isinstance(payload.get("architectures"), dict)
            or len(payload["architectures"]) != 5 ** len(EDGES)
        ):
            raise ValueError(f"invalid compact NASBench201 data: {path}")
        self.dataset = dataset
        self.path = path
        self.data: Dict[str, Any] = payload["architectures"]

    @staticmethod
    def get_configuration_space(seed: Optional[int] = None) -> Any:
        import ConfigSpace as CS

        cs = CS.ConfigurationSpace(seed=seed)
        cs.add_hyperparameters(
            [CS.CategoricalHyperparameter(edge, OPERATIONS) for edge in EDGES]
        )
        return cs

    @staticmethod
    def get_fidelity_space(seed: Optional[int] = None) -> Any:
        import ConfigSpace as CS

        cs = CS.ConfigurationSpace(seed=seed)
        cs.add_hyperparameter(
            CS.UniformIntegerHyperparameter(
                "epoch", lower=1, upper=200, default_value=200
            )
        )
        return cs

    def objective_function(
        self,
        configuration: Any,
        fidelity: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del kwargs
        epoch = int((fidelity or {"epoch": 200}).get("epoch", 200))
        if epoch != 200:
            raise ValueError("compact NASBench201 data supports only epoch=200")
        config_id = configuration_id(configuration)
        objective, cost = self.data[config_id]
        return {
            "function_value": float(objective),
            "cost": float(cost),
            "info": {"fidelity": {"epoch": 200}, "configuration_id": config_id},
        }

    def objective_function_test(
        self,
        configuration: Any,
        fidelity: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.objective_function(configuration, fidelity=fidelity, **kwargs)
