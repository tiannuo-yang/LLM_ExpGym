"""Fail-fast policy matching for official shared execution components.

This is not a security boundary for arbitrary user code. Ordinary callables
and standalone, unbound clocks have no contract and retain their old behavior.
None is an explicitly unlimited budget; UNBOUND means an unused dimension.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from functools import partial
from typing import Any


class _Unset(Enum):
    VALUE = "unbound"


UNBOUND = _Unset.VALUE
_ATTRIBUTE = "__expgym_execution_contract__"


@dataclass(frozen=True)
class ExecutionContract:
    clock: Any
    time_budget: Any = UNBOUND
    overhead_scale: Any = UNBOUND


def _read(target: Any) -> Any:
    contract = getattr(target, _ATTRIBUTE, None)
    if contract is not None and not isinstance(contract, ExecutionContract):
        raise ValueError("Malformed official execution contract")
    return contract


def _contracts(target: Any):
    """Follow standard transparent adapters without inspecting user closures."""
    seen = set()
    while target is not None and id(target) not in seen:
        seen.add(id(target))
        contract = _read(target)
        if contract is not None:
            yield contract
        target = target.func if isinstance(target, partial) else getattr(target, "__wrapped__", None)


def _number(value: Any, name: str) -> Any:
    if value is UNBOUND or (name == "time_budget" and value is None):
        return value
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError(name + " must be finite and non-negative")
    return float(value)


def _merge(old: Any, new: ExecutionContract) -> ExecutionContract:
    if old is None:
        return new
    if old.clock is not new.clock:
        raise ValueError("Execution contract agent_clock identity mismatch")
    values = {}
    for name in ("time_budget", "overhead_scale"):
        previous, proposed = getattr(old, name), getattr(new, name)
        if previous is not UNBOUND and proposed is not UNBOUND and previous != proposed:
            raise ValueError("Execution contract " + name + " mismatch")
        values[name] = proposed if previous is UNBOUND else previous
    return ExecutionContract(new.clock, **values)


def bind_execution_contract(target: Any, *, clock: Any,
                            time_budget: Any = UNBOUND,
                            overhead_scale: Any = UNBOUND) -> None:
    """Attach immutable constraints; already-bound values cannot be changed.

    Constraints are also registered on a supplied clock so empty tool mappings
    and separately constructed official hooks cannot hide a conflicting policy.
    Validate both merges before changing either object. A graph augmenter binds
    only its budget, and a claim hook only its clock, not a fictitious scale.
    """
    contract = ExecutionContract(clock, _number(time_budget, "time_budget"),
                                 _number(overhead_scale, "overhead_scale"))
    if clock is None and contract.time_budget not in (UNBOUND, None):
        raise ValueError("A finite shared execution budget requires an AgentClock")
    merged = contract
    for existing in _contracts(target):
        merged = _merge(existing, merged)
    clock_merged = _merge(_read(clock), contract) if clock is not None else None
    setattr(target, _ATTRIBUTE, merged)
    if clock is not None and clock is not target:
        setattr(clock, _ATTRIBUTE, clock_merged)


def validate_execution_contracts(*, tools: Any, agent_clock: Any,
                                 observation_augmenter: Any, pre_tool_hook: Any,
                                 time_budget: Any, overhead_scale: Any) -> None:
    """Reject mismatched official components before any agent side effects.

    This checks only explicit metadata, including that preserved by wraps().
    It neither infers policy from arbitrary closures nor binds unbound clocks.
    """
    expected = ExecutionContract(agent_clock, time_budget, overhead_scale)
    components = [agent_clock, observation_augmenter, pre_tool_hook]
    components.extend(tools.values())
    for component in components:
        for contract in _contracts(component):
            _merge(contract, expected)
