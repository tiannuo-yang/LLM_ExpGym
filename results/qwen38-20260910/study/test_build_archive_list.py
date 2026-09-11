"""Synthetic-only coverage for the closed-queue archive file selector."""
import fcntl
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from build_archive_list import build, digest, main


class ArchiveListTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='qwen_archive_list_test_')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.invocation = self.root / 'formal/invocations/job_one'
        self.queue = self.root / 'formal/queue'
        self.session = self.queue / 'sessions/100-200'
        self.identity = {'source_tree_sha256': 'a' * 64, 'selection': {'item': 'fixture'}}
        self.raw = self.invocation / 'api_dump/call.json'
        self.put(self.raw, b'fixture model request; selector must not read it\n')
        self.put(self.invocation / 'runtime/hpobench/cache/lock', b'')
        self.put(self.invocation / 'runtime/hpobench/config/.hpobenchrc', b'{}\n')
        self.artifacts = {str(path.relative_to(self.invocation)): self.pin(path)
                          for path in (self.raw, self.invocation / 'runtime/hpobench/cache/lock',
                                       self.invocation / 'runtime/hpobench/config/.hpobenchrc')}
        self.plan = {'schema': 'expgym.study-queue-plan.v1', 'jobs': [
            {'job_id': 'job_one', 'identity': self.identity,
             'args': {'output_dir': str(self.invocation / 'result')}}]}
        self.plan_path = self.root / 'study/plan.json'
        self.dump(self.plan_path, self.plan)
        self.put(self.queue / 'controller.lock', b'')
        self.dump(self.queue / 'definition.json', {
            'schema': 'expgym.queue-definition.v1', 'jobs': [
                {'id': 'job_one', 'identity': self.identity, 'output': str(self.invocation)}]})
        self.dump(self.queue / 'jobs/job_one/started.json', {'identity_sha256': digest(self.identity)})
        self.completion = {'job_id': 'job_one', 'identity_sha256': digest(self.identity),
                           'mode': 'execute', 'exit_code': 0, 'pid': 123,
                           'artifacts': self.artifacts}
        self.dump(self.queue / 'jobs/job_one/completion.json', self.completion)
        self.report = dict(self.completion, passed=True)
        self.dump(self.session / 'job_one.json', self.report)
        self.dump(self.session / 'summary.json', {
            'schema': 'expgym.study-queue-summary.v1', 'planned': 1, 'finished': 1,
            'reports': [self.report], 'unstarted': [], 'passed': True})
        self.put(self.session / 'events.jsonl', b'{"event":"drained","active":0,"unstarted":0}\n')
        self.put(self.session / 'job_one.stdout.log', b'closed worker stdout\n')
        self.put(self.session / 'job_one.stderr.log', b'closed worker stderr\n')
        self.state_path = self.root / 'study/states.json'
        self.state = {'schema': 'qwen38.analysis-states.v1',
                      'plan_sha256': self.pin(self.plan_path)['sha256'],
                      'roots': [{'path': str(self.queue), 'sessions': ['100-200']}]}
        self.dump(self.state_path, self.state)
        self.put(self.root / 'serving/launch01/launcher_exit.json', b'{"exit_code":1}\n')
        self.put(self.root / 'serving/launch01/failed.log', b'failed serving diagnostic\n')
        self.put(self.root / 'serving/launch02/closed.log', b'accepted serving diagnostic\n')
        self.put(self.root / 'native_smoke01/summary.json', b'{"passed":true}\n')
        self.put(self.root / 'study/helper.py', b'# current helper\n')

    def put(self, path, body):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)

    def dump(self, path, value):
        self.put(path, (json.dumps(value, sort_keys=True) + '\n').encode())

    def pin(self, path):
        raw = path.read_bytes()
        return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def binding(self):
        return [(str(self.plan_path), self.pin(self.plan_path)['sha256'],
                 str(self.state_path), self.pin(self.state_path)['sha256'])]

    def test_success_keeps_raw_logs_failed_launch_and_never_reads_payload(self):
        bindings = self.binding()
        original = Path.read_bytes
        def metadata_only(path):
            self.assertFalse(path == self.raw or path.suffix == '.log', 'payload/log read forbidden')
            return original(path)
        with mock.patch.object(Path, 'read_bytes', metadata_only):
            paths, summary = build(self.root, bindings, ['study/helper.py'],
                                   ['native_smoke01', 'serving/launch01', 'serving/launch02'])
        self.assertEqual(paths, sorted(set(paths)))
        self.assertIn(str(self.raw.relative_to(self.root)), paths)
        self.assertIn('serving/launch01/failed.log', paths)
        self.assertIn('formal/queue/sessions/100-200/job_one.stdout.log', paths)
        self.assertIn('formal/queue/sessions/100-200/job_one.stderr.log', paths)
        self.assertIn('formal/queue/sessions/100-200/job_one.json', paths)
        self.assertIn('formal/invocations/job_one/runtime/hpobench/config/.hpobenchrc', paths)
        self.assertNotIn('formal/invocations/job_one/runtime/hpobench/cache/lock', paths)
        self.assertEqual(len(summary['excluded']), 1)
        self.assertFalse(summary['payload_sha256_rechecked'])
        self.assertFalse(summary['publication_scanned'])

    def test_missing_inventory_file_rejected(self):
        self.raw.unlink()
        with self.assertRaises(FileNotFoundError):
            build(self.root, self.binding())

    def test_size_mismatch_rejected(self):
        self.raw.write_bytes(b'different size')
        with self.assertRaisesRegex(ValueError, 'inventory_size'):
            build(self.root, self.binding())

    def test_active_queue_rejected_before_any_payload_registration(self):
        with (self.queue / 'controller.lock').open('rb') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # A missing raw would otherwise fail metadata registration; lock
            # contention must occur first, without looking into invocation.
            self.raw.unlink()
            with self.assertRaises(BlockingIOError):
                build(self.root, self.binding())

    def test_unclosed_or_omitted_new_session_rejected(self):
        (self.queue / 'sessions/101-201').mkdir()
        with self.assertRaisesRegex(ValueError, 'omitted or added'):
            build(self.root, self.binding())
        self.state['roots'][0]['sessions'].append('101-201')
        self.dump(self.state_path, self.state)
        with self.assertRaises(FileNotFoundError):
            build(self.root, self.binding())

    def test_missing_final_drain_rejected(self):
        self.put(self.session / 'events.jsonl', b'{"event":"start","active":1}\n')
        with self.assertRaisesRegex(ValueError, 'natural drain'):
            build(self.root, self.binding())

    def test_traversal_inventory_rejected(self):
        self.completion['artifacts'] = {'../outside.json': {'bytes': 0, 'sha256': 'a' * 64}}
        self.dump(self.queue / 'jobs/job_one/completion.json', self.completion)
        self.report = dict(self.completion, passed=True)
        self.dump(self.session / 'job_one.json', self.report)
        self.dump(self.session / 'summary.json', {'schema': 'expgym.study-queue-summary.v1',
                  'planned': 1, 'finished': 1, 'reports': [self.report], 'unstarted': []})
        with self.assertRaisesRegex(ValueError, 'unsafe_invocation_relative_path'):
            build(self.root, self.binding())

    def test_outside_queue_metadata_rejected(self):
        self.state['roots'][0]['path'] = str(self.root.parent / 'another-study/queue')
        self.dump(self.state_path, self.state)
        with self.assertRaisesRegex(ValueError, 'outside_archive_root'):
            build(self.root, self.binding())

    def test_payload_symlink_rejected(self):
        target = self.invocation / 'other.json'
        self.raw.rename(target)
        self.raw.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symlink_or_non_regular_file'):
            build(self.root, self.binding())

    def test_parent_symlink_and_attachment_symlink_rejected(self):
        (self.root / 'study/linked').symlink_to(self.root / 'study', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink_or_non_directory'):
            build(self.root, self.binding(), ['study/linked/helper.py'])
        (self.root / 'native_smoke01/link').symlink_to(self.root / 'study', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink_or_non_directory'):
            build(self.root, self.binding(), directories=['native_smoke01'])

    def test_private_runtime_weights_data_and_old_draft_rejected(self):
        for name in ('study/private-key.txt', 'runtime/.venv/pyvenv.cfg',
                     'weights/model.safetensors', 'data/corpus.json',
                     'study/draft_v1/plan.json', 'study/formal_plan.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build(self.root, self.binding(), [name])

    def test_recursive_queue_and_broad_attachment_roots_rejected(self):
        for directory in ('formal', 'formal/invocations', 'formal/queue', 'study', 'runtime'):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                build(self.root, self.binding(), directories=[directory])

    def test_only_named_root_plan_is_an_attachment(self):
        self.put(self.root / 'PLAN.zh.md', b'# Closed study execution record\n')
        paths, unused = build(self.root, self.binding(), ['PLAN.zh.md'])
        self.assertIn('PLAN.zh.md', paths)
        for name in ('other.md', 'study/RUN_INPUTS_cache_salt.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build(self.root, self.binding(), [name])

    def test_unindexed_or_undeclared_queue_file_cannot_be_attachment(self):
        for name in ('formal/invocations/job_one/unindexed.json',
                     'other_queue/invocations/job_one/raw.json'):
            self.put(self.root / name, b'unindexed original')
            with self.subTest(name=name), self.assertRaises(ValueError):
                build(self.root, self.binding(), [name])

    def test_completion_cannot_silently_omit_reported_raw(self):
        del self.completion['artifacts']['api_dump/call.json']
        self.dump(self.queue / 'jobs/job_one/completion.json', self.completion)
        with self.assertRaisesRegex(ValueError, 'completion_differs'):
            build(self.root, self.binding())

    def test_payload_cannot_be_opened_as_unlocked_plan_metadata(self):
        binding = list(self.binding()[0])
        binding[0] = str(self.raw)
        with self.assertRaisesRegex(ValueError, 'selection_metadata_must_be_under_study'):
            build(self.root, [binding])

    def test_failed_begun_attempt_needs_inventory_and_keeps_failed_raw(self):
        (self.queue / 'jobs/job_one/completion.json').unlink()
        report = {key: value for key, value in self.report.items() if key != 'artifacts'}
        report.update(exit_code=1, passed=False)
        self.dump(self.session / 'job_one.json', report)
        self.dump(self.session / 'summary.json', {'schema': 'expgym.study-queue-summary.v1',
                  'planned': 1, 'finished': 1, 'reports': [report], 'unstarted': [], 'passed': False})
        with self.assertRaisesRegex(ValueError, 'begun_failed_attempt_needs_explicit_inventory'):
            build(self.root, self.binding())
        self.state['unreceipted_artifacts'] = {str(self.invocation): self.artifacts}
        self.dump(self.state_path, self.state)
        paths, unused = build(self.root, self.binding())
        self.assertIn(str(self.raw.relative_to(self.root)), paths)
        self.assertIn('formal/queue/sessions/100-200/job_one.stderr.log', paths)

    def test_cli_writes_single_package_compatible_path_array(self):
        self.dump(self.root / 'study/attachments.json', ['study/helper.py'])
        output = self.root / 'study/selected-files.json'
        args = ['--root', str(self.root), '--queue'] + list(self.binding()[0]) + [
            '--files', 'study/attachments.json', '--directory', 'serving/launch01',
            '--output', str(output)]
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(args), 0)
        paths = json.loads(output.read_text())
        self.assertIn('serving/launch01/failed.log', paths)
        self.assertIn('study/helper.py', paths)
        self.assertEqual(json.loads(stdout.getvalue())['files'], len(paths))

    def test_wrong_plan_pin_and_receipt_owner_rejected(self):
        binding = list(self.binding()[0])
        binding[1] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            build(self.root, [binding])
        self.completion['job_id'] = 'other'
        self.dump(self.queue / 'jobs/job_one/completion.json', self.completion)
        with self.assertRaisesRegex(ValueError, 'completion_job_id_mismatch'):
            build(self.root, self.binding())

    def test_resume_session_uses_original_completion_inventory(self):
        resumed = self.queue / 'sessions/101-201'
        report = {key: value for key, value in self.report.items() if key != 'artifacts'}
        report['mode'] = 'verify_resume'
        self.dump(resumed / 'job_one.json', report)
        self.dump(resumed / 'summary.json', {'schema': 'expgym.study-queue-summary.v1',
                  'planned': 1, 'finished': 1, 'reports': [report], 'unstarted': []})
        self.put(resumed / 'events.jsonl', b'{"event":"drained","active":0,"unstarted":0}\n')
        self.put(resumed / 'job_one.stdout.log', b'closed resume stdout\n')
        self.put(resumed / 'job_one.stderr.log', b'')
        self.state['roots'][0]['sessions'].append('101-201')
        self.dump(self.state_path, self.state)
        paths, unused = build(self.root, self.binding())
        self.assertEqual(paths.count(str(self.raw.relative_to(self.root))), 1)
        self.assertIn('formal/queue/sessions/101-201/job_one.stdout.log', paths)


if __name__ == '__main__':
    unittest.main(verbosity=2)
