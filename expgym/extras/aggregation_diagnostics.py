"""Score-independent explanations of PoolAct's existing aggregation rules.

This module never evaluates answers, reads performance scores, or changes a
winner. Empty vote keys and explicitly reported abstentions remain votes.
Unknown terminal provenance and abstention status are represented by ``None``.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence


def _vote_groups(
    keys: Sequence[Any], indices: Sequence[int], field: str
) -> List[Dict[str, Any]]:
    groups: Dict[Any, Dict[str, Any]] = {}
    for key, index in zip(keys, indices):
        if key not in groups:
            groups[key] = {
                field: list(key) if isinstance(key, tuple) else key,
                "count": 0,
                "agent_indices": [],
            }
        groups[key]["count"] += 1
        groups[key]["agent_indices"].append(index)
    return list(groups.values())


def _top_groups(groups: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not groups:
        return []
    largest = max(group["count"] for group in groups)
    return [group for group in groups if group["count"] == largest]


def _parse_audit_answer(answer: Any) -> tuple[Dict[str, Any], str]:
    """Match the historical aggregator, not a more permissive score parser."""
    if isinstance(answer, str):
        try:
            answer = json.loads(answer)
        except (json.JSONDecodeError, TypeError):
            return {}, "invalid_json"
    if not isinstance(answer, dict):
        return {}, "not_object"
    return answer, "object"


def _audit_label(value: Any) -> str:
    raw = re.sub(r"[^a-z]", "", str(value or "").lower())
    return {
        "entailment": "Entailment",
        "entailed": "Entailment",
        "contradiction": "Contradiction",
        "contradicted": "Contradiction",
        "notmentioned": "NotMentioned",
        "neutral": "NotMentioned",
    }.get(raw, str(value or "").strip())


def _evidence_key(value: Any) -> tuple[Any, ...]:
    if not isinstance(value, list):
        return ()
    normalized = set()
    for item in value:
        try:
            normalized.add(int(item))
        except (TypeError, ValueError, OverflowError):
            normalized.add(str(item))
    return tuple(sorted(normalized, key=lambda item: (str(type(item)), str(item))))


def build_aggregation_diagnostics(
    scenario: str,
    results: Sequence[Mapping[str, Any]],
    *,
    selected_agent_index: Optional[int] = None,
    search_keys: Optional[Sequence[Sequence[str]]] = None,
    parsed_answers: Optional[Sequence[Mapping[str, Any]]] = None,
    audit_votes: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> Dict[str, Any]:
    """Describe existing votes without consulting answer scores or evaluators.

    Search callers supply their actual canonical ``search_keys``. Tuning callers
    supply their already-selected agent index. Audit callers may supply parsed
    answers and, optionally, already-canonical vote rows with ``agent_index``,
    ``label``, and ``evidence_key`` fields. Indices always address input order;
    agent IDs are metadata and do not change the historical tie-breaking order.

    Only a boolean ``result['abstained']`` declares an abstention status. Refusal
    prose, an empty answer, and an empty name set are not inferred abstentions.
    Audit coverage refers only to the union of observed hypothesis IDs, since
    this helper has no access to gold labels or the expected hypothesis set.
    """
    if not results:
        raise ValueError("results must not be empty")
    if scenario not in {"tuning", "restricted_search", "evidence_audit"}:
        raise ValueError(f"Unknown scenario: {scenario}")
    if (
        selected_agent_index is not None
        and not 0 <= selected_agent_index < len(results)
    ):
        raise ValueError("selected_agent_index is outside results")

    provenance = []
    reported_abstentions = []
    declared_abstentions = []
    for index, result in enumerate(results):
        abstained = result.get("abstained")
        if isinstance(abstained, bool):
            reported_abstentions.append(index)
            if abstained:
                declared_abstentions.append(index)
        else:
            abstained = None
        provenance.append({
            "agent_index": index,
            "agent_id": result.get("agent_id"),
            "termination_reason": result.get("termination_reason"),
            "answer_source": result.get("answer_source"),
            "answer_score_source": result.get("answer_score_source"),
            "abstained": abstained,
        })
    diagnostics: Dict[str, Any] = {
        "version": 1,
        "scenario": scenario,
        "agent_count": len(results),
        "empty_answer_agent_indices": [
            index for index, result in enumerate(results)
            if result.get("answer") is None
            or (
                isinstance(result.get("answer"), str)
                and not result["answer"].strip()
            )
        ],
        "abstention": {
            "policy": "explicit_metadata_only_not_excluded",
            "reported_agent_indices": reported_abstentions,
            "declared_count": (
                len(declared_abstentions) if reported_abstentions else None
            ),
            "declared_agent_indices": (
                declared_abstentions if reported_abstentions else None
            ),
        },
        "agent_provenance": provenance,
    }
    if scenario == "tuning":
        diagnostics.update({
            "selected_agent_index": selected_agent_index,
            "selection_reason": "caller_selected_best_of_n",
            "tie_break_rule": "highest_score_then_first_agent",
        })
        return diagnostics

    if scenario == "restricted_search":
        if search_keys is None or len(search_keys) != len(results):
            raise ValueError("search_keys must contain one canonical key per agent")
        keys = [tuple(key) for key in search_keys]
        groups = _vote_groups(keys, list(range(len(results))), "key")
        leaders = _top_groups(groups)
        preferred = [group for group in leaders if group["key"]] or leaders
        selected = preferred[0]["agent_indices"][0]
        if len(leaders) == 1:
            reason = "highest_vote_count"
        elif len(preferred) == 1:
            reason = "nonempty_key_tiebreak"
        else:
            reason = "first_agent_tiebreak"
        if selected_agent_index is None:
            selected_agent_index = selected
        diagnostics.update({
            "vote_groups": groups,
            "empty_vote_key_agent_indices": [
                index for index, key in enumerate(keys) if not key
            ],
            "empty_vote_key_policy": "included_in_vote_counts_not_an_abstention",
            "selected_agent_index": selected_agent_index,
            "tied_keys": (
                [group["key"] for group in leaders] if len(leaders) > 1 else []
            ),
            "selection_reason": reason,
            "tie_break_rule": "highest_count_then_nonempty_key_then_first_agent",
            "selection_matches_rule": selected_agent_index == selected,
            "winner_has_strict_majority": leaders[0]["count"] > len(results) / 2,
        })
        return diagnostics

    parsed_with_status = [
        _parse_audit_answer(result.get("answer")) for result in results
    ]
    if parsed_answers is None:
        parsed_answers = [parsed for parsed, _ in parsed_with_status]
    if len(parsed_answers) != len(results):
        raise ValueError("parsed_answers must contain one object per agent")
    hypothesis_ids = sorted({key for parsed in parsed_answers for key in parsed})
    hypotheses = {}
    for hypothesis_id in hypothesis_ids:
        if audit_votes is not None:
            rows = list(audit_votes.get(hypothesis_id, []))
        else:
            rows = [
                {
                    "agent_index": index,
                    "label": _audit_label(parsed[hypothesis_id].get("label")),
                    "evidence_key": _evidence_key(
                        parsed[hypothesis_id].get("evidence_ids")
                    ),
                }
                for index, parsed in enumerate(parsed_answers)
                if isinstance(parsed.get(hypothesis_id), dict)
            ]
        label_groups = _vote_groups(
            [row["label"] for row in rows], [row["agent_index"] for row in rows], "label"
        )
        label_leaders = _top_groups(label_groups)
        winning_label = label_leaders[0]["label"] if label_leaders else None
        supporters = [row for row in rows if row["label"] == winning_label]
        evidence_groups = _vote_groups(
            [tuple(row["evidence_key"]) for row in supporters],
            [row["agent_index"] for row in supporters], "evidence_ids",
        )
        evidence_leaders = _top_groups(evidence_groups)
        hypotheses[hypothesis_id] = {
            "missing_agent_indices": [
                index for index, parsed in enumerate(parsed_answers)
                if hypothesis_id not in parsed
            ],
            "invalid_entry_agent_indices": [
                index for index, parsed in enumerate(parsed_answers)
                if hypothesis_id in parsed and not isinstance(parsed[hypothesis_id], dict)
            ],
            "label_votes": label_groups,
            "winning_label": winning_label,
            "label_tied": len(label_leaders) > 1,
            "evidence_votes": evidence_groups,
            "winning_evidence": (
                evidence_leaders[0]["evidence_ids"] if evidence_leaders else None
            ),
            "evidence_tied": len(evidence_leaders) > 1,
        }
    diagnostics.update({
        "audit_parse_policy": "legacy_json_loads_v1",
        "audit_parse_status": [status for _, status in parsed_with_status],
        "observed_hypothesis_ids": hypothesis_ids,
        "hypotheses": hypotheses,
        "tie_break_rule": "highest_count_then_first_agent",
        "evidence_vote_policy": "whole_evidence_set_among_winning_label_supporters",
    })
    return diagnostics
