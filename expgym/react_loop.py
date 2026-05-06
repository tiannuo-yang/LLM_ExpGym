"""Minimal ReAct-style loop plus a fake LLM backend.

Uses proper multi-turn chat messages (system/user/assistant) instead of
flat-string prompts, so chat-tuned LLMs can track their own prior outputs.
"""
from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass
import json
from typing import Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("expgym")

ToolReturn = Union[Tuple[float, float], Tuple[str, float], Tuple[object, float, float]]
ToolFn = Callable[[str], ToolReturn]

Message = Dict[str, str]  # {"role": ..., "content": ...}


@dataclass
class LLMOutput:
    text: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


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
    instruction_tokens: int
    messages: List[Dict[str, str]]


def _estimate_tokens(messages: List[Message]) -> int:
    """Conservative token estimate: ~3 chars per token.

    Qwen/CJK-capable models tokenize at ~3 chars/token for English text
    with JSON/config content.  Using 3 instead of 4 to be safe.
    """
    return sum(len(m.get("content", "")) for m in messages) // 3


def _trim_messages(
    messages: List[Message],
    max_tokens: int,
    *,
    protected_tail: int = 4,
    truncated_obs_chars: int = 600,
) -> List[Message]:
    """Trim older observation messages to stay within context budget.

    Strategy:
      1. Always preserve system prompt (index 0) + initial context (index 1).
      2. Always preserve the most recent *protected_tail* messages.
      3. First pass: truncate long observation messages in the middle.
      4. Second pass: if still over, drop middle messages entirely.
    """
    if _estimate_tokens(messages) <= max_tokens:
        return messages

    result = [copy.copy(m) for m in messages]

    # Boundaries
    protected_start = min(2, len(result))
    protected_end = min(protected_tail, len(result) - protected_start)
    mid_start = protected_start
    mid_end = len(result) - protected_end

    # Pass 1: truncate long observation messages
    for i in range(mid_start, mid_end):
        if _estimate_tokens(result) <= max_tokens:
            break
        msg = result[i]
        content = msg.get("content", "")
        if msg["role"] == "user" and len(content) > truncated_obs_chars:
            result[i] = {**msg, "content": content[:truncated_obs_chars] + "\n[... truncated ...]"}

    # Pass 2: drop middle messages if still over
    if _estimate_tokens(result) > max_tokens and mid_end > mid_start:
        # Drop oldest middle messages one-by-one until under budget
        drop_count = 0
        for i in range(mid_start, mid_end):
            drop_count += 1
            trimmed = (
                result[:mid_start]
                + [{"role": "user", "content": f"[{drop_count} earlier turns omitted]"}]
                + result[mid_start + drop_count:]
            )
            if _estimate_tokens(trimmed) <= max_tokens:
                result = trimmed
                break
        else:
            # Drop all middle messages
            result = (
                result[:mid_start]
                + [{"role": "user", "content": f"[{drop_count} earlier turns omitted]"}]
                + result[mid_end:]
            )

    # Pass 3: if still over, truncate remaining observations (including tail)
    if _estimate_tokens(result) > max_tokens:
        for i in range(len(result) - 1, -1, -1):
            if _estimate_tokens(result) <= max_tokens:
                break
            msg = result[i]
            content = msg.get("content", "")
            if msg["role"] == "user" and len(content) > truncated_obs_chars:
                result[i] = {**msg, "content": content[:truncated_obs_chars] + "\n[... truncated ...]"}

    return result


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
) -> Dict[str, object]:
    """Execute a ReAct loop using proper multi-turn chat messages."""

    # --- Build initial message history ---
    messages: List[Message] = []
    sys_text = system_prompt or build_system_prompt(instruction_notes=instruction_notes)
    messages.append({"role": "system", "content": sys_text})

    if context:
        messages.append({"role": "user", "content": context.strip()})

    # --- Tracking variables ---
    steps: List[str] = []
    total_overhead = 0.0
    answer: Optional[str] = None
    answer_perf: Optional[float] = None
    answer_metrics: Optional[Dict[str, object]] = None
    answer_overhead: Optional[float] = None
    aborted = False
    _over_budget_note: Optional[str] = None
    _prev_augmented_idx: Optional[int] = None
    evaluations = 0
    api_calls = 0
    llm_time = 0.0
    eval_time = 0.0
    prompt_tokens = 0
    completion_tokens = 0
    instruction_tokens = 0

    abort_reason: Optional[str] = None
    eval_records: List[Tuple[str, Optional[str], float, float]] = []
    tool_records: List[Tuple[str, str, Optional[object]]] = []

    # Log system prompt and context for trace output
    steps.append("System Prompt:")
    steps.append(sys_text)
    steps.append("")
    if context:
        steps.append(f"Prompt: Task description:\n{context.strip()}")

    effective_max_steps = max_steps if max_steps is not None else 999999
    for _ in range(effective_max_steps):
        # Inject graph/diversity context into the latest user observation.
        # Each observation permanently keeps its graph snapshot so traces
        # honestly record what the LLM saw at every step.
        if observation_augmenter is not None and len(messages) >= 3:
            last_user = messages[-1]
            if last_user.get("role") == "user" and (len(messages) - 1) != _prev_augmented_idx:
                augmented = observation_augmenter(last_user["content"])
                messages[-1] = {**last_user, "content": augmented}
                _prev_augmented_idx = len(messages) - 1

        # Build send_messages for the LLM call (may be trimmed).
        if max_context_tokens is not None:
            send_messages = _trim_messages(messages, max_context_tokens)
        else:
            send_messages = list(messages)
        start = time.perf_counter()
        llm_output = llm.generate(send_messages)
        api_elapsed = time.perf_counter() - start
        llm_time += api_elapsed
        api_calls += 1
        if llm_output.prompt_tokens is not None:
            prompt_tokens += llm_output.prompt_tokens
            if api_calls == 1:
                instruction_tokens = llm_output.prompt_tokens
        if llm_output.completion_tokens is not None:
            completion_tokens += llm_output.completion_tokens
        output = llm_output.text.strip()
        if not output:
            aborted = True
            abort_reason = "LLM returned empty response"
            break

        # Safety cap: truncate degenerate/runaway outputs (>8000 chars)
        if len(output) > 8000:
            logger.warning("Truncating degenerate LLM output (%d chars -> 8000)", len(output))
            output = output[:8000] + "\n[... output truncated due to excessive length ...]"

        action = _extract_action(output)
        if action:
            truncated = _truncate_after_action(output)
            messages.append({"role": "assistant", "content": truncated})
            _append_to_steps(truncated, steps)
        else:
            answer = _extract_answer(output)
            if answer:
                messages.append({"role": "assistant", "content": output})
                _append_to_steps(output, steps)
                answer_perf, answer_overhead = _lookup_answer_metrics(answer, eval_records)
                break
            messages.append({"role": "assistant", "content": output})
            _append_to_steps(output, steps)
            aborted = True
            abort_reason = "Missing Action directive"
            break

        tool_name, argument = action
        tool = tools.get(tool_name)
        if tool is None:
            aborted = True
            abort_reason = f"Unknown tool '{tool_name}'"
            break

        steps.append(f"Tool input: {argument}")
        try:
            perf, raw_overhead, tool_output = _parse_tool_return(tool(argument))
        except Exception as exc:
            # Gracefully handle tool errors (e.g. malformed LLM payloads)
            perf, raw_overhead, tool_output = None, 0.0, f"Tool error: {exc}"
        overhead = float(raw_overhead) * overhead_scale
        eval_time += overhead
        total_overhead += overhead
        if agent_clock is not None:
            agent_clock.advance(overhead)
        evaluations += 1
        tool_records.append((tool_name, argument, tool_output))

        # Check budget BEFORE recording eval or showing observation —
        # if this eval pushed us over budget, the LLM should not benefit
        # from seeing the result, and it should not appear in
        # eval_records (which the fallback answer logic uses).
        if time_budget is not None and total_overhead >= time_budget:
            # Store the over-budget note but don't append as a separate
            # user message yet — it will be combined with the forced-answer
            # prompt to avoid consecutive user messages.
            _over_budget_note = (
                "Observation: [over-budget — result withheld. "
                "This evaluation exceeded the time budget.]"
            )
            steps.append("Observation: [over-budget, result withheld]")
            aborted = True
            abort_reason = "Time budget exceeded"
            break

        # Record eval AFTER budget check — over-budget evals are excluded.
        if perf is not None:
            canonical_argument = _canonicalize_payload(argument)
            eval_records.append((argument, canonical_argument, perf, overhead))

        if include_cost_in_observation and overhead_scale > 0.0 and overhead >= 0.5:
            # time_aware mode: show cost + time budget remaining.
            # Skip in FREE mode (overhead_scale=0) — don't show "cost=0s"
            # which would signal to the model that tools are free.
            # Also skip when overhead rounds to 0s (e.g. search_meta at
            # 0.05-0.2s) — showing "cost=0s" is misleading.
            # Only show time budget, not step/context budget — those are
            # internal limits, not part of the EEI cost signal.
            budget_parts = []
            if time_budget is not None:
                remaining = max(0.0, time_budget - total_overhead)
                budget_parts.append(f"time_left={remaining:.0f}s")
            budget_hint = ", ".join(budget_parts) if budget_parts else ""
            if tool_output is not None:
                observation = (
                    f"Observation: {tool_output} | cost={overhead:.0f}s"
                )
                if budget_hint:
                    observation += f" [{budget_hint}]"
            else:
                observation = (
                    f"Observation: perf={perf:.6f}, cost={overhead:.0f}s"
                )
                if budget_hint:
                    observation += f" [{budget_hint}]"
        elif include_overhead_in_observation:
            if tool_output is not None:
                observation = f"Observation: {tool_output} | overhead={overhead:.2f}"
            else:
                observation = f"Observation: perf={perf:.6f}, overhead={overhead:.2f}"
        else:
            if tool_output is not None:
                observation = f"Observation: {tool_output}"
            else:
                observation = f"Observation: perf={perf:.6f}"
        messages.append({"role": "user", "content": observation})
        steps.append(observation)
        if max_evals is not None and evaluations >= max_evals:
            aborted = True
            abort_reason = "Maximum evaluations reached"
            break
        if max_prompt_tokens is not None and prompt_tokens >= max_prompt_tokens:
            aborted = True
            abort_reason = "Prompt token budget exceeded"
            break
        if max_context_tokens is not None:
            if _estimate_tokens(messages) >= max_context_tokens:
                aborted = True
                abort_reason = "Context token budget exceeded"
                break
    else:
        aborted = True
        abort_reason = "Maximum steps reached"

    if aborted and answer is None:
        reason_text = abort_reason or "Loop aborted"
        note = (
            f"System: Loop aborted ({reason_text}). "
            "Respond immediately with Answer: <your final choice> "
            "and no other text."
        )
        # If there was an over-budget observation, combine it with the
        # forced-answer prompt into a single user message to preserve
        # proper assistant/user alternation.
        if _over_budget_note is not None:
            note = _over_budget_note + "\n\n" + note
            _over_budget_note = None
        messages.append({"role": "user", "content": note})
        steps.append(note)
        if max_context_tokens is not None:
            send_messages = _trim_messages(messages, max_context_tokens)
        else:
            send_messages = messages
        start = time.perf_counter()
        forced_output = llm.generate(send_messages)
        api_elapsed = time.perf_counter() - start
        llm_time += api_elapsed
        api_calls += 1
        if forced_output.prompt_tokens is not None:
            prompt_tokens += forced_output.prompt_tokens
        if forced_output.completion_tokens is not None:
            completion_tokens += forced_output.completion_tokens
        forced_text = forced_output.text.strip()
        if forced_text:
            messages.append({"role": "assistant", "content": forced_text})
            _append_to_steps(forced_text, steps)
            answer = _extract_answer(forced_text) or forced_text
            _perf_raw, answer_overhead = _finalize_answer(
                answer or "",
                eval_records,
                answer_evaluator,
                tool_records,
                total_overhead,
            )
            answer_perf, answer_metrics = _unpack_perf(_perf_raw)

    if answer is not None and answer_perf is None and answer_metrics is None:
        _perf_raw, answer_overhead = _finalize_answer(
            answer,
            eval_records,
            answer_evaluator,
            tool_records,
            total_overhead,
        )
        answer_perf, answer_metrics = _unpack_perf(_perf_raw)

    # Fallback: if the answer doesn't match any eval_record (e.g. the
    # agent hallucinated a config it never evaluated, or submitted a
    # non-config text), use the best evaluated config instead.  Only
    # applies when there is no external answer_evaluator (i.e. tuning).
    if (
        answer is not None
        and answer_perf is None
        and answer_metrics is None
        and answer_evaluator is None
        and eval_records
    ):
        valid_records = [
            (raw, perf, ovh)
            for raw, _canon, perf, ovh in eval_records
            if perf is not None and perf > 0
        ]
        if valid_records:
            best_raw, best_perf, best_ovh = max(
                valid_records, key=lambda r: r[1]
            )
            answer = best_raw
            answer_perf = best_perf
            answer_overhead = best_ovh
            logger.info(
                "Forced answer didn't match eval records; "
                "falling back to best evaluated config (perf=%.6f)",
                best_perf,
            )

    result = LoopResult(
        answer=answer,
        answer_perf=answer_perf,
        answer_overhead=answer_overhead,
        answer_metrics=answer_metrics,
        steps=steps,
        total_overhead=total_overhead,
        aborted=aborted,
        evaluations=evaluations,
        api_calls=api_calls,
        llm_time=llm_time,
        eval_time=eval_time,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        instruction_tokens=instruction_tokens,
        messages=messages,
    )
    return result.__dict__


def _truncate_after_action(text: str) -> str:
    """Return text up to and including the first Action line."""
    lines = []
    for line in text.splitlines():
        lines.append(line)
        if _normalize_label(line).startswith("Action:"):
            break
    return "\n".join(lines)


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
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
    if isinstance(data, list):
        return json.dumps(data, separators=(",", ":"))
    return None


def _lookup_answer_metrics(
    answer_text: str,
    eval_records: List[Tuple[str, Optional[str], float, float]],
) -> Tuple[Optional[float], Optional[float]]:
    canonical_answer = _canonicalize_payload(answer_text)
    for raw_argument, canonical_argument, perf, overhead in reversed(eval_records):
        if canonical_answer and canonical_argument:
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
            result = evaluator(answer, tool_records)
        except TypeError:
            result = evaluator(answer)
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
    if isinstance(raw, dict):
        primary = raw.get("label_acc")
        if primary is None:
            # Fallback: pick first numeric value
            for v in raw.values():
                if isinstance(v, (int, float)):
                    primary = float(v)
                    break
        return primary, raw
    return float(raw), None


def _parse_tool_return(result: ToolReturn) -> Tuple[Optional[float], float, Optional[object]]:
    if isinstance(result, tuple) and len(result) == 2:
        first, second = result
        if isinstance(first, (int, float)) and isinstance(second, (int, float)):
            return float(first), float(second), None
        if isinstance(second, (int, float)):
            return None, float(second), first
    if isinstance(result, tuple) and len(result) == 3:
        output, perf, overhead = result
        return float(perf) if perf is not None else None, float(overhead), output
    raise TypeError("Tool must return (perf, overhead) or (output, overhead).")


def _extract_answer(block: str) -> Optional[str]:
    lines = block.splitlines()
    for i, line in enumerate(lines):
        clean = _normalize_label(line)
        if "Answer:" in clean:
            first_part = clean.split("Answer:", 1)[-1].strip()
            # Capture remaining lines after "Answer:" for multi-line answers
            remaining = "\n".join(lines[i + 1:]).strip()
            if remaining:
                return first_part + "\n" + remaining if first_part else remaining
            return first_part
    return None


def _extract_action(block: str) -> Optional[Tuple[str, str]]:
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        clean = _normalize_label(lines[i])
        if "Action:" in clean:
            payload = clean.split("Action:", 1)[-1].strip()
            payload = _strip_markup_prefix(payload)
            if "[" in payload and "{" not in payload:
                tool_name, remainder = payload.split("[", 1)
                tool_name = _strip_markup_prefix(tool_name)
                body = remainder
                j = i
                while not body.rstrip().endswith("]") and j + 1 < len(lines):
                    j += 1
                    body += lines[j].strip()
                body = body.strip()
                if body.endswith("]"):
                    argument = body[:-1]
                    return tool_name.strip(), argument
                i = j
            else:
                parts = payload.split(None, 1)
                tool_name = _strip_markup_prefix(parts[0]) if parts else ""
                if len(parts) > 1 and parts[1].strip():
                    return tool_name.strip(), parts[1].strip()
                body = ""
                j = i
                while j + 1 < len(lines):
                    j += 1
                    next_line = lines[j].strip()
                    if next_line:
                        body = next_line
                        break
                return tool_name.strip(), body
        i += 1
    return None


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
        if self._step < len(self._plan):
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
        text = (
            "Thought: I have enough signal from the evaluated configs.\n"
            f"Answer: {choice}"
        )
        return LLMOutput(text=text)
