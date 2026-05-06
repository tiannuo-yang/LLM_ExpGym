"""PoolAct: parallel-agent strategy with a shared cache, ledger, and graph.

PoolAct is the parallel-agent strategy reported in the paper and the
project's second component, alongside the ExpGym evaluation suite. It
coordinates N agents working on the same problem so they share work
instead of duplicating it. The implementation lives at
``expgym.extras.parallel_cache``; this module re-exports the public
surface under a stable path. Prefer ``from expgym.poolact import ...``
over reaching into ``extras``.

Three tool wrappers share a thread-safe observation cache and layer
extra context on top. ``wrap_tools_with_cache`` does only zero-cost
exact-match dedup. ``wrap_tools_with_poolact`` adds a shared exploration
ledger so every agent sees a running summary of what the others have
observed; this is the configuration reported as ``poolact`` in the
paper. ``wrap_tools_with_polact`` swaps the ledger for a shared
exploration graph that records topology rather than a flat summary
(PoolAct v2). The graph variant supports time-gated visibility via
``AgentClock``.

Two augmenter helpers, ``make_ledger_augmenter`` and
``make_graph_augmenter``, build an ``observation_augmenter`` callable
that ``run_react_loop()`` injects into each agent's context after every
tool call. The underlying shared data structures
(``SharedObservationCache``, ``SharedExplorationLedger``,
``SharedExplorationGraph``, ``AgentClock``) are exported for callers
that want to script their own parallel runner. See the README "PoolAct"
section for a minimal usage example.
"""
from __future__ import annotations

from expgym.extras.parallel_cache import (
    AgentClock,
    SharedExplorationGraph,
    SharedExplorationLedger,
    SharedObservationCache,
    make_graph_augmenter,
    make_ledger_augmenter,
    wrap_tools_with_cache,
    wrap_tools_with_polact,
    wrap_tools_with_poolact,
)

__all__ = [
    "AgentClock",
    "SharedExplorationGraph",
    "SharedExplorationLedger",
    "SharedObservationCache",
    "make_graph_augmenter",
    "make_ledger_augmenter",
    "wrap_tools_with_cache",
    "wrap_tools_with_polact",
    "wrap_tools_with_poolact",
]
