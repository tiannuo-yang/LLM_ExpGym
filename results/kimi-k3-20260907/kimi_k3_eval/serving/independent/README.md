# Independent uv serving environment

This directory builds a separate Python environment without `--system-site-packages`.
The installed package versions come from the known working Kimi-K3 CUDA 12.9 image.
Public distributions are installed at their exact image versions with uv; patched
distributions are rebuilt into wheels from the image's installed files. The
repacked SGLang wheel also includes its compiled Python 3.12 extensions.

The build contains 311 distributions: 304 exact public package versions and seven
repacked distributions (`deep-ep`, patched `flashinfer-python`, `hpc-ops`,
`mscclpp`, patched `sgl-deep-gemm`, K3 `sglang`, `sglang-router`). Public CUDA wheels
use explicit cu129 URLs with SHA256 hashes instead of sending unrelated package
names to CUDA-specific indexes. Some pure Python packages (for example ANTLR
4.9.3) require an sdist build because no wheel was published.

From an empty `independent` build directory, run:

```bash
bash prepare_metadata.sh
python3 build_independent.py plan
python3 build_independent.py repack
python3 build_independent.py install-public
python3 build_independent.py install-repacked
source runtime.sh
.venv/bin/python validate_independent.py
.venv/bin/sglang serve --help
```

The managed Python interpreter lives under `independent/python`, so the serving
directory bind mount also contains the interpreter and standard library. No home
directory mount or system Python packages are needed.

For the initial GPU validation, run this environment inside the existing cu129
image. Python dependencies are fully isolated; the image supplies the OS and CUDA
development runtime. The host login node has glibc 2.35 and CUDA 12.8; the image
has Ubuntu 24.04, CUDA 12.9, and driver forward-compatibility libraries. Most core
extensions are ABI-compatible with the host, but the optional SGLang router wheel
is tagged `manylinux_2_39`. No claim of complete native host serving is made.

`runtime.sh` puts this environment's NCCL, NVSHMEM, Torch, and TVM-FFI libraries
first. This is material: host NCCL 2.26 lacks `ncclCommWindowRegister`, used by
SGLang's symmetric-memory JIT; the image version is NCCL 2.28.9. A standalone
native host deployment would additionally need a compatible CUDA toolkit and
forward-compatibility libraries, not just Python wheels.

Audit files:

- `manifests/image-packages.json`: exact original installed distribution versions.
- `manifests/public-requirements.txt`: version/URL-pinned public installations.
- `manifests/wheel-sha256.json`: hashes of baseline repacked wheels.
- `manifests/validation.json`: package locations and import/isolation results.
- `logs/install-public.log`: public package installation and build output.

The raw image's SGLang metadata declares CUDA 13 and a newer DeepGEMM despite
shipping known working CUDA 12.9/DeepGEMM overrides. `--no-deps` intentionally
reproduces the actual installed versions. These original metadata declarations
are preserved, so `uv pip check` can report those historical inconsistencies.
The baseline SGLang wheel preserves version `0.5.16`; any additional serving fix
must be separately patched, hashed, and validated before formal evaluation.

Final serving validation was completed by the deployment owner on 2026-09-07:
the installed SGLang version is `0.5.16+pr32477`, all 340 GPU kernel regressions
passed, all four replicas answered the short API probes, and a 100,174-token
retrieval probe passed. The baseline records in this directory intentionally
retain the pre-patch environment-build evidence. Current acceptance and final
package freeze are `../ACCEPTANCE.json` and `../manifests/final-uv-freeze.txt`.
