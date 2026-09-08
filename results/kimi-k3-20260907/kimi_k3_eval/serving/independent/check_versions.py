"""Check pinned versions without importing the GPU runtime."""
import importlib.metadata
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
normalize = lambda value: re.sub(r'[-_.]+', '-', value).lower()
actual = {normalize(dist.metadata['Name']): dist.version
          for dist in importlib.metadata.distributions()}
expected = json.loads((BASE / 'manifests/image-packages.json').read_text())['packages']
differences = {name: {'expected': info['version'], 'actual': actual.get(name)}
               for name, info in expected.items()
               if actual.get(name) != info['version']}
result = {'expected_count': len(expected), 'actual_count': len(actual),
          'differences': differences}
(BASE / 'manifests/baseline-version-check.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
raise SystemExit(bool(differences))
