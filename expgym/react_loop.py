"""Minimal ReAct-style loop plus a fake LLM backend.

Uses proper multi-turn chat messages (system/user/assistant) instead of
flat-string prompts, so chat-tuned LLMs can track their own prior outputs.
"""
from __future__ import annotations

import copy
from contextlib import nullcontext
import logging
import math
import time
from dataclasses import dataclass, field
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from expgym.errors import ToolInputError
from expgym.execution_contract import validate_execution_contracts
from expgym.tool_protocol import native_system_prompt, native_tool_schemas, resolve_tool_protocol, structured_final_answer, unlabelled_final_answer

logger = logging.getLogger("expgym")

ToolReturn = Union[Tuple[float, float], Tuple[str, float], Tuple[object, float, float]]
ToolFn = Callable[[str], ToolReturn]

Message = Dict[str, Any]


@dataclass
class LLMOutput:
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cached_prompt_tokens: Optional[int] = None
    cache_write_prompt_tokens: Optional[int] = None
    request_attempts: int = 1
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    assistant_message: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    attempt_usage: List[Dict[str, Any]] = field(default_factory=list)


class LLMBackend:
    """Very small interface describing the generate method used by the loop."""

    def generate(self, messages) -> LLMOutput:  # pragma: no cover - interface only
        raise NotImplementedError


@dataclass
class LoopResult:
    answer: Optional[str]
    answer_perf: Optional[float]
    answer_overhead: Optional[float]
    answer_metrics: Optional[Dict[str, object]]
    steps: List[str]
    total_overhead: float
    aborted: bool
    evaluations: int
    api_calls: int
    llm_time: float
    eval_time: float
    prompt_tokens: int
    completion_tokens: int
    cached_prompt_tokens: int
    instruction_tokens: int
    messages: List[Dict[str, str]]
    tool_records: List[Tuple[str, str, Optional[object]]]
    eval_records: List[Tuple[str, Optional[str], float, float]]


def _estimate_tokens(messages: List[Message]) -> int:
    """Approximate serialized-message tokens, including calls and reasoning.

    This character heuristic is not an exact tokenizer guarantee. Null content
    is valid for tool-only responses.
    """
    return sum(len(json.dumps(m, ensure_ascii=False, allow_nan=False)) for m in messages) // 3


def _trim_messages(
    messages: List[Message],
    max_tokens: int,
    *,
    protected_tail: int = 4,
    truncated_obs_chars: int = 600,
) -> List[Message]:
    """Trim observations/whole decision groups without breaking tool pairing.

    Initial instructions and task are immutable. If protected content alone
    cannot fit, return it intact; the caller must not send an over-limit request.
    """
    if _estimate_tokens(messages) <= max_tokens:
        return messages
    result = copy.deepcopy(messages)
    start = 0
    while start < len(result) and result[start].get("role") in ("system", "developer"):
        start += 1
    if start < len(result) and result[start].get("role") == "user":
        start += 1
    prefix = result[:start]
    groups: List[List[Message]] = []
    for message in result[start:]:
        if message.get("role") == "assistant" or not groups:
            groups.append([])
        groups[-1].append(message)
    for group in groups:
        for message in group:
            content = message.get("content")
            observation = (
                message.get("role") == "tool" or
                (message.get("role") == "user" and isinstance(content, str)
                 and content.startswith("Observation:"))
            )
            if observation and isinstance(content, str) and len(content) > truncated_obs_chars:
                message["content"] = content[:truncated_obs_chars] + "\n[... truncated ...]"

    def flatten() -> List[Message]:
        return prefix + [m for group in groups for m in group]

    while len(groups) > 1 and _estimate_tokens(flatten()) > max_tokens:
        # Expand the protected tail to complete groups; never orphan tool calls.
        if sum(len(group) for group in groups[1:]) < protected_tail:
            break
        groups.pop(0)
    return flatten()


def run_react_loop(
    llm: LLMBackend,
    tools: Dict[str, ToolFn],
    time_budget: Optional[float] = None,
    max_steps: int = 10,
    max_evals: Optional[int] = None,
    max_prompt_tokens: Optional[int] = None,
    context: Optional[str] = None,
    instruction_notes: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    include_overhead_in_observation: bool = False,
    include_cost_in_observation: bool = False,
    answer_evaluator: Optional[Callable[[str], float]] = None,
    overhead_scale: float = 1.0,
    max_context_tokens: Optional[int] = None,
    observation_augmenter: Optional[Callable[[str], str]] = None,
    agent_clock: object = None,
    pre_tool_hook: Optional[Callable[[str, str], None]] = None,
    llm_lock: Optional[Any] = None,
    capture_trace_v2: bool = False,
    tool_protocol: str = "auto",
    max_protocol_retries: int = 0,
    tuning_final_policy: str = "legacy",
) -> Dict[str, object]:
    """Run one agent; native and text transports share the same budget rules.

    The library preserves zero protocol repairs by default. Runners may
    explicitly request bounded repairs; every repair uses a normal agent step.
    One forced final call remains the historical, recorded horizon exemption.
    Infrastructure exceptions propagate; only ToolInputError is model feedback.
    max_prompt_tokens is an admission threshold on cumulative reported prompt
    usage, not an exact pre-tokenized allowance for the next request.
    """
    if tool_protocol not in ("auto", "native", "text"):
        raise ValueError("tool_protocol must be auto, native, or text")
    if tuning_final_policy not in ("legacy", "submitted"):
        raise ValueError("tuning_final_policy must be legacy or submitted")
    for name, value in (("max_steps", max_steps), ("max_evals", max_evals),
                        ("max_protocol_retries", max_protocol_retries),
                        ("max_prompt_tokens", max_prompt_tokens),
                        ("max_context_tokens", max_context_tokens)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise ValueError(name + " must be a non-negative integer or None")
    if max_protocol_retries is None:
        raise ValueError("max_protocol_retries must be an integer")
    for name, value in (("time_budget", time_budget), ("overhead_scale", overhead_scale)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or value < 0):
            raise ValueError(name + " must be finite and non-negative")
    if overhead_scale is None:
        raise ValueError("overhead_scale cannot be None")
    validate_execution_contracts(
        tools=tools, agent_clock=agent_clock,
        observation_augmenter=observation_augmenter, pre_tool_hook=pre_tool_hook,
        time_budget=time_budget, overhead_scale=overhead_scale,
    )
    resolved_protocol = resolve_tool_protocol(llm, tool_protocol)
    native = resolved_protocol == "native"
    schemas = native_tool_schemas(tools) if native else None
    schema_token_estimate = (len(json.dumps(schemas, ensure_ascii=False, allow_nan=False)) // 3
                             if native else 0)
    sys_text = system_prompt or build_system_prompt(instruction_notes=instruction_notes)
    if native:
        sys_text = native_system_prompt(sys_text)
    messages: List[Message] = [{"role": "system", "content": sys_text}]
    if context:
        messages.append({"role": "user", "content": context.strip()})
    steps: List[str] = ["System Prompt:", sys_text, ""]
    if context:
        steps.append(f"Prompt: Task description:\n{context.strip()}")
    total_overhead = 0.0
    answer: Optional[str] = None
    answer_perf: Optional[float] = None
    answer_metrics: Optional[Dict[str, object]] = None
    answer_overhead: Optional[float] = None
    answer_source: Optional[str] = None
    answer_score_source: Optional[str] = None
    aborted = False
    abort_reason: Optional[str] = None
    over_budget_note: Optional[str] = None
    prev_augmented_idx: Optional[int] = None
    evaluations = api_calls = agent_steps = protocol_retries = 0
    http_request_attempts = 0
    llm_time = eval_time = 0.0
    prompt_tokens = completion_tokens = cached_prompt_tokens = instruction_tokens = 0
    eval_records: List[Tuple[str, Optional[str], float, float]] = []
    tool_records: List[Tuple[str, str, Optional[object]]] = []
    llm_call_traces: List[Dict[str, object]] = []
    tool_call_traces: List[Dict[str, object]] = []
    protocol_failures: List[Dict[str, object]] = []
    usage_attempts: List[Dict[str, object]] = []

    def augment_latest_message() -> None:
        nonlocal prev_augmented_idx
        if observation_augmenter is None or len(messages) < 2:
            return
        index = len(messages) - 1
        message = messages[index]
        if message.get("role") not in ("user", "tool") or index == prev_augmented_idx:
            return
        content = message.get("content")
        if not isinstance(content, str):
            raise TypeError("Environment messages must contain text")
        messages[index] = {**message, "content": observation_augmenter(content)}
        prev_augmented_idx = index

    def prepared_messages() -> Optional[List[Message]]:
        if max_prompt_tokens is not None and prompt_tokens >= max_prompt_tokens:
            return None
        if max_context_tokens is not None:
            message_allowance = max_context_tokens - schema_token_estimate
            if message_allowance < 0:
                return None
            prepared = _trim_messages(messages, message_allowance)
            if _estimate_tokens(prepared) + schema_token_estimate > max_context_tokens:
                return None
        else:
            prepared = messages
        return copy.deepcopy(prepared)

    def generate(send_messages: List[Message], *, forced: bool) -> Tuple[LLMOutput, Dict[str, object]]:
        nonlocal llm_time, api_calls, http_request_attempts
        nonlocal prompt_tokens, completion_tokens, cached_prompt_tokens, instruction_tokens
        start = time.perf_counter()
        if native:
            output = llm.generate(send_messages, tools=schemas, tool_choice="none" if forced else "auto")
        else:
            output = llm.generate(send_messages)
        elapsed = time.perf_counter() - start
        llm_time += elapsed
        api_calls += 1
        http_request_attempts += output.request_attempts
        if output.prompt_tokens is not None:
            prompt_tokens += output.prompt_tokens
            if api_calls == 1:
                instruction_tokens = output.prompt_tokens
        if output.completion_tokens is not None:
            completion_tokens += output.completion_tokens
        if output.cached_prompt_tokens is not None:
            cached_prompt_tokens += output.cached_prompt_tokens
        if output.tool_calls:
            # Backend implementations other than the built-in client must also
            # satisfy the envelope contract before any hook or tool can run.
            ids = set()
            for native_call in output.tool_calls:
                call_id = native_call.get("id") if isinstance(native_call, dict) else None
                if not isinstance(call_id, str) or not call_id.strip() or call_id in ids:
                    raise ValueError("Native response requires non-empty unique call IDs")
                ids.add(call_id)
        attempts = copy.deepcopy(output.attempt_usage)
        usage_attempts.append({"llm_call_index": api_calls, "attempts": attempts})
        original = copy.deepcopy(output.assistant_message)
        if original is None:
            original = {"role": "assistant", "content": output.text}
            if output.tool_calls:
                original["tool_calls"] = copy.deepcopy(output.tool_calls)
        record = {
            "input_messages": copy.deepcopy(send_messages),
            "output_message": original,
            "output_message_index": None,
            "raw_output": output.text,
            "finish_reason": output.finish_reason,
            "attempt_usage": attempts,
            "forced": forced,
            "latency_seconds": elapsed,
            "request_attempts": output.request_attempts,
            "usage": {
                "input_tokens": output.prompt_tokens,
                "output_tokens": output.completion_tokens,
                "cache": {
                    "reported": output.cached_prompt_tokens is not None or output.cache_write_prompt_tokens is not None,
                    "read_tokens": output.cached_prompt_tokens,
                    "write_tokens": output.cache_write_prompt_tokens,
                },
            },
        }
        return output, record

    def record_assistant(output: LLMOutput, record: Dict[str, object], text: str) -> None:
        if native or output.tool_calls:
            message = copy.deepcopy(record["output_message"])
        else:
            message = {"role": "assistant", "content": text}
        messages.append(message)
        record["output_message_index"] = len(messages) - 1
        if record["raw_output"] == message.get("content"):
            record.pop("raw_output", None)
        llm_call_traces.append(record)
        _append_to_steps(text, steps)
        if output.tool_calls:
            steps.append("Native tool calls: " + json.dumps(output.tool_calls, ensure_ascii=False, allow_nan=False))

    def reject_decision(output: LLMOutput, reason: str, *, forced: bool) -> None:
        protocol_failures.append({
            "agent_step": agent_steps, "llm_call_index": api_calls,
            "forced": forced, "reason": reason, "finish_reason": output.finish_reason,
        })
        notice = "Protocol error: " + reason + ". No tool was executed."
        # Every delivered native call gets a paired rejection, including a
        # forbidden multiple-call batch. Never execute only the first one.
        if output.tool_calls:
            seen = set()
            for call in output.tool_calls:
                call_id = call.get("id")
                if not isinstance(call_id, str) or not call_id or call_id in seen:
                    raise ValueError("Native response has invalid call IDs; cannot safely continue its history")
                seen.add(call_id)
                messages.append({"role": "tool", "tool_call_id": call_id, "content": notice})
        elif not forced:
            messages.append({
                "role": "user",
                "content": notice + (" Use the supplied function tools or submit your final answer."
                                    if native else " Use one Action directive or Answer: followed by your final answer."),
            })
        steps.append(notice)

    effective_max_steps = max_steps if max_steps is not None else 999999
    for step_index in range(effective_max_steps):
        if max_evals is not None and evaluations >= max_evals:
            aborted, abort_reason = True, "Maximum evaluations reached"
            break
        if time_budget is not None and total_overhead >= time_budget:
            aborted, abort_reason = True, "Time budget exceeded"
            break
        lock_context = llm_lock if llm_lock is not None else nullcontext()
        with lock_context:
            augment_latest_message()
            send_messages = prepared_messages()
            if send_messages is None:
                aborted = True
                abort_reason = ("Prompt token budget exceeded" if max_prompt_tokens is not None
                                and prompt_tokens >= max_prompt_tokens else "Context token budget exceeded")
                break
            output, call_trace = generate(send_messages, forced=False)
            agent_steps += 1
            text = output.text.strip()
            action = None
            protocol_error = None
            if output.finish_reason == "length":
                protocol_error = "Model completion token limit reached"
            elif output.tool_calls:
                if not native:
                    protocol_error = "Native tool calls received in text protocol"
                elif len(output.tool_calls) != 1:
                    protocol_error = "Exactly one native tool call is allowed per decision"
                else:
                    function = output.tool_calls[0].get("function") or {}
                    name, argument = function.get("name"), function.get("arguments")
                    try:
                        if not isinstance(name, str) or not name:
                            raise ValueError("missing function name")
                        if not isinstance(argument, str):
                            raise ValueError("arguments must be a JSON object string")
                        parsed = json.loads(argument)
                        if not isinstance(parsed, dict):
                            raise ValueError("arguments must be a JSON object")
                        json.dumps(parsed, allow_nan=False)
                        action = (name, argument)
                    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
                        protocol_error = "Invalid native function arguments: " + str(exc)
            elif native:
                if _extract_action(text) is not None:
                    protocol_error = "Text Action is not a native function call"
                elif text:
                    answer = _extract_answer(text) or structured_final_answer(text) or unlabelled_final_answer(text)
                    if answer is None:
                        protocol_error = "No final answer outside reasoning or protocol examples"
                else:
                    protocol_error = "LLM returned empty response"
            else:
                action = _extract_action(text)
                if action is None:
                    answer = _extract_answer(text)
                    if not answer:
                        protocol_error = "Missing Action directive" if text else "LLM returned empty response"
            if action is not None and action[0] not in tools:
                protocol_error = f"Unknown tool '{action[0]}'"
                action = None
            record_assistant(output, call_trace, _truncate_after_action(text) if action and not native else text)
            if protocol_error is not None:
                reject_decision(output, protocol_error, forced=False)
                if protocol_retries < max_protocol_retries and step_index + 1 < effective_max_steps:
                    protocol_retries += 1
                    continue
                aborted, abort_reason = True, protocol_error
                break
            if answer is not None:
                answer_source = "natural_model_answer"
                break
            if action is None:
                raise RuntimeError("Decision produced neither an answer nor a tool action")
            tool_name, argument = action
            tool = tools[tool_name]
            request_message_index = len(messages) - 1
            if pre_tool_hook is not None:
                pre_tool_hook(tool_name, argument)

        steps.append(f"Tool input: {argument}")
        input_error = False
        try:
            perf, raw_overhead, tool_output = _parse_tool_return(tool(argument))
        except ToolInputError as exc:
            input_error = True
            perf, raw_overhead, tool_output = None, 0.0, f"Tool error: {exc}"
        overhead = raw_overhead * overhead_scale
        if not math.isfinite(overhead) or not math.isfinite(total_overhead + overhead):
            raise ValueError("Tool cost overflow")
        eval_time += overhead
        total_overhead += overhead
        if agent_clock is not None:
            agent_clock.advance(overhead)
        evaluations += 1
        tool_records.append((tool_name, argument, tool_output))
        tool_trace: Dict[str, object] = {
            "request_message_index": request_message_index,
            "result_message_index": None, "name": tool_name,
            "arguments": _trace_argument(argument), "raw_arguments": argument,
            "canonical_argument": _canonicalize_payload(argument),
            "tool_result": copy.deepcopy(tool_output),
            "performance": perf, "simulated_cost_seconds": overhead,
            "visible_to_model": False, "included_in_eval_records": False,
            "input_error": input_error,
        }
        if time_budget is not None and total_overhead >= time_budget:
            over_budget_note = (
                "Observation: [over-budget — result withheld. "
                "This evaluation reached or exceeded the time budget.]"
            )
            steps.append("Observation: [over-budget, result withheld]")
            if tool_output is not None:
                tool_trace["withheld_result"] = tool_output
            if native:
                messages.append({
                    "role": "tool", "tool_call_id": output.tool_calls[0]["id"],
                    "name": tool_name, "content": over_budget_note,
                })
                tool_trace["result_message_index"] = len(messages) - 1
                tool_trace["observation"] = over_budget_note
                tool_trace["response_kind"] = "withheld_notice"
                over_budget_note = None
            tool_call_traces.append(tool_trace)
            aborted, abort_reason = True, "Time budget exceeded"
            break
        if perf is not None:
            eval_records.append((argument, _canonicalize_payload(argument), perf, overhead))
            tool_trace["included_in_eval_records"] = True
        observation = "Observation: " + (str(tool_output) if tool_output is not None else f"perf={perf:.6f}")
        if include_cost_in_observation and overhead_scale > 0.0 and overhead >= 0.5:
            observation += f" | cost={overhead:.0f}s" if tool_output is not None else f", cost={overhead:.0f}s"
            if time_budget is not None:
                observation += f" [time_left={max(0.0, time_budget - total_overhead):.0f}s]"
        elif include_overhead_in_observation:
            observation += f" | overhead={overhead:.2f}" if tool_output is not None else f", overhead={overhead:.2f}"
        message = {"role": "user", "content": observation}
        if native:
            message.update(role="tool", tool_call_id=output.tool_calls[0]["id"], name=tool_name)
        messages.append(message)
        steps.append(observation)
        tool_trace.update(visible_to_model=True, result_message_index=len(messages) - 1, observation=observation)
        if tool_output is not None and not isinstance(tool_output, str):
            tool_trace["structured_result"] = tool_output
        tool_call_traces.append(tool_trace)
    else:
        aborted, abort_reason = True, "Maximum steps reached"

    if aborted and answer is None:
        note = (f"System: Loop aborted ({abort_reason or 'Loop aborted'}). "
                "Respond immediately with Answer: <your final choice> and no other text.")
        if over_budget_note is not None:
            note = over_budget_note + "\n\n" + note
        messages.append({"role": "user", "content": note})
        steps.append(note)
        lock_context = llm_lock if llm_lock is not None else nullcontext()
        with lock_context:
            augment_latest_message()
            send_messages = prepared_messages()
            # Do not silently send a request larger than its context/token cap.
            if send_messages is not None:
                forced, forced_trace = generate(send_messages, forced=True)
                forced_text = forced.text.strip()
                record_assistant(forced, forced_trace, forced_text)
                if forced.tool_calls:
                    reject_decision(forced, "Tools are disabled during forced final", forced=True)
                elif forced.finish_reason == "length":
                    reject_decision(forced, "Forced final completion token limit reached", forced=True)
                elif forced_text:
                    # A textual Action is not a forced answer either.
                    if _extract_action(forced_text) is not None:
                        reject_decision(forced, "Action received during forced final", forced=True)
                    else:
                        answer = (_extract_answer(forced_text) or structured_final_answer(forced_text)
                                  or unlabelled_final_answer(forced_text))
                        if answer is None:
                            reject_decision(forced, "Forced final contains only reasoning or protocol examples", forced=True)
                        else:
                            answer_source = "forced_model_answer"
                else:
                    reject_decision(forced, "Forced final returned empty response", forced=True)

    if answer is not None:
        raw_perf, answer_overhead = _finalize_answer(
            answer, eval_records, answer_evaluator, tool_records, total_overhead,
        )
        answer_perf, answer_metrics = _unpack_perf(raw_perf)
        if answer_evaluator is not None:
            answer_score_source = "answer_evaluator"
        elif answer_perf is not None:
            answer_score_source = "matching_tool_call"
    if (tuning_final_policy == "legacy" and answer is not None and answer_perf is None
            and answer_metrics is None and answer_evaluator is None and eval_records):
        scored = [(raw, perf, overhead) for raw, _, perf, overhead in eval_records if perf is not None]
        if scored:
            answer, answer_perf, answer_overhead = max(scored, key=lambda record: record[1])
            answer_source = answer_score_source = "best_evaluated_fallback"

    result = LoopResult(
        answer=answer, answer_perf=answer_perf, answer_overhead=answer_overhead,
        answer_metrics=answer_metrics, steps=steps, total_overhead=total_overhead,
        aborted=aborted, evaluations=evaluations, api_calls=api_calls,
        llm_time=llm_time, eval_time=eval_time, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, cached_prompt_tokens=cached_prompt_tokens,
        instruction_tokens=instruction_tokens, messages=messages,
        tool_records=tool_records, eval_records=eval_records,
    ).__dict__
    result.update(
        tool_protocol=resolved_protocol, max_protocol_retries=max_protocol_retries,
        tuning_final_policy=tuning_final_policy, protocol_retries=protocol_retries,
        protocol_failures=protocol_failures, agent_steps=agent_steps,
        http_request_attempts=http_request_attempts, usage_attempts=usage_attempts,
        termination_reason=abort_reason if aborted else "Natural answer",
        answer_source=answer_source, answer_score_source=answer_score_source,
    )
    if capture_trace_v2:
        result["_trace_v2_capture"] = {
            "llm_calls": llm_call_traces, "tool_calls": tool_call_traces,
            "termination_reason": result["termination_reason"], "answer_source": answer_source,
        }
    return result


def _truncate_after_action(text: str) -> str:
    """Retain the complete real action, not just its first JSON line."""
    from expgym.tool_protocol import truncate_text_action
    return truncate_text_action(text)


def _append_to_steps(text: str, steps: List[str]) -> None:
    """Append non-empty lines from text to steps list."""
    for line in text.splitlines():
        clean = line.strip()
        if clean:
            steps.append(clean)


def build_system_prompt(
    *,
    instruction_notes: Optional[List[str]] = None,
    force_answer: bool = False,
    force_reason: Optional[str] = None,
) -> str:
    instruction_lines = [
        "You are a tool-using assistant operating in a Thought/Action/Observation loop.",
        "",
        "On EVERY turn you MUST output BOTH:",
        "  Thought: <your reasoning>",
        "  Action: <tool_name> <json_payload>",
        "Then STOP immediately and wait for the Observation from the system.",
        "",
        "Rules:",
        "- Always include BOTH a Thought AND an Action. Never output only a Thought.",
        "- Only one Action per turn.",
        "- Do not write Observation yourself.",
        "- When confident in your final answer, reply with ONLY: Answer: <your answer>",
    ]
    if force_answer:
        reason = force_reason or "a limit was reached"
        instruction_lines.append(
            f"The loop stopped because {reason}. Respond immediately with "
            "`Answer: <final choice>` and no other text."
        )
    if instruction_notes:
        instruction_lines.extend(note for note in instruction_notes if note)
    return "\n".join(instruction_lines)


def _canonicalize_payload(payload: str) -> Optional[str]:
    try:
        data = json.loads(payload)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return None
    try:
        if isinstance(data, dict):
            return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if isinstance(data, list):
            return json.dumps(data, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return None
    return None


def _trace_argument(payload: str) -> object:
    """Preserve machine-readable tool arguments without duplicating raw JSON."""
    try:
        value = json.loads(payload)
        json.dumps(value, allow_nan=False)
        return value
    except (ValueError, TypeError, OverflowError, RecursionError):
        return {"raw": payload, "encoding": "text"}


def _lookup_answer_metrics(
    answer_text: str,
    eval_records: List[Tuple[str, Optional[str], float, float]],
) -> Tuple[Optional[float], Optional[float]]:
    canonical_answer = _canonicalize_payload(answer_text)
    for raw_argument, canonical_argument, perf, overhead in reversed(eval_records):
        # A JSON configuration must match the complete answer; mentioning it
        # inside prose is not a scored final configuration.
        if canonical_argument is not None:
            if canonical_answer == canonical_argument:
                return perf, overhead
        elif canonical_answer:
            continue
        else:
            if raw_argument in answer_text:
                return perf, overhead
    return None, None


def _finalize_answer(
    answer: str,
    eval_records: List[Tuple[str, Optional[str], float, float]],
    evaluator: Optional[Callable[[str], float]],
    tool_records: List[Tuple[str, str, Optional[object]]],
    total_overhead: float,
) -> Tuple[Optional[object], Optional[float]]:
    """Return (perf_or_metrics, overhead).

    If the evaluator returns a dict, the dict is returned as-is so the
    caller can store it in ``answer_metrics``.
    """
    if evaluator is not None:
        try:
            signature = inspect.signature(evaluator)
        except (TypeError, ValueError) as exc:
            raise TypeError("Answer evaluator must expose a callable signature") from exc
        try:
            signature.bind(answer, tool_records)
        except TypeError:
            signature.bind(answer)
            result = evaluator(answer)
        else:
            result = evaluator(answer, tool_records)
        return result, total_overhead
    return _lookup_answer_metrics(answer, eval_records)


def _unpack_perf(
    raw: Optional[object],
) -> Tuple[Optional[float], Optional[Dict[str, object]]]:
    """Unpack an evaluator result into (scalar_perf, metrics_dict).

    If *raw* is a dict (multi-metric evaluator), extract ``label_acc`` as the
    primary scalar and return the full dict as metrics.  Otherwise treat *raw*
    as a plain float.
    """
    if raw is None:
        return None, None
    # Validate before extracting a primary scalar; invalid backend values must
    # never become a finite score through clipping or fallback selection.
    json.dumps(raw, allow_nan=False)
    if isinstance(raw, dict):
        primary = raw.get("label_acc")
        if primary is None:
            # Fallback: pick first numeric value
            for v in raw.values():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    primary = float(v)
                    break
        if isinstance(primary, bool) or not isinstance(primary, (int, float)) or not math.isfinite(primary):
            raise ValueError("Evaluator metrics must contain a finite numeric primary score")
        return float(primary), raw
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise TypeError("Evaluator performance must be numeric, not boolean or text")
    scalar = float(raw)
    if not math.isfinite(scalar):
        raise ValueError("Evaluator performance must be finite")
    return scalar, None


def _parse_tool_return(result: ToolReturn) -> Tuple[Optional[float], float, Optional[object]]:
    if not isinstance(result, tuple) or len(result) not in (2, 3):
        raise TypeError("Tool must return (perf, cost), (output, cost), or (output, perf, cost)")
    if len(result) == 2:
        first, cost = result
        if isinstance(first, bool):
            raise TypeError("Tool performance cannot be boolean")
        perf, output = (first, None) if isinstance(first, (int, float)) else (None, first)
    else:
        output, perf, cost = result
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise ValueError("Tool cost must be finite and non-negative")
    if perf is not None:
        if isinstance(perf, bool) or not isinstance(perf, (int, float)) or not math.isfinite(perf):
            raise ValueError("Tool performance must be finite numeric or None")
        perf = float(perf)
    return perf, float(cost), output


def _extract_answer(block: str) -> Optional[str]:
    from expgym.tool_protocol import extract_text_answer
    return extract_text_answer(block)


def _extract_action(block: str) -> Optional[Tuple[str, str]]:
    from expgym.tool_protocol import extract_text_action
    return extract_text_action(block)


def _strip_json_protocol_suffix(argument: str) -> str:
    """Drop a joined ReAct directive after an otherwise complete JSON value.

    Real chat models occasionally omit the requested newline and emit output
    such as ``Action: tool {"x": 1}Answer: ...``.  Passing the joined suffix to
    a JSON tool turns a valid action into a spurious parse error.  Only known
    protocol labels are stripped; arbitrary trailing text remains malformed
    and is still surfaced through the normal tool-error path.
    """
    if not argument or argument[0] not in "{[\"":
        return argument
    try:
        _value, end = json.JSONDecoder().raw_decode(argument)
    except (json.JSONDecodeError, TypeError):
        return argument
    trailing = argument[end:].lstrip()
    if not trailing:
        return argument[:end]
    normalized = _normalize_label(trailing).lower()
    if any(
        normalized.startswith(label)
        for label in ("thought:", "action:", "answer:", "observation:", "system:")
    ):
        return argument[:end]
    return argument


def _normalize_label(line: str) -> str:
    clean = line.strip()
    while clean and clean[0] in "*_ -":
        clean = clean[1:].lstrip()
    return clean


def _strip_markup_prefix(text: str) -> str:
    clean = text
    while clean and clean[0] in "*_` -":
        clean = clean[1:].lstrip()
    return clean


class FakeLLM(LLMBackend):
    """Rule-based LLM stub that replays a predefined plan of tool calls."""

    def __init__(
        self,
        plan: Optional[List[Tuple[str, str]]] = None,
        *,
        config_ids: Optional[List[str]] = None,
        probes: int = 3,
        final_answer: Optional[str] = None,
    ) -> None:
        if plan is None:
            cfgs = config_ids or []
            limited = cfgs[: max(1, probes)] if cfgs else []
            plan = [("run_config", cfg_id) for cfg_id in limited]
        self._plan = plan
        self._step = 0
        self._last_payload: Optional[str] = None
        self._last_tool: Optional[str] = None
        self._final_answer = final_answer

    def generate(self, messages) -> LLMOutput:
        # A budget/horizon stop can occur before this stub exhausts its plan.
        # Honor the same final-answer instruction as a real backend instead
        # of returning another Action that cannot be scored as a configuration.
        latest = messages[-1] if isinstance(messages, list) and messages else {}
        forced_answer = (
            isinstance(latest, dict)
            and latest.get("role") == "user"
            and "System: Loop aborted (" in latest.get("content", "")
            and "Respond immediately with Answer:" in latest.get("content", "")
        )
        if not forced_answer and self._step < len(self._plan):
            tool_name, payload = self._plan[self._step]
            self._last_payload = payload
            self._last_tool = tool_name
            self._step += 1
            text = (
                f"Thought: I will inspect candidate {self._step}.\n"
                f"Action: {tool_name} {payload}"
            )
            return LLMOutput(text=text)

        self._step += 1
        choice = self._final_answer or self._last_payload or "No viable configuration"
        if forced_answer:
            return LLMOutput(text=f"Answer: {choice}")
        text = (
            "Thought: I have enough signal from the evaluated configs.\n"
            f"Answer: {choice}"
        )
        return LLMOutput(text=text)
