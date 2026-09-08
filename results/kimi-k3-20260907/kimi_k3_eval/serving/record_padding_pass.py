"""Create a serving gate only for a passing suite and the patched wheel."""
import datetime
import importlib.metadata
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = Path(__file__).resolve().parent
version = importlib.metadata.version("sglang")
assert version == "0.5.16+pr32477", version
suites = ET.parse(BASE / "manifests/padding-tests.xml").getroot()
tests = failures = errors = 0
for suite in suites.iter("testsuite"):
    tests += int(suite.attrib.get("tests", 0))
    failures += int(suite.attrib.get("failures", 0))
    errors += int(suite.attrib.get("errors", 0))
assert tests >= 7 and failures == errors == 0
record = {"completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "sglang_version": version, "job_id": os.getenv("SLURM_JOB_ID"),
          "tests": tests, "failures": failures, "errors": errors,
          "wheel_manifest": json.loads((BASE / "manifests/patched-sglang-wheel.json").read_text())}
(BASE / "manifests/padding-tests-passed.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
