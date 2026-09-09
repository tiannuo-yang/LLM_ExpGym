#!/usr/bin/env python3
"""Candidate-only deterministic metadata batches; no payload or authority reads."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
COMMON = BASE.parent / 'shard_delivery_candidate_v2/common.py'
COMMON_SHA = '7147524d5799dc1264f088518db19251c5f906bc2da501854ce279f56d73263e'
if hashlib.sha256(COMMON.read_bytes()).hexdigest() != COMMON_SHA:
    raise RuntimeError('frozen_helper_identity')
loader = importlib.util.spec_from_file_location('batch_frozen_common', COMMON)
c = importlib.util.module_from_spec(loader)
loader.loader.exec_module(c)
validator = c.scanner()  # Hash-pinned source only; no validate/scan/secret call.
MAX_FILES = 5000
MANIFEST_BYTES = 6 * 1024**2
INPUT_SCHEMA = 'sealed-publication-file-inventory-v1'


def relative(value):
    path = validator.relative(value)
    c.need(path.as_posix() == value and not validator.denied(value), 'unsafe_relative_path')
    try:
        c.need(len(value.encode('utf-8')) <= 4096, 'path_too_long')
    except UnicodeError:
        raise c.DeliveryError('invalid_path_utf8') from None
    return path


def build(inventory, inventory_sha256, max_files=MAX_FILES, manifest_bytes=MANIFEST_BYTES):
    """Pure metadata transformation. ROOT authority is declared, not verified here."""
    c.checksum(inventory_sha256)
    c.number(max_files, MAX_FILES, 'batch_file_limit', 1)
    c.number(manifest_bytes, MANIFEST_BYTES, 'batch_manifest_limit', 1)
    c.need(isinstance(inventory, dict) and set(inventory) ==
           {'schema_version', 'issuer', 'sealed', 'authority_ref', 'files'}, 'inventory_schema')
    c.need(inventory['schema_version'] == INPUT_SCHEMA and inventory['issuer'] == 'ROOT'
           and inventory['sealed'] is True, 'root_sealed_inventory_required')
    authority = inventory['authority_ref']
    c.need(isinstance(authority, dict) and set(authority) == {'path', 'sha256'}, 'authority_ref_schema')
    relative(authority['path'])
    c.checksum(authority['sha256'])
    rows = inventory['files']
    c.need(isinstance(rows, list) and bool(rows), 'empty_inventory')
    seen, paths = set(), []
    for row in rows:
        c.need(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'file_row_schema')
        path = relative(row['path'])
        c.need(row['path'] not in seen, 'duplicate_original_path')
        seen.add(row['path'])
        paths.append(path)
        c.need(type(row['bytes']) is int and row['bytes'] >= 0, 'invalid_original_size')
        c.need(row['bytes'] <= c.MEMBER, 'blocked_original_over_100_mib_no_chunk')
        c.checksum(row['sha256'])
    c.need(not any(parent.as_posix() in seen for path in paths for parent in path.parents
                   if parent.as_posix() != '.'), 'file_directory_path_collision')
    rows = sorted(rows, key=lambda row: row['path'])
    ordered = hashlib.sha256()
    for row in rows:
        ordered.update(c.encoded(row))

    def new_spec(number):
        return {'schema_version': 1, 'approved': False, 'candidate': True,
                'require_secret_sources': True, 'publication_authorized': False,
                'scope': 'Metadata batch candidate only; ROOT review and original-content sealing remain required.',
                'source_inventory_sha256': inventory_sha256, 'authority_ref': authority,
                'batch_number': number, 'artifacts': [],
                'required_stages': ['full_content_scan', 'root_publication_acceptance']}

    outputs, batches, restored_rows = {}, [], []
    spec, length, batch_rows = new_spec(1), 0, []
    length = len(c.encoded(spec))

    def finish():
        payload = c.encoded(spec)
        c.need(batch_rows and len(payload) == length and len(payload) <= manifest_bytes,
               'encoded_manifest_limit_or_size_accounting')
        name = 'batch-%06d.candidate.json' % spec['batch_number']
        outputs[name] = payload
        batches.append({'path': name, 'bytes': len(payload), 'sha256': c.sha(payload),
                        'file_count': len(batch_rows), 'original_bytes': sum(r['bytes'] for r in batch_rows),
                        'first_path': batch_rows[0]['path'], 'last_path': batch_rows[-1]['path']})
        restored_rows.extend({'path': a['source'], 'bytes': a['files'][0]['bytes'],
                              'sha256': a['files'][0]['sha256']} for a in spec['artifacts'])

    for number, row in enumerate(rows, 1):
        basename = relative(row['path']).name
        artifact = {'id': 'file_%09d' % number, 'kind': 'sealed_file', 'sealed': True,
                    'source': row['path'], 'target': row['path'],
                    'anchor': {'path': basename, 'sha256': row['sha256']},
                    'files': [{'path': basename, 'bytes': row['bytes'], 'sha256': row['sha256']}]}
        added = len(c.encoded(artifact)) - 1  # Artifact has no trailing newline inside the array.
        if batch_rows and (len(batch_rows) == max_files or length + added + 1 > manifest_bytes):
            finish()
            spec, batch_rows = new_spec(len(batches) + 1), []
            length = len(c.encoded(spec))
        added += bool(batch_rows)  # Exact comma byte, with no estimates or UTF-8 character counts.
        c.need(length + added <= manifest_bytes, 'blocked_single_metadata_row_exceeds_batch_limit')
        spec['artifacts'].append(artifact)
        batch_rows.append(row)
        length += added
    finish()
    c.need(restored_rows == rows, 'batch_union_or_order_mismatch')
    index = {'schema_version': 'publication-batch-candidate-index-v1', 'candidate': True,
             'approved': False, 'publication_authorized': False, 'source_inventory_sha256': inventory_sha256,
             'authority_ref': authority, 'authority_ref_verified': False, 'file_count': len(rows),
             'original_bytes': sum(r['bytes'] for r in rows), 'ordered_file_rows_sha256': ordered.hexdigest(),
             'limits': {'max_files': max_files, 'manifest_bytes': manifest_bytes,
                        'original_file_bytes': c.MEMBER, 'index_bytes': c.INDEX_LIMIT},
             'batch_count': len(batches), 'batches': batches,
             'original_payloads_read': False, 'security_scan_performed': False,
             'known_secrets_read': False, 'pack_performed': False, 'publication_performed': False,
             'frozen_tools': {'common_sha256': COMMON_SHA, 'scanner_sha256': c.SCANNER_SHA}}
    index_raw = c.encoded(index)
    c.need(len(index_raw) <= c.INDEX_LIMIT, 'candidate_index_limit')
    outputs['INDEX.candidate.json'] = index_raw  # Written last; not an approval or publication marker.
    return outputs


def prepare(inventory_path, inventory_sha256, output, max_files=MAX_FILES, manifest_bytes=MANIFEST_BYTES):
    output = c.fresh(output)  # Existing parent required; reject symlinks and any existing output.
    raw = validator.stable_read(c.lexical(inventory_path), limit=c.MEMBER)
    c.need(c.sha(raw) == c.checksum(inventory_sha256), 'external_inventory_digest_mismatch')
    outputs = build(c.strict_json(raw), inventory_sha256, max_files, manifest_bytes)
    output.mkdir(mode=0o700, exist_ok=False)
    for name, payload in outputs.items():
        c.write_new(output / name, payload)
    c.sync_directory(output)
    return {'candidate_preparation_complete': True, 'approved': False,
            'index_sha256': c.sha(outputs['INDEX.candidate.json']), 'batch_count': len(outputs) - 1,
            'security_scan_performed': False, 'publication_performed': False}


def main():
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise c.DeliveryError('invalid_arguments')
    try:
        parser = Parser(description=__doc__)
        parser.add_argument('--inventory', type=Path, required=True)
        parser.add_argument('--inventory-sha256', required=True)
        parser.add_argument('--output-dir', type=Path, required=True)
        parser.add_argument('--max-files', type=int, default=MAX_FILES)
        parser.add_argument('--manifest-bytes', type=int, default=MANIFEST_BYTES)
        args = parser.parse_args()
        print(json.dumps(prepare(args.inventory, args.inventory_sha256, args.output_dir,
                                 args.max_files, args.manifest_bytes)))
        return 0
    except Exception as exc:
        code = str(exc) if isinstance(exc, (c.DeliveryError, validator.CheckError)) else 'metadata_prepare_failed'
        print(json.dumps({'candidate_preparation_complete': False, 'approved': False, 'rule': code,
                          'security_scan_performed': False, 'publication_performed': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
