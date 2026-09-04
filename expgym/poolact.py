"""Public PoolAct API.

PoolAct runs multiple agents on the same ExpGym item with three pieces of
shared state: an observation cache, an exploration graph, and a reasoning
lock. Tool executions remain parallel; only the LLM decision that reads the
graph and records its next claim is serialized.

The easiest entry point is ``scripts/eval_poolact.sh``. Library users can
create a :class:`PoolActCoordinator`, bind each agent's tools, and pass the
returned hooks to :func:`expgym.react_loop.run_react_loop`.
"""
from __future__ import annotations

import json
import re
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from expgym.extras.parallel_cache import (
    ActionClaim,
    AgentClock,
    SharedExplorationGraph,
    SharedExplorationLedger,
    SharedObservationCache,
    make_graph_augmenter,
    make_ledger_augmenter,
    make_pre_tool_hook,
    wrap_tools_with_cache,
    wrap_tools_with_ledger,
    wrap_tools_with_polact,
    wrap_tools_with_poolact,
)

POOLACT_PROTOCOL_VERSION = "paper-graph-lock-v1"


@dataclass
class PoolActAgentRuntime:
    """Per-agent values passed to ``run_react_loop``."""

    tools: Dict[str, Callable]
    clock: AgentClock
    observation_augmenter: Callable[[str], str]
    pre_tool_hook: Callable[[str, str], None]
    reasoning_lock: threading.Lock


class PoolActCoordinator:
    """Own the shared state for one N-agent PoolAct run."""

    def __init__(self, n_agents: int, *, diversity_mode: bool = True) -> None:
        if n_agents < 1:
            raise ValueError("n_agents must be at least 1")
        self.n_agents = n_agents
        self.cache = SharedObservationCache()
        self.graph = SharedExplorationGraph(
            n_agents=n_agents,
            diversity_mode=diversity_mode,
        )
        self.reasoning_lock = threading.Lock()

    def bind_tools(
        self,
        tools: Dict[str, Callable],
        agent_id: int,
        *,
        overhead_scale: float = 1.0,
    ) -> PoolActAgentRuntime:
        """Wrap one agent's tools and return all ReAct-loop hooks."""
        if agent_id < 0 or agent_id >= self.n_agents:
            raise ValueError(
                f"agent_id must be in [0, {self.n_agents}), got {agent_id}"
            )
        clock = AgentClock()
        wrapped = wrap_tools_with_poolact(
            tools,
            self.cache,
            self.graph,
            agent_id,
            clock=clock,
            overhead_scale=overhead_scale,
        )
        return PoolActAgentRuntime(
            tools=wrapped,
            clock=clock,
            observation_augmenter=make_graph_augmenter(
                self.graph,
                clock=clock,
                agent_id=agent_id,
            ),
            pre_tool_hook=make_pre_tool_hook(
                self.graph,
                agent_id,
                clock=clock,
            ),
            reasoning_lock=self.reasoning_lock,
        )

    def stats(self) -> Dict[str, Dict[str, Any]]:
        """Return a serializable snapshot of the shared state."""
        return {"cache": self.cache.stats(), "graph": self.graph.stats()}


def run_agents_parallel(
    n_agents: int,
    run_agent: Callable[[int], Dict[str, Any]],
    *,
    max_workers: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Run agent callbacks concurrently and return results by agent ID."""
    if n_agents < 1:
        raise ValueError("n_agents must be at least 1")
    workers = max_workers or n_agents
    if workers < 1:
        raise ValueError("max_workers must be at least 1")
    indexed: Dict[int, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(workers, n_agents)) as executor:
        futures = {
            executor.submit(run_agent, agent_id): agent_id
            for agent_id in range(n_agents)
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            indexed[agent_id] = future.result()
    return [indexed[agent_id] for agent_id in range(n_agents)]


def _search_vote_key(answer: Any) -> tuple[str, ...]:
    """Canonicalize a search answer so name order does not split a vote."""
    text = str(answer or "").strip()
    if not text:
        return ()
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if isinstance(parsed, list):
        parts = [str(value) for value in parsed]
    else:
        parts = re.split(r"[,;\n]", text)
    normalized = {
        " ".join(
            re.sub(r"^\s*\d+[.)]\s*", "", part)
            .strip()
            .strip("-*•")
            .lower()
            .split()
        )
        for part in parts
        if str(part).strip()
    }
    normalized.discard("")
    return tuple(sorted(normalized))


def _evaluate_aggregate(
    evaluator: Optional[Callable], answer: str
) -> tuple[Optional[float], Optional[Dict[str, Any]]]:
    if evaluator is None:
        return None, None
    try:
        score = evaluator(answer, [])
    except TypeError:
        score = evaluator(answer)
    if isinstance(score, dict):
        primary = score.get("label_acc")
        return (
            float(primary) if isinstance(primary, (int, float)) else None,
            score,
        )
    if isinstance(score, (int, float)):
        return float(score), None
    return None, None


def aggregate_results(
    scenario: str,
    results: Sequence[Dict[str, Any]],
    *,
    answer_evaluator: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Aggregate answers using the methods reported in the paper.

    Tuning uses best-of-N, restricted search uses semantic majority vote over
    name sets, and evidence audit votes independently per hypothesis.
    """
    if not results:
        raise ValueError("results must not be empty")
    individual_answers = [result.get("answer") or "" for result in results]
    individual_perfs = [result.get("answer_perf") for result in results]

    if scenario == "tuning":
        best = max(
            results,
            key=lambda result: (
                float(result["answer_perf"])
                if isinstance(result.get("answer_perf"), (int, float))
                else float("-inf")
            ),
        )
        return {
            "method": "best_of_n",
            "answer": best.get("answer") or "",
            "answer_perf": best.get("answer_perf"),
            "answer_metrics": best.get("answer_metrics"),
            "individual_answers": individual_answers,
            "individual_perfs": individual_perfs,
        }

    if scenario == "restricted_search":
        keys = [_search_vote_key(answer) for answer in individual_answers]
        winning_key = Counter(keys).most_common(1)[0][0]
        winner_index = keys.index(winning_key)
        answer = str(individual_answers[winner_index])
        perf, metrics = _evaluate_aggregate(answer_evaluator, answer)
        return {
            "method": "majority_vote",
            "answer": answer,
            "answer_perf": perf,
            "answer_metrics": metrics,
            "individual_answers": individual_answers,
            "individual_perfs": individual_perfs,
        }

    if scenario != "evidence_audit":
        raise ValueError(f"Unknown scenario: {scenario}")

    parsed_answers: List[Dict[str, Any]] = []
    for answer in individual_answers:
        try:
            parsed = json.loads(answer) if isinstance(answer, str) else answer
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        parsed_answers.append(parsed if isinstance(parsed, dict) else {})

    hypothesis_ids = sorted(
        {hypothesis_id for parsed in parsed_answers for hypothesis_id in parsed}
    )
    voted: Dict[str, Any] = {}
    for hypothesis_id in hypothesis_ids:
        entries = [
            parsed[hypothesis_id]
            for parsed in parsed_answers
            if isinstance(parsed.get(hypothesis_id), dict)
        ]
        labels = [str(entry.get("label", "")) for entry in entries]
        if not labels:
            continue
        winning_label = Counter(labels).most_common(1)[0][0]
        evidence = [
            tuple(sorted(entry.get("evidence_ids") or [], key=str))
            for entry, label in zip(entries, labels)
            if label == winning_label
        ]
        winning_evidence = Counter(evidence).most_common(1)[0][0] if evidence else ()
        voted[hypothesis_id] = {
            "label": winning_label,
            "evidence_ids": list(winning_evidence),
        }

    answer = json.dumps(voted, sort_keys=True)
    perf, metrics = _evaluate_aggregate(answer_evaluator, answer)
    return {
        "method": "per_hypothesis_majority_vote",
        "answer": answer,
        "answer_perf": perf,
        "answer_metrics": metrics,
        "individual_answers": individual_answers,
        "individual_perfs": individual_perfs,
    }


__all__ = [
    "ActionClaim",
    "AgentClock",
    "PoolActAgentRuntime",
    "PoolActCoordinator",
    "POOLACT_PROTOCOL_VERSION",
    "SharedExplorationGraph",
    "SharedExplorationLedger",
    "SharedObservationCache",
    "aggregate_results",
    "make_graph_augmenter",
    "make_ledger_augmenter",
    "make_pre_tool_hook",
    "run_agents_parallel",
    "wrap_tools_with_cache",
    "wrap_tools_with_ledger",
    "wrap_tools_with_polact",
    "wrap_tools_with_poolact",
]
