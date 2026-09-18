#!/usr/bin/env python3
"""Validate HPO graph identities in saved agent input messages, without model calls.

This deliberately does not import the graph implementation under test. Full
configuration payloads supply identities; each rendered snapshot supplies its
own alias namespace. A repeated configuration may legitimately have a self-loop.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


GRAPH_START = re.compile(r"\[(?:Parallel Exploration[^\]\n]*|Shared Exploration Graph)\]")
EXPLICIT_ALIAS = re.compile(r"^(E:(?:h:[0-9a-f]{12,64}|sha256:[0-9a-f]{64}))\s+(.+)$")
NODE_RESULT = re.compile(r"\s+->\s+(?:perf=)?(?:INVALID|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)(?=\s|,|$)")
PATH_SUFFIX = re.compile(r"\s+\[(?:(?:\d+x,\s*)?agents\s+[\d,]+|\d+x)\]\s*$")


def _payload(raw: Any):
    try:
        value = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return None
    if isinstance(value, dict):
        key = json.dumps(value, sort_keys=True, separators=(",", ":"))
        display = "{" + ",".join("{}:{}".format(k, v) for k, v in sorted(value.items())) + "}"
    elif isinstance(value, list):
        key = json.dumps(value, separators=(",", ":"))
        display = "[" + ",".join(str(v) for v in value) + "]"
    else:
        return None
    return key, display, hashlib.sha256(key.encode("utf-8")).hexdigest()


def _content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(part.get("text", "") for part in value
                         if isinstance(part, dict) and isinstance(part.get("text"), str))
    return ""


def verify_graph(result: dict) -> dict:
    """Return JSON-serializable acceptance evidence for one PoolAct result.

    ``ok`` is false on any graph validation failure. ``applicable`` is false
    for naive/cached or non-HPO results, where no shared graph is expected.
    Original result dictionaries are never mutated.
    """
    config = result.get("config", {})
    strategy = result.get("strategy")
    protocol = config.get("poolact_protocol")
    scenario = config.get("scenario")
    limitations = [
        "Checks saved user/tool message snapshots, not an assertion that every stored message was sent byte-identically on the provider wire.",
        "Checks identity, alias uniqueness, full-payload source binding and endpoint existence; does not simulate alternative sharing, decisions, timing, or outcomes.",
        "Uses full canonical payloads from this pool's tool/evaluation records; it does not reconstruct hidden runtime graph objects or prove cross-pool isolation.",
        "Legacy v3 labels are diagnosed from their documented 80-character prefix rule; modern long labels must match the complete payload SHA256 and be unique in each visible snapshot.",
    ]
    response = {"schema": "expgym.hpo-graph-acceptance.v1", "ok": True,
                "status": "PASS", "applicable": True, "strategy": strategy,
                "protocol": protocol, "scenario": scenario,
                "counters": {}, "error_counts": {}, "errors": [],
                "limitations": limitations}
    if strategy in {"naive", "cached"} or scenario not in {"tuning", None}:
        response.update(status="NOT_APPLICABLE", applicable=False,
                        reason="No HPO shared graph is expected for this strategy/scenario.")
        return response
    counters, error_counts = Counter(), Counter()
    errors = []

    def fail(code, location, **details):
        error_counts[code] += 1
        if len(errors) < 30:
            errors.append({"code": code, **location, **details})

    agents = result.get("agent_results")
    if strategy != "poolact":
        fail("unknown_strategy", {}, value=strategy)
    if not isinstance(agents, list) or not agents:
        fail("missing_agent_results", {})
        agents = []
    # A display string is not an identity. Bind it back to every full payload
    # first, then reject ambiguous or mismatched renderings within snapshots.
    by_display = defaultdict(set)
    payloads = {}
    repeated_source = defaultdict(Counter)
    for ai, agent in enumerate(agents):
        agent_id = str(agent.get("agent_id", ai))
        has_source_tools = False
        for record in agent.get("tool_records", []):
            if isinstance(record, (list, tuple)) and len(record) >= 2 and record[0] == "evaluate_config":
                parsed = _payload(record[1])
                if parsed:
                    key, display, digest = parsed
                    payloads[key] = digest
                    by_display[display].add(key)
                    repeated_source[agent_id][key] += 1
                    has_source_tools = True
                    counters["source_tool_payload_records"] += 1
        for record in agent.get("eval_records", []):
            if isinstance(record, (list, tuple)) and record:
                parsed = _payload(record[0])
                if parsed:
                    key, display, digest = parsed
                    payloads[key] = digest
                    by_display[display].add(key)
                    if not has_source_tools:
                        repeated_source[agent_id][key] += 1
                    counters["source_visible_evaluation_records"] += 1
    counters["source_unique_full_configurations"] = len(payloads)
    digests = defaultdict(set)
    for key, digest in payloads.items():
        digests[digest].add(key)
    for digest, keys in digests.items():
        if len(keys) > 1:
            fail("full_identity_digest_collision", {}, digest=digest, different_payloads=len(keys))
    legacy = isinstance(protocol, str) and protocol.endswith("v3")
    for ai, agent in enumerate(agents):
        messages = agent.get("messages")
        if not isinstance(messages, list):
            fail("missing_agent_messages", {"agent_index": ai})
            continue
        for mi, message in enumerate(messages):
            if not isinstance(message, dict) or message.get("role") not in {"user", "tool"}:
                continue
            content = _content(message.get("content"))
            matches = list(GRAPH_START.finditer(content))
            for gi, match in enumerate(matches):
                counters["graph_snapshots"] += 1
                block = content[match.start():matches[gi + 1].start() if gi + 1 < len(matches) else len(content)]
                location = {"agent_index": ai, "agent_id": agent.get("agent_id", ai),
                            "message_index": mi, "snapshot_index": gi,
                            "snapshot_sha256": hashlib.sha256(block.encode("utf-8")).hexdigest()}
                if "== Already Explored ==" in block and "== Exploration Paths ==" in block:
                    counters["unified_snapshots"] += 1
                    nodes = block.split("== Already Explored ==", 1)[1].split("== Exploration Paths ==", 1)[0]
                    paths = block.split("== Exploration Paths ==", 1)[1].split("== Coverage Gap ==", 1)[0]
                elif "=== Evaluated Configs ===" in block:
                    counters["default_snapshots"] += 1
                    nodes = block.split("=== Evaluated Configs ===", 1)[1].split("=== Best So Far ===", 1)[0]
                    paths = ""
                else:
                    fail("unsupported_graph_layout", location)
                    continue
                aliases = defaultdict(set)
                present_keys = set()
                for line in nodes.splitlines():
                    line = line.strip()
                    if not line or line == "None completed yet." or line.startswith('END:"') or line.startswith("by=["):
                        continue
                    perf_match = list(NODE_RESULT.finditer(line))
                    if not perf_match:
                        fail("unparsed_evaluation_node", location, line=line[:180])
                        continue
                    counters["node_rows"] += 1
                    body = line[:perf_match[-1].start()]
                    labeled = EXPLICIT_ALIAS.match(body)
                    alias, display = (labeled.group(1), labeled.group(2)) if labeled else (None, body)
                    candidates = by_display.get(display, set())
                    if len(candidates) != 1:
                        fail("node_payload_not_unique" if candidates else "node_payload_missing", location,
                             alias=alias, matching_full_payloads=len(candidates), display_sha256=hashlib.sha256(display.encode()).hexdigest())
                        continue
                    key = next(iter(candidates))
                    digest = payloads[key]
                    if key in present_keys:
                        fail("duplicate_full_node_in_snapshot", location, digest=digest)
                    present_keys.add(key)
                    if alias:
                        counters["explicit_hash_node_rows"] += 1
                        suffix = alias.split(":", 2)[2]
                        if not digest.startswith(suffix) or (alias.startswith("E:sha256:") and len(suffix) != 64):
                            fail("hash_alias_payload_mismatch", location, alias=alias, full_payload_sha256=digest)
                    else:
                        alias = "E:" + (key[:80] if legacy else key)
                        if len(key) > 80:
                            counters["legacy_unlabeled_long_node_rows"] += 1
                            if not legacy:
                                fail("modern_long_node_missing_hash_alias", location, full_payload_sha256=digest)
                    aliases[alias].add(key)
                for alias, keys in aliases.items():
                    if len(keys) > 1:
                        fail("rendered_identity_collision", location, alias=alias,
                             distinct_payload_sha256=sorted(payloads[k] for k in keys))
                for line in paths.splitlines():
                    line = line.strip()
                    if not line or line == "No multi-step paths recorded yet.":
                        continue
                    agent_suffix = re.search(r"\bagents\s+([\d,]+)\]\s*$", line)
                    path_agents = agent_suffix.group(1).split(",") if agent_suffix else []
                    line = PATH_SUFFIX.sub("", line)
                    if " --> " not in line:
                        fail("unparsed_path", location, line=line[:180])
                        continue
                    source, target = line.split(" --> ", 1)
                    counters["path_rows"] += 1
                    endpoints = []
                    for side, endpoint in (("from", source), ("to", target)):
                        bound = aliases.get(endpoint, set())
                        counters["path_endpoints"] += 1
                        if len(bound) != 1:
                            fail("path_endpoint_ambiguous" if bound else "path_endpoint_missing", location,
                                 side=side, endpoint=endpoint, matching_full_payloads=len(bound))
                            endpoints.append(None)
                        else:
                            endpoints.append(next(iter(bound)))
                    if source == target:
                        counters["rendered_self_loops"] += 1
                        if endpoints[0] is not None and endpoints[0] == endpoints[1]:
                            counters["unambiguous_same_configuration_self_loops"] += 1
                            for path_agent in path_agents:
                                if repeated_source[path_agent][endpoints[0]] < 2:
                                    fail("self_loop_without_repeated_source_configuration", location,
                                         endpoint=source, path_agent_id=path_agent)
    if payloads and counters["graph_snapshots"] == 0:
        fail("missing_all_graph_snapshots", {})
    response.update(ok=not bool(error_counts), status="FAIL" if error_counts else "PASS",
                    counters=dict(counters), error_counts=dict(error_counts), errors=errors,
                    error_count=sum(error_counts.values()), examples_truncated=sum(error_counts.values()) > len(errors))
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    check = verify_graph(json.loads(args.result.read_text()))
    serialized = json.dumps(check, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    else:
        print(serialized, end="")
    raise SystemExit(0 if check["ok"] else 1)
