"""TensorFlow-free, max-fidelity NASBench101 adapter for the paper sweep."""
from __future__ import annotations

import hashlib
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


SCHEMA = "expgym.nasbench101-maxfidelity.v1"
OPERATIONS = (
    "conv1x1-bn-relu",
    "conv3x3-bn-relu",
    "maxpool3x3",
)
CANONICAL_OPERATIONS = (
    "conv3x3-bn-relu",
    "conv1x1-bn-relu",
    "maxpool3x3",
)
VERTICES = 7
MAX_EDGES = 9
EDGE_COUNT = VERTICES * (VERTICES - 1) // 2


def default_data_path() -> Path:
    repo_data = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "hpo_tuning"
        / "hpobench_data"
    )
    return (
        Path(os.environ.get("XDG_DATA_HOME", str(repo_data)))
        / "nasbench_101_compact.pkl"
    )


def _empty_matrix() -> List[List[int]]:
    return [[0 for _ in range(VERTICES)] for _ in range(VERTICES)]


def _matrix_for_variant(configuration: Any, variant: str) -> List[List[int]]:
    matrix = _empty_matrix()
    if variant == "A":
        index = 0
        for row in range(VERTICES):
            for column in range(row + 1, VERTICES):
                matrix[row][column] = int(configuration[f"edge_{index}"])
                index += 1
        return matrix

    if variant == "B":
        bitlist = [0] * EDGE_COUNT
        for index in range(MAX_EDGES):
            bitlist[int(configuration[f"edge_{index}"])] = 1
        encoded = 0
        for bit in bitlist:
            encoded = (encoded << 1) | bit
        for column in range(VERTICES):
            for row in range(column):
                bit_index = row + column * (column - 1) // 2
                matrix[row][column] = (encoded >> bit_index) % 2
        return matrix

    if variant == "C":
        probabilities = np.asarray(
            [float(configuration[f"edge_{index}"]) for index in range(EDGE_COUNT)]
        )
        selected = np.argsort(probabilities, kind="quicksort")[::-1][
            : int(configuration["num_edges"])
        ]
        selected_set = {int(index) for index in selected}
        index = 0
        for row in range(VERTICES):
            for column in range(row + 1, VERTICES):
                matrix[row][column] = int(index in selected_set)
                index += 1
        return matrix

    raise ValueError(f"NASBench101 variant must be A, B, or C, got {variant!r}")


def _prune(
    matrix: Sequence[Sequence[int]],
    operations: Sequence[str],
) -> Optional[Tuple[List[List[int]], List[str]]]:
    from_input = {0}
    frontier = [0]
    while frontier:
        source = frontier.pop()
        for target in range(source + 1, VERTICES):
            if matrix[source][target] and target not in from_input:
                from_input.add(target)
                frontier.append(target)

    from_output = {VERTICES - 1}
    frontier = [VERTICES - 1]
    while frontier:
        target = frontier.pop()
        for source in range(target):
            if matrix[source][target] and source not in from_output:
                from_output.add(source)
                frontier.append(source)

    keep = sorted(from_input.intersection(from_output))
    if len(keep) < 2:
        return None
    pruned_matrix = [[int(matrix[row][column]) for column in keep] for row in keep]
    pruned_operations = [str(operations[index]) for index in keep]
    return pruned_matrix, pruned_operations


def _hash_module(matrix: Sequence[Sequence[int]], labels: Sequence[int]) -> str:
    vertices = len(matrix)
    in_edges = [sum(matrix[row][column] for row in range(vertices)) for column in range(vertices)]
    out_edges = [sum(matrix[row]) for row in range(vertices)]
    hashes = [
        hashlib.md5(str(item).encode("utf-8")).hexdigest()
        for item in zip(out_edges, in_edges, labels)
    ]
    for _ in range(vertices):
        updated = []
        for vertex in range(vertices):
            incoming = [hashes[row] for row in range(vertices) if matrix[row][vertex]]
            outgoing = [hashes[column] for column in range(vertices) if matrix[vertex][column]]
            value = "".join(sorted(incoming)) + "|" + "".join(sorted(outgoing)) + "|" + hashes[vertex]
            updated.append(hashlib.md5(value.encode("utf-8")).hexdigest())
        hashes = updated
    return hashlib.md5(str(sorted(hashes)).encode("utf-8")).hexdigest()


def configuration_hash(configuration: Any, variant: str) -> Optional[str]:
    """Return NASBench's isomorphism-invariant hash, or None when invalid."""
    normalized_variant = variant.upper()
    matrix = _matrix_for_variant(configuration, normalized_variant)
    if sum(sum(row) for row in matrix) > MAX_EDGES:
        return None
    operations = ["input"] + [
        str(configuration[f"op_node_{index}"]) for index in range(5)
    ] + ["output"]
    pruned = _prune(matrix, operations)
    if pruned is None:
        return None
    pruned_matrix, pruned_operations = pruned
    labels = [-1] + [
        CANONICAL_OPERATIONS.index(operation)
        for operation in pruned_operations[1:-1]
    ] + [-2]
    return _hash_module(pruned_matrix, labels)


class CompactNasBench101Benchmark:
    """HPOBench-compatible access to the fixed 108-epoch NASBench101 slice."""

    def __init__(
        self,
        variant: str,
        rng: Optional[int] = None,
        data_path: Optional[Path] = None,
    ) -> None:
        del rng
        self.variant = variant.upper()
        if self.variant not in {"A", "B", "C"}:
            raise ValueError("NASBench101 variant must be A, B, or C")
        self.path = data_path or default_data_path()
        try:
            with self.path.open("rb") as handle:
                payload = pickle.load(handle)
        except OSError as exc:
            raise FileNotFoundError(
                f"compact NASBench101 data is missing at {self.path}; "
                "run `python scripts/download_data.py --only hpobench`"
            ) from exc
        architectures = payload.get("architectures") if isinstance(payload, dict) else None
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SCHEMA
            or not isinstance(architectures, dict)
            or payload.get("architectures_count") != len(architectures)
        ):
            raise ValueError(f"invalid compact NASBench101 data: {self.path}")
        self.data: Dict[str, Tuple[float, float, float]] = architectures

    def get_configuration_space(self, seed: Optional[int] = None) -> Any:
        import ConfigSpace as CS

        cs = CS.ConfigurationSpace(seed=seed)
        cs.add_hyperparameters(
            [CS.CategoricalHyperparameter(f"op_node_{index}", OPERATIONS) for index in range(5)]
        )
        if self.variant == "A":
            cs.add_hyperparameters(
                [CS.CategoricalHyperparameter(f"edge_{index}", (0, 1)) for index in range(EDGE_COUNT)]
            )
        elif self.variant == "B":
            choices = tuple(range(EDGE_COUNT))
            cs.add_hyperparameters(
                [CS.CategoricalHyperparameter(f"edge_{index}", choices) for index in range(MAX_EDGES)]
            )
        else:
            cs.add_hyperparameter(
                CS.UniformIntegerHyperparameter("num_edges", lower=0, upper=MAX_EDGES)
            )
            cs.add_hyperparameters(
                [
                    CS.UniformFloatHyperparameter(f"edge_{index}", lower=0.0, upper=1.0)
                    for index in range(EDGE_COUNT)
                ]
            )
        return cs

    @staticmethod
    def get_fidelity_space(seed: Optional[int] = None) -> Any:
        import ConfigSpace as CS

        cs = CS.ConfigurationSpace(seed=seed)
        cs.add_hyperparameter(
            CS.OrdinalHyperparameter("budget", sequence=(4, 12, 36, 108), default_value=108)
        )
        return cs

    def objective_function(
        self,
        configuration: Any,
        fidelity: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        del kwargs
        budget = int((fidelity or {"budget": 108}).get("budget", 108))
        if budget != 108:
            raise ValueError("compact NASBench101 data supports only budget=108")
        module_hash = configuration_hash(configuration, self.variant)
        row = self.data.get(module_hash) if module_hash is not None else None
        if row is None:
            return {
                "function_value": 1.0,
                "cost": 0.0,
                "info": {"fidelity": {"budget": 108}, "module_hash": module_hash},
            }
        validation_error, _test_error, cost = row
        return {
            "function_value": float(validation_error),
            "cost": float(cost),
            "info": {"fidelity": {"budget": 108}, "module_hash": module_hash},
        }

    def objective_function_test(
        self,
        configuration: Any,
        fidelity: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        result = self.objective_function(configuration, fidelity=fidelity, **kwargs)
        module_hash = result["info"]["module_hash"]
        row = self.data.get(module_hash) if module_hash is not None else None
        if row is not None:
            result["function_value"] = float(row[1])
        return result
