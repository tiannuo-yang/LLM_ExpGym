"""Build a reproducible K3 wheel with the exact upstream PR #32477 changes."""
import base64
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
VERSION = "0.5.16+pr32477"
baseline = BASE / "independent/wheels/sglang-0.5.16-cp312-cp312-linux_x86_64.whl"
output_dir = BASE / "wheels"
output_dir.mkdir(exist_ok=True)
output = output_dir / f"sglang-{VERSION}-cp312-cp312-linux_x86_64.whl"
runtime_files = ["sglang/kernels/jit/csrc/elementwise/kvcache.cuh",
                 "sglang/kernels/ops/kvcache/kvcache.py"]
record = {"base_wheel": str(baseline), "base_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
          "upstream_pr": "https://github.com/sgl-project/sglang/pull/32477",
          "upstream_merge": "ee678910f7000aa43886f218de0e159bf418f1b5",
          "version": VERSION, "runtime_files": {}}
with zipfile.ZipFile(baseline) as archive:
    payload = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/RECORD")}
for name in runtime_files:
    original = (BASE / "patches/original/python" / name).read_bytes()
    patched = (BASE / "patches/source/python" / name).read_bytes()
    assert payload[name] == original, f"Baseline differs from audited upstream base: {name}"
    payload[name] = patched
    record["runtime_files"][name] = {"before": hashlib.sha256(original).hexdigest(),
                                   "after": hashlib.sha256(patched).hexdigest()}
old_dist = "sglang-0.5.16.dist-info"
new_dist = f"sglang-{VERSION}.dist-info"
payload = {name.replace(old_dist + "/", new_dist + "/"): data for name, data in payload.items()}
metadata_name = new_dist + "/METADATA"
metadata = payload[metadata_name].decode()
assert "\nVersion: 0.5.16\n" in metadata
payload[metadata_name] = metadata.replace("\nVersion: 0.5.16\n", f"\nVersion: {VERSION}\n").encode()
version_file = "sglang/_version.py"
if version_file in payload:
    payload[version_file] = re.sub(rb"(__version__\s*=\s*version\s*=\s*)['\"]0\.5\.16['\"]",
                                    lambda m: m.group(1) + repr(VERSION).encode(), payload[version_file])
rows = []
for name, data in sorted(payload.items()):
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    rows.append((name, "sha256=" + digest, str(len(data))))
rows.append((new_dist + "/RECORD", "", ""))
record_csv = io.StringIO()
csv.writer(record_csv, lineterminator="\n").writerows(rows)
payload[new_dist + "/RECORD"] = record_csv.getvalue().encode()
with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(payload.items()):
        info = zipfile.ZipInfo(name, date_time=(2026, 7, 29, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, data)
record["output_wheel"] = str(output)
record["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
(BASE / "manifests/patched-sglang-wheel.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
