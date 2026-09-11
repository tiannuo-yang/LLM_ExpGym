#!/usr/bin/env python3
"""Build one package_run.py-compatible file list; never seal or read raw payloads.

Reuses analyze_qwen.states/Inputs for plan identity and closed queue checks.
Each --queue takes PLAN PLAN_SHA256 STATES STATES_SHA256. STATES is the same
qwen38.analysis-states.v1 input used by analysis, including every closed session
and explicit inventories for any begun failed attempt. Add the formal queue and
task smoke queue separately; their plans are not interchangeable.
Plan/state inputs and the attachment-path array must reside under study/.

After both queues and serving are closed, use --root <qwen-study-root>, then:
  --queue study/formal_plan_cache_salt.json <accepted-pin> <formal-states> <pin>
  --queue study/task_smoke_plan_cache_salt.json <accepted-pin> <smoke-states> <pin>
  --directory native_smoke01 --directory serving/launch01
  --directory serving/launch02 --files <explicit-attachment-paths.json>
  --output <fresh-file-list.json>

The explicit attachment array should select RUN_INPUTS_launch02.json, the
accepted formal_cache_salt matrix/coverage/runtime environment, data_inventory,
the current helper/analysis/report scripts and tests, accepted CPU validation,
and runtime/{pyproject.toml,uv.lock,runtime-env.sh,versions.json}. Never select
the whole study/runtime directory. Add final analysis/report directories only
after their own writers finish. Source/data/checkpoint identities remain in
provenance; external source checkouts, dataset copies, environments and weights
are not copied by this program. Failed serving/launch01 is intentionally kept.

Only directory attachments are walked, and only their explicit descendants.
Invocation payloads come exclusively from completion inventories (or explicit
failed-attempt inventories), never a recursive raw search. Metadata and file
sizes are checked, not payload SHA256; unchanged-size content verification and
four-source secret scanning belong to existing analysis/seal tools. stdout
records intentional derived-cache exclusions. Output is only a path array,
not a publication-clearance receipt. A later seal must use the same root.

Do not run on an active queue. Advisory controller locks are held throughout
selection. Closed queues do not prove a serving process or external writer is
quiescent; freeze/close attached diagnostics before building and sealing.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import stat
import sys

sys.dont_write_bytecode = True
from analyze_qwen import Inputs, digest, pin_ok, states

SOURCE_REPO = Path(__file__).resolve().parents[2] / 'LLM_ExpGym-qwen38-20260910'
sys.path.insert(0, str(SOURCE_REPO))
from expgym.delivery import canonical_path, validate_paths

OLD_INPUTS = {
    'study/formal_plan.json', 'study/task_smoke_plan.json',
    'study/task_smoke_matrix.json', 'study/RUN_INPUTS.json',
    'study/RUN_INPUTS_cache_salt.json',
}
PRIVATE_NAME = re.compile(r'(^|[._-])(private[-_]?key|api[-_]?key|secrets?|credentials)([._-]|$)', re.I)
ATTACHMENT_TOP_LEVELS = {'study', 'runtime', 'serving', 'native_smoke01',
                         'analysis', 'report', 'reports', 'results'}


def require(condition, rule):
    if not condition:
        raise ValueError(rule)


class Selection:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.files = {}
        self.excluded = {}
        self.directory_identity = {}
        self.directory_snapshots = {}
        self.blocked_attachment_roots = set()
        self.directory(self.root)

    def relative(self, value):
        path = Path(value)
        require('..' not in path.parts, 'path_outside_archive_root')
        path = path if path.is_absolute() else self.root / path
        try:
            relative = path.relative_to(self.root).as_posix()
        except ValueError:
            raise ValueError('path_outside_archive_root')
        canonical_path(relative)  # Reuse the delivery tool's complete path policy.
        parts = Path(relative).parts
        require(parts[0] != 'data', 'dataset_copy_excluded')
        require(relative not in OLD_INPUTS and not relative.startswith(
            ('study/draft_v1/', 'study/formal_v1/')), 'unexecuted_draft_excluded')
        require(not any(PRIVATE_NAME.search(part) for part in parts), 'private_path_excluded')
        return relative

    def path(self, value):
        return self.root / self.relative(value)

    def metadata_path(self, value):
        name = self.relative(value)
        require(Path(name).parts[0] == 'study', 'selection_metadata_must_be_under_study')
        return self.root / name

    def attachment_path(self, value, *, directory=False):
        name = self.relative(value)
        path = self.root / name
        # Duplicate already-inventoried files are harmless. An attachment must
        # not smuggle an unindexed invocation or undeclared queue into the list.
        if not directory and name in self.files:
            return path
        require(Path(name).parts[0] in ATTACHMENT_TOP_LEVELS
                or (not directory and name == 'PLAN.zh.md'), 'attachment_scope_not_admitted')
        require(not any(path == other or path in other.parents or other in path.parents
                        for other in self.blocked_attachment_roots), 'queue_tree_requires_inventory')
        return path

    def directory(self, path):
        unchecked = []
        for current in (path,) + tuple(path.parents):
            if current in self.directory_identity:
                break
            unchecked.append(current)
        for current in reversed(unchecked):
            info = current.lstat()
            require(stat.S_ISDIR(info.st_mode), 'symlink_or_non_directory_parent')
            signature = (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode))
            previous = self.directory_identity.setdefault(current, signature)
            require(previous == signature, 'directory_replaced_during_selection')

    def add(self, value, pin=None):
        name = self.relative(value)
        path = self.root / name
        self.directory(path.parent)
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode), 'symlink_or_non_regular_file')
        if pin is not None:
            require(pin_ok(pin) and pin['bytes'] == info.st_size, 'inventory_size_or_pin_mismatch')
        signature = (info.st_dev, info.st_ino, info.st_mode, info.st_size,
                     info.st_mtime_ns, info.st_ctime_ns)
        prior = self.files.setdefault(name, (signature, pin))
        require(prior[0] == signature, 'file_changed_during_selection')
        require(prior[1] is None or pin is None or prior[1] == pin, 'conflicting_inventory_pin')
        return path

    def artifact(self, root, relative, pin):
        # These are derivable runtime state, not model observations/results.
        # Keep .hpobenchrc; exclude cache/socket state the packager cannot accept.
        require(isinstance(relative, str) and relative and not Path(relative).is_absolute()
                and all(part not in ('', '.', '..') for part in relative.split('/')),
                'unsafe_invocation_relative_path')
        path = root / relative
        if relative.startswith(('runtime/hpobench/cache/', 'runtime/hpobench/sockets/')):
            require(pin_ok(pin), 'invalid_excluded_inventory_pin')
            name = path.relative_to(self.root).as_posix()
            self.excluded[name] = 'derived_hpobench_cache_or_socket_state'
            return
        self.add(path, pin)

    def walk_attachment(self, value):
        path = self.attachment_path(value, directory=True)
        name = path.relative_to(self.root).as_posix()
        require(name not in ('study', 'runtime', 'serving'), 'broad_attachment_directory_forbidden')
        self.directory(path)
        for directory, subdirs, names in os.walk(path, followlinks=False):
            current = Path(directory)
            self.directory_snapshots[current] = tuple(sorted(subdirs + names))
            for child in subdirs:
                self.relative(current / child)
                self.directory(current / child)
            for child in names:
                self.add(current / child)

    def finish(self):
        for name in list(self.files):
            self.add(name)
        for path, signature in self.directory_identity.items():
            info = path.lstat()
            require(stat.S_ISDIR(info.st_mode) and
                    (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)) == signature,
                    'directory_replaced_during_selection')
        for path, before in self.directory_snapshots.items():
            require(tuple(sorted(child.name for child in path.iterdir())) == before,
                    'attachment_directory_changed_during_selection')
        return validate_paths(list(self.files))


class MetadataInputs(Inputs):
    """Constrain reused analyzer reads before they can open any input file."""
    def __init__(self, selection):
        super().__init__()
        self.selection = selection

    def register(self, path, role, pin=None):
        checked = self.selection.add(path, pin)
        return super().register(checked, role, pin)


def build(root, queues, files=(), directories=()):
    selected = Selection(root)
    inputs = MetadataInputs(selected)
    require(bool(queues), 'explicit_queue_bindings_required')
    with ExitStack() as stack:
        attempts_by_queue = []
        queue_roots = set()
        invocation_roots = set()
        for plan_path, plan_sha, state_path, state_sha in queues:
            require(re.fullmatch('[0-9a-f]{64}', plan_sha or '')
                    and re.fullmatch('[0-9a-f]{64}', state_sha or ''), 'explicit_input_sha256_required')
            plan = inputs.json(selected.metadata_path(plan_path), 'accepted_plan', plan_sha)
            require(plan.get('schema') == 'expgym.study-queue-plan.v1'
                    and isinstance(plan.get('jobs'), list) and plan['jobs'], 'invalid_queue_plan')
            require(len({job['job_id'] for job in plan['jobs']}) == len(plan['jobs']), 'duplicate_plan_job')
            spec = inputs.json(selected.metadata_path(state_path), 'closed_queue_states', state_sha)
            require(spec.get('plan_sha256') == plan_sha, 'states_bound_to_wrong_plan')
            # Preflight roots and lock ancestors before the reused states()
            # opens actual lock files; never inspect formal payload here.
            for item in spec.get('roots', []):
                queue_root = selected.path(item['path'])
                require(queue_root not in queue_roots, 'duplicate_queue_state_root')
                queue_roots.add(queue_root)
                selected.add(queue_root / 'controller.lock')
                selected.blocked_attachment_roots.add(queue_root.parent)
            attempts = states(plan, spec, inputs, stack)
            for rows in attempts.values():
                for attempt in rows:
                    output = selected.path(attempt['artifact_root'])
                    require(not any(output == prior or output in prior.parents or prior in output.parents
                                    for prior in invocation_roots), 'overlapping_invocation_roots')
                    invocation_roots.add(output)
            attempts_by_queue.append((spec, attempts))
        # All declared controllers are now locked and every session is closed.
        for spec, attempts in attempts_by_queue:
            for job_id, rows in attempts.items():
                for attempt in rows:
                    root = selected.path(attempt['artifact_root'])
                    receipt = attempt['receipt']
                    require(receipt is None or receipt.get('job_id') == job_id,
                            'completion_job_id_mismatch')
                    if receipt is not None:
                        executions = [report for report in attempt['reports']
                                      if report.get('mode') == 'execute' and report.get('exit_code') == 0
                                      and report.get('passed') is True]
                        require(len(executions) == 1 and receipt == {
                            key: value for key, value in executions[0].items() if key != 'passed'},
                            'completion_differs_from_successful_session_report')
                    inventory = receipt['artifacts'] if receipt else spec.get(
                        'unreceipted_artifacts', {}).get(str(root))
                    require(not attempt['started'] or inventory is not None,
                            'begun_failed_attempt_needs_explicit_inventory')
                    for name, pin in (inventory or {}).items():
                        selected.artifact(root, name, pin)
            for item in spec['roots']:
                queue_root = selected.path(item['path'])
                for session_name in item['sessions']:
                    session = queue_root / 'sessions' / session_name
                    summary = inputs.json(session / 'summary.json', 'closed_queue_session')
                    for report in summary['reports']:
                        job_id = report['job_id']
                        separate = inputs.json(session / (job_id + '.json'), 'session_job_report')
                        require(separate == report, 'session_report_differs_from_summary')
                        # Failed before Popen may legitimately have no stdio.
                        for suffix in ('.stdout.log', '.stderr.log'):
                            path = session / (job_id + suffix)
                            if 'pid' in report or path.exists():
                                selected.add(path)
        for name in list(inputs.files):
            selected.add(name)
        for name in files:
            selected.add(selected.attachment_path(name))
        for name in directories:
            selected.walk_attachment(name)
        inputs.finish()  # Existing metadata SHA/stat guard; no payload reads.
        paths = selected.finish()
    return paths, {'files': len(paths), 'queues': len(queues),
                   'bytes': sum(row[0][3] for row in selected.files.values()),
                   'excluded': [{'path': name, 'reason': reason}
                                for name, reason in sorted(selected.excluded.items())],
                   'payload_sha256_rechecked': False, 'publication_scanned': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--queue', nargs=4, action='append', required=True,
                        metavar=('PLAN', 'PLAN_SHA256', 'STATES', 'STATES_SHA256'))
    parser.add_argument('--files', type=Path, help='JSON array of explicit root-relative attachment files')
    parser.add_argument('--directory', action='append', default=[], help='One explicit, closed attachment directory')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        require(not args.output.exists() and not args.output.is_symlink(), 'fresh_output_required')
        files = []
        if args.files:
            # Read only the explicit path-list itself; never any referenced key.
            selected = Selection(args.root)
            inputs = MetadataInputs(selected)
            files = inputs.json(selected.metadata_path(args.files), 'explicit_attachments')
            require(isinstance(files, list), 'attachment_path_array_required')
        paths, summary = build(args.root, args.queue, files, args.directory)
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(paths, handle, indent=2)
            handle.write('\n')
        print(json.dumps(summary, sort_keys=True))
        return 0
    except Exception as exc:
        # Avoid reflecting arbitrary payload/path values in diagnostics.
        code = str(exc) if type(exc) is ValueError and re.fullmatch('[a-z0-9_]+', str(exc)) else 'archive_selection_failed'
        print(json.dumps({'passed': False, 'rule': code}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
