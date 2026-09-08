#!/usr/bin/env python3
"""Check isolation and CPU importability; does not claim GPU serving passed."""
import importlib
import importlib.metadata
import json
import os
import platform
import re
import site
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ENV = BASE / '.venv'
actual = {}
for distribution in importlib.metadata.distributions():
    name = distribution.metadata['Name']
    actual[name] = {'version': distribution.version,
                    'location': str(Path(distribution.locate_file('')).resolve())}
external = {name: info for name, info in actual.items()
            if not Path(info['location']).is_relative_to(ENV)}
normalize = lambda value: re.sub(r'[-_.]+', '-', value).lower()
actual_normalized = {normalize(name): info for name, info in actual.items()}
expected = json.loads((BASE / 'manifests/image-packages.json').read_text())['packages']
version_mismatches = {
    name: {'expected': info['version'], 'actual': actual_normalized.get(name, {}).get('version')}
    for name, info in expected.items()
    if actual_normalized.get(name, {}).get('version') != info['version']
}
checks = {}
for name in ['torch', 'transformers', 'flashinfer', 'sgl_kernel', 'sglang',
             'sglang.srt.grpc._core', 'sglang.srt.multimodal._core']:
    try:
        module = importlib.import_module(name)
        checks[name] = {'ok': True, 'file': str(getattr(module, '__file__', None))}
    except Exception as error:
        checks[name] = {'ok': False, 'error': str(error)}
result = {
    'python': sys.version, 'executable': sys.executable,
    'resolved_executable': str(Path(sys.executable).resolve()),
    'platform': platform.platform(), 'user_site_enabled': site.ENABLE_USER_SITE,
    'pyvenv_config': (ENV / 'pyvenv.cfg').read_text(),
    'external_distributions': external, 'distribution_count': len(actual),
    'version_mismatches_from_baseline': version_mismatches,
    'packages': actual, 'imports': checks,
    'gpu_serving_verified': False,
    'runtime_note': 'Use the cu129 image for OS/CUDA toolchain; Python packages are isolated.',
}
(BASE / 'manifests/validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in [
    'executable', 'resolved_executable', 'user_site_enabled', 'external_distributions',
    'distribution_count', 'version_mismatches_from_baseline', 'imports', 'gpu_serving_verified']}, indent=2))
if external or site.ENABLE_USER_SITE or version_mismatches or any(not info['ok'] for info in checks.values()):
    raise SystemExit(1)
