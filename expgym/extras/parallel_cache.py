"""Shared observation cache and exploration ledger/graph for PoolAct.

This module backs the PoolAct strategy and is what ``expgym.poolact``
re-exports. It sits under ``expgym.extras`` because it is not part of
the core evaluation suite: nothing in ``react_loop``, the three
scenarios, or ``demo_experiment`` imports from here. Importing is
opt-in.

Public surface:
    SharedObservationCache       thread-safe exact-match cache (zero-cost dedup)
    SharedExplorationLedger      records observations for context injection
    SharedExplorationGraph       graph representation of parallel exploration
    wrap_tools_with_cache        caching-only tool wrapper
    wrap_tools_with_poolact      caching + ledger recording
    wrap_tools_with_polact       caching + graph recording (PoolAct v2)
    make_ledger_augmenter        observation_augmenter that injects ledger
    make_graph_augmenter         observation_augmenter that injects graph
"""
from __future__ import annotations

import json
import re
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# AgentClock — simulated time tracker for parallel agents
# ---------------------------------------------------------------------------

class AgentClock:
    """Tracks an agent's cumulative simulated time.

    Used for time-gated visibility: cache/graph entries are only visible
    to an agent if their completion_time <= agent's current clock.
    """

    def __init__(self) -> None:
        self._time: float = 0.0

    @property
    def now(self) -> float:
        """Current simulated time."""
        return self._time

    def advance(self, dt: float) -> None:
        """Advance the clock by *dt* seconds."""
        self._time += dt


# ---------------------------------------------------------------------------
# Helper: extract raw overhead from tool result tuples
# ---------------------------------------------------------------------------

def _extract_overhead_from_result(result: Any) -> float:
    """Extract the raw overhead value from a tool result tuple.

    Handles the react_loop contract:
    - 2-tuple (perf_or_output, overhead) -> overhead
    - 3-tuple (output, perf, overhead) -> overhead
    Returns 0.0 on failure.
    """
    if isinstance(result, tuple) and len(result) in (2, 3):
        try:
            return float(result[-1])
        except (TypeError, ValueError):
            pass
    return 0.0


# ---------------------------------------------------------------------------
# SharedObservationCache (Layer 0: passive deduplication)
# ---------------------------------------------------------------------------

class SharedObservationCache:
    """Thread-safe cache mapping (tool_name, canonical_payload) -> result.

    Used by the ``cached`` and ``poolact`` parallel strategies so that
    when agent B calls the same tool with the same arguments that agent A
    already called, the cached result is returned with zero overhead cost.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: Dict[Tuple[str, str], Tuple[Any, float]] = {}
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _canonicalize(payload: str) -> str:
        """Canonicalize a JSON payload string for cache key matching."""
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            return payload
        if isinstance(data, dict):
            return json.dumps(data, sort_keys=True, separators=(",", ":"))
        if isinstance(data, list):
            return json.dumps(data, separators=(",", ":"))
        return payload

    def get(
        self,
        tool_name: str,
        payload: str,
        *,
        visible_before: Optional[float] = None,
    ) -> Optional[Any]:
        """Look up a cached result. Returns None on miss.

        Args:
            visible_before: If set, only return results whose
                completion_time <= visible_before.  ``None`` (default)
                means see everything (backward compat).
        """
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            if key in self._cache:
                result, completion_time = self._cache[key]
                if visible_before is not None and completion_time > visible_before:
                    self._misses += 1
                    return None
                self._hits += 1
                return result
            self._misses += 1
            return None

    def put(
        self,
        tool_name: str,
        payload: str,
        result: Any,
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Store a result in the cache.

        First-writer-wins: if the key already exists, keep the original
        result and the earlier (min) completion_time so the entry becomes
        visible as early as possible.
        """
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            if key in self._cache:
                existing_result, existing_ct = self._cache[key]
                self._cache[key] = (existing_result, min(existing_ct, completion_time))
            else:
                self._cache[key] = (result, completion_time)

    def stats(self) -> Dict[str, int]:
        """Return cache statistics."""
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
            }


# ---------------------------------------------------------------------------
# SharedExplorationLedger (Layer 1: active context injection)
# ---------------------------------------------------------------------------

@dataclass
class LedgerEntry:
    """A single observation recorded in the shared ledger."""
    agent_id: int
    tool_name: str
    payload_summary: str
    result_summary: str
    cache_hit: bool
    timestamp: float = field(default_factory=time.time)


class SharedExplorationLedger:
    """Thread-safe ledger recording all observations across parallel agents.

    The ledger is the key innovation in PoolAct: before each agent's LLM
    call, the ledger is formatted and injected into the agent's observation
    context, enabling stigmergic coordination --- agents see what others
    have tried and found, and can steer their exploration accordingly.
    """

    def __init__(self, max_display_entries: int = 30):
        self._lock = threading.Lock()
        self._entries: List[LedgerEntry] = []
        self._max_display = max_display_entries

    def record(
        self,
        agent_id: int,
        tool_name: str,
        payload_summary: str,
        result_summary: str,
        cache_hit: bool = False,
    ) -> None:
        """Record an observation from any agent."""
        entry = LedgerEntry(
            agent_id=agent_id,
            tool_name=tool_name,
            payload_summary=payload_summary,
            result_summary=result_summary,
            cache_hit=cache_hit,
        )
        with self._lock:
            self._entries.append(entry)

    def format_for_injection(self, max_entries: Optional[int] = None) -> str:
        """Format the ledger as a context block for injection.

        Returns a compact summary of all observations from all agents.
        Empty string if no entries recorded yet.
        """
        with self._lock:
            entries = list(self._entries)

        if not entries:
            return ""

        max_e = max_entries or self._max_display
        n_agents = len(set(e.agent_id for e in entries))
        n_unique = sum(1 for e in entries if not e.cache_hit)
        n_cached = sum(1 for e in entries if e.cache_hit)

        lines = [
            "--- Shared Exploration Ledger "
            "({} observations from {} agents, {} unique, {} cached) ---".format(
                len(entries), n_agents, n_unique, n_cached
            )
        ]

        # Show most recent entries (newest last)
        display = entries[-max_e:]
        if len(entries) > max_e:
            lines.append(
                "[...{} earlier entries omitted...]".format(len(entries) - max_e)
            )

        for e in display:
            hit_tag = " [cached]" if e.cache_hit else ""
            lines.append(
                "[Agent {}] {} {} -> {}{}".format(
                    e.agent_id, e.tool_name, e.payload_summary,
                    e.result_summary, hit_tag,
                )
            )

        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        """Return ledger statistics."""
        with self._lock:
            entries = list(self._entries)
        return {
            "total_entries": len(entries),
            "unique_entries": sum(1 for e in entries if not e.cache_hit),
            "cached_entries": sum(1 for e in entries if e.cache_hit),
            "agents": len(set(e.agent_id for e in entries)),
        }


# ---------------------------------------------------------------------------
# Helper: zero overhead on cache hit
# ---------------------------------------------------------------------------

def _zero_overhead(result: Any) -> Any:
    """Return a copy of the tool result with overhead (last element) set to 0.

    Matches the ``react_loop._parse_tool_return()`` contract:
    - 2-tuple ``(perf_or_output, overhead)`` -> ``(perf_or_output, 0.0)``
    - 3-tuple ``(output, perf, overhead)`` -> ``(output, perf, 0.0)``
    """
    if isinstance(result, tuple):
        if len(result) == 2:
            return (result[0], 0.0)
        if len(result) == 3:
            return (result[0], result[1], 0.0)
    return result


# ---------------------------------------------------------------------------
# Helper: summarize tool payloads and results for ledger
# ---------------------------------------------------------------------------

def _summarize_payload(payload: str, max_len: int = 120) -> str:
    """Condense a tool payload for ledger display."""
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        s = payload.strip()
        return s[:max_len] + "..." if len(s) > max_len else s

    if isinstance(data, dict):
        # For tuning configs: show key=value pairs compactly
        parts = []
        for k, v in sorted(data.items()):
            if isinstance(v, float):
                parts.append("{}={:.4g}".format(k, v))
            else:
                parts.append("{}={}".format(k, v))
        s = "{" + ", ".join(parts) + "}"
        return s[:max_len] + "..." if len(s) > max_len else s

    s = json.dumps(data, separators=(",", ":"))
    return s[:max_len] + "..." if len(s) > max_len else s


def _summarize_result(tool_name: str, result: Any) -> str:
    """Condense a tool result for ledger display."""
    if isinstance(result, tuple):
        if len(result) == 2:
            val, overhead = result
            if isinstance(val, (int, float)):
                return "perf={:.6f} (cost={:.0f}s)".format(val, overhead)
            # String output (search/audit)
            s = str(val)
            if len(s) > 80:
                s = s[:77] + "..."
            return s
        if len(result) == 3:
            output, perf, overhead = result
            if perf is not None:
                return "perf={:.6f} (cost={:.0f}s)".format(perf, overhead)
            s = str(output)
            if len(s) > 80:
                s = s[:77] + "..."
            return s
    return str(result)[:80]


# ---------------------------------------------------------------------------
# Caching-only wrapper (no ledger)
# ---------------------------------------------------------------------------

def wrap_tools_with_cache(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Dict[str, Callable]:
    """Wrap tool functions to use a shared cache.

    On cache hit, returns the cached result with overhead zeroed out.
    On cache miss, calls the original tool, stores the result, and returns it.

    Args:
        tools: Dict of tool_name -> callable (matches react_loop's ToolFn).
        cache: Shared cache instance.
        clock: Optional AgentClock for time-gated visibility.
        overhead_scale: Scale factor for overhead when computing completion_time.

    Returns:
        New tools dict with wrapped callables.
    """
    wrapped = {}
    for tool_name, func in tools.items():
        wrapped[tool_name] = _make_cached_wrapper(
            tool_name, func, cache,
            clock=clock, overhead_scale=overhead_scale,
        )
    return wrapped


def _make_cached_wrapper(
    tool_name: str,
    original_fn: Callable,
    cache: SharedObservationCache,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Callable:
    """Create a wrapper that checks cache before calling the original tool."""
    def wrapper(payload: str) -> Any:
        vb = clock.now if clock is not None else None
        cached = cache.get(tool_name, payload, visible_before=vb)
        if cached is not None:
            return _zero_overhead(cached)
        result = original_fn(payload)
        raw_overhead = _extract_overhead_from_result(result)
        ct = (clock.now + raw_overhead * overhead_scale) if clock is not None else 0.0
        cache.put(tool_name, payload, result, completion_time=ct)
        return result
    return wrapper


# ---------------------------------------------------------------------------
# PoolAct wrapper (caching + ledger recording)
# ---------------------------------------------------------------------------

def wrap_tools_with_poolact(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    ledger: SharedExplorationLedger,
    agent_id: int,
) -> Dict[str, Callable]:
    """Wrap tool functions with caching + ledger recording for PoolAct.

    Combines two layers:
    - Layer 0 (caching): exact-match deduplication with zero-cost hits
    - Layer 1 (ledger): records every observation for context injection

    Args:
        tools: Dict of tool_name -> callable.
        cache: Shared cache instance.
        ledger: Shared ledger instance.
        agent_id: Identifier for this agent (used in ledger entries).

    Returns:
        New tools dict with wrapped callables.
    """
    wrapped = {}
    for tool_name, func in tools.items():
        wrapped[tool_name] = _make_poolact_wrapper(
            tool_name, func, cache, ledger, agent_id,
        )
    return wrapped


def _make_poolact_wrapper(
    tool_name: str,
    original_fn: Callable,
    cache: SharedObservationCache,
    ledger: SharedExplorationLedger,
    agent_id: int,
) -> Callable:
    """Create a wrapper with caching + ledger recording."""
    def wrapper(payload: str) -> Any:
        payload_summary = _summarize_payload(payload)

        cached = cache.get(tool_name, payload)
        if cached is not None:
            result = _zero_overhead(cached)
            result_summary = _summarize_result(tool_name, cached)
            ledger.record(
                agent_id, tool_name, payload_summary,
                result_summary, cache_hit=True,
            )
            return result

        result = original_fn(payload)
        cache.put(tool_name, payload, result)
        result_summary = _summarize_result(tool_name, result)
        ledger.record(
            agent_id, tool_name, payload_summary,
            result_summary, cache_hit=False,
        )
        return result
    return wrapper


# ---------------------------------------------------------------------------
# Observation augmenter for PoolAct context injection
# ---------------------------------------------------------------------------

def make_ledger_augmenter(
    ledger: SharedExplorationLedger,
) -> Callable[[str], str]:
    """Create an observation_augmenter that appends the shared ledger.

    Pass the returned function as ``observation_augmenter`` to
    ``run_react_loop()`` to inject the ledger into each agent's
    observation context after every tool call.

    Args:
        ledger: Shared ledger instance.

    Returns:
        A callable ``(observation: str) -> str`` that appends the ledger.
    """
    def augmenter(observation: str) -> str:
        ledger_text = ledger.format_for_injection()
        if ledger_text:
            return "{}\n\n{}".format(observation, ledger_text)
        return observation
    return augmenter


# ---------------------------------------------------------------------------
# SharedExplorationGraph (Layer 2: graph-based context injection)
# ---------------------------------------------------------------------------

_DOC_ID_RE = re.compile(r"doc_id=(\d+)")


@dataclass
class SearchNode:
    """A search_meta query node in the exploration graph."""
    query: str
    visited_by: Set[int] = field(default_factory=set)
    visits: int = 0
    returned_doc_ids: List[int] = field(default_factory=list)
    completion_time: float = float("inf")


@dataclass
class FetchNode:
    """A fetch_doc node, merged by doc_id (regardless of query)."""
    doc_id: int
    title: str = ""
    content_snippet: str = ""  # First ~100 chars of content
    visited_by: Set[int] = field(default_factory=set)
    visits: int = 0
    completion_time: float = float("inf")


@dataclass
class EndNode:
    """An agent's final answer."""
    answer: str
    by: Set[int] = field(default_factory=set)


@dataclass
class EvalNode:
    """A config evaluation node for tuning tasks."""
    config_key: str  # Canonical JSON of config (for dedup)
    config_display: str  # Compact display string
    perf: Optional[float] = None  # None if error/invalid
    cost: float = 0.0
    visited_by: Set[int] = field(default_factory=set)
    visits: int = 0
    completion_time: float = float("inf")


@dataclass
class GraphEdge:
    """Directed edge from one node to another, with traversal count."""
    source: str  # Node key
    target: str  # Node key
    count: int = 0
    agents: Set[int] = field(default_factory=set)


class SharedExplorationGraph:
    """Thread-safe graph tracking search_meta and fetch_doc operations.

    Nodes:
      - S:"query" — search_meta calls with returned doc_ids
      - F:doc=ID — fetch_doc calls merged by doc_id
      - END:"answer" — agent final answers

    Edges: directed transitions with [Nx] traversal counts.

    Injected into LLM context before each turn so agents can:
    (1) avoid repeating work, (2) follow promising paths,
    (3) explore untried branches.
    """

    def __init__(
        self,
        n_agents: int = 8,
        max_content_len: int = 100,
        diversity_mode: bool = False,
    ):
        self._lock = threading.Lock()
        self._n_agents = n_agents
        self._max_content_len = max_content_len
        self._diversity_mode = diversity_mode

        # Nodes
        self._search_nodes: Dict[str, SearchNode] = {}  # query -> node
        self._fetch_nodes: Dict[int, FetchNode] = {}    # doc_id -> node
        self._end_nodes: Dict[str, EndNode] = {}        # answer -> node
        self._eval_nodes: Dict[str, EvalNode] = {}      # config_key -> node

        # Edges: (source_key, target_key) -> GraphEdge
        self._edges: Dict[Tuple[str, str], GraphEdge] = {}

        # Per-agent state: last node visited (for edge tracking)
        self._agent_last_node: Dict[int, str] = {}

    def _search_key(self, query: str) -> str:
        return 'S:"{}"'.format(query)

    def _fetch_key(self, doc_id: int) -> str:
        return "F:doc={}".format(doc_id)

    def _end_key(self, answer: str) -> str:
        short = answer[:60].replace('"', "'")
        return 'END:"{}"'.format(short)

    def _eval_key(self, config_key: str) -> str:
        return "E:{}".format(config_key[:80])

    def _add_edge(self, source: str, target: str, agent_id: int) -> None:
        """Add or increment an edge. Caller must hold _lock."""
        key = (source, target)
        if key not in self._edges:
            self._edges[key] = GraphEdge(source=source, target=target)
        self._edges[key].count += 1
        self._edges[key].agents.add(agent_id)

    def record_search_meta(
        self,
        agent_id: int,
        query: str,
        returned_doc_ids: List[int],
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Record a search_meta call."""
        with self._lock:
            skey = self._search_key(query)
            if query not in self._search_nodes:
                self._search_nodes[query] = SearchNode(
                    query=query,
                    returned_doc_ids=returned_doc_ids[:5],
                )
            node = self._search_nodes[query]
            node.visited_by.add(agent_id)
            node.visits += 1
            node.completion_time = min(node.completion_time, completion_time)
            # Update returned_doc_ids if we got more results
            if len(returned_doc_ids) > len(node.returned_doc_ids):
                node.returned_doc_ids = returned_doc_ids[:5]

            # Add edge from previous node
            prev = self._agent_last_node.get(agent_id)
            if prev:
                self._add_edge(prev, skey, agent_id)
            self._agent_last_node[agent_id] = skey

    def record_fetch_doc(
        self,
        agent_id: int,
        doc_id: int,
        title: str,
        content_snippet: str,
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Record a fetch_doc call, merged by doc_id."""
        with self._lock:
            fkey = self._fetch_key(doc_id)
            if doc_id not in self._fetch_nodes:
                self._fetch_nodes[doc_id] = FetchNode(
                    doc_id=doc_id,
                    title=title,
                    content_snippet=content_snippet[:self._max_content_len],
                )
            node = self._fetch_nodes[doc_id]
            node.visited_by.add(agent_id)
            node.visits += 1
            node.completion_time = min(node.completion_time, completion_time)

            # Add edge from previous node
            prev = self._agent_last_node.get(agent_id)
            if prev:
                self._add_edge(prev, fkey, agent_id)
            self._agent_last_node[agent_id] = fkey

    def record_end(self, agent_id: int, answer: str) -> None:
        """Record an agent's final answer."""
        with self._lock:
            ekey = self._end_key(answer)
            if answer not in self._end_nodes:
                self._end_nodes[answer] = EndNode(answer=answer)
            self._end_nodes[answer].by.add(agent_id)

            # Add edge from last node to END
            prev = self._agent_last_node.get(agent_id)
            if prev:
                self._add_edge(prev, ekey, agent_id)

    def record_evaluate_config(
        self,
        agent_id: int,
        config_key: str,
        config_display: str,
        perf: Optional[float],
        cost: float,
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Record an evaluate_config call for tuning tasks.

        Args:
            agent_id: Agent identifier.
            config_key: Canonical JSON of the config (for dedup).
            config_display: Compact display string.
            perf: Performance value (None if error/invalid).
            cost: Overhead time cost.
            completion_time: Simulated time when this eval completed.
        """
        with self._lock:
            ekey = self._eval_key(config_key)
            if config_key not in self._eval_nodes:
                self._eval_nodes[config_key] = EvalNode(
                    config_key=config_key,
                    config_display=config_display,
                    perf=perf,
                    cost=cost,
                )
            node = self._eval_nodes[config_key]
            node.visited_by.add(agent_id)
            node.visits += 1
            node.completion_time = min(node.completion_time, completion_time)
            # Update perf if we got a better result
            if perf is not None and (node.perf is None or perf > node.perf):
                node.perf = perf

            # Add edge from previous node
            prev = self._agent_last_node.get(agent_id)
            if prev:
                self._add_edge(prev, ekey, agent_id)
            self._agent_last_node[agent_id] = ekey

    def format_for_injection(
        self,
        *,
        visible_before: Optional[float] = None,
    ) -> str:
        """Format the graph for LLM context injection.

        In default mode: shows full graph with content snippets.
        In diversity mode: hides content snippets, adds diversity
        instructions, and highlights unfetched document leads.

        Args:
            visible_before: If set, only include nodes whose
                completion_time <= visible_before.  ``None`` (default)
                means see everything (backward compat).

        Returns empty string if no nodes recorded.
        """
        with self._lock:
            search_nodes = dict(self._search_nodes)
            fetch_nodes = dict(self._fetch_nodes)
            end_nodes = dict(self._end_nodes)
            eval_nodes = dict(self._eval_nodes)
            edges = dict(self._edges)

        # Apply time-gating filter if requested
        if visible_before is not None:
            search_nodes = {
                k: v for k, v in search_nodes.items()
                if v.completion_time <= visible_before
            }
            fetch_nodes = {
                k: v for k, v in fetch_nodes.items()
                if v.completion_time <= visible_before
            }
            eval_nodes = {
                k: v for k, v in eval_nodes.items()
                if v.completion_time <= visible_before
            }
            # END nodes have no completion_time — hide them when
            # time-gating is active to prevent future-answer leakage.
            end_nodes = {}
            # Filter edges: both endpoints must be visible
            visible_keys = set()
            for q in search_nodes:
                visible_keys.add(self._search_key(q))
            for did in fetch_nodes:
                visible_keys.add(self._fetch_key(did))
            for ck in eval_nodes:
                visible_keys.add(self._eval_key(ck))
            edges = {
                k: v for k, v in edges.items()
                if k[0] in visible_keys and k[1] in visible_keys
            }

        if not search_nodes and not fetch_nodes and not eval_nodes:
            return ""

        # Tuning mode: only eval nodes present
        if eval_nodes and not search_nodes and not fetch_nodes:
            if self._diversity_mode:
                return self._format_tuning_diversity(eval_nodes, end_nodes, edges)
            return self._format_tuning_default(eval_nodes, end_nodes, edges)

        if self._diversity_mode:
            return self._format_diversity(
                search_nodes, fetch_nodes, end_nodes, edges,
            )
        return self._format_default(
            search_nodes, fetch_nodes, end_nodes, edges,
        )

    def _format_default(
        self,
        search_nodes: Dict[str, SearchNode],
        fetch_nodes: Dict[int, FetchNode],
        end_nodes: Dict[str, EndNode],
        edges: Dict[Tuple[str, str], GraphEdge],
    ) -> str:
        """Original v2 format with full content."""
        lines = [
            "[Shared Exploration Graph]",
            "You are one of {} agents exploring in parallel.".format(
                self._n_agents
            ),
            "Use this to avoid redundant work and leverage cached observations.",
            "Cached fetches cost 0s.",
            "",
            "=== Nodes ===",
        ]

        # Search nodes (sorted by visit count desc, then query)
        for query, node in sorted(
            search_nodes.items(),
            key=lambda x: (-x[1].visits, x[0]),
        ):
            lines.append("")
            lines.append('  S:"{}"'.format(query))
            lines.append(
                "    visited_by=[{}]  visits={}".format(
                    ",".join(str(a) for a in sorted(node.visited_by)),
                    node.visits,
                )
            )
            if node.returned_doc_ids:
                lines.append(
                    "    returned_docs=[{}]".format(
                        ",".join(str(d) for d in node.returned_doc_ids)
                    )
                )

        # Fetch nodes (sorted by visit count desc, then doc_id)
        for doc_id, node in sorted(
            fetch_nodes.items(),
            key=lambda x: (-x[1].visits, x[0]),
        ):
            lines.append("")
            lines.append("  F:doc={}".format(doc_id))
            lines.append(
                "    visited_by=[{}]  visits={}".format(
                    ",".join(str(a) for a in sorted(node.visited_by)),
                    node.visits,
                )
            )
            content = ""
            if node.title:
                content = '"{}"'.format(node.title)
                if node.content_snippet:
                    content += " -- " + node.content_snippet
            elif node.content_snippet:
                content = node.content_snippet
            if content:
                lines.append("    content: {}".format(content))

        # End nodes
        for answer, node in sorted(
            end_nodes.items(),
            key=lambda x: -len(x[1].by),
        ):
            lines.append("")
            short = answer[:60].replace('"', "'")
            lines.append('  END:"{}"'.format(short))
            lines.append(
                "    by=[{}]".format(
                    ",".join(str(a) for a in sorted(node.by))
                )
            )

        # Edges section
        lines.append("")
        lines.append("=== Edges ===")
        lines.append("")

        for (src, tgt), edge in sorted(
            edges.items(),
            key=lambda x: -x[1].count,
        ):
            if edge.count > 1:
                lines.append("  {} --> {} [{}x]".format(src, tgt, edge.count))
            else:
                lines.append("  {} --> {}".format(src, tgt))

        # Warnings section: detect loops
        warnings = self._detect_warnings(search_nodes)
        if warnings:
            lines.append("")
            lines.append("=== Warnings ===")
            for w in warnings:
                lines.append(w)

        return "\n".join(lines)

    def _format_diversity(
        self,
        search_nodes: Dict[str, SearchNode],
        fetch_nodes: Dict[int, FetchNode],
        end_nodes: Dict[str, EndNode],
        edges: Dict[Tuple[str, str], GraphEdge],
    ) -> str:
        """Diversity-encouraging format that prevents herding.

        Key differences from default:
        - No content snippets in F:doc nodes (title only)
        - Adds diversity instructions
        - Highlights unfetched document leads
        - Shows END nodes and edges for full topology
        """
        fetched_ids = set(fetch_nodes.keys())

        # Collect unfetched doc_ids from search results
        unfetched_leads = []
        for query, node in search_nodes.items():
            for doc_id in node.returned_doc_ids:
                if doc_id not in fetched_ids and doc_id not in unfetched_leads:
                    unfetched_leads.append(doc_id)

        lines = [
            "[Shared Exploration Graph]",
            "You are one of {} agents exploring in parallel.".format(
                self._n_agents
            ),
            "IMPORTANT: Your unique value is exploring DIFFERENT paths.",
            "Try queries and documents that other agents have NOT tried.",
            "Cached fetches cost 0s.",
            "",
            "=== Explored ===",
        ]

        # Search nodes — compact format, no returned_docs
        for query, node in sorted(
            search_nodes.items(),
            key=lambda x: (-x[1].visits, x[0]),
        ):
            lines.append(
                '  S:"{}" ({}x by [{}])'.format(
                    query,
                    node.visits,
                    ",".join(str(a) for a in sorted(node.visited_by)),
                )
            )

        # Fetch nodes — title only, no content snippet
        for doc_id, node in sorted(
            fetch_nodes.items(),
            key=lambda x: (-x[1].visits, x[0]),
        ):
            title_part = ""
            if node.title:
                title_part = ' "{}"'.format(node.title)
            lines.append(
                "  F:doc={}{} ({}x by [{}])".format(
                    doc_id,
                    title_part,
                    node.visits,
                    ",".join(str(a) for a in sorted(node.visited_by)),
                )
            )

        # End nodes (answers submitted by other agents)
        if end_nodes:
            lines.append("")
            lines.append("=== Endpoints ===")
            for answer, node in sorted(
                end_nodes.items(),
                key=lambda x: -len(x[1].by),
            ):
                short = answer[:60].replace('"', "'")
                lines.append('  END:"{}" by=[{}]'.format(
                    short,
                    ",".join(str(a) for a in sorted(node.by)),
                ))

        # Edges
        if edges:
            lines.append("")
            lines.append("=== Edges ===")
            for (src, tgt), edge in sorted(
                edges.items(),
                key=lambda x: -x[1].count,
            ):
                if edge.count > 1:
                    lines.append(
                        "  {} --> {} [{}x]".format(src, tgt, edge.count)
                    )
                else:
                    lines.append("  {} --> {}".format(src, tgt))

        # Unfetched leads section
        if unfetched_leads:
            lines.append("")
            lines.append("=== Unfetched Leads ===")
            lines.append(
                "These docs appeared in search results but nobody "
                "fetched them yet:"
            )
            lines.append(
                "  [{}]".format(
                    ",".join(str(d) for d in unfetched_leads[:15])
                )
            )

        # Warnings
        warnings = self._detect_warnings(search_nodes)
        if warnings:
            lines.append("")
            lines.append("=== Warnings ===")
            for w in warnings:
                lines.append(w)

        return "\n".join(lines)

    def _format_tuning_default(
        self,
        eval_nodes: Dict[str, EvalNode],
        end_nodes: Dict[str, EndNode],
        edges: Dict[Tuple[str, str], GraphEdge],
    ) -> str:
        """Default format for tuning: show all configs with perf + cost."""
        lines = [
            "[Shared Exploration Graph]",
            "You are one of {} agents tuning in parallel.".format(
                self._n_agents
            ),
            "Use this to avoid redundant configs and learn from others' results.",
            "Cached evaluations cost 0s.",
            "",
            "=== Evaluated Configs ===",
        ]

        # Sort by perf descending (None last), then by visits
        sorted_nodes = sorted(
            eval_nodes.values(),
            key=lambda n: (n.perf is not None, n.perf or 0.0, n.visits),
            reverse=True,
        )

        for node in sorted_nodes:
            perf_str = "perf={:.6f}".format(node.perf) if node.perf is not None else "INVALID"
            lines.append(
                "  {} -> {}, cost={:.0f}s ({}x by [{}])".format(
                    node.config_display,
                    perf_str,
                    node.cost,
                    node.visits,
                    ",".join(str(a) for a in sorted(node.visited_by)),
                )
            )

        # Best so far
        best = max(
            (n for n in eval_nodes.values() if n.perf is not None),
            key=lambda n: n.perf,
            default=None,
        )
        if best is not None:
            lines.append("")
            lines.append("=== Best So Far ===")
            lines.append(
                "  perf={:.6f} {} (by agent {})".format(
                    best.perf,
                    best.config_display,
                    ",".join(str(a) for a in sorted(best.visited_by)),
                )
            )

        # End nodes
        for answer, node in sorted(
            end_nodes.items(),
            key=lambda x: -len(x[1].by),
        ):
            lines.append("")
            short = answer[:60].replace('"', "'")
            lines.append('  END:"{}"'.format(short))
            lines.append(
                "    by=[{}]".format(
                    ",".join(str(a) for a in sorted(node.by))
                )
            )

        return "\n".join(lines)

    def _format_tuning_diversity(
        self,
        eval_nodes: Dict[str, EvalNode],
        end_nodes: Dict[str, EndNode],
        edges: Dict[Tuple[str, str], GraphEdge],
    ) -> str:
        """Informational format for tuning: shared landscape, soft diversity.

        Shows configs with performance so agents can learn the landscape.
        Explicitly tells agents that re-evaluating cached configs costs 0s,
        encouraging natural exploitation of cache hits while still allowing
        exploration.  Avoids aggressive "try DIFFERENT" instructions that
        prevent cache hits under tight budgets.
        """
        lines = [
            "[Shared Evaluation History]",
            "You are one of {} agents working in parallel.".format(
                self._n_agents
            ),
            "Below are ALL actions evaluated so far (by any agent).",
            "Re-submitting a previously-tried action costs 0s (cached).",
            "Use these results to make informed decisions.",
            "",
            "=== Actions Evaluated ===",
        ]

        # Sort by perf descending (None last)
        sorted_nodes = sorted(
            eval_nodes.values(),
            key=lambda n: (n.perf is not None, n.perf or 0.0),
            reverse=True,
        )

        for node in sorted_nodes:
            perf_str = "{:.6f}".format(node.perf) if node.perf is not None else "INVALID"
            lines.append(
                "  {} -> {} (by [{}])".format(
                    node.config_display,
                    perf_str,
                    ",".join(str(a) for a in sorted(node.visited_by)),
                )
            )

        # End nodes
        if end_nodes:
            lines.append("")
            lines.append("=== Endpoints ===")
            for answer, node in sorted(
                end_nodes.items(),
                key=lambda x: -len(x[1].by),
            ):
                short = answer[:60].replace('"', "'")
                lines.append('  END:"{}" by=[{}]'.format(
                    short,
                    ",".join(str(a) for a in sorted(node.by)),
                ))

        # Edges
        if edges:
            lines.append("")
            lines.append("=== Edges ===")
            for (src, tgt), edge in sorted(
                edges.items(),
                key=lambda x: -x[1].count,
            ):
                if edge.count > 1:
                    lines.append(
                        "  {} --> {} [{}x]".format(src, tgt, edge.count)
                    )
                else:
                    lines.append("  {} --> {}".format(src, tgt))

        # Summary stats — audit vs tuning have different goals
        valid = [n for n in eval_nodes.values() if n.perf is not None]
        is_audit = any(
            n.config_display.startswith("nda:") for n in eval_nodes.values()
        )
        if valid and is_audit:
            correct = sum(1 for n in valid if n.perf == 1.0)
            incomplete = sum(1 for n in valid if n.perf == 0.5)
            irrelevant = sum(1 for n in valid if n.perf == 0.0)
            n_unique_ndas = len(set(
                n.config_display.split("ev:")[0].strip()
                for n in eval_nodes.values()
            ))
            lines.append("")
            lines.append(
                "=== Progress: {}/{} NDAs attempted, {} Correct, "
                "{} Incomplete, {} Irrelevant ===".format(
                    n_unique_ndas, n_unique_ndas,
                    correct, incomplete, irrelevant,
                )
            )
            lines.append(
                "Goal: get ALL NDAs to Correct. Re-submitting a "
                "cached action costs 0s."
            )
        elif valid:
            best_perf = max(n.perf for n in valid)
            n_unique = len(eval_nodes)
            lines.append("")
            lines.append(
                "Best score so far: {:.6f} from {} unique actions.".format(
                    best_perf, n_unique,
                )
            )
            lines.append(
                "You can re-submit a known-good action (free) or "
                "try new approaches to improve."
            )

        return "\n".join(lines)

    @staticmethod
    def _detect_warnings(
        search_nodes: Dict[str, SearchNode],
    ) -> List[str]:
        """Detect loop warnings in search nodes."""
        warnings = []
        for query, node in search_nodes.items():
            if node.visits > len(node.visited_by):
                warnings.append(
                    '  LOOP: S:"{}" -- {} visits by {} agents'.format(
                        query, node.visits, len(node.visited_by),
                    )
                )
        return warnings

    def stats(self) -> Dict[str, Any]:
        """Return graph statistics."""
        with self._lock:
            return {
                "search_nodes": len(self._search_nodes),
                "fetch_nodes": len(self._fetch_nodes),
                "eval_nodes": len(self._eval_nodes),
                "end_nodes": len(self._end_nodes),
                "edges": len(self._edges),
                "total_visits": sum(
                    n.visits for n in self._search_nodes.values()
                ) + sum(
                    n.visits for n in self._fetch_nodes.values()
                ) + sum(
                    n.visits for n in self._eval_nodes.values()
                ),
            }


# ---------------------------------------------------------------------------
# Helper: parse search_meta and fetch_doc results for graph recording
# ---------------------------------------------------------------------------

def _parse_search_meta_result(result_str: str) -> List[int]:
    """Extract doc_ids from search_meta result string."""
    return [int(m.group(1)) for m in _DOC_ID_RE.finditer(result_str)]


def _parse_fetch_doc_result(result_str: str) -> Tuple[int, str, str]:
    """Extract (doc_id, title, snippet) from fetch_doc result string.

    Returns:
        (doc_id, title, first_chunk_snippet)
    """
    doc_id = -1
    title = ""
    snippet = ""
    # Parse doc_id
    m = _DOC_ID_RE.search(result_str)
    if m:
        doc_id = int(m.group(1))
    # Parse title
    tm = re.search(r"title=([^|]+)", result_str)
    if tm:
        title = tm.group(1).strip()
    # Extract first chunk as snippet
    lines = result_str.split("\n")
    for line in lines:
        if line.startswith("- "):
            snippet = line[2:100]
            break
    return doc_id, title, snippet


def _parse_search_meta_payload(payload_str: str) -> str:
    """Extract query from search_meta payload."""
    try:
        data = json.loads(payload_str)
        return str(data.get("query", "")).strip()
    except (json.JSONDecodeError, TypeError, AttributeError):
        return payload_str.strip()


def _parse_fetch_doc_payload(payload_str: str) -> Tuple[str, int]:
    """Extract (query, doc_id) from fetch_doc payload."""
    try:
        data = json.loads(payload_str)
        query = str(data.get("query", "")).strip()
        doc_id = int(data.get("doc_id", -1))
        return query, doc_id
    except (json.JSONDecodeError, TypeError, ValueError):
        return "", -1


def _parse_evaluate_config(
    payload_str: str, result_str: str,
) -> Tuple[str, str, Optional[float]]:
    """Parse evaluate_config payload and result for graph recording.

    Returns:
        (config_key, config_display, perf) where:
        - config_key: canonical JSON string (for dedup)
        - config_display: compact display string
        - perf: float if valid result, None if error/invalid
    """
    # Parse config from payload
    try:
        data = json.loads(payload_str)
    except (json.JSONDecodeError, TypeError):
        return "", "", None

    if isinstance(data, dict):
        config_key = json.dumps(data, sort_keys=True, separators=(",", ":"))
        # Compact display: abbreviate long configs
        items = sorted(data.items())
        if len(items) <= 6:
            config_display = "{" + ",".join(
                "{}:{}".format(k, v) for k, v in items
            ) + "}"
        else:
            shown = items[:4]
            config_display = "{" + ",".join(
                "{}:{}".format(k, v) for k, v in shown
            ) + ",...+" + str(len(items) - 4) + "}"
    elif isinstance(data, list):
        config_key = json.dumps(data, separators=(",", ":"))
        config_display = "[" + ",".join(str(v) for v in data[:6])
        if len(data) > 6:
            config_display += ",...+" + str(len(data) - 6)
        config_display += "]"
    else:
        return "", "", None

    # Parse perf from result
    perf = None
    # Try to parse as float directly (evaluate_config returns perf float)
    try:
        val = float(result_str)
        # perf=0.0 means invalid/degenerate config in HPOBench
        if val > 0.0:
            perf = val
    except (ValueError, TypeError):
        pass
    # Try to extract perf= pattern
    if perf is None:
        m = re.search(r"perf=([\d.]+)", result_str)
        if m:
            perf_val = float(m.group(1))
            if perf_val > 0.0:
                perf = perf_val

    return config_key, config_display, perf


# ---------------------------------------------------------------------------
# PoLACT wrapper (caching + graph recording)
# ---------------------------------------------------------------------------

def wrap_tools_with_polact(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Dict[str, Callable]:
    """Wrap tool functions with caching + graph recording for PoLACT.

    Combines:
    - Layer 0 (caching): exact-match deduplication with zero-cost hits
    - Layer 2 (graph): records exploration topology for context injection

    Args:
        tools: Dict of tool_name -> callable.
        cache: Shared cache instance.
        graph: Shared exploration graph instance.
        agent_id: Identifier for this agent.
        clock: Optional AgentClock for time-gated visibility.
        overhead_scale: Scale factor for overhead when computing completion_time.

    Returns:
        New tools dict with wrapped callables.
    """
    wrapped = {}
    for tool_name, func in tools.items():
        wrapped[tool_name] = _make_polact_wrapper(
            tool_name, func, cache, graph, agent_id,
            clock=clock, overhead_scale=overhead_scale,
        )
    return wrapped


def _make_polact_wrapper(
    tool_name: str,
    original_fn: Callable,
    cache: SharedObservationCache,
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Callable:
    """Create a wrapper with caching + graph recording."""
    def wrapper(payload: str) -> Any:
        vb = clock.now if clock is not None else None
        # Check cache first
        cached = cache.get(tool_name, payload, visible_before=vb)
        if cached is not None:
            result = _zero_overhead(cached)
            # Record in graph — pass inf so min() won't lower existing ct
            _record_in_graph(
                graph, agent_id, tool_name, payload, cached,
                completion_time=float("inf"),
            )
            return result

        # Cache miss — call original tool
        result = original_fn(payload)
        raw_overhead = _extract_overhead_from_result(result)
        ct = (clock.now + raw_overhead * overhead_scale) if clock is not None else 0.0
        cache.put(tool_name, payload, result, completion_time=ct)
        # Record in graph
        _record_in_graph(
            graph, agent_id, tool_name, payload, result,
            completion_time=ct,
        )
        return result
    return wrapper


def _record_in_graph(
    graph: SharedExplorationGraph,
    agent_id: int,
    tool_name: str,
    payload: str,
    result: Any,
    *,
    completion_time: float = 0.0,
) -> None:
    """Record a tool call in the exploration graph."""
    # Extract the string result from the tuple
    result_str = ""
    overhead = 0.0
    if isinstance(result, tuple):
        result_str = str(result[0]) if result else ""
        if len(result) >= 2:
            try:
                overhead = float(result[-1])
            except (TypeError, ValueError):
                pass
    else:
        result_str = str(result)

    if tool_name == "search_meta":
        query = _parse_search_meta_payload(payload)
        doc_ids = _parse_search_meta_result(result_str)
        if query:
            graph.record_search_meta(
                agent_id, query, doc_ids,
                completion_time=completion_time,
            )

    elif tool_name == "fetch_doc":
        _query, doc_id = _parse_fetch_doc_payload(payload)
        if doc_id >= 0:
            _, title, snippet = _parse_fetch_doc_result(result_str)
            graph.record_fetch_doc(
                agent_id, doc_id, title, snippet,
                completion_time=completion_time,
            )

    elif tool_name == "evaluate_config":
        config_key, config_display, perf = _parse_evaluate_config(
            payload, result_str,
        )
        if config_key:
            graph.record_evaluate_config(
                agent_id, config_key, config_display, perf, overhead,
                completion_time=completion_time,
            )

    elif tool_name == "human_feedback":
        config_key, config_display, perf = _parse_human_feedback(
            payload, result_str,
        )
        if config_key:
            graph.record_evaluate_config(
                agent_id, config_key, config_display, perf, overhead,
                completion_time=completion_time,
            )


def _parse_human_feedback(
    payload: str, result_str: str,
) -> Tuple[Optional[str], str, Optional[float]]:
    """Parse human_feedback payload and result for graph recording.

    Returns (config_key, config_display, perf) where:
    - config_key: canonical JSON of payload (for dedup)
    - config_display: compact display with nda_id, evidence, and
      the actual feedback label (Correct / Incomplete / Irrelevant)
    - perf: 1.0 for "Evidence Correct", 0.5 for "Incomplete", 0.0 otherwise
    """
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return None, "", None

    if not isinstance(data, dict):
        return None, "", None

    nda_id = data.get("nda_id", "?")
    evidence_ids = data.get("evidence_ids", [])
    config_key = json.dumps(data, sort_keys=True, separators=(",", ":"))

    # Determine human-readable feedback label for display
    perf: Optional[float] = None
    if "Evidence Correct" in result_str:
        perf = 1.0
    elif "Evidence Incomplete" in result_str:
        perf = 0.5
    elif "Irrelevant" in result_str:
        perf = 0.0

    # Include the raw feedback text in the display so agents
    # see "Correct" / "Incomplete | missing: ..." / "Irrelevant"
    # instead of opaque numeric scores.
    feedback = result_str.strip() if result_str else "?"
    config_display = "nda:{}  ev:{}  [{}]".format(
        nda_id, evidence_ids, feedback,
    )

    return config_key, config_display, perf


# ---------------------------------------------------------------------------
# Graph augmenter for PoLACT context injection
# ---------------------------------------------------------------------------

def make_graph_augmenter(
    graph: SharedExplorationGraph,
    *,
    clock: Optional[AgentClock] = None,
) -> Callable[[str], str]:
    """Create an observation_augmenter that appends the exploration graph.

    Pass the returned function as ``observation_augmenter`` to
    ``run_react_loop()`` to inject the graph into each agent's
    observation context after every tool call.

    Args:
        graph: Shared exploration graph instance.
        clock: Optional AgentClock for time-gated visibility.

    Returns:
        A callable ``(observation: str) -> str`` that appends the graph.
    """
    def augmenter(observation: str) -> str:
        vb = clock.now if clock is not None else None
        graph_text = graph.format_for_injection(visible_before=vb)
        if graph_text:
            return "{}\n\n{}".format(observation, graph_text)
        return observation
    return augmenter
