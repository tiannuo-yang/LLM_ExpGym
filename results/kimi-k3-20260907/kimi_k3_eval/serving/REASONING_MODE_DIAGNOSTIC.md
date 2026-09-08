# Kimi-K3 requested thinking-off: offline diagnostic

Date: 2026-09-07. Scope: the completed 136-request benchmark smoke, deployment
`1203299`, fixed independent SGLang `0.5.16+pr32477`. This diagnostic reads saved
HTTP responses and installed source only. It sends no model requests, changes
no serving or evaluation configuration, and does not assert which marker
sequence the model actually generated.

## Result and reporting label

Use **“requested `thinking=false`; 6/136 responses contain nonempty
server-parsed `reasoning_content`.”** Do not describe the measured run as
guaranteed non-thinking, or interpret the reported zero reasoning-token count
as proof that no reasoning text was generated.

The [machine-readable evidence](REASONING_MODE_DIAGNOSTIC.json) records each
affected dump, SHA-256 hashes for all 136 responses and 17 relevant source
files, exact source locations, and the offline parser fixtures. The
[protocol report](../reports/smoke_protocol_diagnostic.md) provides the broader
ReAct/action-format audit.

| Saved-response observation | Count |
| --- | ---: |
| Requests explicitly containing `chat_template_kwargs.thinking=false` | 136/136 |
| Non-streaming responses | 136/136 |
| Reported top-level `usage.reasoning_tokens=0` | 136/136 |
| Responses with nonempty parsed `reasoning_content` | 6/136 |
| Total characters in those six fields | 21,707 |
| Affected requests with two input messages (first turn) | 6/6 |
| Affected responses also containing native tools markup in content | 4/6 |

The other two affected responses have valid textual `Action:` content. All
six are first-turn requests, excluding retained assistant history as the
source of these particular fields. The single arithmetic acceptance probe
returned valid content without a reasoning field under `thinking=false`;
that is a property of that probe, not a universal mode guarantee. Historical
acceptance statements about that probe must be read with this scope.

## Fixed source references

`SRT` below is the literal installed-source root:

```text
/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/independent/.venv/lib/python3.12/site-packages/sglang/srt
```

`CKPT` is the literal checkpoint root:

```text
/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3
```

The JSON evidence expands every reference into an absolute path and records
the file hash, so these line references are tied to the installed version.

### The template switch is not a hard decoder constraint

`SRT/entrypoints/openai/serving_chat.py:1022–1056` passes the request's template
kwargs to the tokenizer. `CKPT/tokenization_kimi.py:357–386` accepts
`thinking=True` by default and forwards it to the chat encoder.
`CKPT/encoding_k3.py:642–644` selects a think-open or response-open generation
prefix. Its lines 409–426 also omit historical think-channel content when
thinking is false. Neither operation masks future generated think markers.

This low-level switch differs from the checkpoint's documented usage:
`CKPT/README.md:625–629` describes always-thinking operation and preservation
of the complete assistant message, including reasoning and tool calls, in
multi-turn history. The benchmark's paper-alignment choice is therefore a
documented departure from recommended K3 usage, not a new server-native
default or a guaranteed hard non-thinking mode.

### A parser ambiguity prevents reconstructing the generated markers

`SRT/parser/reasoning_parser.py:464–484` is the K3 non-streaming parser. With
`force_reasoning=false`, it returns all text as ordinary content only when
both think-open and think-close are absent. If open is absent, line 470 sets
the reasoning start offset to zero. An isolated close therefore places all
preceding text into `reasoning_content`. Parsing uses string searches, without
checking whether the marker occurs in a structurally valid channel or a
quoted example. `serving_chat.py:1670–1683` still applies the parser to
thinking-off requests when `separate_reasoning=true`.

The offline audit compiles only the original result class and the original
`KimiK3Detector.detect_and_parse` method, without importing SGLang/CUDA. Its
fixtures contain no wrappers or tools, for which content cleanup is identity.
With `_in_reasoning=false`, these distinct generated-text inputs produce
identical parsed fields:

```text
Thought: ordinary visible deliberation<|close|>think<|sep|>Action: evaluate_config {}
<|open|>think<|sep|>Thought: ordinary visible deliberation<|close|>think<|sep|>Action: evaluate_config {}
```

Both yield:

```json
{"reasoning_content": "Thought: ordinary visible deliberation", "content": "Action: evaluate_config {}"}
```

Ordinary `Thought:` text with no think markers stays entirely in content.
Thus the field is not evidence of the word “Thought” being specially parsed.
Saved `response_raw` is the HTTP JSON body, already post-parser; it is not the
pre-parser generation stream or token IDs. The six real responses cannot
distinguish actual think-open generation from orphan-close misclassification.
The fixtures prove this non-identifiability, not which case occurred in vivo.

### Why the usage counter is zero

`SRT/entrypoints/openai/serving_chat.py:2189–2193` resolves the K3 thinking
toggle to false. Lines 803 and 829 pass that value as `require_reasoning`.
`SRT/managers/schedule_batch.py:811–815` stores this flag and initializes the
reasoning-token counter to zero.

`SRT/managers/scheduler_components/batch_result_processor.py:990–992` updates
reasoning tokens **only when `req.require_reasoning` is true**.
`SRT/entrypoints/openai/usage_processor.py:35–36` sums the resulting metadata
counter; it does not tokenize the later parser-produced `reasoning_content`.
Consequently the zero count is expected for these thinking-off requests even
when the response parser separates a nonempty field.

This is not a single-token-marker support failure: `scheduler.py:744–748`
retains the complete end-marker token sequence, and
`schedule_batch.py:1676–1688` uses a sequence matcher across decode steps.
The available counters cannot recover the actual reasoning-field token count.

## Hard controls: what is and is not enabled

All 136 request payloads were checked: none supplies `response_format`,
`json_schema`, `regex`, `ebnf`, `grammar`, `custom_logit_processor`, or
`logit_bias`. The actual replica log explicitly records
`enable_custom_logit_processor=False`; `serve_node.sh` does not enable it.
No hard structural think-channel exclusion was applied. The ordinary grammar
backend being available on the server does not mean a request grammar was
activated.

- `reasoning_effort="none"` only sets thinking template defaults
  (`protocol.py:931–944`); it is not a stronger decoder constraint.
- `separate_reasoning=false` only bypasses response parsing. It does not
  prohibit generation. Stop sequences truncate output, not force a valid
  answer without reasoning.
- `thinking_budget=0` is not a prohibition on entering thinking again.
  `constrained/reasoner_grammar_backend.py:102–110,183–200` starts a
  thinking-off request in its generation state; the reasoning budget is not
  active there.
- `logit_bias=-100` is additive weighting, not a hard prohibition
  (`sampling/sampling_batch_info.py:296–297`).
- An explicit grammar can hard-mask vocabulary
  (`sampling/sampling_batch_info.py:293–294`), but it must actually exclude
  think-channel sequences. An ordinary JSON schema with arbitrary strings
  does not establish that property.
- A custom processor can assign negative infinity to disallowed tokens
  (`sampling/custom_logit_processor.py:47–58`), but the current server rejects
  custom processors because the feature is disabled
  (`managers/tokenizer_manager.py:1088–1095`). K3's structural open/close tokens
  are shared across think, response, and tools formats
  (`function_call/kimik3_format.py:1–7`), so indiscriminately banning an open
  token would also damage the required output protocol. A targeted solution
  needs sequence-aware constraints.

No K3-specific, already-enabled hard-off control was found in this deployment.
Introducing grammar or custom logit constraints would be a new, separately
validated experimental condition; none was introduced during pilot/full.
Even a structural channel constraint would not establish absence of semantic
reasoning or internal model computation.

## Reproduce without serving traffic

Run the standard-library-only audit from any working directory:

```bash
python3 /lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/reasoning_mode_diagnostic.py
```

It prints JSON to stdout, reads only saved files, asserts the expected smoke
counts and parser ambiguity, and neither writes files nor makes network calls.
The saved JSON was generated with this script; its own hash is included.
