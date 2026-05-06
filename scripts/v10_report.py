"""Generate V10 experiment report for completed models."""
import json
import os
import sys
from collections import defaultdict

BASE = "budget_sweep_results/v10"
MODELS = ["dsv3", "gpt52", "gemini3", "haiku45"]
MODEL_NAMES = {
    "dsv3": "DeepSeek-V3.2",
    "gpt52": "GPT-5.2",
    "gemini3": "Gemini-3-Flash",
    "haiku45": "Claude-Haiku-4.5",
    "qwen3max": "Qwen3-Max",
}
MODES = ["free", "low", "high"]
SCENARIOS = ["tuning", "search", "audit"]


def load_traces(models=None):
    """Load all traces into a list of dicts."""
    models = models or MODELS
    results = []
    for model in models:
        for mode in MODES:
            trace_dir = os.path.join(BASE, "%s_%s" % (model, mode), "traces")
            if not os.path.isdir(trace_dir):
                continue
            for fn in sorted(os.listdir(trace_dir)):
                if not fn.endswith(".json"):
                    continue
                fpath = os.path.join(trace_dir, fn)
                with open(fpath) as fh:
                    data = json.load(fh)

                if fn.startswith("tuning"):
                    scenario = "tuning"
                elif fn.startswith("restricted_search"):
                    scenario = "search"
                elif fn.startswith("evidence_audit"):
                    scenario = "audit"
                else:
                    continue

                entry = {
                    "model": model,
                    "mode": mode,
                    "scenario": scenario,
                    "perf": data.get("answer_perf"),
                    "evals": data.get("evaluations"),
                    "aborted": data.get("aborted", False),
                    "file": fn,
                    "answer": data.get("answer", ""),
                    "steps": data.get("steps", []),
                }
                results.append(entry)
    return results


def compute_audit_metrics(entry):
    """Compute label_acc, evidence_acc, verification_eff for an audit trace."""
    # Import evaluator
    sys.path.insert(0, ".")

    # Parse doc index from filename: evidence_audit_cc-large_N_m3_r0_s1206.json
    parts = entry["file"].replace(".json", "").split("_")
    doc_idx = int(parts[3])
    cc_split = "cc-large"

    from expgym.task_evidence_audit import build_answer_evaluator
    evaluator = build_answer_evaluator(doc_idx, cc_split)

    # Extract tool records from steps (messages)
    tool_records = []
    steps = entry["steps"]
    if isinstance(steps, list):
        for i, msg in enumerate(steps):
            if isinstance(msg, str) and msg.startswith("Action: human_feedback"):
                # Extract argument
                arg = msg.replace("Action: human_feedback ", "").strip()
                tool_records.append(("human_feedback", arg, None))

    metrics = evaluator(entry["answer"], tool_records)
    return metrics


def mean(vals):
    return sum(vals) / len(vals) if vals else None


def fmt(v, decimals=4):
    if v is None:
        return "N/A"
    return ("%%.%df" % decimals) % v


def main():
    results = load_traces()
    print("Loaded %d traces" % len(results))

    # ==================== TUNING ====================
    tuning = [r for r in results if r["scenario"] == "tuning"]

    print()
    print("## Tuning Results")
    print()
    print("3 HPOBench tasks (nasbench101_C, nasbench201_imagenet16-120, paramnet_letter_steps) x 3 reps each.")
    print("Budget = 3x oracle_mean_cost. Temperature = 0.7 for reps > 1.")
    print()
    print("### Mean Performance (across tasks x reps)")
    print()
    print("| Model | free | low | high | free-high |")
    print("|-------|------|-----|------|-----------|")
    for model in MODELS:
        vals = {}
        for mode in MODES:
            perfs = [r["perf"] for r in tuning if r["model"] == model and r["mode"] == mode and r["perf"] is not None]
            vals[mode] = mean(perfs)
        delta = (vals["free"] - vals["high"]) if vals["free"] is not None and vals["high"] is not None else None
        print("| %s | %s | %s | %s | %s |" % (
            MODEL_NAMES.get(model, model),
            fmt(vals["free"]), fmt(vals["low"]), fmt(vals["high"]), fmt(delta),
        ))

    # Per-task
    tasks_set = set()
    for r in tuning:
        fname = r["file"].replace("tuning_", "").split("_m3")[0]
        tasks_set.add(fname)
    tasks = sorted(tasks_set)

    print()
    print("### Per-Task Breakdown")
    for task in tasks:
        print()
        print("**%s**" % task)
        print()
        print("| Model | free | low | high |")
        print("|-------|------|-----|------|")
        for model in MODELS:
            row = []
            for mode in MODES:
                perfs = [r["perf"] for r in tuning
                         if r["model"] == model and r["mode"] == mode
                         and task in r["file"] and r["perf"] is not None]
                row.append(fmt(mean(perfs)))
            print("| %s | %s | %s | %s |" % (MODEL_NAMES.get(model, model), row[0], row[1], row[2]))

    # Degenerate runs
    degen = [r for r in tuning if r["perf"] is not None and r["perf"] <= 0.48]
    if degen:
        print()
        print("### Degenerate Runs (perf <= 0.48)")
        print()
        for r in degen:
            print("- %s_%s: %s perf=%.4f" % (r["model"], r["mode"], r["file"], r["perf"]))

    # ==================== SEARCH ====================
    search = [r for r in results if r["scenario"] == "search"]

    print()
    print("## Search Results")
    print()
    print("50 musique_4hop questions x 1 rep. Budget = 3x 300s = 900s.")
    print("Performance = F1 score (exact string match).")
    print()
    print("### Mean F1")
    print()
    print("| Model | free | low | high | free-high |")
    print("|-------|------|-----|------|-----------|")
    for model in MODELS:
        vals = {}
        for mode in MODES:
            perfs = [r["perf"] for r in search if r["model"] == model and r["mode"] == mode and r["perf"] is not None]
            vals[mode] = mean(perfs)
        delta = (vals["free"] - vals["high"]) if vals["free"] is not None and vals["high"] is not None else None
        print("| %s | %s | %s | %s | %s |" % (
            MODEL_NAMES.get(model, model),
            fmt(vals["free"]), fmt(vals["low"]), fmt(vals["high"]), fmt(delta),
        ))

    # Abort rates
    print()
    print("### Abort Rates")
    print()
    print("| Model | free | low | high |")
    print("|-------|------|-----|------|")
    for model in MODELS:
        row = []
        for mode in MODES:
            total = len([r for r in search if r["model"] == model and r["mode"] == mode])
            aborted = sum(1 for r in search if r["model"] == model and r["mode"] == mode and r["aborted"])
            row.append("%d/%d (%.0f%%)" % (aborted, total, 100 * aborted / total if total else 0))
        print("| %s | %s | %s | %s |" % (MODEL_NAMES.get(model, model), row[0], row[1], row[2]))

    # ==================== AUDIT ====================
    audit = [r for r in results if r["scenario"] == "audit"]

    print()
    print("## Audit Results")
    print()
    print("13 cc-large docs x 1 rep. Budget = 3x 300s = 900s.")
    print()

    # Compute detailed metrics
    audit_metrics = []
    for r in audit:
        try:
            m = compute_audit_metrics(r)
            m["model"] = r["model"]
            m["mode"] = r["mode"]
            m["file"] = r["file"]
            audit_metrics.append(m)
        except Exception as e:
            print("WARNING: failed to compute metrics for %s: %s" % (r["file"], e))

    print("### Label Accuracy")
    print()
    print("| Model | free | low | high | free-high |")
    print("|-------|------|-----|------|-----------|")
    for model in MODELS:
        vals = {}
        for mode in MODES:
            accs = [m["label_acc"] for m in audit_metrics if m["model"] == model and m["mode"] == mode]
            vals[mode] = mean(accs)
        delta = (vals["free"] - vals["high"]) if vals["free"] is not None and vals["high"] is not None else None
        print("| %s | %s | %s | %s | %s |" % (
            MODEL_NAMES.get(model, model),
            fmt(vals["free"]), fmt(vals["low"]), fmt(vals["high"]), fmt(delta),
        ))

    print()
    print("### Evidence Accuracy")
    print()
    print("| Model | free | low | high | free-high |")
    print("|-------|------|-----|------|-----------|")
    for model in MODELS:
        vals = {}
        for mode in MODES:
            accs = [m["evidence_acc"] for m in audit_metrics if m["model"] == model and m["mode"] == mode]
            vals[mode] = mean(accs)
        delta = (vals["free"] - vals["high"]) if vals["free"] is not None and vals["high"] is not None else None
        print("| %s | %s | %s | %s | %s |" % (
            MODEL_NAMES.get(model, model),
            fmt(vals["free"]), fmt(vals["low"]), fmt(vals["high"]), fmt(delta),
        ))

    print()
    print("### Verification Efficiency")
    print()
    print("| Model | free | low | high |")
    print("|-------|------|-----|------|")
    for model in MODELS:
        row = []
        for mode in MODES:
            effs = [m["verification_eff"] for m in audit_metrics if m["model"] == model and m["mode"] == mode and m["verification_eff"] is not None]
            row.append(fmt(mean(effs)))
        print("| %s | %s | %s | %s |" % (MODEL_NAMES.get(model, model), row[0], row[1], row[2]))

    # ==================== EVAL COUNTS ====================
    print()
    print("## Evaluation Counts (avg per trace)")
    print()
    for sc_name, sc_label in [("tuning", "Tuning"), ("search", "Search"), ("audit", "Audit")]:
        sc_data = [r for r in results if r["scenario"] == sc_name]
        print("### %s" % sc_label)
        print()
        print("| Model | free | low | high |")
        print("|-------|------|-----|------|")
        for model in MODELS:
            row = []
            for mode in MODES:
                evals_l = [r["evals"] for r in sc_data if r["model"] == model and r["mode"] == mode and r["evals"] is not None]
                row.append(fmt(mean(evals_l), 1))
            print("| %s | %s | %s | %s |" % (MODEL_NAMES.get(model, model), row[0], row[1], row[2]))
        print()

    # ==================== SUMMARY ====================
    print()
    print("## Summary")
    print()
    print("### Overall Performance (all scenarios, all modes)")
    print()
    print("| Model | Tuning (mean) | Search F1 (mean) | Audit Label (mean) | Audit Evidence (mean) |")
    print("|-------|---------------|------------------|--------------------|-----------------------|")
    for model in MODELS:
        t_perfs = [r["perf"] for r in tuning if r["model"] == model and r["perf"] is not None]
        s_perfs = [r["perf"] for r in search if r["model"] == model and r["perf"] is not None]
        a_label = [m["label_acc"] for m in audit_metrics if m["model"] == model]
        a_evid = [m["evidence_acc"] for m in audit_metrics if m["model"] == model]
        print("| %s | %s | %s | %s | %s |" % (
            MODEL_NAMES.get(model, model),
            fmt(mean(t_perfs)), fmt(mean(s_perfs)),
            fmt(mean(a_label)), fmt(mean(a_evid)),
        ))


if __name__ == "__main__":
    main()
