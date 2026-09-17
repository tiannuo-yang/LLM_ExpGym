#!/usr/bin/env python3
"""Copy a fixed selected-slot inventory, without inference calls or rescoring.

The output JSON files are byte-for-byte originals. Pool results contain all
members, so the companion agent files are not duplicated in this browsing view.
Full original directory layouts remain available in the raw archives.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import time


def is_true(value):
    return value is True or str(value).lower() in {"true", "1"}


def safe_component(value):
    value = str(value)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", value) or value in {".", ".."}:
        raise ValueError("unsafe destination component")
    return value


def signature(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def copy_one(row, dest):
    row = dict(row)
    if not is_true(row["execution_complete"]):
        row.update(trajectory_file="", trajectory_bytes="", trajectory_sha256="",
                   embedded_agents="", trajectory_identity_check="not_completed")
        return row
    source = Path(row["result_path"])
    old = source.lstat()
    if not stat.S_ISREG(old.st_mode):
        raise ValueError("source must be a regular file")
    raw = source.read_bytes()
    if signature(source.stat()) != signature(old):
        raise ValueError("source changed while reading")
    digest = hashlib.sha256(raw).hexdigest()
    expected = row.get("result_sha256", "")
    if expected and digest != expected:
        raise ValueError("frozen result identity mismatch")
    obj = json.loads(raw)
    if row["system"] == "poolact":
        if not isinstance(obj.get("agent_results"), list) or len(obj["agent_results"]) != 4:
            raise ValueError("pool must contain all four agent trajectories")
        agents = 4
    else:
        agents = 1
    relative = Path("trajectories") / safe_component(row["model"]) / safe_component(row["system"]) / (safe_component(row["slot_id"]) + ".json")
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.exists():
        # A restart may reuse an identical completed copy; never overwrite.
        if target.read_bytes() != raw:
            raise ValueError("existing destination differs")
    else:
        with target.open("xb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(raw)
    row.update(trajectory_file=relative.as_posix(), trajectory_bytes=len(raw),
               trajectory_sha256=digest, embedded_agents=agents,
               trajectory_identity_check="matched_frozen_sha256" if expected else "copied_and_hashed_current_original")
    return row


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slots", type=Path, required=True)
    p.add_argument("--delivery", type=Path, required=True)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()
    start = time.monotonic()
    input_bytes = args.slots.read_bytes()
    rows = list(csv.DictReader(io.StringIO(input_bytes.decode(), newline="")))
    assert len(rows) == 4698
    assert len({r["slot_id"] for r in rows}) == len(rows)
    assert sum(is_true(r["execution_complete"]) for r in rows) == 4682
    args.delivery.mkdir(parents=True, exist_ok=True, mode=0o700)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        output = list(pool.map(lambda r: copy_one(r, args.delivery), rows))
    n1 = [r for r in output if r["trajectory_file"] and r["system"] == "expgym"]
    n4 = [r for r in output if r["trajectory_file"] and r["system"] == "poolact"]
    assert len(n1) == 2496 and len(n4) == 2186
    folder = args.delivery / "index"
    folder.mkdir(exist_ok=True)
    with (folder / "selected_slots.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    summary = dict(schema="expgym.ad03.trajectory-copy.v1",
                   report_commit="ad03e8c42ca501016176ee1bc407b38499178506",
                   planned_slots=len(rows), completed_canonical_files=len(n1)+len(n4),
                   n1_files=len(n1), n4_files=len(n4),
                   agent_trajectories=len(n1)+4*len(n4),
                   copied_bytes=sum(int(r["trajectory_bytes"] or 0) for r in output),
                   frozen_hash_matches=sum(r["trajectory_identity_check"] == "matched_frozen_sha256" for r in output),
                   unhashed_originals_at_input=sum(r["trajectory_identity_check"] == "copied_and_hashed_current_original" for r in output),
                   input_csv_sha256=hashlib.sha256(input_bytes).hexdigest(),
                   elapsed_seconds=round(time.monotonic()-start, 3), new_model_calls=0,
                   scope="Only selected completed canonical results copied; incomplete slots remain in CSV with no invented trajectory. Pool files contain all four native member records. No JSON payload was rewritten.")
    write_json(folder / "TRAJECTORY_COPY.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
