"""Post-freeze metadata/arithmetic review; no scorer, model, raw or table reads."""
import collections, csv, hashlib, io, json, math, pathlib, re, statistics, sys
OP = pathlib.Path("/lustrefs/users/chufan.shi/codex_space_tn/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909")
REPORT = OP / "dual_model_analysis_fixed8_v2"
PIN = "aa2f55e3b42d179e505603ce2f4870c56582e5ec7152ad901f355729b43ff854"
PERF = set("f1 f1_mi f1_mv evidence_acc evidence_acc_mi evidence_acc_mv label_acc label_acc_mi label_acc_mv gap gap_mi gap_bon raw_perf raw_perf_mi raw_perf_bon".split())
read_refs = {}
def get(path, expected=None):
    path = pathlib.Path(path)
    assert path.is_file() and not path.is_symlink(), str(path)
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
    ref = dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    if expected:
        assert ref["sha256"]==expected["sha256"] and ("bytes" not in expected or ref["bytes"]==expected["bytes"]),str(path)
    if str(path) in read_refs: assert ref==read_refs[str(path)]
    read_refs[str(path)]=ref
    return data
def js(path): return json.loads(get(path))
def rows(path): return list(csv.DictReader(io.StringIO(get(path).decode())))
def cmap(seq,key="comparison"): return {r[key]:r for r in seq}
idx=json.loads(get(REPORT/"INDEX.json",dict(sha256=PIN,bytes=3554)))
assert {x.name for x in REPORT.iterdir()}==set(idx["files"])|{"INDEX.json"}
for name,ref in idx["files"].items(): get(REPORT/name,ref)
report_refs=js(REPORT/"INPUT_REFS.json")["refs"]
assert len(report_refs)==101 and len({r["path"] for r in report_refs})==101
for ref in report_refs: get(ref["path"],ref)
extract=js(REPORT/"NUMERICAL_EXTRACT.json")
primary=rows(REPORT/"PRIMARY_RESULTS.csv")
negative=rows(REPORT/"NEGATIVE_PERFORMANCE.csv")
assert len(primary)==12 and len(negative)==49
md=get(REPORT/"REPORT.zh.md").decode()
nmd=get(REPORT/"NEGATIVE_PERFORMANCE.md").decode()
summary={}; expected_prim=[]; expected_neg=[]; arithmetic=[]
for model,folder in [("kimi-k3","actual_k3_fixed8_composite_export_v2_py311_final"),("glm-5.3","actual_formal_export_glm_completed_v2")]:
    root=OP/folder; effects=rows(root/"effects.csv"); metrics=rows(root/"metrics.csv")
    logical=rows(root/"logical_outcomes.csv"); result=js(root/"results.json"); manifest=js(root/"manifest.json")
    assert len(effects)==514 and len(metrics)==7687 and len(logical)==783
    assert len(result["paired_rows"])==5393 and len(result["raw_terminals"])==1881 and len(result["artifact_specs"])==705
    assert len({x["invocation_id"] for x in logical})==705
    assert all(x["execution_state"]=="terminal" and x["score_state"]=="score" for x in logical)
    assert all(x["ci"]==x["p_value"]=="" for x in effects)
    p=[x for x in effects if x["role"]=="primary"]; neg=[x for x in effects if x["metric"] in PERF and x["effect"] and float(x["effect"])<0]
    assert {x["comparison"].split("__")[1] for x in p}=={"E-S","E-A","E-H","P-S","P-A","P-H"}
    expected_prim.extend(p); expected_neg.extend(neg)
    assert cmap(p)==cmap(extract["models"][model]["primary_csv_exact"])
    assert cmap(neg)==cmap(extract["models"][model]["negative_performance_csv_exact"])
    counts=dict(collections.Counter("unknown" if x["effect"]=="" else "positive" if float(x["effect"])>0 else "negative" if float(x["effect"])<0 else "zero" for x in effects))
    nulls=dict(collections.Counter(x["metric"] for x in metrics if x["value"]==""))
    unknown=dict(collections.Counter(x["metric"] for x in effects if x["effect"]==""))
    noanswer=sum(int(x["model_no_answer_count"]) for x in logical)
    nalogical=[x for x in logical if int(x["model_no_answer_count"])>0]
    gap100=[x for x in metrics if x["metric"].startswith("gap") and x["value"] and float(x["value"])>100]
    assert counts==extract["models"][model]["all_effect_counts"]
    assert nulls==extract["models"][model]["null_metric_cells"]=={"feedback_visible":366}
    assert unknown==extract["models"][model]["unknown_comparison_metrics"]=={"feedback_visible":28}
    assert noanswer==extract["models"][model]["model_no_answer_agents"]
    assert len(nalogical)==extract["models"][model]["logical_with_model_no_answer"]
    assert gap100==extract["models"][model]["gap_above_100_cells"]
    itemstatus=dict(collections.Counter(x["item_status"] for x in manifest["logical_rows"]))
    assert itemstatus=={"mixed_or_unknown":453,"previously_inspected":330}
    assert manifest["repeat_policy"]=={s:{"evidence_audit":1,"restricted_search":1,"tuning":3} for s in ["expgym","poolact"]}
    bycomp=cmap(result["comparisons"],"id")
    for e in p:
        c=bycomp[e["comparison"]]; pairs=[x for x in result["paired_rows"] if x["comparison"]==e["comparison"]]
        assert result["metric_definitions"][e["metric"]]["higher_is_better"] is True
        expected_kind="expgym_free_tight" if e["system"]=="expgym" else "poolact_vs_naive"
        assert c["kind"]==expected_kind
        assert len(pairs)==int(e["n_pairs_descriptive_not_independent_n"])
        assert len({x["item"] for x in pairs})==int(e["n_items"])
        outers=sorted({x["outerseed"] for x in pairs})
        assert len(outers)==int(e["n_outer_repeats"])
        for pair in pairs:
            delta=pair["baseline"]-pair["target"] if e["system"]=="expgym" else pair["target"]-pair["baseline"]
            assert math.isclose(delta,pair["effect"],abs_tol=2e-13,rel_tol=0)
        values=[math.fsum(x["effect"] for x in pairs if x["outerseed"]==o)/sum(x["outerseed"]==o for x in pairs) for o in outers]
        csvouter=json.loads(e["outer_bundle_effects"])
        assert all(math.isclose(a,b,abs_tol=2e-13,rel_tol=0) for a,b in zip(values,csvouter))
        assert math.isclose(math.fsum(values)/len(values),float(e["effect"]),abs_tol=2e-13,rel_tol=0)
        if len(values)>1:
            mean=math.fsum(csvouter)/len(csvouter)
            independent_sd=math.sqrt(math.fsum((x-mean)**2 for x in csvouter)/(len(csvouter)-1))
            assert math.isclose(independent_sd,float(e["outerrep_descriptive_sd"]),abs_tol=2e-13,rel_tol=0)
        else: assert e["outerrep_descriptive_sd"]==""
        assert not c["quality_gate_ids"] and c["bootstrap_method"]=="disabled_descriptive_only"
        arithmetic.append(dict(comparison=e["comparison"],paired_rows=len(pairs),outer_values=csvouter,effect=e["effect"],sd=e["outerrep_descriptive_sd"],direction=expected_kind))
    summary[model]=dict(effects=counts,negative_performance=len(neg),metrics=len(metrics),pairs=5393,logical=783,invocations=705,agents=1881,model_no_answer_agents=noanswer,model_no_answer_logical=len(nalogical),model_no_answer_invocations=len({x["invocation_id"] for x in nalogical}),null_metrics=nulls,unknown_effects=unknown,gap_above100=len(gap100),item_status=itemstatus)
assert cmap(primary)==cmap(expected_prim) and cmap(negative)==cmap(expected_neg)
old=rows(OP/"actual_formal_export_k3_node_failure_v2/effects.csv")
oldneg=[x for x in old if x["metric"] in PERF and x["effect"] and float(x["effect"])<0]
assert len(oldneg)==23 and all(cmap(negative)[x["comparison"]]==x for x in oldneg)
# The human-readable negative table carries every original CSV string and no extra row.
mdneg=[line.split("|")[1:-1] for line in nmd.splitlines() if re.match(r"\| (kimi-k3|glm-5.3)__",line)]
assert len(mdneg)==49
for cells in mdneg:
    v=[x.strip() for x in cells]; e=cmap(negative)[v[0]]
    assert v[1]==e["system"]+" / "+e["slice"]
    assert v[2]==(e["regime"] or "Free→Tight")+" / "+e["strategy"]
    assert v[3:7]==[e[k] for k in ["metric","baseline","target","effect"]]
    assert v[7]==(e["outerrep_descriptive_sd"] or "null (R1)")
# Compare all 12 main table numbers at their stated six-decimal presentation.
lines=[x for x in md.splitlines() if re.match(r"\| (K3|GLM) \| (Exp|Pool) ",x)]
assert len(lines)==12
for line,e in zip(lines,primary):
    v=[x.strip() for x in line.split("|")[1:-1]]
    assert v[2:5]==[format(float(e[k]),".6f") for k in ["baseline","target","effect"]]
    assert v[5]==(format(float(e["outerrep_descriptive_sd"]),".6f") if e["outerrep_descriptive_sd"] else "null（R1）")
links=[]
for text in [md,nmd]:
    for link in re.findall(r"\]\(([^)]+)\)",text):
        assert not re.match(r"^[a-z]+:",link),link
        dest=(REPORT/link.split("#")[0]).resolve()
        assert dest.is_file(),link
        links.append(dict(link=link,resolved=str(dest)))
# Re-read every explicit input for SHA/stat stability; no recursive discovery.
for ref in list(read_refs.values()): get(ref["path"],ref)
print(json.dumps(dict(status="PASS_BOUNDED_POST_REPORT_NUMERICAL_CHECK",report_index_sha256=PIN,report_files=14,report_bytes=294735,pinned_author_inputs=101,input_refs=list(read_refs.values()),models=summary,primary_exact=12,negative_exact=49,old_k3_negative_exact=23,primary_pair_arithmetic=arithmetic,arithmetic_absolute_tolerance=2e-13,table_and_csv_comparison_tolerance=0,ci_p_all_null=True,local_links=links,prohibited_calls=0,independent_raw_or_scorer_review_performed_here=False,python=sys.version),ensure_ascii=False,indent=2))

