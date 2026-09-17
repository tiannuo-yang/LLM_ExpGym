#!/usr/bin/env python3
"""Copy the nine already sealed cohorts without extracting or repacking raw data.

Metadata is pinned to the frozen lineage index. Each compressed archive is read
exactly once during copying, with its inherited SHA checked before promotion.
Per-member identities are inherited, not falsely claimed as newly decompressed.
Gemini is intentionally owned by a separate snapshot consolidation step.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import time

W = Path('/lustrefs/users/chufan.shi/codex_space_tn')
P = W / 'publication/five_model_report_20260911'
LINEAGE = P / 'results/six-models-lineage-20260914/ARCHIVE_INDEX.json'
DEST = W / 'deliveries/paper-ad03e8c-20260916'
LEGACY = W / 'publication/k3_composite_full_remote.2xWrw79q/repo/results/portable-eval-20260908/full_delivery_v5'
RERUN = W / 'eval_material_rerun_20260912/delivery_prepare/remote_verify_outputs'


def relative(value):
    p = PurePosixPath(value)
    assert value and not p.is_absolute() and '..' not in p.parts and p.as_posix() == value
    return p


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path, expected=None):
    assert not path.is_symlink() and path.is_file(), f'metadata_type:{path}'
    data = path.read_bytes()
    if expected:
        assert digest(data) == expected, f'metadata_digest:{path}'
    return json.loads(data), data


def category(path):
    if '/api_dump/' in path or '/dumps/' in path:
        return 'api_request_response_dump'
    if ('/agents/agent_' in path or '/traces-v2/' in path) and '/_terminal_evidence/' not in path:
        return 'canonical_trajectory'
    if '/_terminal_evidence/' in path:
        return 'terminal_evidence'
    return 'result_or_control'


class Plan:
    def __init__(self):
        self.files = {}
        self.archives = []
        self.cohorts = []
        self.members = []

    def add(self, source, destination, expected=None, size=None, role='control'):
        assert not source.is_symlink() and source.is_file(), f'missing:{source}'
        if size is None or expected is None:
            data = source.read_bytes()
            size, expected = len(data), digest(data)
        info = source.stat()
        assert stat.S_ISREG(info.st_mode) and info.st_size == size
        row = dict(source_path=str(source), path=destination, bytes=size, sha256=expected, role=role)
        if destination in self.files:
            assert self.files[destination] == row
        self.files[destination] = row
        return row

    def modern(self, cohort, root, manifest_sha, original_root, visibility, parent_commit, outer=None):
        manifest_path = root / 'manifest.json'
        manifest, raw = load(manifest_path, manifest_sha)
        assert manifest['schema'] == 'expgym.delivery.v1'
        payload_prefix = 'payload/' if outer else ''
        prefix = f'raw_archives/{cohort}/' + payload_prefix
        local_manifest = prefix + 'manifest.json'
        self.add(manifest_path, local_manifest, digest(raw), len(raw), 'member_manifest')
        paths = set()
        groups = {}
        roles = {}
        for row in manifest['files']:
            relative(row['path'])
            assert row['path'] not in paths
            paths.add(row['path'])
            groups.setdefault(row['archive'], []).append(row)
            name = category(row['path'])
            roles[name] = roles.get(name, 0) + 1
        for row in manifest['archives']:
            relative(row['path'])
            members = groups.pop(row['path'])
            destination = prefix + row['path']
            self.add(root / row['path'], destination, row['sha256'], row['bytes'], 'archive')
            self.archives.append(dict(cohort_id=cohort, archive=destination, archive_sha256=row['sha256'], archive_bytes=row['bytes'], format=manifest['schema'], manifest=local_manifest, manifest_sha256=digest(raw), member_inventory=local_manifest, member_inventory_sha256=digest(raw), member_count=len(members), original_bytes=sum(x['bytes'] for x in members), original_path_root=str(original_root), original_path_rule='source_path = original_path_root / member.path', visibility=visibility, source_commit=parent_commit, source_archive=str(root / row['path'])))
            for member in members:
                self.members.append(dict(cohort_id=cohort, archive_file=destination, member_path=member['path'], tar_member_path=member['path'], bytes=member['bytes'], sha256=member['sha256'], original_path=str(original_root/member['path']), member_inventory=local_manifest))
        assert not groups
        if outer:
            for row in outer:
                rel = PurePosixPath(row['path']).relative_to('bundles', cohort.split('_')[0]).as_posix()
                self.add(root.parent / rel, f'raw_archives/{cohort}/{rel}', row['sha256'], row['bytes'])
        self.cohorts.append(dict(cohort_id=cohort, format=manifest['schema'], manifest=local_manifest, manifest_sha256=digest(raw), archive_count=len(manifest['archives']), member_count=len(paths), original_bytes=sum(x['bytes'] for x in manifest['files']), archive_bytes=sum(x['bytes'] for x in manifest['archives']), member_role_counts=roles, original_path_root=str(original_root), source_manifest=str(manifest_path), visibility=visibility, source_commit=parent_commit, public_scan_inherited=manifest.get('security', {}).get('public_scan_passed', False)))

    def legacy(self, cohort, root, index_name, expected, original_root, source_commit):
        collection, raw = load(root / index_name, expected)
        assert collection['schema'] == 'whole-file-collection-v1'
        prefix = f'raw_archives/{cohort}/'
        self.add(root / index_name, prefix + index_name, expected, len(raw), 'collection_manifest')
        all_paths = set()
        roles = {}
        total_archive_bytes = 0
        archives_before = len(self.archives)
        for bundle in collection['bundles']:
            rel_index = relative(bundle['index']).as_posix()
            index_path = root / rel_index
            index, body = load(index_path, bundle['sha256'])
            self.add(index_path, prefix + rel_index, bundle['sha256'], len(body), 'bundle_manifest')
            rel_payload = PurePosixPath(rel_index).parent
            rel_bundle = rel_payload.parent
            complete_path = root / rel_bundle / 'COMPLETE.json'
            complete, _ = load(complete_path)
            assert complete['complete'] and complete['binding']['index_sha256'] == bundle['sha256']
            self.add(complete_path, prefix + (rel_bundle / 'COMPLETE.json').as_posix())
            scan = index['source_scan']
            self.add(index_path.parent / relative(scan['path']), prefix + (rel_payload / scan['path']).as_posix(), scan['sha256'], scan['bytes'])
            bundle_count = 0
            bundle_bytes = 0
            for shard in index['shards']:
                member_source = index_path.parent / relative(shard['index'])
                members, member_body = load(member_source, shard['index_sha256'])
                member_local = prefix + (rel_payload / shard['index']).as_posix()
                self.add(member_source, member_local, shard['index_sha256'], shard['index_bytes'], 'member_manifest')
                rows = members['files']
                assert len(rows) == shard['file_count']
                for row in rows:
                    relative(row['path'])
                    assert row['path'] not in all_paths
                    all_paths.add(row['path'])
                    name = category(row['path'])
                    roles[name] = roles.get(name, 0) + 1
                expanded = sum(x['bytes'] for x in rows)
                # Legacy tar also embeds its member-index JSON as one control.
                assert expanded + len(member_body) == shard['expanded_bytes']
                bundle_count += len(rows)
                bundle_bytes += expanded
                archive_local = prefix + (rel_payload / relative(shard['archive'])).as_posix()
                source = index_path.parent / shard['archive']
                self.add(source, archive_local, shard['sha256'], shard['bytes'], 'archive')
                total_archive_bytes += shard['bytes']
                self.archives.append(dict(cohort_id=cohort, archive=archive_local, archive_sha256=shard['sha256'], archive_bytes=shard['bytes'], format='whole-file-collection-v1', manifest=prefix + index_name, manifest_sha256=expected, member_inventory=member_local, member_inventory_sha256=shard['index_sha256'], member_count=len(rows), original_bytes=expanded, original_path_root=str(original_root), original_path_rule='source_path = original_path_root / member.path', visibility='inherited_public_archive', source_commit=source_commit, source_archive=str(source)))
                for member in rows:
                    self.members.append(dict(cohort_id=cohort, archive_file=archive_local, member_path=member['path'], tar_member_path='data/'+member['path'], bytes=member['bytes'], sha256=member['sha256'], original_path=str(original_root/member['path']), member_inventory=member_local))
            assert (bundle_count, bundle_bytes) == (bundle['file_count'], bundle['original_bytes'])
        assert len(all_paths) == collection['file_count']
        self.cohorts.append(dict(cohort_id=cohort, format=collection['schema'], manifest=prefix + index_name, manifest_sha256=expected, archive_count=len(self.archives)-archives_before, member_count=collection['file_count'], original_bytes=collection['original_bytes'], archive_bytes=total_archive_bytes, member_role_counts=roles, original_path_root=str(original_root), source_manifest=str(root / index_name), visibility='inherited_public_archive', source_commit=source_commit, public_scan_inherited=True))


def prepare():
    lineage, _ = load(LINEAGE)
    old = {x['model']: x for x in lineage['published_four_model_parent']['models']}
    plan = Plan()
    plan.legacy('kimi_original', LEGACY, 'INDEX.kimi-k3-composite-v1.json', old['kimi-k3']['raw_entry']['sha256'], W, old['kimi-k3']['data_commit'])
    glmroot = LEGACY / 'glm-5.3-original-completed-20260909/payload/collection'
    plan.legacy('glm_original', glmroot, 'INDEX.json', old['glm-5.3']['raw_entry']['sha256'], W, old['glm-5.3']['data_commit'])
    plan.modern('qwen_original', W/'qwen38_eval_20260910/remote_verify_ff8c572_20260911/sealed', old['qwen3.8-2.4t-a95b-fp8']['raw_entry']['sha256'], W/'qwen38_eval_20260910', 'inherited_public_archive', old['qwen3.8-2.4t-a95b-fp8']['data_commit'])
    plan.modern('deepseek_original', W/'deepseek_flash_eval_20260911/remote_verified_v1/sealed', old['deepseek-v4-flash-0731']['raw_entry']['sha256'], W/'deepseek_flash_eval_20260911', 'inherited_public_archive', old['deepseek-v4-flash-0731']['data_commit'])
    gpt = lineage['original_gpt_local_delivery']['collections'][0]
    plan.modern('gpt_original', Path(gpt['manifest']['local_path']).parent, gpt['manifest']['sha256'], W/'LLM_ExpGym_api_studies_20260910', 'local_only_no_new_public_clearance', '')
    for model in lineage['targeted_rerun']['inherited_index']['models']:
        name = model['model']
        plan.modern(f'{name}_rerun_20260912', RERUN/name/'payload', model['manifest']['sha256'], W/'eval_material_rerun_20260912'/name, 'inherited_public_archive', lineage['targeted_rerun']['commit'], model['outer_files'])
    # Original legacy tool byte identities are pinned internally by their loader.
    tools_root = LEGACY/'kimi-k3-original-node-failure-20260909/payload/tools/publication'
    for rel in ['collection_restore_candidate_v2/restore_collection.py', 'shard_delivery_candidate_v2/common.py', 'shard_delivery_candidate_v2/restore.py', 'validate_bundle_v2.py']:
        plan.add(tools_root/rel, 'tools/legacy/'+rel, role='restore_tool')
    for rel in ['scripts/package_run.py', 'expgym/delivery.py', 'expgym/__init__.py']:
        plan.add(P/rel, 'tools/modern/'+rel, role='restore_tool')
    return plan


def copy_one(row, destination):
    source = Path(row['source_path'])
    target = destination / relative(row['path'])
    target.parent.mkdir(parents=True, exist_ok=True)
    assert not target.exists(), f'fresh_target_required:{target}'
    before = source.stat()
    sha = hashlib.sha256()
    size = 0
    partial = target.with_name(target.name + '.copying')
    with source.open('rb') as src, partial.open('xb') as dst:
        for block in iter(lambda: src.read(1024*1024), b''):
            sha.update(block)
            size += len(block)
            dst.write(block)
    after = source.stat()
    assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns), 'source_changed'
    assert (size, sha.hexdigest()) == (row['bytes'], row['sha256']), f'copy_digest:{source}'
    os.replace(partial, target)


def write_json(path, obj):
    with path.open('x', encoding='utf-8') as out:
        json.dump(obj, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def add_tar_member_metadata():
    """Add actual tar names from recorded archive formats; never open payloads."""
    with (DEST/'raw_archives/ARCHIVES.csv').open(newline='', encoding='utf-8') as stream:
        formats = {row['archive']: row['format'] for row in csv.DictReader(stream)}
    source = DEST/'raw_archives/MEMBERS.csv'
    target = source.with_name('MEMBERS.csv.add-tar-member-path')
    before = source.stat()
    counts = {'whole-file-collection-v1': 0, 'expgym.delivery.v1': 0}
    with source.open(newline='', encoding='utf-8') as stream, target.open('x', newline='', encoding='utf-8') as out:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames)
        assert 'tar_member_path' not in fields, 'already_has_tar_member_path'
        fields.insert(fields.index('member_path') + 1, 'tar_member_path')
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        for row in reader:
            fmt = formats[row['archive_file']]
            assert fmt in counts, 'unsupported_recorded_archive_format'
            relative(row['member_path'])
            row['tar_member_path'] = ('data/' if fmt == 'whole-file-collection-v1' else '') + row['member_path']
            counts[fmt] += 1
            writer.writerow(row)
    after = source.stat()
    assert (before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
    assert sum(counts.values()) == 245679, 'unexpected_original_member_count'
    os.replace(target, source)
    print(json.dumps({'status': 'PASS', 'metadata_only': True, 'archive_payloads_read': 0, 'members': sum(counts.values()), 'by_format': counts}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--add-tar-member-metadata', action='store_true')
    args = parser.parse_args()
    if args.add_tar_member_metadata:
        add_tar_member_metadata()
        return
    start = time.monotonic()
    plan = prepare()
    summary = dict(cohorts=plan.cohorts, copied_files=len(plan.files), archives=len(plan.archives), archive_bytes=sum(x['archive_bytes'] for x in plan.archives), original_members=sum(x['member_count'] for x in plan.cohorts), original_bytes=sum(x['original_bytes'] for x in plan.cohorts))
    if not args.execute:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    assert not (DEST/'raw_archives/ARCHIVES.json').exists()
    for num, row in enumerate(plan.files.values(), 1):
        copy_one(row, DEST)
        if num % 100 == 0:
            print(json.dumps({'copied_files':num,'total_files':len(plan.files)}), flush=True)
    summary.update(schema='expgym.consolidated-inherited-archives.v1', report_commit='ad03e8c42ca501016176ee1bc407b38499178506', archives=plan.archives, consolidation='byte-identical regular file copies, no symlinks; compressed archive SHA256 verified during copy', member_identity_scope='Inherited pinned per-member identities; no old tar re-extraction or new member scan', restored_members_this_step=0, source_scope='Nine pre-existing sealed cohorts only; Gemini snapshot is separately consolidated', elapsed_seconds=time.monotonic()-start, copied_files_inventory=list(plan.files.values()))
    write_json(DEST/'raw_archives/ARCHIVES.json', summary)
    with (DEST/'raw_archives/MEMBERS.csv').open('x', newline='', encoding='utf-8') as out:
        writer=csv.DictWriter(out, fieldnames=list(plan.members[0]))
        writer.writeheader()
        writer.writerows(plan.members)
    with (DEST/'raw_archives/ARCHIVES.csv').open('x', newline='', encoding='utf-8') as out:
        writer=csv.DictWriter(out, fieldnames=list(plan.archives[0]))
        writer.writeheader()
        writer.writerows(plan.archives)
    print(json.dumps({'status':'PASS','cohorts':len(plan.cohorts),'archives':len(plan.archives),'archive_bytes':summary['archive_bytes'],'original_members':summary['original_members'],'copied_files':len(plan.files),'elapsed_seconds':summary['elapsed_seconds']}), flush=True)


if __name__ == '__main__':
    main()
