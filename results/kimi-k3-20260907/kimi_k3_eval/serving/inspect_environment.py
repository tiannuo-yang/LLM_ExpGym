"""Record package and CUDA provenance without recording environment secrets."""
import importlib.metadata
import hashlib
import json
import platform
import sys
from pathlib import Path

import torch
import sglang

BASE = Path(__file__).resolve().parent
independent = Path(sys.prefix).resolve() == (BASE / "independent/.venv").resolve()
record = {
    "python": sys.version,
    "executable": sys.executable,
    "platform": platform.platform(),
    "sglang_file": sglang.__file__,
    "torch_cuda": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "uv_environment_type": "independent uv environment; no inherited Python packages" if independent else "bootstrap uv overlay with inherited image Python dependencies",
    "python_package_inheritance": not independent,
    "image": "/lustrefs/users/chufan.shi/codex_space/Tau_vision/.images/sglang_k3_cu12.sqsh",
    "packages": {name: importlib.metadata.version(name) for name in [
        "sglang", "torch", "transformers", "sglang-kernel", "flashinfer-python", "uvicorn", "fastapi"
    ]},
}
(BASE / "manifests" / "environment.json").write_text(json.dumps(record, indent=2) + "\n")
distributions = {}
for dist in importlib.metadata.distributions():
    name = dist.metadata.get("Name")
    if name:
        distributions.setdefault(name, dist.version)
(BASE / "manifests" / "all-distributions.json").write_text(json.dumps(dict(sorted(distributions.items())), indent=2) + "\n")
(BASE / "manifests" / "all-distributions.txt").write_text("\n".join(f"{name}=={version}" for name, version in sorted(distributions.items())) + "\n")
source_root = BASE / "image_source" / "sgl-workspace" / "sglang"
source_hashes = {}
for relative in ["docker/kimi_k3/kimi_k3_cu12.Dockerfile", "python/sglang/srt/models/kimi_k3.py",
                 "python/sglang/srt/entrypoints/openai/serving_chat.py", "python/sglang/srt/parser/reasoning_parser.py"]:
    path = source_root / relative
    if path.exists():
        source_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
(BASE / "manifests" / "source-sha256.json").write_text(json.dumps(source_hashes, indent=2) + "\n")
runtime_root = Path(sglang.__file__).parent
runtime_hashes = {name: hashlib.sha256((runtime_root / name).read_bytes()).hexdigest() for name in [
    "srt/models/kimi_k3.py", "srt/entrypoints/openai/serving_chat.py",
    "kernels/jit/csrc/elementwise/kvcache.cuh", "kernels/ops/kvcache/kvcache.py"]}
(BASE / "manifests" / "runtime-source-sha256.json").write_text(json.dumps(runtime_hashes, indent=2) + "\n")
print(json.dumps(record, indent=2))
