"""Configuration tuning environment with 10 integer parameters."""
from __future__ import annotations

import hashlib
import json
import math
from numbers import Integral, Real
import random
import os
import threading
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any

from expgym.react_loop import build_system_prompt as build_react_system_prompt
from expgym.errors import InvalidConfigurationError

warnings.filterwarnings(
    "ignore",
    message=r"The sklearn\.ensemble\.forest module is  deprecated.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"The sklearn\.tree\.tree module is  deprecated.*",
    category=FutureWarning,
)


@dataclass(frozen=True)
class ParameterRange:
    name: str
    low: int
    high: int


PARAMETER_RANGES: List[ParameterRange] = [
    ParameterRange("num_layers", 2, 12),
    ParameterRange("hidden_width", 64, 768),
    ParameterRange("attention_heads", 2, 16),
    ParameterRange("ffn_expansion", 1, 8),
    ParameterRange("dropout_x100", 0, 40),
    ParameterRange("learning_rate_x1e5", 3, 80),
    ParameterRange("weight_decay_x1e4", 0, 20),
    ParameterRange("warmup_steps", 0, 4000),
    ParameterRange("batch_size", 8, 512),
    ParameterRange("gradient_accumulation", 1, 16),
]

# --- HPOBench paper-task support. ---

HPOBENCH_ROOT = os.environ.get(
    "HPOBENCH_ROOT",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "hpo_tuning", "HPOBench"
    ),
)
HPOBENCH_CONFIG_PATH = Path(
    os.path.dirname(os.path.dirname(__file__)), "configs", "hpobench_tasks.yaml"
)
_HPOBENCH_CONFIG_CACHE: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class HPOBenchTask:
    name: str
    benchmark: Any
    config_space: Any
    fidelity: Dict[str, float]


def _load_hpobench_config() -> Dict[str, Any]:
    global _HPOBENCH_CONFIG_CACHE
    if _HPOBENCH_CONFIG_CACHE is not None:
        return _HPOBENCH_CONFIG_CACHE
    if not HPOBENCH_CONFIG_PATH.exists():
        _HPOBENCH_CONFIG_CACHE = {}
        return _HPOBENCH_CONFIG_CACHE
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "pyyaml is required to read configs/hpobench_tasks.yaml."
        ) from exc
    with HPOBENCH_CONFIG_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    tasks = data.get("tasks", {}) if isinstance(data, dict) else {}
    _HPOBENCH_CONFIG_CACHE = tasks if isinstance(tasks, dict) else {}
    return _HPOBENCH_CONFIG_CACHE


def _get_hpobench_fidelity_settings(task_name: str) -> Tuple[Dict[str, Any], List[str]]:
    tasks = _load_hpobench_config()
    entry = tasks.get(task_name, {})
    if not isinstance(entry, dict):
        return {}, []
    fidelity_spec = entry.get("fidelity", {})
    if not isinstance(fidelity_spec, dict):
        return {}, []
    fidelity: Dict[str, Any] = {}
    tips: List[str] = []
    for name, spec in fidelity_spec.items():
        if not isinstance(spec, dict):
            continue
        default = spec.get("default")
        if default is not None:
            fidelity[name] = default
        parts: List[str] = []
        meaning = spec.get("meaning")
        if meaning:
            parts.append(f"meaning: {meaning}")
        choices = spec.get("choices")
        if choices is not None:
            parts.append(f"choices={choices}")
        else:
            if "min" in spec and "max" in spec:
                parts.append(f"range={spec['min']} to {spec['max']}")
        if default is not None:
            parts.append(f"default={default}")
        if parts:
            tips.append(f"- {name}: " + ", ".join(parts))
    return fidelity, tips


def _apply_fidelity_settings(
    task_name: str,
    fidelity_space: Any,
    fallback: Dict[str, Any],
) -> Dict[str, Any]:
    overrides, _ = _get_hpobench_fidelity_settings(task_name)
    if not overrides:
        return fallback
    allowed = (
        {hp.name for hp in fidelity_space.get_hyperparameters()}
        if fidelity_space is not None
        else set(fallback)
    )
    unknown = [name for name in overrides if name not in allowed]
    if unknown:
        raise ValueError(f"Unknown fidelity keys for {task_name}: {unknown}")
    updated = dict(fallback)
    updated.update(overrides)
    return updated


_HPOBENCH_CACHE: Dict[str, Any] = {}
_HPOBENCH_CACHE_LOCK = threading.Lock()
_HPOBENCH_EVAL_LOCKS: Dict[str, threading.Lock] = {}
_HPOBENCH_FALLBACK_EVAL_LOCK = threading.Lock()


def _load_hpobench(task_name: str) -> HPOBenchTask:
    with _HPOBENCH_CACHE_LOCK:
        if task_name not in _HPOBENCH_CACHE:
            _HPOBENCH_CACHE[task_name] = _load_hpobench_uncached(task_name)
            _HPOBENCH_EVAL_LOCKS[task_name] = threading.Lock()
        return _HPOBENCH_CACHE[task_name]


def _load_hpobench_uncached(task_name: str) -> HPOBenchTask:
    if not os.path.isdir(HPOBENCH_ROOT):
        raise FileNotFoundError(
            f"HPOBench not found at {HPOBENCH_ROOT}. Please download it first."
        )
    import sys

    if HPOBENCH_ROOT not in sys.path:
        sys.path.insert(0, HPOBENCH_ROOT)

    try:
        import ConfigSpace as CS  # noqa: F401
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "ConfigSpace is required for HPOBench tasks. Install it first."
        ) from exc

    if task_name == "hpobench:svm_surrogate":
        warnings.filterwarnings(
            "ignore",
            message=r"The sklearn\.ensemble\.forest module is  deprecated.*",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"The sklearn\.tree\.tree module is  deprecated.*",
            category=FutureWarning,
        )
        warnings.filterwarnings(
            "ignore",
            message=r"Trying to unpickle estimator .* from version .*",
            category=UserWarning,
        )
        from hpobench.benchmarks.surrogates.svm_benchmark import (
            SurrogateSVMBenchmark,
        )

        bench = SurrogateSVMBenchmark(rng=1)
        cs = bench.get_configuration_space(seed=1)
        fidelity_space = bench.get_fidelity_space(seed=1)
        fidelity = {"dataset_fraction": 1.0}
        fidelity = _apply_fidelity_settings(task_name, fidelity_space, fidelity)
        result = HPOBenchTask(name=task_name, benchmark=bench, config_space=cs, fidelity=fidelity)
        return result

    if task_name.startswith("hpobench:nasbench201:"):
        parts = task_name.split(":")
        if len(parts) < 3:
            raise ValueError("NASBench201 task must be hpobench:nasbench201:<dataset>")
        dataset = parts[2]
        from expgym.compact_nasbench201 import CompactNasBench201Benchmark

        if dataset not in {"cifar10-valid", "cifar100", "imagenet16-120"}:
            raise ValueError(
                "Unknown NASBench201 dataset. Choose from: "
                "cifar10-valid, cifar100, imagenet16-120"
            )
        bench = CompactNasBench201Benchmark(dataset=dataset, rng=1)
        cs = bench.get_configuration_space(seed=1)
        fidelity_space = bench.get_fidelity_space(seed=1)
        fidelity = {}
        for hp in fidelity_space.get_hyperparameters():
            fidelity[hp.name] = hp.default_value
        fidelity = _apply_fidelity_settings(task_name, fidelity_space, fidelity)
        result = HPOBenchTask(name=task_name, benchmark=bench, config_space=cs, fidelity=fidelity)
        return result

    if task_name.startswith("hpobench:nasbench101:"):
        parts = task_name.split(":")
        if len(parts) < 3:
            raise ValueError("NASBench101 task must be hpobench:nasbench101:<A|B|C>")
        variant = parts[2].upper()
        from expgym.compact_nasbench101 import CompactNasBench101Benchmark

        if variant not in {"A", "B", "C"}:
            raise ValueError("NASBench101 variant must be A, B, or C.")
        bench = CompactNasBench101Benchmark(variant=variant, rng=1)
        cs = bench.get_configuration_space(seed=1)
        fidelity_space = bench.get_fidelity_space(seed=1)
        fidelity = {}
        for hp in fidelity_space.get_hyperparameters():
            fidelity[hp.name] = hp.default_value
        fidelity = _apply_fidelity_settings(task_name, fidelity_space, fidelity)
        result = HPOBenchTask(name=task_name, benchmark=bench, config_space=cs, fidelity=fidelity)
        return result

    if task_name.startswith("hpobench:paramnet:"):
        # Format: hpobench:paramnet:<dataset>:(steps|time)[:reduced]
        parts = task_name.split(":")
        if len(parts) < 4:
            raise ValueError(
                "ParamNet task must be hpobench:paramnet:<dataset>:(steps|time)[:reduced]"
            )
        dataset = parts[2]
        mode = parts[3]
        reduced = len(parts) > 4 and parts[4] == "reduced"

        dataset_title = dataset.capitalize() if dataset != "mnist" else "Mnist"
        if dataset == "optdigits":
            dataset_title = "Optdigits"
        if dataset == "poker":
            dataset_title = "Poker"
        if dataset == "higgs":
            dataset_title = "Higgs"
        if dataset == "letter":
            dataset_title = "Letter"
        if dataset == "adult":
            dataset_title = "Adult"

        if mode not in {"steps", "time"}:
            raise ValueError("ParamNet mode must be 'steps' or 'time'")

        prefix = "ParamNetReduced" if reduced else "ParamNet"
        suffix = "OnStepsBenchmark" if mode == "steps" else "OnTimeBenchmark"
        class_name = f"{prefix}{dataset_title}{suffix}"

        from hpobench.benchmarks.surrogates import paramnet_benchmark as paramnet

        if not hasattr(paramnet, class_name):
            raise ValueError(f"Unknown ParamNet class: {class_name}")
        bench_cls = getattr(paramnet, class_name)
        bench = bench_cls(rng=1)
        cs = bench.get_configuration_space(seed=1)
        fidelity_space = bench.get_fidelity_space(seed=1)
        fidelity = {}
        for hp in fidelity_space.get_hyperparameters():
            fidelity[hp.name] = hp.default_value
        fidelity = _apply_fidelity_settings(task_name, fidelity_space, fidelity)
        result = HPOBenchTask(name=task_name, benchmark=bench, config_space=cs, fidelity=fidelity)
        return result

    raise ValueError(f"Unknown tuning task: {task_name}")


def _nasbench101_edge_pairs(variant: str) -> List[Tuple[int, int]]:
    """Edge-index meanings, in the same order as the compact NAS101 decoder."""
    if variant.upper() == "B":
        # B's selectors address the reversed bit string, decoded by column.
        return [pair for _, pair in sorted(
            (20 - (row + column * (column - 1) // 2), (row, column))
            for column in range(7) for row in range(column)
        )]
    return [(row, column) for row in range(7) for column in range(row + 1, 7)]


def _task_hints(task_name: str) -> Optional[str]:
    """Return task-specific semantic hints to help LLMs understand the search space."""
    if task_name.startswith("hpobench:nasbench101:"):
        variant = task_name.split(":")[2].upper()
        if variant not in {"A", "B", "C"}:
            raise ValueError("NASBench101 variant must be A, B, or C.")
        common = (
            f"Note: NASBench101-{variant} is a neural architecture search task on a "
            "7-node directed acyclic graph (DAG). Node 0 is the input and node 6 "
            "is the output; op_node_0 through op_node_4 specify operations on "
            "nodes 1 through 5. The decoded graph must have AT MOST 9 edges "
            "and a connected path from node 0 to node 6. Graphs with more than "
            "9 edges or no input-to-output path will always score 0. "
            "You must specify ALL parameters in every evaluation call. "
        )
        if variant == "A":
            encoding = (
                "Each of the 21 edge_0 through edge_20 parameters is a binary "
                "adjacency entry (0=absent, 1=present), ordered row by row in "
                "the upper-triangular adjacency matrix. Set unused edges to 0; "
                "do not set all 21 entries to 1. Edge parameter mapping: "
            )
        elif variant == "B":
            encoding = (
                "The 9 parameters edge_0 through edge_8 are edge-ID selectors, "
                "each an integer from 0 to 20, NOT binary adjacency entries. "
                "Each selector chooses one edge from the mapping below. "
                "Repeated IDs select that edge only once, so duplicates can "
                "represent fewer than 9 edges. There is no unused sentinel: "
                "ID 0 is a real edge (5->6), not an absent edge. IDs use the "
                "decoder's reversed column-wise bit order. Edge-ID mapping: "
            )
        else:
            encoding = (
                "The 21 parameters edge_0 through edge_20 are real-valued "
                "edge priorities in [0,1], NOT binary adjacency entries. "
                "num_edges is an integer from 0 to 9; exactly the num_edges "
                "highest-priority edges are selected (top-k). A priority of "
                "0 is not an absent-edge sentinel; selection depends on rank. "
                "Use distinct priorities to avoid tie ambiguity. num_edges=0 "
                "selects no edges and cannot connect input to output. Priorities "
                "use row-wise upper-triangular order. Edge parameter mapping: "
            )
        prefix = "" if variant == "B" else "edge_"
        mapping = ", ".join(
            f"{prefix}{index}={source}->{target}"
            for index, (source, target) in enumerate(_nasbench101_edge_pairs(variant))
        )
        return common + encoding + mapping + "."
    if task_name.startswith("hpobench:nasbench201:"):
        return (
            "Note: This is a neural architecture search task. "
            "Each parameter selects an operation for an edge in a fixed cell structure. "
            "All operations are valid; explore diverse combinations for better performance."
        )
    return None


def _describe_config_space(cs: Any) -> str:
    lines = ["Parameter ranges:"]
    for hp in cs.get_hyperparameters():
        if hasattr(hp, "lower") and hasattr(hp, "upper"):
            log_note = " (log)" if getattr(hp, "log", False) else ""
            lines.append(
                f"- {hp.name}: {hp.lower} to {hp.upper}{log_note} (default={hp.default_value})"
            )
        else:
            choices = getattr(hp, "choices", None)
            if choices is not None:
                lines.append(f"- {hp.name}: choices={list(choices)} (default={hp.default_value})")
            else:
                lines.append(f"- {hp.name}: default={hp.default_value}")
    return "\n".join(lines)


def _schema_scalar(value: Any) -> Any:
    """Convert ConfigSpace/NumPy scalars without losing JSON field types."""
    if hasattr(value, "item"):
        value = value.item()
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real) and math.isfinite(value):
        return float(value)
    raise TypeError(f"Unsupported JSON schema scalar: {value!r}")


def _schema_enum(values: Any) -> Dict[str, Any]:
    values = [_schema_scalar(value) for value in values]
    types = set()
    for value in values:
        types.add("null" if value is None else "boolean" if isinstance(value, bool)
                  else "integer" if isinstance(value, int)
                  else "number" if isinstance(value, float) else "string")
    if "number" in types:
        types.discard("integer")
    if not types:
        raise ValueError("A hyperparameter must have at least one allowed value")
    return {"type": next(iter(types)) if len(types) == 1 else sorted(types), "enum": values}


def _ensure_supported_config_space(config_space: Any) -> None:
    """Fail explicitly for spaces outside the flat scalar tool contract.

    These are task-definition errors, not errors in a model's configuration.
    The nine paper tasks are unconditional, unquantized numeric/string spaces.
    """
    for accessor, label in (("get_conditions", "conditional"),
                            ("get_forbiddens", "forbidden-clause")):
        getter = getattr(config_space, accessor, None)
        if getter is not None and getter():
            raise ValueError("Unsupported {} configuration space".format(label))
    for hp in config_space.get_hyperparameters():
        if getattr(hp, "q", None) is not None:
            raise ValueError("Unsupported quantized hyperparameter: {}".format(hp.name))
        values = (getattr(hp, "choices", None) if hasattr(hp, "choices") else
                  getattr(hp, "sequence", None) if hasattr(hp, "sequence") else
                  [hp.value] if hasattr(hp, "value") else None)
        if values is not None:
            for raw in values:
                value = _schema_scalar(raw)
                if value is None or isinstance(value, bool):
                    raise ValueError("Unsupported boolean/null hyperparameter: {}".format(hp.name))
        elif not (hasattr(hp, "lower") and hasattr(hp, "upper")):
            raise TypeError("Unsupported hyperparameter type: {}".format(type(hp).__name__))
        else:
            bounds = [_schema_scalar(hp.lower), _schema_scalar(hp.upper)]
            if any(isinstance(bound, bool) or not isinstance(bound, Real) for bound in bounds):
                raise ValueError("Hyperparameter bounds must be finite numbers: {}".format(hp.name))
            if bounds[0] > bounds[1]:
                raise ValueError("Hyperparameter bounds are reversed: {}".format(hp.name))


def _config_space_schema(config_space: Any) -> Dict[str, Any]:
    """Describe the existing flat, all-parameters-required HPO tool payload."""
    _ensure_supported_config_space(config_space)
    properties = {}
    for hp in config_space.get_hyperparameters():
        if hasattr(hp, "choices"):
            prop = _schema_enum(hp.choices)
        elif hasattr(hp, "sequence"):
            prop = _schema_enum(hp.sequence)
        elif hasattr(hp, "lower") and hasattr(hp, "upper"):
            is_integer = any("IntegerHyperparameter" in cls.__name__
                             for cls in type(hp).__mro__)
            prop = {"type": "integer" if is_integer else "number",
                    "minimum": _schema_scalar(hp.lower), "maximum": _schema_scalar(hp.upper)}
            if getattr(hp, "log", False):
                prop["description"] = "Log-scaled hyperparameter; provide its value within the stated bounds."
        elif hasattr(hp, "value"):
            prop = _schema_enum([hp.value])
        else:
            raise TypeError(f"Unsupported hyperparameter type for tool schema: {type(hp).__name__}")
        properties[hp.name] = prop
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def _backend_number(value: Any, field: str, minimum: float,
                    maximum: Optional[float] = None) -> float:
    """Validate backend numbers before conversion, clipping, or normalization.

    This deliberately does not raise InvalidConfigurationError: a corrupt
    backend result must fail scoring rather than be counted as a model error.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("Backend {} must be a real number".format(field))
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("Backend {} must be finite".format(field)) from exc
    if not math.isfinite(number):
        raise ValueError("Backend {} must be finite".format(field))
    if number < minimum or (maximum is not None and number > maximum):
        raise ValueError("Backend {} outside supported range".format(field))
    return number


def _hpobench_evaluate(task: HPOBenchTask, config: Dict[str, Any]) -> Tuple[float, float]:
    # Benchmark instances are shared across PoolAct agents. Guard mutable
    # ConfigSpace/surrogate state when agents evaluate concurrently.
    lock = _HPOBENCH_EVAL_LOCKS.get(
        getattr(task, "name", ""),
        _HPOBENCH_FALLBACK_EVAL_LOCK,
    )
    with lock:
        result = task.benchmark.objective_function(
            configuration=config,
            fidelity=task.fidelity,
        )
    if not isinstance(result, Mapping):
        raise TypeError("HPOBench result must be a mapping")
    # Required fields: missing output is a backend failure, not a zero score.
    obj_value = _backend_number(result["function_value"], "function_value", 0.0, 100.0)
    cost = _backend_number(result["cost"], "cost", 0.0)
    if 1.0 < obj_value <= 100.0:
        perf = 1.0 - (obj_value / 100.0)
    else:
        perf = 1.0 - obj_value
    perf = max(0.0, min(1.0, perf))
    return perf, cost


def list_hpobench_tasks() -> List[str]:
    """Return exactly the nine data-complete tasks in the paper matrix."""
    return [
        "hpobench:paramnet:adult:steps",
        "hpobench:paramnet:higgs:steps",
        "hpobench:paramnet:letter:steps",
        "hpobench:nasbench101:A",
        "hpobench:nasbench101:B",
        "hpobench:nasbench101:C",
        "hpobench:nasbench201:cifar10-valid",
        "hpobench:nasbench201:cifar100",
        "hpobench:nasbench201:imagenet16-120",
    ]

# --- Environment mechanics (deterministic perf/overhead surfaces). ---


def _normalize(value: int, bounds: ParameterRange) -> float:
    return (value - bounds.low) / (bounds.high - bounds.low)


def _vectorize(config: Dict[str, int]) -> List[float]:
    return [_normalize(config[bounds.name], bounds) for bounds in PARAMETER_RANGES]


def _denormalize(vec: List[float]) -> Dict[str, float]:
    values: Dict[str, float] = {}
    for value, bounds in zip(vec, PARAMETER_RANGES):
        values[bounds.name] = bounds.low + value * (bounds.high - bounds.low)
    return values


def _hash_noise(values: List[float], scale: float) -> float:
    key = ",".join(f"{v:.6f}" for v in values)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    raw = int.from_bytes(digest[:4], "big") / 2**32
    return (raw - 0.5) * 2 * scale


def _performance(vec: List[float]) -> float:
    raw = _denormalize(vec)
    dropout_rate = raw["dropout_x100"] / 100.0
    lr = raw["learning_rate_x1e5"] * 1e-5
    weight_decay = raw["weight_decay_x1e4"] * 1e-4
    warmup_steps = raw["warmup_steps"]
    batch_size = raw["batch_size"]
    grad_acc = raw["gradient_accumulation"]

    depth_n = vec[0]
    width_n = vec[1]
    heads_n = vec[2]
    ffn_n = vec[3]
    warmup_n = warmup_steps / 4000.0
    eff_batch = batch_size * grad_acc
    eff_batch_n = eff_batch / (512.0 * 16.0 + 1e-8)

    capacity_raw = (
        0.6 * depth_n
        + 0.7 * width_n
        + 0.3 * ffn_n
        + 0.2 * heads_n
    )
    capacity_term = 0.25 * math.tanh(capacity_raw)

    log_lr = math.log10(lr)
    log_lr_star = math.log10(3e-4)
    opt_lr_term = math.exp(-((log_lr - log_lr_star) ** 2) / (2 * 0.25 ** 2))

    wd_star = 5e-4
    log_wd = math.log10(weight_decay + 1e-10)
    log_wd_star = math.log10(wd_star)
    opt_wd_term = math.exp(-((log_wd - log_wd_star) ** 2) / (2 * 0.35 ** 2))

    warmup_star = 400.0 / 4000.0
    opt_warmup_term = math.exp(-((warmup_n - warmup_star) ** 2) / (2 * 0.12 ** 2))

    batch_star = 0.25
    opt_batch_term = math.exp(-((eff_batch_n - batch_star) ** 2) / (2 * 0.18 ** 2))

    opt_term = (
        0.18 * opt_lr_term
        + 0.08 * opt_wd_term
        + 0.08 * opt_warmup_term
        + 0.08 * opt_batch_term
    )

    drop_star = 0.15
    drop_term = 0.10 * math.exp(-((dropout_rate - drop_star) ** 2) / (2 * 0.08 ** 2))

    over_cap = max(0.0, capacity_raw - 1.1)
    overfit_penalty = 0.35 * over_cap

    noise = _hash_noise(vec, scale=0.005)
    score = 0.3 + capacity_term + opt_term + drop_term - overfit_penalty + noise

    # s = max(0.0, min(1.0, score))
    # tail_start = 0.75  # 从这个分数开始“变难”（可调：0.7~0.85）
    # gamma = 3.0        # 尾部压缩强度（可调：2~5，越大越难拿高分）
    # if s > tail_start:
    #     t = (s - tail_start) / (1.0 - tail_start)  # t in (0,1]
    #     s = tail_start + (t ** gamma) * (1.0 - tail_start)
    # return s
    score = _backend_number(score, "builtin raw performance", -math.inf)
    return max(0.0, min(1.0, score))


def _overhead(vec: List[float]) -> float:
    raw = _denormalize(vec)
    num_layers = raw["num_layers"]
    hidden_width = raw["hidden_width"]
    attention_heads = raw["attention_heads"]
    ffn_expansion = raw["ffn_expansion"]
    lr = raw["learning_rate_x1e5"] * 1e-5
    warmup_steps = raw["warmup_steps"]
    batch_size = raw["batch_size"]
    grad_acc = raw["gradient_accumulation"]

    depth_factor = num_layers / 2.0
    width_factor = (hidden_width / 64.0) ** 2
    ffn_factor = 0.6 + 0.4 * (ffn_expansion / 8.0)
    head_factor = 0.6 + 0.4 * (attention_heads / 16.0)
    eff_batch = batch_size * grad_acc
    batch_factor = eff_batch / 8.0

    compute_units = depth_factor * width_factor * ffn_factor * head_factor * batch_factor
    # Keep overhead responsive without hard-saturating most configs.
    base_seconds = 6.0 + 12.0 * math.log10(1.0 + compute_units)

    warmup_term = 1.0 + 0.25 * (warmup_steps / 4000.0)

    log_lr = math.log10(lr)
    log_lr_star = math.log10(3e-4)
    lr_dev = log_lr - log_lr_star
    lr_penalty_factor = 1.0 + 0.35 * min(1.5, (lr_dev ** 2) / (0.5 ** 2))

    noise = _hash_noise(list(reversed(vec)), scale=0.005)
    overhead = base_seconds * warmup_term * lr_penalty_factor + noise
    overhead = _backend_number(overhead, "builtin raw cost", 0.0)
    return max(8.0, min(140.0, overhead))


def _validate_config(config: Dict[str, int]) -> None:
    if not isinstance(config, dict):
        raise InvalidConfigurationError("Configuration must be a dict")
    missing = [p.name for p in PARAMETER_RANGES if p.name not in config]
    if missing:
        raise InvalidConfigurationError(f"Missing parameters: {missing}")
    unknown = set(config) - {p.name for p in PARAMETER_RANGES}
    if unknown:
        raise InvalidConfigurationError(f"Unknown hyperparameter(s) {unknown}")
    for bounds in PARAMETER_RANGES:
        value = config[bounds.name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidConfigurationError(f"Parameter {bounds.name} must be an integer")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite or value != int(value):
            raise InvalidConfigurationError(f"Parameter {bounds.name} must be a finite integer")
        if not bounds.low <= value <= bounds.high:
            raise InvalidConfigurationError(
                f"Parameter {bounds.name}={value} outside range [{bounds.low}, {bounds.high}]"
            )
        config[bounds.name] = int(value)


def evaluate_config(config: Dict[str, int]) -> Tuple[float, float]:
    """Return (performance, overhead) for the given configuration dict."""

    if not isinstance(config, dict):
        raise InvalidConfigurationError("Configuration must be a dict")
    normalized = dict(config)
    _validate_config(normalized)
    vec = _vectorize(normalized)
    perf = _backend_number(_performance(vec), "builtin performance", 0.0, 1.0)
    cost = _backend_number(_overhead(vec), "builtin cost", 0.0)
    return perf, cost


def evaluate_config_action(payload: str) -> Tuple[float, float]:
    """Parse a JSON payload and forward to ``evaluate_config``."""

    try:
        data = json.loads(payload)
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise InvalidConfigurationError(
            f"Invalid JSON payload: {exc}. Send a single valid JSON object."
        ) from exc
    if isinstance(data, list):
        if len(data) != len(PARAMETER_RANGES):
            raise InvalidConfigurationError("Expected list of length 10 for configuration vector")
        config = {rng.name: value for rng, value in zip(PARAMETER_RANGES, data)}
    elif isinstance(data, dict):
        config = data
    else:
        raise InvalidConfigurationError("Configuration payload must be dict or list")
    return evaluate_config(config)


def evaluate_hpobench_action(task: HPOBenchTask, payload: str) -> Tuple[Any, ...]:
    try:
        data = json.loads(payload)
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise InvalidConfigurationError(
            f"Invalid JSON payload: {exc}. Send a single valid JSON object."
        ) from exc
    allowed = {hp.name for hp in task.config_space.get_hyperparameters()}
    fidelity_keys = set(task.fidelity.keys())
    if isinstance(data, list):
        parameters = list(task.config_space.get_hyperparameters())
        if len(data) != len(parameters):
            raise InvalidConfigurationError(
                f"Expected list of length {len(parameters)} for configuration vector"
            )
        config = {hp.name: value for hp, value in zip(parameters, data)}
    elif isinstance(data, dict):
        config = {k: v for k, v in data.items() if k in allowed}
        unknown = [k for k in data.keys() if k not in allowed and k not in fidelity_keys]
        if unknown:
            raise InvalidConfigurationError(f"Unknown hyperparameter(s) {set(unknown)}")
    else:
        raise InvalidConfigurationError("Configuration payload must be dict or list")
    error = _validate_hpobench_config(task.config_space, config)
    if error is not None:
        raise InvalidConfigurationError(error)
    perf, cost = _hpobench_evaluate(task, config)
    if perf == 0.0:
        return (
            "perf=0.000000 (invalid or degenerate configuration, try a different one)",
            0.0,
            cost,
        )
    return perf, cost


def _validate_hpobench_config(config_space: Any, config: Dict[str, Any]) -> Optional[str]:
    _ensure_supported_config_space(config_space)
    missing = [hp.name for hp in config_space.get_hyperparameters() if hp.name not in config]
    if missing:
        return f"Invalid config: missing {', '.join(missing)}. You must specify ALL parameters."
    errors = []
    for hp in config_space.get_hyperparameters():
        value = config[hp.name]
        # JSON scalars only. bool is not an integer hyperparameter, and
        # nonfinite values must not reach ConfigSpace or a benchmark backend.
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            errors.append(f"{hp.name} invalid type")
            continue
        if isinstance(value, (int, float)):
            try:
                finite_value = math.isfinite(value)
            except OverflowError:
                finite_value = False
            if not finite_value:
                errors.append(f"{hp.name} must be finite")
                continue
        if hasattr(hp, "choices") or hasattr(hp, "sequence") or hasattr(hp, "value"):
            choices = (hp.choices if hasattr(hp, "choices") else
                       hp.sequence if hasattr(hp, "sequence") else [hp.value])
            matching = [choice for choice in choices
                        if not isinstance(choice, bool)
                        and ((isinstance(value, str) and isinstance(choice, str))
                             or (isinstance(value, (int, float)) and isinstance(choice, Real)))
                        and value == choice]
            if not matching:
                errors.append(f"{hp.name} out of range")
            elif isinstance(matching[0], Integral):
                # ConfigSpace 0.4 and 1.x differ on 1.0 for integer choices.
                # Preserve its mathematical meaning, consistently in both.
                config[hp.name] = int(value)
        elif hasattr(hp, "lower") and hasattr(hp, "upper"):
            if not isinstance(value, (int, float)):
                errors.append(f"{hp.name} invalid type")
                continue
            is_integer = any("IntegerHyperparameter" in cls.__name__
                             for cls in type(hp).__mro__)
            if is_integer:
                if value != int(value):
                    errors.append(f"{hp.name} must be integer")
                    continue
                config[hp.name] = int(value)
            if value < hp.lower or value > hp.upper:
                errors.append(f"{hp.name} out of range")
    if errors:
        return f"Invalid config: {'; '.join(errors)}"
    return None


def describe_parameter_ranges() -> str:
    lines = ["Parameter ranges (integers):"]
    for rng in PARAMETER_RANGES:
        lines.append(f"- {rng.name}: {rng.low}-{rng.high}")
    return "\n".join(lines)


def format_config(config: Dict[str, int]) -> str:
    ordered = {rng.name: config[rng.name] for rng in PARAMETER_RANGES}
    return json.dumps(ordered, separators=(",", ":"))


def _sample_configs(samples: int, seed: int) -> List[Dict[str, int]]:
    rand = random.Random(seed)
    configs: List[Dict[str, int]] = []
    for _ in range(samples):
        config = {
            bounds.name: rand.randint(bounds.low, bounds.high)
            for bounds in PARAMETER_RANGES
        }
        configs.append(config)
    return configs


REFERENCE_CONFIGS: List[Dict[str, int]] = sorted(
    _sample_configs(256, seed=21), key=lambda cfg: evaluate_config(cfg)[0], reverse=True
)[:8]


def summarize_goal(include_overhead: bool) -> str:
    if include_overhead:
        return "Goal: tune the system for high performance while managing overhead."
    return "Goal: tune the system for high performance."

# --- Scenario wiring (prompt + FakeLLM helpers). ---


def build_context(
    include_overhead: bool, *, tuning_task: str = "neural_network_training",
    tool_protocol: str = "text",
) -> str:
    """Scenario context for the tuning task."""
    if tool_protocol not in ("text", "native"):
        raise ValueError("build_context tool_protocol must be resolved text or native")
    tool_instruction = (
        'Action format: Action: evaluate_config {"param": value, ...}'
        if tool_protocol == "text" else
        'Call the evaluate_config function with arguments {"param": value, ...} using a native tool call.'
    )

    if tuning_task == "neural_network_training":
        lines = [
            summarize_goal(include_overhead),
            describe_parameter_ranges(),
            tool_instruction,
            "Answer format: Answer: {\"param\": value, ...}",
        ]
    else:
        task = _load_hpobench(tuning_task)
        lines = [
            "Goal: tune the system for high performance.",
            _describe_config_space(task.config_space),
        ]
        hints = _task_hints(tuning_task)
        if hints:
            lines.append(hints)
        lines.extend([
            tool_instruction,
            "Answer format: Answer: {\"param\": value, ...}",
        ])
    if include_overhead:
        lines.append("Note: Overhead reflects latency; manage the time budget.")
    return "\n".join(lines)


def build_instruction_notes(_: bool) -> List[str]:
    """Scenario prompt notes for the tuning task."""

    return []


def build_system_prompt(include_overhead: bool, *, tuning_task: str = "neural_network_training") -> str:
    notes = []
    if include_overhead:
        notes.append("Overhead values reflect latency; manage the time budget.")
    return build_react_system_prompt(instruction_notes=notes)


def build_fake_plan(
    probes: int,
    *,
    tuning_task: str = "neural_network_training",
    row_index: Optional[int] = None,
    seed: Optional[int] = None,
) -> List[tuple[str, str]]:
    """Return a deterministic FakeLLM plan for the tuning task."""

    _ = row_index
    if tuning_task == "neural_network_training":
        candidate_configs = REFERENCE_CONFIGS[: max(1, probes)]
        payloads = [format_config(cfg) for cfg in candidate_configs]
        return [("evaluate_config", payload) for payload in payloads]
    task = _load_hpobench(tuning_task)
    import numpy as np

    with _HPOBENCH_EVAL_LOCKS[task.name]:
        if seed is not None:
            task.config_space.seed(seed)
        configs = [
            dict(task.config_space.sample_configuration())
            for _ in range(max(1, probes))
        ]
    # ConfigSpace 1.x can return NumPy scalars for categorical choices.
    # Preserve their numeric/boolean types in the JSON sent by the fake agent.
    payloads = [
        json.dumps({
            name: value.item() if isinstance(value, np.generic) else value
            for name, value in config.items()
        })
        for config in configs
    ]
    return [("evaluate_config", payload) for payload in payloads]


def build_tools(*, tuning_task: str = "neural_network_training") -> Dict[str, Callable[[str], Tuple[float, float]]]:
    if tuning_task == "neural_network_training":
        def evaluate(payload: str):
            return evaluate_config_action(payload)

        properties = {bounds.name: {"type": "integer", "minimum": bounds.low,
                                    "maximum": bounds.high} for bounds in PARAMETER_RANGES}
        parameters = {"type": "object", "properties": properties,
                      "required": list(properties), "additionalProperties": False}
        description = "Evaluate a complete flat configuration and return performance and simulated evaluation cost."
    else:
        task = _load_hpobench(tuning_task)

        def evaluate(payload: str):
            return evaluate_hpobench_action(task, payload)

        parameters = _config_space_schema(task.config_space)
        description = (
            f"Evaluate a complete flat configuration for {tuning_task}. "
            "Return performance and simulated evaluation cost; fidelity is fixed "
            f"at {json.dumps(task.fidelity, sort_keys=True)} and is not an input field."
        )
        hints = _task_hints(tuning_task)
        if hints:
            description += " " + hints
    evaluate.__expgym_tool_schema__ = {
        "name": "evaluate_config", "description": description, "parameters": parameters,
    }
    return {"evaluate_config": evaluate}


SCENARIO = {
    "name": "tuning",
    "tools": build_tools,
    "build_context": build_context,
    "build_instruction_notes": build_instruction_notes,
    "build_fake_plan": build_fake_plan,
    "build_system_prompt": build_system_prompt,
}
