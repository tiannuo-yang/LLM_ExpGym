# Native task context v3 — isolated candidate

Classification: Static/fake validation. This directory is a candidate patch,
not an applied live change and not a model-performance result. `baseline/`
contains the 80 files from `accepted-source-v2.tar.gz`; `repo/` is the isolated
candidate. No serving, harness, dataset, or historical result file is changed.

The shared `resolve_tool_protocol(llm, requested="auto")` resolves the same
text/native choice for the loop and the three runner task-context builders.
Only source-owned Action instruction lines are conditional. Dataset questions,
document segments, hypotheses, parameter hints, and final-answer instructions
are not globally rewritten. Text builder defaults retain the frozen v2 bytes.
Fake clients still resolve to text; no model-name or backend-label branching
was added. Loop execution-contract checks retain their original precedence
before accessing the backend capability property.

Direct library callers must opt into matching task instructions:

```python
from expgym.tool_protocol import resolve_tool_protocol
from expgym.task_restricted_search import build_context, build_tools
from expgym.react_loop import run_react_loop

protocol = resolve_tool_protocol(llm, "auto")
context = build_context(False, row_index=0, tool_protocol=protocol)
result = run_react_loop(
    llm=llm, tools=build_tools(), time_budget=None, context=context,
    tool_protocol=protocol,
)
```

The loop does not silently fix a caller-supplied text context in native mode.
Custom scenario hooks without a protocol keyword remain caller-owned; their
returned text is unchanged. Existing custom-system protocol validation and
nonprotocol system/instruction-note preservation remain intact.

Validation includes 24 default-context hashes computed from the unchanged
baseline, all nine HPO hint branches with an in-memory configuration-space
fixture, three scenarios through demo/sweep/three Pool strategies using the
real OpenAI-compatible client with a CPU mock transport, explicit text mode on
a native-capable client, complete tool/reasoning history, literal Action/Thought
data, and contract property-access ordering. It is not a new nine-benchmark
data evaluation or a real-model compatibility/performance result.

Final artifacts and exact hashes are indexed in `receipt.json`. The final
patch is `native_task_context_v3.final.patch`; the earlier `.patch` is an
intermediate 17-test draft retained for provenance and must not be applied.
The `validation/*final*` logs cover the frozen 18-test candidate. Earlier logs
are retained rather than relabeled as final. `scripts/check.sh` creates and
removes its own temporary fake result directory; its stdout remains in the log.

No commit, push, GPU call, model API call, A21 run, or live patch application
was performed. Applying the patch or authorizing further real runs remains a
separate reviewed coordination step.
