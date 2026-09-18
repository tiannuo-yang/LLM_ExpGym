#!/usr/bin/env python3
"""Standalone stdlib replay of all published Whois endpoints and cost projections.

The aggregation functions are copied from frozen analyze_n1.py SHA256
05f8e02ca484efd57784842b758d1916b6b09bb1941f4b82d1a06ed28ec504b5.
Only the model list and error-message count extend to Gemini/1170. No raw data,
original workspace, network or plotting dependency is required for --check.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
MODELS = ("gpt", "kimi", "glm", "qwen", "deepseek", "gemini")
BETAS = (1, 5, 10, 15, 20)
TOKENS = ("input_tokens", "output_tokens", "total_tokens", "reasoning_tokens", "cached_input_tokens")
QUESTIONS = tuple((s, q) for s,n in (("phantom_seed2",20),("phantom_seed3",19)) for q in range(n))

def truth(v):
    return str(v).lower() == "true"

def number(v):
    if v in (None, "", "null", "None"):
        return None
    n = float(v)
    if not math.isfinite(n):
        raise ValueError("non-finite numerical input")
    return n

def beta(v):
    n = number(v)
    if n is None or n != int(n) or n not in BETAS:
        raise ValueError("unsupported beta")
    return int(n)

def summarize(items, agents, attempts):
    keys = [(m, b) for m in MODELS for b in BETAS]
    grouped, ag, at = defaultdict(list), defaultdict(list), defaultdict(list)
    seen = set()
    for r in items:
        key = (r["model"], beta(r["beta"]), r["data_source"], int(r["question_index"]))
        if key in seen:
            raise ValueError("duplicate study slot")
        seen.add(key)
        if key[2:] not in QUESTIONS or r["repeat"] != "R1":
            raise ValueError("unexpected question/repeat")
        grouped[key[:2]].append(r)
    if seen != {(m, b, s, q) for m, b in keys for s, q in QUESTIONS}:
        raise ValueError("matrix must explicitly account for all 1170 slots")
    for r in agents:
        ag[(r["model"], beta(r["beta"]))].append(r)
    for r in attempts:
        at[(r["model"], beta(r["beta"]))].append(r)
    result = []
    for key in keys:
        rows, aa, usage = grouped[key], ag[key], at[key]
        values = [number(r["f1"]) for r in rows if truth(r["score_complete"]) and number(r["f1"]) is not None]
        out = {"model": key[0], "beta": key[1], "cohort": "historical_beta10" if key[1] == 10 else "new_20260916", "expected_items": 39, "execution_complete": sum(truth(r["execution_complete"]) for r in rows), "score_known": len(values), "score_unknown": 39 - len(values), "mean_f1": sum(values) / 39 if len(values) == 39 else None, "known_subset_mean_f1": sum(values) / len(values) if values else None, "repeat_count": 1, "agent_metrics_known": len(aa), "attempt_rows": len(usage) if aa else None, "attempt_errors": sum(r["state"] != "success" for r in usage) if aa else None, "missing_final_agents": sum(truth(r["missing_final"]) for r in aa) if aa else None}
        out["zero_score_items"] = sum(v == 0 for v in values)
        out["protocol_affected_agents"] = sum((number(r["protocol_failure_events"]) or 0) > 0 for r in aa) if aa else None
        for name in TOKENS:
            known = [number(r[name]) for r in usage if number(r[name]) is not None]
            out[name + "_known_sum"] = sum(known) if usage else None
            out[name + "_unknown_attempts"] = len(usage) - len(known) if usage else None
            out[name + "_complete_total"] = sum(known) if usage and len(known) == len(usage) else None
        for name in ("evaluations", "simulated_feedback_seconds", "agent_wall_seconds", "protocol_failure_events"):
            known = [number(r[name]) for r in aa if number(r[name]) is not None]
            out[name + "_known_sum"] = sum(known) if aa else None
            out[name + "_unknown_agents"] = len(aa) - len(known) if aa else None
        result.append(out)
    return result


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def text_row(row):
    return {k:"" if v is None else str(v) for k,v in row.items()}


def check(bundle):
    items=read_csv(bundle/"inputs/items.csv")
    agents=read_csv(bundle/"inputs/agents.csv")
    attempts=read_csv(bundle/"inputs/attempts.csv")
    assert len(items)==1170
    assert all(truth(r["execution_complete"]) and truth(r["score_complete"]) and 0<=number(r["f1"])<=1 for r in items)
    job_keys={(r["model"],r["job_id"]):r for r in items if r["job_id"]}
    seen_agents=set()
    for r in agents:
        key=(r["model"],r["job_id"])
        assert key in job_keys and key not in seen_agents
        assert all(str(r[k])==str(job_keys[key][k]) for k in ("beta","data_source","question_index","repeat"))
        seen_agents.add(key)
    seen_attempts=set()
    counts=Counter()
    for r in attempts:
        key=(r["model"],r["job_id"])
        rid=key+(r["request_id"],)
        assert key in seen_agents and rid not in seen_attempts
        seen_attempts.add(rid)
        counts[key]+=1
    for r in agents:
        n=number(r["http_request_attempts"])
        assert n is None or counts[r["model"],r["job_id"]]==n
    derived=summarize(items,agents,attempts)
    for r in derived:
        if r["model"]=="gemini" and r["beta"]!=10:
            r["cohort"]="new_openrouter_20260917"
    assert [text_row(r) for r in derived]==read_csv(bundle/"aggregate_metrics.csv"), "aggregate mismatch"
    by={(r["model"],r["beta"]):r for r in derived}
    differences=read_csv(bundle/"budget_differences.csv")
    assert len(differences)==24 and len({(r["model"],r["target_beta"]) for r in differences})==24
    for r in differences:
        m,t=r["model"],int(r["target_beta"])
        assert m in MODELS and t in (1,5,10,15) and int(r["baseline_beta"])==20
        assert r["direction"]=="target minus beta20" and int(r["paired_known"])==int(r["paired_expected"])==39
        assert number(r["mean_f1_difference"])==by[m,t]["mean_f1"]-by[m,20]["mean_f1"]
        assert truth(r["historical_cohort_comparison"])==(t==10)
        assert r["provider_cohort_change"]==("True" if t==10 else "False") if m=="gemini" else r["provider_cohort_change"]==""
    providers=read_csv(bundle/"provider_cohorts.csv")
    assert len(providers)==195 and Counter(r["provider"] for r in providers)=={"openrouter":156,"sub2api":39}
    assert all((r["provider"]=="sub2api")== (int(r["beta"])==10) for r in providers)
    adopted=read_csv(bundle/"adoption_sources.csv")
    assert len(adopted)==156 and Counter(r["cohort"] for r in adopted)=={"original_execution_offline_export":8,"continuation_first_execution":148}
    recovered={r["active_job_id"] for r in adopted if r["cohort"]=="original_execution_offline_export"}
    assert all(r["agent_wall_seconds"]=="" for r in agents if r["model"]=="gemini" and r["job_id"] in recovered)
    assert all(by["gemini",10][k] is None for k in ("attempt_rows","total_tokens_known_sum","agent_wall_seconds_known_sum"))
    result=dict(passed=True,slots=1170,endpoint_aggregates=30,budget_differences=24,gemini_slots=195,gemini_new_slots=156,historical_beta10_reused=39,gemini_new_attempts=sum(r["model"]=="gemini" for r in attempts),original_models_preserved_in_published_inputs=5,raw_or_network_access=False)
    print(json.dumps(result,sort_keys=True))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle",type=Path,default=Path(__file__).resolve().parent)
    p.add_argument("--check",action="store_true",help="verify; verification is also the default")
    args=p.parse_args()
    check(args.bundle)


if __name__=="__main__":
    main()
