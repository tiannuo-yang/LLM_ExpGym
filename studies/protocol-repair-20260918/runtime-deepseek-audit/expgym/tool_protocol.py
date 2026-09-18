"""Provider-independent tool schemas and conservative final-answer parsing.

This module never executes a tool, reads reference answers, or changes scores.
Transport and scenario functions remain separate from the agent decision loop.
"""
from __future__ import annotations

import copy
import json
import math
import re
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

ANSWER_PROTOCOL_VERSION = "final-answer-boundary-v2"
AUDIT_ANSWER_PROTOCOL_VERSION = "audit-json-wrapper-v2"
AUDIT_FIELD_PROTOCOL_VERSION = "audit-literal-label-legacy-evidence-v2"
SEARCH_ANSWER_PROTOCOL_VERSION = "search-name-set-v2"


class AuditAnswerTypeError(ValueError):
    """The parsed Audit payload is not an object."""


def resolve_tool_protocol(llm: object, requested: str = "auto") -> str:
    """Resolve one protocol for both task instructions and loop transport."""
    if requested not in ("auto", "native", "text"):
        raise ValueError("tool_protocol must be auto, native, or text")
    capable = bool(getattr(llm, "supports_native_tools", False))
    native = requested == "native" or (requested == "auto" and capable)
    if native and not capable:
        raise ValueError("Native tools require a backend advertising supports_native_tools")
    return "native" if native else "text"


def _reject_constant(value: str) -> None:
    raise ValueError(f"Nonfinite JSON number: {value}")


def _finite_json(value: Any) -> Any:
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("JSON numbers must be finite")
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return value


def parse_json_answer(text: str) -> Any:
    """Parse one complete JSON answer, allowing a surrounding fence/semicolon.

    Do not search arbitrary prose for a JSON object: quoted example actions and
    configurations inside reasoning are not automatically final submissions.
    """
    if not isinstance(text, str):
        raise ValueError("A JSON answer must be text")
    cleaned = text.strip().rstrip(";").strip()
    if cleaned.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", cleaned, re.S | re.I)
        if match is None:
            raise ValueError("Unclosed or unsupported JSON fence")
        cleaned = match.group(1).strip().rstrip(";").strip()
    try:
        return _finite_json(json.loads(cleaned, parse_constant=_reject_constant))
    except (RecursionError, OverflowError) as exc:
        raise ValueError("JSON answer exceeds parser limits") from exc


_LABEL = re.compile(r"\b(?P<label>Final\s+Answer|Answer|Action|Observation|Thought|System)\s*:", re.I)
_ANSWER_LABEL = re.compile(
    r"(?<![^\W_])(?P<label>Final\s+Answer|Answer)(?P<closing>\*\*|__|\*|_)?\s*:", re.I,
)
_REASONING_TAG = re.compile(r"<(/?)(think|analysis|reasoning)\s*>", re.I)
_LINE_MARKUP = re.compile(r"[ \t]*(?:(?:[-+*]|\d+[.)])\s+)?(?:\#{1,6}\s+)?[*_]*[ \t]*\Z")
_EXAMPLE_OR_NEGATION = re.compile(
    r"\b(?:example|examples|quoted?|quoting|hypothetical|suppose|pretend|"
    r"do\s+not\s+(?:submit|execute|call|output|write|use)|"
    r"don['’]t\s+(?:submit|execute|call|output|write|use)|"
    r"(?:not|never)\s+(?:submit|execute|call|output|write|use)|"
    r"(?:not|isn['’]t)\s+(?:an?\s+)?(?:final\s+)?(?:answer|action)|"
    r"(?:would|could|might)\s+(?:say|write|output)|e\.g\.)\b", re.I,
)


def _protocol_view(text: str) -> Optional[str]:
    """Mask quotations, code and explicit reasoning without changing offsets.

    Apostrophes within words are not quote delimiters. An unclosed reasoning
    region invalidates the turn, rather than exposing its tentative decisions.
    """
    visible = list(text)

    def hide(start: int, end: int) -> None:
        for pos in range(start, end):
            if visible[pos] not in "\r\n":
                visible[pos] = " "

    position = 0
    while position < len(text):
        tag = _REASONING_TAG.match(text, position)
        if tag:
            if tag.group(1):
                return None
            stack, end = [tag.group(2).lower()], tag.end()
            for closing in _REASONING_TAG.finditer(text, end):
                end = closing.end()
                name = closing.group(2).lower()
                if closing.group(1):
                    if not stack or name != stack[-1]:
                        return None
                    stack.pop()
                else:
                    stack.append(name)
                if not stack:
                    break
            if stack:
                return None
            hide(position, end)
            position = end
            continue
        char = text[position]
        if char == "`" or (char == "~" and text.startswith("~~~", position)):
            width = 1
            while position + width < len(text) and text[position + width] == char:
                width += 1
            closing = text.find(char * width, position + width)
            end = len(text) if closing < 0 else closing + width
            hide(position, end)
            position = end
            continue
        if char in "\"'“‘":
            if char == "'" and position > 0 and (
                text[position - 1].isalnum()
                or re.search(r"\w(?:\*{1,2}|_{1,2})$", text[:position])
            ):
                position += 1
                continue
            delimiter = {"“": "”", "‘": "’"}.get(char, char)
            end = position + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                    continue
                if text[end] == delimiter:
                    end += 1
                    break
                end += 1
            end = min(end, len(text))
            hide(position, end)
            position = end
            continue
        position += 1
    return "".join(visible)


def _unfinished_example(prefix: str, visible_prefix: str) -> bool:
    """Track an explicitly introduced unquoted example across several lines."""
    blocked, fence = False, None
    for line, visible_line in zip(prefix.splitlines(), visible_prefix.splitlines()):
        stripped = visible_line.strip()
        marker = re.match(r"(`{3,}|~{3,})", line.strip())
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif marker.group(1)[0] == fence:
                fence, blocked = None, False
            continue
        if fence is not None:
            continue
        if _EXAMPLE_OR_NEGATION.search(stripped) and (
            stripped.endswith(":")
            or re.search(r"\b(?:is|be|following|submit|output|write|execute|call|use)\s*$", stripped, re.I)
        ):
            blocked = True
        elif re.match(r"(?:Thought:\s*)?(?:Now\s+I\s+(?:will|shall)|Actual\s+(?:decision|action|answer)\s*:)", stripped, re.I):
            blocked = False
    return blocked


def _directive_boundary(text: str, view: str, start: int) -> bool:
    line_start = view.rfind("\n", 0, start) + 1
    before = view[line_start:start]
    original_before = text[line_start:start]
    if _unfinished_example(text[:line_start], view[:line_start]):
        return False
    # A Markdown quotation or a quoted label is never an executable directive.
    if original_before.lstrip().startswith(">"):
        return False
    if _LINE_MARKUP.fullmatch(before):
        return bool(_LINE_MARKUP.fullmatch(original_before)
                    or re.search(r"</(?:think|analysis|reasoning)\s*>\s*[*_]*\s*$", original_before, re.I))
    # Accept a missing newline after a completed decision sentence. Merely
    # discussing an Action/Answer label inside a sentence is not a directive.
    stripped = before.rstrip(" *_\t")
    if not stripped:
        return False
    if _EXAMPLE_OR_NEGATION.search(before):
        return False
    if stripped[-1] in ".!?;":
        return True
    # Historical list-form reasoning sometimes joins its last evidence list
    # directly to Answer:. This is distinct from a bare JSON final plus another.
    return stripped[-1] == "]" and bool(re.match(r"\s*[-+*]\s+", before))


def _content_start(text: str, end: int) -> int:
    match = re.match(r"[ \t]*[*_]{0,2}\s*", text[end:])
    return end + match.end()


def _answer_content_start(text: str, match: re.Match) -> Optional[int]:
    """Remove markup belonging to the label, never markup in its payload."""
    prefix = text[:match.start()]
    opening = re.search(r"(\*\*|__|\*|_)$", prefix)
    marker = opening.group(1) if opening else ""
    closing = match.group("closing") or ""
    if closing and closing != marker:
        return None
    end = match.end()
    if marker and not closing:
        # **Answer:** and **Answer**: are both label wrappers.
        if text.startswith(marker, end):
            end += len(marker)
        # **Answer: Ada** emphasizes the whole submission. Its closing marker
        # belongs to the original payload and is retained, as in the historical
        # line parser; task-level name/JSON rules decide how to interpret it.
    while end < len(text) and text[end].isspace():
        end += 1
    return end


def _answer_payload(text: str) -> Optional[Tuple[str, bool]]:
    """Find one unambiguous directive and return its literal suffix.

    An introduction ending in ``final answer:`` is not a submission. Consecutive
    empty answer headings are wrappers, but two nonempty submissions are never
    resolved by taking the first/last one or consulting task reference answers.
    The boolean reports a line-start directive (which may contain plain text).
    """
    view = _protocol_view(text)
    if view is None or extract_text_action(text) is not None:
        return None
    labels = list(_ANSWER_LABEL.finditer(view))
    eligible = []
    for match in labels:
        if not _directive_boundary(text, view, match.start()):
            # A mention in prose is not another submission. Quoted/code/example
            # regions are already masked or rejected by _directive_boundary.
            continue
        start = _answer_content_start(text, match)
        if start is None:
            return None
        eligible.append((match, start))
    if not eligible:
        return None
    for (previous, start), (following, _) in zip(eligible, eligible[1:]):
        line_start = text.rfind("\n", 0, following.start()) + 1
        if text[start:line_start].strip():
            return None
        # Only line markup can separate adjacent empty headings.
        if not _LINE_MARKUP.fullmatch(text[line_start:following.start()]):
            return None
    match, start = eligible[-1]
    # A bare structured answer before a labelled one is a double submission.
    first = eligible[0][0]
    first_line_start = text.rfind("\n", 0, first.start()) + 1
    prefix_end = (first_line_start
                  if _LINE_MARKUP.fullmatch(text[first_line_start:first.start()])
                  else first.start())
    try:
        earlier = parse_json_answer(text[:prefix_end])
    except (ValueError, TypeError):
        pass
    else:
        if isinstance(earlier, (dict, list)):
            return None
    line_start = view.rfind("\n", 0, match.start()) + 1
    line_final = bool(_LINE_MARKUP.fullmatch(view[line_start:match.start()]))
    candidate = text[start:].strip()
    return (candidate, line_final) if candidate else None


def structured_final_answer(text: str) -> Optional[str]:
    """Recognize a complete structured final, including an inline Answer label.

    Only one nonempty final directive is allowed, outside quoted examples and
    closed reasoning regions. Its suffix must be a finite JSON object or list.
    Callers still prefer explicit actions over textual answers in legacy mode.
    """
    if not isinstance(text, str):
        return None
    if _protocol_view(text) is None or extract_text_action(text) is not None:
        return None
    try:
        value = parse_json_answer(text)
    except (ValueError, TypeError):
        pass
    else:
        return json.dumps(value, ensure_ascii=False, allow_nan=False) if isinstance(value, (dict, list)) else None
    payload = _answer_payload(text)
    if payload is None:
        return None
    candidate, _ = payload
    try:
        value = parse_json_answer(candidate)
    except (ValueError, TypeError):
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return None


def extract_text_answer(text: str) -> Optional[str]:
    """Extract a unique final, preserving the payload's literal contents."""
    if not isinstance(text, str):
        return None
    payload = _answer_payload(text)
    if payload is not None and payload[1]:
        return payload[0]
    return structured_final_answer(text)


def unlabelled_final_answer(text: str) -> Optional[str]:
    """Accept ordinary answer text, not a rejected protocol/reasoning example.

    Native responses and the historical forced-final path permit bare prose.
    They must not use that permission to bypass the explicit-answer parser's
    rejection of quoted directives, examples or incomplete reasoning regions.
    Call this only after explicit/structured final parsing; an answer containing
    literal protocol labels can still be submitted with an explicit Answer label.
    Tagged reasoning plus a final also requires that explicit final delimiter.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    if (_protocol_view(text) is None or _LABEL.search(text) or _ANSWER_LABEL.search(text)
            or _REASONING_TAG.search(text)):
        return None
    return text.strip()


def parse_final_answer(text: str, *, allow_unlabelled: bool = True) -> Optional[str]:
    """The shared runtime/offline text-to-final boundary, independent of task.

    Callers must reject provider-native tool calls and length-truncated outputs
    before invoking this text-only helper. Bare prose is enabled only where the
    transport already permits it (native or forced-final responses).
    """
    if not isinstance(text, str) or extract_text_action(text) is not None:
        return None
    answer = extract_text_answer(text)
    if answer is None and allow_unlabelled:
        answer = unlabelled_final_answer(text)
    return answer


def parse_audit_answer(prediction: Any) -> Dict[str, Any]:
    """Parse the same Audit payload for individual scoring and pool voting.

    Accept one object, an optional semicolon, and a complete JSON/no-language
    fence. Preserve the historical acceptance of explanation after a closing
    fence, but reject another object, fence, or protocol directive in that tail.
    Never extract a JSON example from arbitrary leading prose or alter fields.
    """
    if isinstance(prediction, dict):
        return prediction
    if not isinstance(prediction, str):
        raise AuditAnswerTypeError("An Audit answer must be a JSON object")
    # Keep the historical JSON field/coercion semantics. The versioned change
    # concerns wrappers and voting acceptance, not evidence or label values.
    cleaned = prediction.strip().rstrip(";").strip()
    try:
        value = json.loads(cleaned)
    except (ValueError, TypeError, RecursionError, OverflowError):
        match = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```(.*)", cleaned, re.S | re.I)
        if match is None:
            raise ValueError("Invalid Audit JSON wrapper") from None
        body, tail = match.groups()
        tail = tail.lstrip().lstrip(";").strip()
        view = _protocol_view(tail)
        tail_directives = (view is not None and any(
            _directive_boundary(tail, view, label.start())
            for pattern in (_LABEL, _ANSWER_LABEL)
            for label in pattern.finditer(view)
        ))
        if (view is None or "```" in tail or "~~~" in tail
                or tail_directives
                or "{" in view or "}" in view
                or re.search(r"(?m)^\s*\[", view)):
            raise ValueError("Ambiguous Audit answer after closing fence")
        try:
            value = json.loads(body.strip().rstrip(";").strip())
        except (ValueError, TypeError, RecursionError, OverflowError) as exc:
            raise ValueError("Invalid Audit JSON contents") from exc
    if not isinstance(value, dict):
        raise AuditAnswerTypeError("An Audit answer must be a JSON object")
    return value


def parse_search_answer(text: str) -> set[str]:
    """The existing name-F1 acceptance set, shared with Search majority vote."""
    if not text or not text.strip():
        return set()
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list):
            return {" ".join(str(name).lower().split()) for name in parsed if str(name).strip()}
    except (json.JSONDecodeError, TypeError):
        pass
    names = set()
    for part in re.split(r"[,;\n]", text):
        cleaned = re.sub(r"^\s*[\d]+[.)]\s*", "", part).strip().strip("-*•").strip()
        if 1 <= len(cleaned.split()) <= 5:
            names.add(" ".join(cleaned.lower().split()))
    return names


def audit_label_key(value: Any) -> str:
    """Keep literal label strings; never turn an incorrect alias into a label.

    Non-string labels cannot equal any public Audit label and share the invalid
    empty-string key. They are still votes, rather than silent abstentions.
    """
    return value if isinstance(value, str) else ""


def audit_evidence_key(value: Any) -> Tuple[int, ...]:
    """Match the historical individual metric's all-or-empty int-set rule.

    Its acceptance of non-list iterables and int-convertible values is retained
    for compatibility. This helper does not infer or repair evidence IDs.
    """
    try:
        values = {int(item) for item in value}
    except Exception:
        values = set()
    return tuple(sorted(values, key=str))


class _TextAction(NamedTuple):
    name: str
    payload: str
    end: int


def _bracket_end(text: str, start: int) -> Optional[int]:
    depth, quote, position = 0, None, start
    while position < len(text):
        char = text[position]
        if quote:
            if char == "\\":
                position += 2
                continue
            if char == quote:
                quote = None
        elif char == "'" and position > start and text[position - 1].isalnum():
            pass
        elif char in "\"'":
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return position + 1
        position += 1
    return None


def _protocol_suffix(text: str) -> bool:
    return bool(re.match(r"\s*[*_\- ]*(?:Thought|Action|Final\s+Answer|Answer|Observation|System)\s*:", text, re.I))


def _text_action(text: str) -> Optional[_TextAction]:
    if not isinstance(text, str):
        return None
    view = _protocol_view(text)
    if view is None:
        return None
    for match in _LABEL.finditer(view):
        if match.group("label").lower() != "action" or not _directive_boundary(text, view, match.start()):
            continue
        start = _content_start(text, match.end())
        tool = re.match(r"`?([A-Za-z_][A-Za-z0-9_.-]*)`?", text[start:])
        if tool is None:
            return None
        name = tool.group(1)
        name_end = start + tool.end()
        if name_end < len(text) and text[name_end] == "[":
            end = _bracket_end(text, name_end)
            if end is None:
                return None
            return _TextAction(name, text[name_end + 1:end - 1].strip(), end)
        if name_end < len(text) and not text[name_end].isspace():
            return None
        body_start = name_end
        while body_start < len(text) and text[body_start].isspace():
            body_start += 1
        if body_start == len(text) or _protocol_suffix(text[body_start:]):
            return _TextAction(name, "", name_end)
        body = text[body_start:]
        try:
            value, consumed = json.JSONDecoder(parse_constant=_reject_constant).raw_decode(body)
            _finite_json(value)
        except (ValueError, TypeError, RecursionError, OverflowError):
            consumed = None
        if consumed is not None and (not body[consumed:].strip() or _protocol_suffix(body[consumed:])):
            return _TextAction(name, body[:consumed], body_start + consumed)
        if body[0] == "[" and consumed is None:
            # Space-separated legacy brackets remain accepted for non-JSON
            # arguments; a valid JSON array above keeps its brackets intact.
            bracket_end = _bracket_end(text, body_start)
            if bracket_end is not None and (not text[bracket_end:].strip() or _protocol_suffix(text[bracket_end:])):
                return _TextAction(name, text[body_start + 1:bracket_end - 1].strip(), bracket_end)
        if body[0] in "{[":
            # Preserve malformed JSON and arbitrary trailing prose for the tool
            # error path, but stop before a later unquoted protocol directive.
            end = len(text)
            for suffix in _LABEL.finditer(view, body_start):
                if _directive_boundary(text, view, suffix.start()):
                    end = suffix.start()
                    break
            payload = text[body_start:end].rstrip()
            return _TextAction(name, payload, body_start + len(payload))
        # Legacy named/non-JSON arguments occupy one nonempty line.
        newline = text.find("\n", body_start)
        end = len(text) if newline < 0 else newline
        payload = text[body_start:end].rstrip()
        return _TextAction(name, payload, body_start + len(payload))
    return None


def extract_text_action(text: str) -> Optional[Tuple[str, str]]:
    """Extract the first explicit unquoted text-protocol action and its payload."""
    action = _text_action(text)
    return (action.name, action.payload) if action is not None else None


def truncate_text_action(text: str) -> str:
    """Keep the complete first action, excluding model-fabricated later turns."""
    action = _text_action(text)
    return text[:action.end].rstrip() if action is not None else text


def native_tool_schemas(tools: Dict[str, Callable]) -> List[Dict[str, Any]]:
    """Convert scenario metadata to OpenAI-compatible function definitions.

    Custom scenarios may omit metadata; their fallback explicitly permits a JSON
    object and does not invent argument names. Built-in scenarios supply exact
    schemas. Wrappers must preserve ``__expgym_tool_schema__``.
    """
    result = []
    for name, function in tools.items():
        schema = getattr(function, "__expgym_tool_schema__", None)
        if schema is None:
            schema = {
                "name": name,
                "description": (getattr(function, "__doc__", None) or name).strip(),
                "parameters": {"type": "object", "properties": {}, "additionalProperties": True},
            }
        else:
            schema = copy.deepcopy(schema)
            if schema.get("name") != name:
                raise ValueError(f"Tool schema name does not match registered tool: {name}")
            if not isinstance(schema.get("parameters"), dict):
                raise ValueError(f"Tool schema lacks parameters: {name}")
        result.append({"type": "function", "function": schema})
    return result


NATIVE_PROTOCOL_INSTRUCTION = (
    "Interaction protocol: use the API's supplied function tools to acquire feedback. "
    "A textual Action directive or an imitation of a tool result is not a tool call. "
    "Make at most one function call per assistant turn. After receiving the real tool "
    "result, decide whether another observation is useful. When ready, submit your "
    "final answer in the task's required format (Answer: followed by the answer is "
    "also accepted). Do not invent observations or claim an unexecuted call succeeded."
)


# Keep this byte-for-byte identical to build_system_prompt's fixed prefix.
LEGACY_PROTOCOL_INSTRUCTION = "\n".join([
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
])


def native_system_prompt(prompt: str) -> str:
    """Replace only the known complete legacy prefix, never arbitrary lines."""
    if prompt == LEGACY_PROTOCOL_INSTRUCTION or prompt.startswith(LEGACY_PROTOCOL_INSTRUCTION + "\n"):
        remaining = prompt[len(LEGACY_PROTOCOL_INSTRUCTION):]
    else:
        visible = _protocol_view(prompt)
        visible = prompt if visible is None else visible
        labelled_directive = any(
            re.search(r"\b(?:Action|Thought)\s*:\s*(?:<|\{|\[)", line, re.I)
            or (re.search(r"\b(?:Action|Thought)\s*:", line, re.I)
                and re.search(r"\b(?:must|output|emit|respond|reply|write|include|follow|format|protocol|loop)\b", line, re.I)
                and not re.search(r"\b(?:literal|field|schema|data|quotation)\b", line, re.I))
            or re.match(r"\s*[*_\- ]*Action\s*:\s*[A-Za-z_][\w.-]*\s+\{", line, re.I)
            for line in visible.splitlines()
        )
        labelled_fields = [line for line in visible.splitlines()
                           if re.match(r"\s*[*_\- ]*(?:Action|Thought)\s*:", line, re.I)
                           and not re.search(r"\b(?:literal|field|schema|data|quotation)\b", line, re.I)]
        paired_legacy_labels = (any(re.search(r"\bThought\s*:", line, re.I) for line in labelled_fields)
                                and any(re.search(r"\bAction\s*:", line, re.I) for line in labelled_fields))
        if (labelled_directive or paired_legacy_labels
                or re.search(r"Thought\s*/\s*Action|both\s+(?:a\s+)?Thought\s+and\s+(?:an?\s+)?Action|one\s+Action\s+per\s+turn", visible, re.I)):
            raise ValueError("Custom system prompt conflicts with native tool protocol; choose tool_protocol='text' or supply a native-compatible prompt")
        remaining = prompt
    return remaining + ("\n\n" if remaining else "") + NATIVE_PROTOCOL_INSTRUCTION
