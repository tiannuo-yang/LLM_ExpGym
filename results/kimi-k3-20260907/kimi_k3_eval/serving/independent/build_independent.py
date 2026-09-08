#!/usr/bin/env python3
"""Recreate the image's Python packages in a uv environment without inheritance.

All writes are restricted to this script's directory. Installed wheels retain
upstream METADATA; --no-deps is intentional because the published K3 metadata
declares CUDA 13 while the verified image uses CUDA 12.9 overrides.
"""
from __future__ import annotations

import argparse
import base64
import csv
import email
import hashlib
import html
import io
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
IMAGE = Path('/lustrefs/users/chufan.shi/codex_space/Tau_vision/.images/sglang_k3_cu12.sqsh')
SITE = Path('usr/local/lib/python3.12/dist-packages')
META = BASE / 'image_metadata' / SITE
SOURCE = BASE / 'image_packages/sgl-workspace/sglang/python/sglang'
UV = '/lustrefs/users/chufan.shi/.local/bin/uv'
PATCHED = {'sglang', 'deep-ep', 'sgl-deep-gemm', 'flashinfer-python'}


def norm(value):
    return re.sub(r'[-_.]+', '-', value).lower()


def metadata():
    result = {}
    for path in sorted(META.glob('*.dist-info')):
        msg = email.message_from_string((path / 'METADATA').read_text())
        result[norm(msg['Name'])] = {
            'name': msg['Name'], 'version': msg['Version'],
            'metadata_directory': path.name,
            'direct_url': json.loads((path / 'direct_url.json').read_text())
            if (path / 'direct_url.json').exists() else None,
        }
    return result


def plan(extra_repack):
    packages = metadata()
    repack = PATCHED | {norm(x) for x in extra_repack}
    public = []
    for key, info in packages.items():
        direct = info['direct_url'] or {}
        url = direct.get('url', '')
        if url.startswith('file:') or direct.get('dir_info') or direct.get('vcs_info'):
            repack.add(key)
        if key not in repack:
            if url.startswith('https://') and url.split('#')[0].endswith('.whl'):
                hashes = direct.get('archive_info', {}).get('hashes', {})
                fragment = '#sha256=' + hashes['sha256'] if hashes.get('sha256') else ''
                public.append(f"{info['name']} @ {url}{fragment}")
            elif '+cu129' in info['version'] or key == 'flashinfer-cubin':
                index = ('https://flashinfer.ai/whl/cu129' if key == 'flashinfer-jit-cache'
                         else 'https://flashinfer.ai/whl' if key == 'flashinfer-cubin'
                         else 'https://download.pytorch.org/whl/cu129')
                page_url = index + '/' + key + '/'
                with urllib.request.urlopen(page_url, timeout=60) as response:
                    page = response.read().decode()
                matches = []
                prefix = key.replace('-', '_') + '-' + info['version'] + '-'
                for raw in re.findall(r'href=[\"\']([^\"\']+)', page):
                    link = urllib.parse.urljoin(page_url, html.unescape(raw))
                    filename = urllib.parse.unquote(urllib.parse.urlparse(link).path.rsplit('/', 1)[-1])
                    if filename.startswith(prefix) and filename.endswith('.whl'):
                        if ('cp312-cp312' in filename and 'x86_64' in filename) or 'py3-none-any' in filename or (re.search(r'cp3(?:[6-9]|1[0-2])-abi3', filename) and 'x86_64' in filename):
                            matches.append(link)
                if len(matches) != 1:
                    raise RuntimeError(f'Expected one compatible wheel for {key}: {matches}')
                public.append(f"{info['name']} @ {matches[0]}")
            else:
                public.append(f"{info['name']}=={info['version']}")
    result = {'image': str(IMAGE), 'packages': packages, 'repack': sorted(repack),
              'public_count': len(public), 'environment_inherits_site_packages': False}
    (BASE / 'manifests/image-packages.json').write_text(json.dumps(result, indent=2) + '\n')
    (BASE / 'manifests/public-requirements.txt').write_text('\n'.join(public) + '\n')
    print(json.dumps({'packages': len(packages), 'repack': result['repack'],
                      'public_count': len(public)}, indent=2), flush=True)
    return result


def repack(info):
    dist = info['metadata_directory']
    msg = email.message_from_string((META / dist / 'WHEEL').read_text())
    tag = msg.get('Tag', 'py3-none-any')
    if norm(info['name']) == 'sglang':
        tag = 'cp312-cp312-linux_x86_64'
    wheel_name = f"{norm(info['name']).replace('-', '_')}-{info['version']}-{tag}.whl"
    target = BASE / 'wheels' / wheel_name
    if target.exists():
        print(f'Already packed {target.name}', flush=True)
        return
    payload = {}
    records = list(csv.reader((META / dist / 'RECORD').read_text().splitlines()))
    paths = []
    for row in records:
        name = row[0]
        if name.startswith('../') or '__pycache__' in name or name.endswith('.pyc'):
            continue
        if '__editable__' in name or name.endswith(('/RECORD', '/INSTALLER', '/REQUESTED', '/direct_url.json')):
            continue
        paths.append(str(SITE / name))
    directory = BASE / 'image_packages'
    if norm(info['name']) == 'sglang':
        paths.append('sgl-workspace/sglang/python/sglang')
    if paths:
        subprocess.run(['unsquashfs', '-processors', '8', '-no-progress', '-no-xattrs',
                        '-force', '-dest', str(directory), str(IMAGE), *paths], check=True)
    for row in records:
        name = row[0]
        path = directory / SITE / name
        if name.startswith('../') or '__pycache__' in name or name.endswith('.pyc'):
            continue
        if '__editable__' in name or name.endswith(('/RECORD', '/INSTALLER', '/REQUESTED', '/direct_url.json')):
            continue
        if path.is_file():
            payload[name] = path
    if norm(info['name']) == 'sglang':
        for path in SOURCE.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                payload['sglang/' + path.relative_to(SOURCE).as_posix()] = path
    wheel_metadata = 'Wheel-Version: 1.0\nGenerator: expgym-image-repacker\nRoot-Is-Purelib: false\nTag: ' + tag + '\n'
    output_records = []
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for name, path in sorted(payload.items()):
            value = wheel_metadata.encode() if name == dist + '/WHEEL' else path.read_bytes()
            archive.writestr(name, value)
            digest = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b'=').decode()
            output_records.append([name, 'sha256=' + digest, str(len(value))])
        output_records.append([dist + '/RECORD', '', ''])
        content = io.StringIO()
        csv.writer(content, lineterminator='\n').writerows(output_records)
        archive.writestr(dist + '/RECORD', content.getvalue())
    print(f'Packed {target.name}: {target.stat().st_size:,} bytes / {len(payload)} files', flush=True)


def install_public():
    command = [UV, 'pip', 'install', '--python', str(BASE / '.venv/bin/python'),
               '--no-deps', '--python-platform', 'x86_64-manylinux_2_39',
               '--requirements', str(BASE / 'manifests/public-requirements.txt')]
    with (BASE / 'logs/install-public.log').open('w') as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    print(f'Public installation exit code {result.returncode}; logs/install-public.log', flush=True)
    return result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['plan', 'repack', 'install-public', 'install-repacked'])
    parser.add_argument('--repack', nargs='*', default=[])
    args = parser.parse_args()
    for directory in ['logs', 'manifests', 'wheels']:
        (BASE / directory).mkdir(exist_ok=True)
    if args.action == 'plan':
        plan(args.repack)
    elif args.action == 'repack':
        data = json.loads((BASE / 'manifests/image-packages.json').read_text())
        for key in data['repack']:
            repack(data['packages'][key])
        sums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted((BASE / 'wheels').glob('*.whl'))}
        (BASE / 'manifests/wheel-sha256.json').write_text(json.dumps(sums, indent=2) + '\n')
    elif args.action == 'install-public':
        sys.exit(install_public())
    else:
        subprocess.run([UV, 'pip', 'install', '--python', str(BASE / '.venv/bin/python'),
                        '--no-deps', '--python-platform', 'x86_64-manylinux_2_39',
                        *map(str, sorted((BASE / 'wheels').glob('*.whl')))], check=True)


if __name__ == '__main__':
    main()
