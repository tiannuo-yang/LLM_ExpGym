"""Config table tool used by the minimal ExpGym demo."""
from __future__ import annotations

from typing import Dict, Tuple

ConfigEntry = Dict[str, float]

# Handcrafted trade-offs so the ReAct loop has interesting choices.
CONFIGS: Dict[str, ConfigEntry] = {
    "cfg_01": {"perf": 0.42, "overhead": 0.15},
    "cfg_02": {"perf": 0.44, "overhead": 0.60},
    "cfg_03": {"perf": 0.55, "overhead": 0.30},
    "cfg_04": {"perf": 0.56, "overhead": 0.95},
    "cfg_05": {"perf": 0.61, "overhead": 0.40},
    "cfg_06": {"perf": 0.60, "overhead": 1.20},
    "cfg_07": {"perf": 0.63, "overhead": 0.48},
    "cfg_08": {"perf": 0.62, "overhead": 1.35},
    "cfg_09": {"perf": 0.66, "overhead": 0.55},
    "cfg_10": {"perf": 0.67, "overhead": 1.50},
    "cfg_11": {"perf": 0.70, "overhead": 0.65},
    "cfg_12": {"perf": 0.68, "overhead": 1.70},
    "cfg_13": {"perf": 0.71, "overhead": 0.90},
    "cfg_14": {"perf": 0.73, "overhead": 1.90},
    "cfg_15": {"perf": 0.75, "overhead": 1.05},
    "cfg_16": {"perf": 0.78, "overhead": 2.30},
    "cfg_17": {"perf": 0.80, "overhead": 1.40},
    "cfg_18": {"perf": 0.81, "overhead": 2.60},
    "cfg_19": {"perf": 0.83, "overhead": 1.85},
    "cfg_20": {"perf": 0.84, "overhead": 2.75},
    "cfg_21": {"perf": 0.86, "overhead": 2.10},
    "cfg_22": {"perf": 0.86, "overhead": 3.40},
    "cfg_23": {"perf": 0.88, "overhead": 2.60},
    "cfg_24": {"perf": 0.89, "overhead": 3.80},
}


def run_config(config_id: str) -> Tuple[float, float]:
    """Return the (performance, overhead) pair for the given config id."""

    try:
        config = CONFIGS[config_id]
    except KeyError as exc:  # provide a clearer error than the default repr
        raise KeyError(f"Unknown config_id: {config_id}") from exc
    return config["perf"], config["overhead"]
