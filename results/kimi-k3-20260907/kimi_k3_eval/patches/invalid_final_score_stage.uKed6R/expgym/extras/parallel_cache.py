"""Shared cache and exploration graph used by PoolAct.

Provides:
- SharedObservationCache: thread-safe exact-match cache (zero-cost dedup)
- SharedExplorationLedger: records all observations for context injection
- SharedExplorationGraph: graph-based representation of parallel exploration
- wrap_tools_with_cache: caching-only tool wrapper
- wrap_tools_with_poolact: paper implementation (cache + graph + claims)
- wrap_tools_with_polact: backwards-compatible alias for the paper implementation
- wrap_tools_with_ledger: legacy flat-ledger experiment
- make_ledger_augmenter: creates observation_augmenter for react_loop
- make_graph_augmenter: creates observation_augmenter with graph injection
"""
from __future__ import annotations

import copy
import json
import re
import threading
import time
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

        Earliest simulated completion wins. Physical thread scheduling can
        differ from the simulated EEI timeline, so a later ``put`` may replace
        an entry when its completion time is earlier.
        """
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            if key in self._cache:
                existing_result, existing_ct = self._cache[key]
                if completion_time < existing_ct:
                    self._cache[key] = (result, completion_time)
                else:
                    self._cache[key] = (existing_result, existing_ct)
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
    """Legacy flat ledger retained for prototype compatibility."""

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

def _summarize_payload(payload: str) -> str:
    """Condense a tool payload for ledger/claim display.

    Never truncates dict payloads — agents need full configs to
    learn from others' choices.
    """
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return payload.strip()

    if isinstance(data, dict):
        parts = []
        for k, v in sorted(data.items()):
            if isinstance(v, float):
                parts.append("{}={:.4g}".format(k, v))
            else:
                parts.append("{}={}".format(k, v))
        return "{" + ", ".join(parts) + "}"

    return json.dumps(data, separators=(",", ":"))


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
        scaled_overhead = raw_overhead * overhead_scale
        # The ReAct loop owns the clock and advances it exactly once after
        # parsing the tool return.  The wrapper only predicts when this
        # result becomes visible on the simulated parallel timeline.
        ct = (clock.now + scaled_overhead) if clock is not None else 0.0
        cache.put(tool_name, payload, result, completion_time=ct)
        return result
    return wrapper


# ---------------------------------------------------------------------------
# Legacy ledger wrapper
# ---------------------------------------------------------------------------

def wrap_tools_with_ledger(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    ledger: SharedExplorationLedger,
    agent_id: int,
) -> Dict[str, Callable]:
    """Wrap tools with the legacy flat exploration ledger.

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
        wrapped[tool_name] = _make_ledger_wrapper(
            tool_name, func, cache, ledger, agent_id,
        )
    return wrapped


def _make_ledger_wrapper(
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
    """A search_meta or search query node in the exploration graph."""
    query: str
    visited_by: Set[int] = field(default_factory=set)
    visits: int = 0
    returned_doc_ids: List[int] = field(default_factory=list)
    article_title: str = ""  # For single-tool search (Phantom Wiki)
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


@dataclass
class ActionClaim:
    """A pending-or-completed claim on a tool action.

    Lifecycle: record_claim() sets start_time (completion_time=inf).
    complete_claim() sets completion_time when the tool finishes.

    Visibility from another agent at time *t*:
      - start_time > t  → invisible (hasn't started yet)
      - start_time ≤ t AND completion_time > t  → in-progress
      - completion_time ≤ t  → completed (cache handles this)
    """
    agent_id: int
    tool_name: str
    display: str          # Human-readable summary for graph injection
    start_time: float = 0.0
    completion_time: float = float("inf")


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

        # Pending claims: (tool_name, canonical_payload) -> [ActionClaim]
        # Used by the PoolAct wrapper to prevent duplicate work.
        self._claims: Dict[Tuple[str, str], List[ActionClaim]] = {}

    # ------------------------------------------------------------------
    # Claim helpers (shared canonical key with cache)
    # ------------------------------------------------------------------

    @staticmethod
    def _canonicalize(payload: str) -> str:
        """Canonicalize a JSON payload string for claim key matching."""
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            return payload
        if isinstance(data, dict):
            return json.dumps(data, sort_keys=True, separators=(",", ":"))
        if isinstance(data, list):
            return json.dumps(data, separators=(",", ":"))
        return payload

    @staticmethod
    def _claim_display(tool_name: str, payload: str) -> str:
        """Build a human-readable one-liner for a claim."""
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            data = None

        if tool_name == "search" and isinstance(data, dict):
            q = data.get("query", payload)
            return 'search "{}"'.format(str(q)[:60])
        if tool_name == "search_meta" and isinstance(data, dict):
            q = data.get("query", payload)
            return 'search_meta "{}"'.format(str(q)[:60])
        if tool_name == "human_feedback" and isinstance(data, dict):
            nda = data.get("nda_id", "?")
            evs = data.get("evidence_ids", [])
            return "verify nda:{} ev:{}".format(nda, evs)
        if tool_name == "evaluate_config":
            summary = _summarize_payload(payload)
            return "evaluate {}".format(summary)
        if tool_name == "fetch_doc" and isinstance(data, dict):
            doc_id = data.get("doc_id", "?")
            return "fetch doc={}".format(doc_id)
        return "{} {}".format(tool_name, _summarize_payload(payload))

    def record_claim(
        self,
        tool_name: str,
        payload: str,
        agent_id: int,
        *,
        start_time: float = 0.0,
    ) -> None:
        """Record that *agent_id* has started executing *tool_name(payload)*.

        Creates an ActionClaim with ``completion_time=inf`` (pending).
        """
        key = (tool_name, self._canonicalize(payload))
        display = self._claim_display(tool_name, payload)
        claim = ActionClaim(
            agent_id=agent_id,
            tool_name=tool_name,
            display=display,
            start_time=start_time,
        )
        with self._lock:
            self._claims.setdefault(key, []).append(claim)

    def has_pending_claim(
        self,
        tool_name: str,
        payload: str,
        agent_id: int,
    ) -> bool:
        """Return True if *agent_id* already has a pending claim."""
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            for claim in self._claims.get(key, []):
                if (claim.agent_id == agent_id
                        and claim.completion_time == float("inf")):
                    return True
        return False

    def complete_claim(
        self,
        tool_name: str,
        payload: str,
        agent_id: int,
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Mark *agent_id*'s pending claim as completed."""
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            for claim in reversed(self._claims.get(key, [])):
                if (claim.agent_id == agent_id
                        and claim.completion_time == float("inf")):
                    claim.completion_time = completion_time
                    break

    def is_in_progress_by_other(
        self,
        tool_name: str,
        payload: str,
        agent_id: int,
        *,
        visible_at: Optional[float] = None,
    ) -> bool:
        """Check if another agent has an in-progress claim for this action.

        Returns True if any **other** agent's claim satisfies:
          ``start_time <= visible_at``  AND  ``completion_time > visible_at``
        i.e. it has started but not yet finished from the observer's
        perspective.
        """
        key = (tool_name, self._canonicalize(payload))
        with self._lock:
            for claim in self._claims.get(key, []):
                if claim.agent_id == agent_id:
                    continue
                if visible_at is not None:
                    if claim.start_time > visible_at:
                        continue  # Hasn't started yet from my perspective
                    if claim.completion_time <= visible_at:
                        continue  # Already completed
                return True
        return False

    def get_visible_pending(
        self,
        *,
        visible_at: Optional[float] = None,
        agent_id: Optional[int] = None,
    ) -> List[ActionClaim]:
        """Return claims that appear in-progress to the observer.

        Used by ``format_for_injection`` to populate the 'In Progress'
        section of the graph display.
        """
        pending: List[ActionClaim] = []
        with self._lock:
            for claims in self._claims.values():
                for claim in claims:
                    if visible_at is not None:
                        if claim.start_time > visible_at:
                            continue
                        if claim.completion_time <= visible_at:
                            continue
                    # Optionally skip own claims (show only others')
                    if agent_id is not None and claim.agent_id == agent_id:
                        continue
                    pending.append(ActionClaim(
                        agent_id=claim.agent_id,
                        tool_name=claim.tool_name,
                        display=claim.display,
                        start_time=claim.start_time,
                        completion_time=claim.completion_time,
                    ))
        return pending

    # ------------------------------------------------------------------
    # Node key helpers
    # ------------------------------------------------------------------

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

    def record_search(
        self,
        agent_id: int,
        query: str,
        article_title: str,
        *,
        completion_time: float = 0.0,
    ) -> None:
        """Record a single-tool search call (Phantom Wiki V17).

        One node per query, storing the returned article title.
        """
        with self._lock:
            skey = self._search_key(query)
            if query not in self._search_nodes:
                self._search_nodes[query] = SearchNode(
                    query=query, article_title=article_title,
                )
            node = self._search_nodes[query]
            node.visited_by.add(agent_id)
            node.visits += 1
            node.completion_time = min(node.completion_time, completion_time)
            if not node.article_title and article_title:
                node.article_title = article_title

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
        agent_id: Optional[int] = None,
    ) -> str:
        """Format the graph for LLM context injection.

        In default mode: shows full graph with content snippets.
        In diversity mode: unified coverage-map format that frames
        shared results as explored territory and highlights gaps.

        Args:
            visible_before: If set, only include nodes whose
                completion_time <= visible_before.  ``None`` (default)
                means see everything (backward compat).
            agent_id: The viewing agent's ID.  Used in diversity mode
                to label own vs others' results.

        Returns empty string if no nodes recorded.
        """
        with self._lock:
            # Formatting happens after releasing the lock. Deep-copy mutable
            # nodes/sets so concurrent agents cannot mutate the snapshot while
            # it is being iterated.
            search_nodes = copy.deepcopy(self._search_nodes)
            fetch_nodes = copy.deepcopy(self._fetch_nodes)
            end_nodes = copy.deepcopy(self._end_nodes)
            eval_nodes = copy.deepcopy(self._eval_nodes)
            edges = copy.deepcopy(self._edges)

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

        # Collect visible pending claims
        pending_claims = self.get_visible_pending(
            visible_at=visible_before, agent_id=agent_id,
        )

        if not search_nodes and not fetch_nodes and not eval_nodes \
                and not pending_claims:
            return ""

        # Diversity mode: unified coverage-map format for all scenarios
        if self._diversity_mode:
            return self._format_unified(
                search_nodes, fetch_nodes, eval_nodes,
                end_nodes, edges,
                agent_id=agent_id,
                pending_claims=pending_claims,
            )

        # Non-diversity mode: original formats
        if eval_nodes and not search_nodes and not fetch_nodes:
            return self._format_tuning_default(eval_nodes, end_nodes, edges)
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
            if node.article_title:
                lines.append(
                    '    article="{}"'.format(node.article_title)
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

    def _format_unified(
        self,
        search_nodes: Dict[str, SearchNode],
        fetch_nodes: Dict[int, FetchNode],
        eval_nodes: Dict[str, EvalNode],
        end_nodes: Dict[str, EndNode],
        edges: Dict[Tuple[str, str], GraphEdge],
        *,
        agent_id: Optional[int] = None,
        pending_claims: Optional[List[ActionClaim]] = None,
    ) -> str:
        """Unified coverage-map format for all scenarios in diversity mode.

        Design principles:
        1. Show IN-PROGRESS actions first (most actionable — avoid these)
        2. Show COMPLETED actions as explored territory
        3. Edges show exploration paths taken by agents
        4. COVERAGE GAP highlights what's NOT been tried
        5. Agent identity labels own vs others' work
        """
        agent_label = "Agent {}".format(agent_id) if agent_id is not None else "You"
        lines = [
            "[Parallel Exploration — {} of {}]".format(agent_label, self._n_agents),
            "You are one of {} agents solving this task in parallel.".format(
                self._n_agents
            ),
            "Shared state below shows what other agents have explored and are exploring.",
            "Use this to plan your next action — prioritize paths not yet explored.",
            "",
        ]

        pending = pending_claims or []
        has_search = bool(search_nodes)
        has_eval = bool(eval_nodes)
        is_audit = has_eval and any(
            n.config_display.startswith("nda:") for n in eval_nodes.values()
        )

        # === In Progress === (show before explored — most actionable)
        if pending:
            lines.append("== In Progress ==")
            for claim in sorted(pending, key=lambda c: c.start_time):
                lines.append(
                    "  {} [agent {}]".format(claim.display, claim.agent_id)
                )
            lines.append("")
        else:
            lines.append("== In Progress ==")
            lines.append("  None.")
            lines.append("")

        # === Already Explored ===
        lines.append("== Already Explored ==")

        if has_search:
            for query, node in sorted(
                search_nodes.items(),
                key=lambda x: (-x[1].visits, x[0]),
            ):
                who = sorted(node.visited_by)
                marker = " (you)" if agent_id in who else ""
                title_part = ' -> "{}"'.format(node.article_title) if node.article_title else ""
                lines.append(
                    '  search "{}"{} [agents {}]{}'.format(
                        query, title_part,
                        ",".join(str(a) for a in who), marker,
                    )
                )

        if fetch_nodes:
            for doc_id, node in sorted(fetch_nodes.items()):
                who = sorted(node.visited_by)
                marker = " (you)" if agent_id in who else ""
                title = ' "{}"'.format(node.title) if node.title else ""
                lines.append(
                    "  fetch doc={}{} [agents {}]{}".format(
                        doc_id,
                        title,
                        ",".join(str(a) for a in who),
                        marker,
                    )
                )

        if has_eval:
            # Group by NDA for audit, or show all for tuning
            sorted_nodes = sorted(
                eval_nodes.values(),
                key=lambda n: (n.perf is not None, n.perf or 0.0),
                reverse=True,
            )
            for node in sorted_nodes:
                who = sorted(node.visited_by)
                marker = " (you)" if agent_id in who else ""
                if is_audit:
                    lines.append(
                        "  {} [agents {}]{}".format(
                            node.config_display,
                            ",".join(str(a) for a in who), marker,
                        )
                    )
                else:
                    perf_str = "{:.6f}".format(node.perf) if node.perf is not None else "INVALID"
                    lines.append(
                        "  {} -> {} [agents {}]{}".format(
                            node.config_display, perf_str,
                            ",".join(str(a) for a in who), marker,
                        )
                    )

        if not has_search and not fetch_nodes and not has_eval:
            lines.append("  None completed yet.")

        # === Exploration Paths ===
        lines.append("")
        lines.append("== Exploration Paths ==")
        if edges:
            for (src, tgt), edge in sorted(
                edges.items(),
                key=lambda x: -x[1].count,
            ):
                agents_str = ",".join(str(a) for a in sorted(edge.agents))
                if edge.count > 1:
                    lines.append(
                        "  {} --> {} [{}x, agents {}]".format(
                            src, tgt, edge.count, agents_str,
                        )
                    )
                else:
                    lines.append(
                        "  {} --> {} [agents {}]".format(
                            src, tgt, agents_str,
                        )
                    )
        else:
            lines.append("  No multi-step paths recorded yet.")

        # === Coverage Gap ===
        lines.append("")
        lines.append("== Coverage Gap ==")

        if is_audit:
            # Show only how many NDAs have been attempted — no
            # Resolved/Unresolved judgments that reduce agent independence.
            attempted_ndas: set = set()
            for node in eval_nodes.values():
                disp = node.config_display
                nda_part = disp.split("ev:")[0].strip() if "ev:" in disp else disp
                attempted_ndas.add(nda_part)
            lines.append(
                "  {} NDAs attempted so far.".format(len(attempted_ndas))
            )
        elif has_eval:
            valid = [n for n in eval_nodes.values() if n.perf is not None]
            if valid:
                best = max(n.perf for n in valid)
                lines.append(
                    "  {} unique configs evaluated, best: {:.6f}".format(
                        len(eval_nodes), best,
                    )
                )
            else:
                lines.append("  No valid configuration found yet.")
        elif has_search:
            fetched_ids = set(fetch_nodes.keys())
            unfetched = []
            for node in search_nodes.values():
                for did in node.returned_doc_ids:
                    if did not in fetched_ids and did not in unfetched:
                        unfetched.append(did)
            lines.append(
                "  {} queries explored so far.".format(len(search_nodes))
            )
            if unfetched:
                lines.append(
                    "  Unfetched leads: [{}]".format(
                        ",".join(str(d) for d in unfetched[:10])
                    )
                )
            else:
                lines.append("  Try a query not listed above.")
        else:
            lines.append("  Select an action not listed above.")

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
            total_claims = sum(len(v) for v in self._claims.values())
            pending_claims = sum(
                1 for claims in self._claims.values()
                for c in claims if c.completion_time == float("inf")
            )
            return {
                "search_nodes": len(self._search_nodes),
                "fetch_nodes": len(self._fetch_nodes),
                "eval_nodes": len(self._eval_nodes),
                "end_nodes": len(self._end_nodes),
                "edges": len(self._edges),
                "total_claims": total_claims,
                "pending_claims": pending_claims,
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

def _parse_search_payload(payload_str: str) -> str:
    """Extract query from Phantom Wiki search payload."""
    try:
        data = json.loads(payload_str)
        return str(data.get("query", "")).strip()
    except (json.JSONDecodeError, TypeError, AttributeError):
        return payload_str.strip()


def _parse_search_result_title(result_str: str) -> str:
    """Extract article title from Phantom Wiki search result.

    Format: 'Article: <title>\\n\\n<content>'
    """
    if result_str.startswith("Article: "):
        first_line = result_str.split("\n", 1)[0]
        return first_line[len("Article: "):].strip()
    return ""


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
        items = sorted(data.items())
        config_display = "{" + ",".join(
            "{}:{}".format(k, v) for k, v in items
        ) + "}"
    elif isinstance(data, list):
        config_key = json.dumps(data, separators=(",", ":"))
        config_display = "[" + ",".join(str(v) for v in data) + "]"
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
# PoolAct wrapper (caching + graph recording)
# ---------------------------------------------------------------------------

def wrap_tools_with_poolact(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Dict[str, Callable]:
    """Wrap tools with the PoolAct strategy described in the paper.

    Combines:
    - Layer 0 (caching): exact-match deduplication with zero-cost hits
    - Layer 2 (graph): records exploration topology for context injection
    - Layer 3 (claims): pending-action claims for "In Progress" visibility

    Every tool call records a pending claim **before** execution and
    marks it completed **after**.  This populates the graph's
    "In Progress" section, giving other agents soft guidance about
    what's currently being worked on.  No hard blocking — the LLM
    decides how to respond to the information.

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
    # Before the graph implementation was finalized, the public prototype
    # used this name for a flat ledger.  Keep that call shape working while
    # making the graph implementation the unambiguous default.
    if isinstance(graph, SharedExplorationLedger):
        return wrap_tools_with_ledger(tools, cache, graph, agent_id)

    wrapped = {}
    for tool_name, func in tools.items():
        wrapped[tool_name] = _make_poolact_graph_wrapper(
            tool_name, func, cache, graph, agent_id,
            clock=clock, overhead_scale=overhead_scale,
        )
    return wrapped


def _make_poolact_graph_wrapper(
    tool_name: str,
    original_fn: Callable,
    cache: SharedObservationCache,
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Callable:
    """Create a wrapper with caching + graph recording + pending claims.

    No hard blocking.  Claims populate the graph's "In Progress"
    section.  The LLM sees this via the observation augmenter and
    decides how to act.

    Flow:
    1. Check cache (time-gated) → if hit, return cached result (0s).
    2. Record claim if not already registered by pre_tool_hook.
    3. Execute tool, advance clock.
    4. Complete claim, cache result, record in graph.

    When used with ``make_pre_tool_hook()``, claims are recorded
    early (right after the LLM outputs the Action) so other threads
    can see them during their own LLM calls.  The wrapper then skips
    duplicate claim recording (step 2) but still completes the claim.
    """
    def wrapper(payload: str) -> Any:
        vb = clock.now if clock is not None else None

        # 1. Cache hit — result already available (instant, no overhead).
        # A pre_tool_hook may already have recorded this action as pending;
        # complete that claim here or it would remain "In Progress" forever.
        cached = cache.get(tool_name, payload, visible_before=vb)
        if cached is not None:
            result = _zero_overhead(cached)
            graph.complete_claim(
                tool_name, payload, agent_id,
                completion_time=vb if vb is not None else 0.0,
            )
            _record_in_graph(
                graph, agent_id, tool_name, payload, cached,
                completion_time=vb if vb is not None else 0.0,
            )
            return result

        # 2. Record claim only if pre_tool_hook hasn't already done it.
        start_time = vb if vb is not None else 0.0
        if not graph.has_pending_claim(tool_name, payload, agent_id):
            graph.record_claim(
                tool_name, payload, agent_id, start_time=start_time,
            )

        # 3. Execute tool
        try:
            result = original_fn(payload)
        except BaseException:
            # Failed tools must not leave a permanent pending claim.  There
            # is no completed observation to cache or add to the graph.
            graph.complete_claim(
                tool_name, payload, agent_id, completion_time=start_time,
            )
            raise
        raw_overhead = _extract_overhead_from_result(result)
        scaled_overhead = raw_overhead * overhead_scale
        ct = (clock.now + scaled_overhead) if clock is not None else 0.0

        # 4. Complete claim + cache + graph
        graph.complete_claim(
            tool_name, payload, agent_id, completion_time=ct,
        )
        cache.put(tool_name, payload, result, completion_time=ct)
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

    if tool_name == "search":
        query = _parse_search_payload(payload)
        title = _parse_search_result_title(result_str)
        if query:
            graph.record_search(
                agent_id, query, title,
                completion_time=completion_time,
            )

    elif tool_name == "search_meta":
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
# Graph augmenter for PoolAct context injection
# ---------------------------------------------------------------------------

def make_graph_augmenter(
    graph: SharedExplorationGraph,
    *,
    clock: Optional[AgentClock] = None,
    agent_id: Optional[int] = None,
) -> Callable[[str], str]:
    """Create an observation_augmenter that appends the exploration graph.

    Pass the returned function as ``observation_augmenter`` to
    ``run_react_loop()`` to inject the graph into each agent's
    observation context after every tool call.

    The graph is **appended** so the LLM reads its own query result
    first (preserving query→result coherence), then sees coordination
    context for planning the next action.

    Args:
        graph: Shared exploration graph instance.
        clock: Optional AgentClock for time-gated visibility.
        agent_id: The agent's ID, used to label own vs others' results.

    Returns:
        A callable ``(observation: str) -> str`` that appends the graph.
    """
    def augmenter(observation: str) -> str:
        vb = clock.now if clock is not None else None
        graph_text = graph.format_for_injection(
            visible_before=vb, agent_id=agent_id,
        )
        if graph_text:
            return "{}\n\n{}".format(observation, graph_text)
        return observation
    return augmenter


def make_pre_tool_hook(
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
) -> Callable[[str, str], None]:
    """Create a pre_tool_hook that records claims early.

    Called by ``run_react_loop()`` right after the LLM outputs an
    Action — before the tool wrapper executes.  This gives other
    parallel agents a full LLM-call-duration window (~3s real time)
    to see the claim as "In Progress" in the graph.

    The PoolAct wrapper's own claim recording is skipped when a claim
    already exists (idempotent).
    """
    def hook(tool_name: str, payload: str) -> None:
        start_time = clock.now if clock is not None else 0.0
        if not graph.has_pending_claim(tool_name, payload, agent_id):
            graph.record_claim(
                tool_name, payload, agent_id, start_time=start_time,
            )
    return hook


def wrap_tools_with_polact(
    tools: Dict[str, Callable],
    cache: SharedObservationCache,
    graph: SharedExplorationGraph,
    agent_id: int,
    *,
    clock: Optional[AgentClock] = None,
    overhead_scale: float = 1.0,
) -> Dict[str, Callable]:
    """Compatibility alias for :func:`wrap_tools_with_poolact`.

    ``polact`` was an internal typo retained by early experiment scripts.
    New code should use ``wrap_tools_with_poolact``.
    """
    return wrap_tools_with_poolact(
        tools,
        cache,
        graph,
        agent_id,
        clock=clock,
        overhead_scale=overhead_scale,
    )
