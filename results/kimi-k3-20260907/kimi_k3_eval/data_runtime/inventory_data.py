"""Load selected paper items and hash the locally retained benchmark files."""
from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import math
import pickle
import subprocess
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2] / "LLM_ExpGym"
    sys.path.insert(0, str(repo))
    from scripts import download_data
    from expgym import task_restricted_search as search
    from expgym import task_evidence_audit as audit

    checks = {}
    for name, function in download_data.STEPS:
        ok, message = function(True)
        checks[name] = {"passed": ok, "message": message}
        assert ok, message
    qa = search._load_qa(1)
    corpus = search._load_corpus(1)
    assert len(qa) == 35, len(qa)
    assert all(row["type"] in [11, 12] for row in qa[:18]), qa[:18]
    assert all(row["type"] in [27, 28] for row in qa[18:]), qa[18:]
    audit_data = audit._load_data()
    hints = audit._load_hints()
    audit_items = []
    for index in range(13):
        doc = audit._get_doc(index)
        assert doc.segments and doc.annotations
        assert doc.doc_id in hints, "Missing hints for document {}".format(doc.doc_id)
        span_ids = {int(segment["span_index"]) for segment in doc.segments}
        for annotation in doc.annotations.values():
            assert set(annotation.get("spans", [])).issubset(span_ids)
        audit_items.append({"index": index, "doc_id": doc.doc_id, "file_name": doc.file_name, "segments": len(doc.segments), "hypotheses": len(doc.annotations)})
    assert [item["doc_id"] for item in audit_items] == [1, 2, 4, 5, 6, 8, 11, 18, 21, 22, 23, 24, 25]

    data = repo / "data"
    compact_tables = []
    with (data / "hpo_tuning/hpobench_data/nasbench_101_compact.pkl").open("rb") as handle:
        nas101 = pickle.load(handle)
    table101 = nas101["architectures"]
    assert len(table101) == 423624
    assert all(len(key) == 32 and all(math.isfinite(value) for value in row) and 0 <= row[0] <= 1 and 0 <= row[1] <= 1 and row[2] >= 0 for key, row in table101.items())
    best101 = min(row[0] for row in table101.values())
    assert math.isclose(best101, download_data.NASBENCH101_BEST_VALIDATION_ERROR, abs_tol=1e-12)
    compact_tables.append({"dataset": "nasbench101", "architectures": len(table101), "minimum_error": best101, "all_metrics_finite": True})
    expected_keys = {"".join(key) for key in itertools.product("01234", repeat=6)}
    expected_minima = {"cifar10-valid": 8.393333349609364, "cifar100": 26.49666666666667, "imagenet16-120": 53.1555555352105}
    for dataset, expected in expected_minima.items():
        with (data / "hpo_tuning/hpobench_data/nasbench_201_compact" / (dataset + ".pkl")).open("rb") as handle:
            table201 = pickle.load(handle)["architectures"]
        assert set(table201) == expected_keys
        assert all(all(math.isfinite(value) for value in row) and 0 <= row[0] <= 100 and row[1] >= 0 for row in table201.values())
        best = min(row[0] for row in table201.values())
        assert math.isclose(best, expected, abs_tol=1e-9)
        compact_tables.append({"dataset": "nasbench201:" + dataset, "architectures": len(table201), "minimum_error": best, "all_metrics_finite": True, "complete_config_keyspace": True})
    snapshot = Path(search.PHANTOM_WIKI_SNAPSHOT)
    files = sorted(set(
        [path for path in snapshot.rglob("*") if path.is_file()]
        + [path for path in (data / "hpo_tuning/hpobench_data").rglob("*") if path.is_file() and not path.name.endswith((".download", ".lock"))]
        + list((data / "contract-nli").glob("*.json"))
        + [data / "hpo_tuning/oracle3.json", repo / "configs/hpobench_tasks.yaml", repo / "configs/audit_hypothesis_orders.json"]
    ))
    records = [{"path": str(path.relative_to(repo)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files]
    report = {
        "classification": "Static/fake validation",
        "passed": True,
        "repository_commit": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "hpobench_commit": subprocess.check_output(["git", "-C", str(data / "hpo_tuning/HPOBench"), "rev-parse", "HEAD"], text=True).strip(),
        "phantom_wiki_revision": download_data.PHANTOM_WIKI_HF_REV,
        "checks": checks,
        "compact_tables": compact_tables,
        "hpobench_git_status": subprocess.check_output(["git", "-C", str(data / "hpo_tuning/HPOBench"), "status", "--short"], text=True).strip(),
        "search": {"seed": 1, "selected_count": len(qa), "corpus_articles": len(corpus), "type_counts": dict(collections.Counter(row["type"] for row in qa)), "items": [{"index": i, "type": row["type"], "difficulty": row["difficulty"], "question": row["question"], "answer": row["answer"]} for i, row in enumerate(qa)]},
        "audit": {"available_documents": len(audit_data["documents"]), "selected_count": len(audit_items), "items": audit_items},
        "files": records,
        "retained_file_bytes": sum(record["bytes"] for record in records),
        "provenance_note": "HPO upstream checksums and NAS oracles verified by download_data.py; PhantomWiki revision pinned; Audit upstream archive lacks a repository-pinned checksum, so its observed SHA256 is recorded here.",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "search_items": 35, "poolact_search_items": 18, "audit_items": 13, "files_hashed": len(records), "retained_file_bytes": report["retained_file_bytes"], "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    main()
