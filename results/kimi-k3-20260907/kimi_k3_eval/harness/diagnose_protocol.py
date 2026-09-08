#!/usr/bin/env python3
"""Read completed ExpGym/PoolAct runs and diagnose textual ReAct adherence.

Does not contact the endpoint or alter benchmark inputs/results. Generated reports
separate model protocol behavior from score integrity and transport success.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "LLM_ExpGym"))
from expgym.react_loop import _extract_action, _truncate_after_action
from expgym.trace_v2 import _termination_code

NATIVE = "<|open|>tools<|sep|>"
CALL_PATTERN = re.compile(r'<\|open\|>call\s+tool=')
ABORT_PATTERN = re.compile(r"System: Loop aborted \((.*?)\)\. Respond immediately", re.S)
SCENARIO_TOOL = {"tuning": "evaluate_config", "restricted_search": "search", "evidence_audit": "human_feedback"}


def read(path):
    return json.loads(path.read_text())


def rel(path):
    try:
        return str(path.relative_to(BASE))
    except ValueError:
        return str(path)


def count(rs):
    native_traces = sum(r["raw_native_responses"] > 0 for r in rs)
    native_missing = sum(r["native_before_missing_action"] for r in rs)
    missing = sum(r["reason"] == "missing_action" for r in rs)
    return {
        "traces": len(rs),
        "native_traces": native_traces,
        "native_then_missing_fraction_of_native_traces": native_missing / native_traces if native_traces else None,
        "native_then_missing_fraction_of_missing_action": native_missing / missing if missing else None,
        "termination_reasons": dict(Counter(r["reason"] for r in rs)),
        "answer_sources": dict(Counter(r["answer_source"] or "not_serialized" for r in rs)),
        **{name: sum(r[name] for r in rs) for name in [
            "terminated", "forced_final_calls", "api_calls", "tool_evaluations",
            "raw_native_responses", "trace_native_messages", "raw_native_calls",
            "trace_native_calls", "native_before_missing_action", "normal_responses_over_8000_chars",
            "cap_removed_action_parser_candidates", "cap_removed_known_tool_json_candidates",
            "raw_to_trace_expected_text_equal",
        ]},
        "all_saved_score_checks_pass": all(r["score_valid"] for r in rs),
    }


def diagnose(root, dump_root):
    progress, manifest = read(root / "progress.json"), read(root / "manifest.json")
    if progress["status"] != "completed":
        raise SystemExit("Run still incomplete; no protocol-failure report produced: " + str(progress["job_counts"]))
    raw = []
    for path in sorted(dump_root.rglob("*.json")):
        d = read(path)
        choices = (d.get("response_json") or {}).get("choices") or []
        choice = choices[0] if choices else {}
        message = choice.get("message") or {}
        content = message.get("content") or ""
        if not isinstance(content, str):
            raise ValueError(f"Non-text content in {path}")
        request = d.get("request_payload") or {}
        forced = any("System: Loop aborted (" in m.get("content", "") for m in request.get("messages", [])[-1:])
        stripped = content.strip()
        capped = not forced and len(stripped) > 8000
        processed = stripped[:8000] + "\n[... output truncated due to excessive length ...]" if capped else stripped
        action = _extract_action(processed)
        # _extract_action searches for Action: anywhere in a line, including
        # quoted prose. A returned tuple alone does not establish a valid tool
        # request, nor that executing it would succeed without the cap.
        uncapped_candidate = _extract_action(stripped)
        candidate_removed = capped and bool(uncapped_candidate) and not action
        candidate_evidence = None
        known_tool_json_candidate = False
        if candidate_removed:
            context = d.get("context") or {}
            scenario = (context.get("job") or {}).get("scenario") or context.get("scenario")
            expected_tool = SCENARIO_TOOL.get(scenario)
            tool_name, payload = uncapped_candidate
            parsed_type, json_error = None, None
            try:
                parsed_type = type(json.loads(payload)).__name__
            except (TypeError, ValueError) as exc:
                json_error = str(exc)
            known_tool_json_candidate = tool_name == expected_tool and parsed_type is not None
            offset = stripped.find("Action:")
            candidate_evidence = {
                "first_action_literal_character_zero_based": offset,
                "literal_context_excerpt": stripped[max(0, offset - 150):offset + 500],
                "extracted_tool": tool_name, "expected_scenario_tool": expected_tool,
                "extracted_payload_excerpt": payload[:500],
                "payload_json_valid": parsed_type is not None,
                "payload_json_type": parsed_type, "payload_json_error": json_error,
                "known_tool_and_json_candidate_only": known_tool_json_candidate,
                "interpretation": "Parser tuple disappears after cap; may be prose/quotation. Even known-tool + valid JSON is not schema/execution validation. No tool executed by diagnostic.",
            }
        if action and not forced:
            processed = _truncate_after_action(processed)
        raw.append({
            "path": rel(path), "client_id": d.get("client_id"), "request_id": d.get("request_id"),
            "generation_id": d.get("generation_id"), "state": d.get("state"),
            "start": d.get("started_at_utc"), "context": d.get("context") or {},
            "forced": forced, "text": content, "processed": processed,
            "native": NATIVE in content, "native_call_count": len(CALL_PATTERN.findall(content)),
            "finish_reason": choice.get("finish_reason"), "structured_tool_calls": bool(message.get("tool_calls")),
            "reasoning_content_present": bool(message.get("reasoning_content")),
            "reasoning_content_chars": len(message.get("reasoning_content") or ""),
            "reasoning_content_sha256": hashlib.sha256(message["reasoning_content"].encode()).hexdigest() if message.get("reasoning_content") else None,
            "reasoning_tokens": (d.get("response_json") or {}).get("usage", {}).get("reasoning_tokens"),
            "thinking": request.get("chat_template_kwargs", {}).get("thinking"),
            "has_action_parser_candidate_before_cap": bool(uncapped_candidate),
            "has_action_parser_candidate_after_cap": bool(action),
            "cap_removed_action_parser_candidate": candidate_removed,
            "cap_removed_known_tool_json_candidate": known_tool_json_candidate,
            "cap_candidate_evidence": candidate_evidence,
            "over_8000_normal": capped,
        })
    duplicate_request_ids = sorted(key for key, value in Counter(a["request_id"] for a in raw).items() if value > 1)
    if duplicate_request_ids:
        raise ValueError("Duplicate request IDs in dump root; select one stage namespace, not the shared pilot/full parent: " + str(duplicate_request_ids[:10]))
    by_client = defaultdict(list)
    for item in raw:
        by_client[item["client_id"]].append(item)
    for items in by_client.values():
        items.sort(key=lambda x: (x["start"], x["request_id"]))

    rows = []
    for path in sorted(root.glob("expgym/**/traces-v2/*.json")):
        d = read(path)
        outcome = d["outcome"]
        rows.append({
            "path": rel(path), "runner": "expgym", "scenario": d["task"]["scenario"],
            "regime": d["task"]["budget"]["regime"], "strategy": None, "agent_id": None,
            "client_id": d["run"]["api_dump"]["client_id"], "reason": outcome.get("termination_reason"),
            "reason_source": "trace_v2_outcome", "answer_source": outcome.get("answer_source"),
            "terminated": outcome["status"] != "completed", "api_calls": len(d["llm_calls"]),
            "forced_final_calls": sum(c.get("forced", False) for c in d["llm_calls"]),
            "tool_evaluations": len(d["tool_calls"]), "score_valid": outcome["validation"]["passed"],
            "score": outcome["score"], "messages": d["messages"],
        })
    for path in sorted(root.glob("poolact/**/result.json")):
        d = read(path)
        config = d["config"]
        for agent in d["agent_results"]:
            agent_path = path.parent / "agents" / f"agent_{agent['agent_id']}.json"
            if not agent_path.exists():
                raise ValueError(f"Missing agent file: {agent_path}")
            reason, forced = None, 0
            for message in agent["messages"]:
                if message["role"] == "user":
                    match = ABORT_PATTERN.search(message.get("content", ""))
                    if match:
                        reason, forced = match.group(1), forced + 1
            rows.append({
                "path": rel(agent_path), "runner": "poolact", "scenario": config["scenario"],
                "regime": config["cost_regime"], "strategy": d["strategy"], "agent_id": agent["agent_id"],
                "client_id": agent["api_dump"]["client_id"],
                "reason": _termination_code(reason if agent["aborted"] else "Natural answer", agent["aborted"]),
                "reason_text": reason, "reason_source": "inferred_from_saved_forced_prompt; field_not_serialized",
                "answer_source": None, "terminated": agent["aborted"], "api_calls": agent["api_calls"],
                "forced_final_calls": forced, "tool_evaluations": agent["evaluations"],
                "score_valid": agent["score_check"]["ok"],
                "score": {"value": agent.get("answer_perf"), "metrics": agent.get("answer_metrics")},
                "messages": agent["messages"],
            })
    for row in rows:
        attempts = by_client[row["client_id"]]
        successes = [a for a in attempts if a["state"] == "success"]
        assistants = [m["content"] for m in row.pop("messages") if m["role"] == "assistant"]
        row.update({
            "raw_attempts": len(attempts), "raw_successful_calls": len(successes),
            "raw_forced_calls": sum(a["forced"] for a in successes),
            "raw_native_responses": sum(a["native"] for a in successes),
            "trace_native_messages": sum(NATIVE in s for s in assistants),
            "raw_native_calls": sum(a["native_call_count"] for a in successes),
            "trace_native_calls": sum(len(CALL_PATTERN.findall(s)) for s in assistants),
            "normal_responses_over_8000_chars": sum(a["over_8000_normal"] for a in successes),
            "cap_removed_action_parser_candidates": sum(a["cap_removed_action_parser_candidate"] for a in successes),
            "cap_removed_known_tool_json_candidates": sum(a["cap_removed_known_tool_json_candidate"] for a in successes),
            "raw_to_trace_expected_text_equal": len(successes) == len(assistants) and all(a["processed"] == t for a, t in zip(successes, assistants)),
            "raw_success_request_ids": [a["request_id"] for a in successes],
        })
        row["raw_to_trace_mismatches"] = [{
            "request_id": a["request_id"], "raw_chars": len(a["text"]), "trace_chars": len(t),
            "raw_sha256": hashlib.sha256(a["text"].encode()).hexdigest(),
            "trace_sha256": hashlib.sha256(t.encode()).hexdigest(),
            "expected_processed_sha256": hashlib.sha256(a["processed"].encode()).hexdigest(),
        } for a, t in zip(successes, assistants) if a["processed"] != t]
        normal = [a for a in successes if not a["forced"]]
        row["native_before_missing_action"] = bool(row["reason"] == "missing_action" and normal and normal[-1]["native"])
    if len(rows) != progress["expected_counts"]["total_agent_traces"]:
        raise ValueError(f"Expected {progress['expected_counts']}, found {len(rows)} traces")

    groups = {"all": count(rows)}
    for runner in ["expgym", "poolact"]:
        groups[runner] = count([r for r in rows if r["runner"] == runner])
        for scenario in ["tuning", "restricted_search", "evidence_audit"]:
            groups[runner + "/" + scenario] = count([r for r in rows if r["runner"] == runner and r["scenario"] == scenario])
    for strategy in ["naive", "cached", "poolact"]:
        groups["poolact/strategy/" + strategy] = count([r for r in rows if r["runner"] == "poolact" and r["strategy"] == strategy])
    native_evidence = []
    for a in raw:
        if a["native"]:
            evidence = {k: a[k] for k in ["path", "client_id", "request_id", "generation_id", "context", "forced", "native_call_count", "finish_reason", "structured_tool_calls", "reasoning_content_present", "reasoning_tokens", "thinking", "over_8000_normal", "has_action_parser_candidate_before_cap", "has_action_parser_candidate_after_cap", "cap_removed_action_parser_candidate", "cap_removed_known_tool_json_candidate"]}
            evidence.update({"response_chars": len(a["text"]), "native_start_character_zero_based": a["text"].index(NATIVE), "sha256": hashlib.sha256(a["text"].encode()).hexdigest(), "tag_excerpt": a["text"][a["text"].index(NATIVE):][:340]})
            native_evidence.append(evidence)
    return {
        "schema_version": 2, "created_at": datetime.now(timezone.utc).isoformat(),
        "revision_note": "v2 replaces the v1 cap_removed_textual_action_responses claim with parser-candidate counts, adds static payload checks and per-case evidence; it makes no executable-action or causal claim",
        "scope": "completed real run; textual ReAct protocol diagnostic, not independent integrity audit",
        "stage": manifest["stage"], "smoke_finished_at": progress["finished_at"],
        "job_counts": progress["job_counts"], "expected_counts": progress["expected_counts"],
        "settings": manifest["settings"], "source_tree_sha256": manifest["source_tree_sha256"], "groups": groups,
        "promotion_map_path": manifest.get("promotion_map"),
        "raw_dump_stats": {
            "attempts": len(raw), "states": dict(Counter(a["state"] for a in raw)),
            "finish_reasons": dict(Counter(a["finish_reason"] for a in raw)),
            "thinking_values": dict(Counter(str(a["thinking"]) for a in raw)),
            "reasoning_tokens_values": dict(Counter(str(a["reasoning_tokens"]) for a in raw)),
            "structured_tool_calls_responses": sum(a["structured_tool_calls"] for a in raw),
            "reasoning_content_nonempty_responses": sum(a["reasoning_content_present"] for a in raw),
            "reasoning_content_total_chars": sum(a["reasoning_content_chars"] for a in raw),
            "native_responses": sum(a["native"] for a in raw), "native_calls": sum(a["native_call_count"] for a in raw),
            "linked_client_ids": len(by_client), "saved_trace_client_ids": len({r["client_id"] for r in rows}),
            "unlinked_client_ids": sorted(set(by_client) - {r["client_id"] for r in rows}),
        },
        "trace_rows": rows, "native_response_evidence": native_evidence,
        "cap_candidate_evidence": [{"path": a["path"], "client_id": a["client_id"], "request_id": a["request_id"], "response_chars": len(a["text"]), "finish_reason": a["finish_reason"], **a["cap_candidate_evidence"]} for a in raw if a["cap_candidate_evidence"]],
        "reasoning_content_evidence": [{k: a[k] for k in ["path", "client_id", "request_id", "thinking", "reasoning_tokens", "reasoning_content_chars", "reasoning_content_sha256"]} for a in raw if a["reasoning_content_present"]],
        "definitions": {
            "native_response": "response_json.choices[0].message.content contains exact K3 XTML <|open|>tools<|sep|>; request history and response_raw serialization are not double-counted",
            "native_call": "literal <|open|>call tool= opening in generated response; distinct from response count",
            "trace_native_messages": "assistant messages only, excluding duplicated steps and prompt text",
            "poolact_termination_reason": "inferred from saved System: Loop aborted (...) prompt plus aborted flag; legacy LoopResult does not serialize termination_reason",
            "raw_to_trace": "client_id linkage, successful responses by start time, current normal-turn 8000-character cap and Action truncation; forced-final content only stripped",
            "cap_removed_action_parser_candidates": "_extract_action returns a tuple before cap and none after cap; includes prose/quoted Action: fragments and does not establish an executable action or causation of execution failure",
            "cap_removed_known_tool_json_candidates": "subset whose extracted tool matches the scenario and payload passes json.loads; still no argument schema or environment execution validation",
            "promotion_linkage": "persisted client_id and successful response text determine linkage; original context/run_id/path strings are preserved as evidence and are not matching keys. Independent dump audit verifies promotion map and hashes",
            "raw_dump_scope": "raw_dump_stats counts every attempt under the selected stage dump root, while trace groups use saved client_ids only; unlinked_client_ids lists historical/unselected sessions. Repeated request IDs are rejected to prevent double-counting pilot/full copies",
            "native_before_missing_action": "last successful normal response contains native tool envelope and saved/inferred terminal reason is missing_action; cap interference counted separately",
            "completed_only": "requires progress.status==completed and exact saved expected trace count; no in-flight output counted as failure",
        },
    }


def markdown(report):
    g, raw = report["groups"], report["raw_dump_stats"]
    lines = [f"# {report['stage']} textual ReAct 协议诊断", "", f"完成时间：{report['smoke_finished_at']}。{report['job_counts']['completed']} 个 jobs、{g['all']['traces']} 条 agent traces。统计仅使用已完成结果。", "", "版本2修正：旧字段cap_removed_textual_action_responses仅代表解析器候选，不能解释为可执行Action被截掉。此版重命名并加入工具名/JSON检查及原文证据；旧报告保留供追溯。", "",
             "| 路径/场景 | traces | missing_action | forced final | 原始native响应 | trace native消息 |",
             "|---|---:|---:|---:|---:|---:|"]
    for key in ["expgym", "expgym/tuning", "expgym/restricted_search", "expgym/evidence_audit", "poolact", "poolact/tuning", "poolact/restricted_search", "poolact/evidence_audit"]:
        a = g[key]
        lines.append(f"| {key} | {a['traces']} | {a['termination_reasons'].get('missing_action', 0)} | {a['forced_final_calls']} | {a['raw_native_responses']} | {a['trace_native_messages']} |")
    allg = g["all"]
    lines += ["", f"原始 HTTP attempts={raw['attempts']}；state={raw['states']}；finish_reason={raw['finish_reasons']}。thinking={raw['thinking_values']}，reasoning_tokens={raw['reasoning_tokens_values']}；结构化 tool_calls 非空响应={raw['structured_tool_calls_responses']}。",
              "", f"native标签共出现在 {raw['native_responses']} 个响应 / {raw['native_calls']} 个call开头；{allg['native_before_missing_action']}/{allg['native_traces']} 条含native标签trace在最后一个常规响应出现native标签后终止为missing_action，占全部missing_action的 {allg['native_before_missing_action']}/{allg['termination_reasons'].get('missing_action', 0)}。原始响应与保存trace在应用现有截断规则后完全一致：{allg['raw_to_trace_expected_text_equal']}/{allg['traces']}。",
              "", f"常规响应超过8000字符：{allg['normal_responses_over_8000_chars']}；截断前存在、截断后消失的Action解析候选：{allg['cap_removed_action_parser_candidates']}，其中仅通过预期工具名+JSON语法检查的候选：{allg['cap_removed_known_tool_json_candidates']}。解析器会匹配长Thought中引用的Action:，因此这些计数不证明存在可执行动作，也不能据此归因于cap。即使工具名和JSON有效，仍未验证参数schema或实际执行。此cap是仓库既有行为，forced final不受该8000字符cap约束。",
              "", f"thinking参数与返回的reasoning字段需分开报告：{raw['reasoning_content_nonempty_responses']} 个响应的reasoning_content非空，共 {raw['reasoning_content_total_chars']} 字符，虽usage.reasoning_tokens的取值为 {raw['reasoning_tokens_values']}。因此只能确认请求了thinking=false及服务报告的token字段，不能据此证明模型完全没有产生reasoning channel。客户端仅保存content到多轮trace history，完整reasoning_content仍可在原始dump按request_id查验。",
              "", "终止原因（原字段名是 termination_reason）：", "", "```json", json.dumps({key: g[key]['termination_reasons'] for key in ['expgym', 'poolact']}, ensure_ascii=False, indent=2), "```", "",
              "ExpGym answer_source：`" + json.dumps(g['expgym']['answer_sources'], ensure_ascii=False) + "`。PoolAct legacy agent结果未序列化termination_reason/answer_source；此处termination原因从保存的强制回答提示推导，不能将推导字段当原始字段。", "",
              "promotion匹配使用保存的client_id与逐响应文本；原dumpcontext中的pilot路径和run_id作为证据保留，不影响full中的对应关系。promotion map及文件hash由独立dump审计确认。本脚本只应扫描目标stage的dump目录；若同时扫描pilot/full副本，重复request_id会拒绝。raw总体计数涵盖该目录全部attempt，trace分组仅统计保存client_id关联的attempt。", "",
              "## 解释与论文语义", "",
              "本次请求使用论文textual ReAct：Action: tool_name JSON。K3原生XTML工具通道 `<|open|>tools<|sep|><|open|>call tool=...` 不属于该语法。客户端未发送结构化tools，也未转换XTML；此类工具意图不会作为Action执行，随后按仓库协议强制最终回答。应同时报告协议遵循失败率、实际tool调用、强制回答率及得分，不能将其仅解释为任务知识能力不足，也不能用score复算通过替代交互协议成功。", "",
              "missing_action与有效最终得分可同时成立：强制回答后原中断标记仍保留；Tuning还可能使用best_evaluated_fallback。HTTP成功、结果完整性、动作格式遵循和语义正确率是不同维度。", "",
              "在严格主实验中保留统一textual ReAct语义并披露这些失败。若另做K3 native适配，需将其列为独立协议敏感性实验，并对ExpGym及PoolAct各策略应用相同适配，重新保留manifest和dump；不要把适配后的结果混入原配置。smoke的4-step/3-evaluation/N=2不能用于推断论文30-step/N=4失败率。", "",
              "代码依据：LLM_ExpGym/expgym/react_loop.py:304（8000字符cap）、:312（Action/Answer解析）、:332（missing_action）、:453（forced final）、:519（tuning fallback）、:737（字面Action）；expgym/llm_clients.py:358（仅content）、:405（无tools）；expgym/trace_v2.py:202（原因映射）。原始标签证据及request/client/trace对应关系见同名JSON。", ""]
    for item in report["cap_candidate_evidence"]:
        lines.extend(["", "### 截断候选逐例", "", f"request_id `{item['request_id']}`；原始 {item['response_chars']} 字符，finish_reason={item['finish_reason']}，首个Action: offset={item['first_action_literal_character_zero_based']}。提取工具 `{item['extracted_tool']}`；payload JSON有效={item['payload_json_valid']}。", "", "```text", item["literal_context_excerpt"], "```", "", "提取payload：", "", "```text", item["extracted_payload_excerpt"], "```", "", "这里只记录静态解析候选，不认为未截断时工具即可成功执行。"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dump-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    report = diagnose(args.run_dir.resolve(), args.dump_dir.resolve())
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    args.output_prefix.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    args.output_prefix.with_suffix(".md").write_text(markdown(report))
    print(json.dumps({"output_prefix": str(args.output_prefix), "groups": report["groups"], "raw_dump_stats": report["raw_dump_stats"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
