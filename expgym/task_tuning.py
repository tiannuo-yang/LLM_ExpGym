"""Configuration tuning environment with 10 integer parameters."""
from __future__ import annotations

import hashlib
import json
import math
import random
import os
import threading
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any

from expgym.react_loop import build_system_prompt as build_react_system_prompt

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


def _task_hints(task_name: str) -> Optional[str]:
    """Return task-specific semantic hints to help LLMs understand the search space."""
    if task_name.startswith("hpobench:nasbench101:"):
        return (
            "Note: This is a neural architecture search task on a 7-node directed acyclic graph (DAG). "
            "The edge_* parameters form the upper-triangular adjacency matrix (0 or 1) of the DAG. "
            "The op_node_* parameters choose the operation for each intermediate node. "
            "Node 0 is the input and node 6 is the output. "
            "IMPORTANT CONSTRAINTS: "
            "(1) The total number of edges set to 1 must be AT MOST 9. "
            "Architectures with more than 9 edges are INVALID and will always score 0. "
            "(2) There must be a connected path from the input node (0) to the output node (6). "
            "Disconnected graphs are degenerate and score 0. "
            "(3) Do NOT set all edges to 1 — that exceeds the 9-edge limit. "
            "You must specify ALL parameters in every evaluation call (set unused edges to 0)."
        )
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
    obj_value = float(result.get("function_value", 1.0))
    cost = float(result.get("cost", 0.0))
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
    return max(8.0, min(140.0, overhead))


def _validate_config(config: Dict[str, int]) -> None:
    missing = [p.name for p in PARAMETER_RANGES if p.name not in config]
    if missing:
        raise ValueError(f"Missing parameters: {missing}")
    for bounds in PARAMETER_RANGES:
        value = config[bounds.name]
        if not isinstance(value, int):
            raise TypeError(f"Parameter {bounds.name} must be int, got {type(value)!r}")
        if not bounds.low <= value <= bounds.high:
            raise ValueError(
                f"Parameter {bounds.name}={value} outside range [{bounds.low}, {bounds.high}]"
            )


def evaluate_config(config: Dict[str, int]) -> Tuple[float, float]:
    """Return (performance, overhead) for the given configuration dict."""

    _validate_config(config)
    vec = _vectorize(config)
    return _performance(vec), _overhead(vec)


def evaluate_config_action(payload: str) -> Tuple[float, float]:
    """Parse a JSON payload and forward to ``evaluate_config``."""

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON payload: {exc}. Send a single valid JSON object.", 0.0
    if isinstance(data, list):
        if len(data) != len(PARAMETER_RANGES):
            raise ValueError("Expected list of length 10 for configuration vector")
        config = {rng.name: int(value) for rng, value in zip(PARAMETER_RANGES, data)}
    elif isinstance(data, dict):
        config = {name: int(value) for name, value in data.items()}
    else:
        raise TypeError("Configuration payload must be dict or list")
    return evaluate_config(config)


def evaluate_hpobench_action(task: HPOBenchTask, payload: str) -> Tuple[Any, ...]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON payload: {exc}. Send a single valid JSON object.", 0.0
    allowed = {hp.name for hp in task.config_space.get_hyperparameters()}
    fidelity_keys = set(task.fidelity.keys())
    if isinstance(data, list):
        config = {hp.name: data[i] for i, hp in enumerate(task.config_space.get_hyperparameters())}
    elif isinstance(data, dict):
        config = {k: v for k, v in data.items() if k in allowed}
        unknown = [k for k in data.keys() if k not in allowed and k not in fidelity_keys]
        if unknown:
            raise ValueError(f"Unknown hyperparameter(s) {set(unknown)}")
    else:
        raise TypeError("Configuration payload must be dict or list")
    error = _validate_hpobench_config(task.config_space, config)
    if error is not None:
        return error, 0.0
    perf, cost = _hpobench_evaluate(task, config)
    if perf == 0.0:
        return (
            "perf=0.000000 (invalid or degenerate configuration, try a different one)",
            0.0,
            cost,
        )
    return perf, cost


def _validate_hpobench_config(config_space: Any, config: Dict[str, Any]) -> Optional[str]:
    missing = [hp.name for hp in config_space.get_hyperparameters() if hp.name not in config]
    if missing:
        return f"Invalid config: missing {', '.join(missing)}. You must specify ALL parameters."
    errors = []
    for hp in config_space.get_hyperparameters():
        value = config[hp.name]
        if hasattr(hp, "choices"):
            if value not in hp.choices:
                errors.append(f"{hp.name} out of range")
        elif hasattr(hp, "lower") and hasattr(hp, "upper"):
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


def build_context(include_overhead: bool, *, tuning_task: str = "neural_network_training") -> str:
    """Scenario context for the tuning task."""

    if tuning_task == "neural_network_training":
        lines = [
            summarize_goal(include_overhead),
            describe_parameter_ranges(),
            "Action format: Action: evaluate_config {\"param\": value, ...}",
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
            "Action format: Action: evaluate_config {\"param\": value, ...}",
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
    with _HPOBENCH_EVAL_LOCKS[task.name]:
        if seed is not None:
            task.config_space.seed(seed)
        configs = [
            dict(task.config_space.sample_configuration())
            for _ in range(max(1, probes))
        ]
    payloads = [json.dumps(cfg) for cfg in configs]
    return [("evaluate_config", payload) for payload in payloads]


def build_tools(*, tuning_task: str = "neural_network_training") -> Dict[str, Callable[[str], Tuple[float, float]]]:
    if tuning_task == "neural_network_training":
        return {"evaluate_config": evaluate_config_action}
    task = _load_hpobench(tuning_task)
    return {"evaluate_config": lambda payload: evaluate_hpobench_action(task, payload)}


SCENARIO = {
    "name": "tuning",
    "tools": build_tools,
    "build_context": build_context,
    "build_instruction_notes": build_instruction_notes,
    "build_fake_plan": build_fake_plan,
    "build_system_prompt": build_system_prompt,
}
