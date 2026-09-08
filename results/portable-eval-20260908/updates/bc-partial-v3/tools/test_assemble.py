#!/usr/bin/env python3
"""CPU-only fixed-control fixtures; no real credential loading or live data."""
import concurrent.futures
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import assemble as a
c = a.c
import pack
import restore

PUBLIC_CONTROL = Path(__file__).resolve().parent.parent / 'control_originals' / a.CONTROL_NAME
ORIGINAL = PUBLIC_CONTROL if PUBLIC_CONTROL.is_file() else Path(__file__).resolve().parents[2] / a.CONTROL_TARGET


class FixedAssembly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = tempfile.TemporaryDirectory(prefix='bc-assembly-tests-')
        cls.fixture = Path(cls.context.name)
        cls.key = cls.fixture / 'synthetic_marker.txt'
        cls.key.write_text('SYNTHETIC_BC_ASSEMBLY_MARKER_20260908')
        (cls.fixture / 'input.json').write_text('{"value":1}\n')
        source = cls.fixture / 'input.json'
        size, digest = c.stream_hash(source)
        def fixture(target, name):
            spec = {'approved': True, 'require_secret_sources': True, 'artifacts': [{
                'id': 'synthetic', 'sealed': True, 'kind': 'sealed_file', 'source': 'input.json',
                'target': target, 'anchor': {'path': source.name, 'sha256': digest},
                'files': [{'path': source.name, 'bytes': size, 'sha256': digest}]}]}
            manifest = cls.fixture / (name + '.json'); manifest.write_bytes(c.encoded(spec))
            result = pack.pack(manifest, c.sha(manifest.read_bytes()), cls.fixture,
                               cls.fixture / name, [cls.key])
            restore.restore(cls.fixture/name/'payload/INDEX.json', result['index_sha256'],
                            cls.fixture/(name+'-restored'), [cls.key])
            return result['index_sha256']
        cls.index_sha = fixture('synthetic/input.json', 'bundle')
        cls.duplicate_sha = fixture(a.CONTROL_TARGET, 'duplicate')
        cls.control_bytes = a.control_original(ORIGINAL)

    @classmethod
    def tearDownClass(cls):
        cls.context.cleanup()

    def setUp(self):
        self.context = tempfile.TemporaryDirectory(prefix='case-', dir=self.fixture)
        self.base = Path(self.context.name)
        shutil.copytree(self.fixture/'bundle', self.base/'bundle')
        shutil.copytree(self.fixture/'bundle-restored', self.base/'restored')
        self.control = self.base/a.CONTROL_NAME; self.control.write_bytes(self.control_bytes)
        self.output = self.base/'assembled'

    def tearDown(self):
        self.context.cleanup()

    def run_assembly(self, output=None, control=None, index_sha=None):
        return a.assemble(self.base/'bundle/payload/INDEX.json', index_sha or self.index_sha,
                          self.base/'restored', control or self.control, output or self.output, [self.key])

    def reject(self, function=None):
        with self.assertRaises(Exception):
            (function or self.run_assembly)()
        self.assertFalse((self.output/'COMPLETE.json').exists())

    def test_exact_restore_and_source_unchanged(self):
        before = c.inventory(self.base/'restored')
        result = self.run_assembly()
        self.assertEqual((self.output/'payload'/a.CONTROL_TARGET).read_bytes(), self.control_bytes)
        self.assertEqual((self.output/'payload/synthetic/input.json').read_bytes(), b'{"value":1}\n')
        self.assertEqual(result['file_count'], 2)
        self.assertFalse(result['strict_scanner_all_originals_passed'])
        self.assertEqual(c.inventory(self.base/'restored'), before)
        c.verify_completion(self.output, result['binding'])

    def test_existing_empty_destination(self):
        self.output.mkdir(); self.reject()

    def test_existing_populated_destination(self):
        self.output.mkdir(); (self.output/'kept').write_text('untouched')
        self.reject(); self.assertEqual((self.output/'kept').read_text(), 'untouched')

    def test_output_symlink(self):
        before = c.inventory(self.base/'restored')
        self.output.symlink_to(self.base/'restored', target_is_directory=True)
        with self.assertRaises(Exception):
            self.run_assembly()
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(c.inventory(self.base/'restored'), before)

    def test_parent_symlink(self):
        (self.base/'linked').symlink_to(self.base/'restored', target_is_directory=True)
        self.reject(lambda: self.run_assembly(output=self.base/'linked/new'))

    def test_output_inside_input(self):
        self.reject(lambda: self.run_assembly(output=self.base/'restored/new'))

    def test_control_symlink(self):
        self.control.unlink(); self.control.symlink_to(ORIGINAL); self.reject()

    def test_control_wrong_name(self):
        alternate = self.base/'other.json'; alternate.write_bytes(self.control_bytes)
        self.reject(lambda: self.run_assembly(control=alternate))

    def test_control_changed_bytes(self):
        self.control.write_bytes(self.control_bytes.replace(b'2533615', b'2533616', 1)); self.reject()

    def test_control_changed_whitespace(self):
        self.control.write_bytes(self.control_bytes[:-1]); self.reject()

    def test_control_missing(self):
        self.control.unlink(); self.reject()

    def test_known_marker_not_exempted(self):
        marker = 'Explicit ROOT message'
        self.reject(lambda: a.control_original(self.control, [(marker.encode(), marker)]))

    def test_cross_field_marker_not_exempted(self):
        value = c.strict_json(self.control_bytes)
        marker = ''.join(list(value)[:2])
        self.assertNotIn(marker.encode(), self.control_bytes)
        self.reject(lambda: a.control_original(self.control, [(marker.encode(), marker)]))

    def test_more_metadata_findings_rejected(self):
        value = c.strict_json(self.control_bytes); value['password'] = 'synthetic-blocked-value'
        self.control.write_bytes(c.encoded(value)); self.reject()

    def test_high_confidence_pattern_rejected(self):
        value = c.strict_json(self.control_bytes); value['note'] = 'ghp_' + 'x'*32
        self.control.write_bytes(c.encoded(value)); self.reject()

    def test_duplicate_json_key_rejected(self):
        self.control.write_bytes(b'{"x":1,"x":2,"authorization":'+json.dumps(a.CONTROL_PROSE).encode()+b'}')
        self.reject()

    def test_restored_missing(self):
        (self.base/'restored/payload/synthetic/input.json').unlink(); self.reject()

    def test_restored_extra(self):
        (self.base/'restored/payload/extra.json').write_text('{}'); self.reject()

    def test_restored_tampered(self):
        (self.base/'restored/payload/synthetic/input.json').write_text('{"value":2}\n'); self.reject()

    def test_restored_payload_symlink(self):
        path = self.base/'restored/payload/synthetic/input.json'; path.unlink(); path.symlink_to(self.fixture/'input.json')
        self.reject()

    def test_restored_completion_missing(self):
        (self.base/'restored/COMPLETE.json').unlink(); self.reject()

    def test_restored_completion_truncated(self):
        (self.base/'restored/COMPLETE.json').write_text('{'); self.reject()

    def test_restored_completion_extra_field(self):
        path = self.base/'restored/COMPLETE.json'; value = c.strict_json(path.read_bytes()); value['extra'] = True
        path.write_bytes(c.encoded(value)); self.reject()

    def test_bundle_extra_file(self):
        (self.base/'bundle/payload/extra.json').write_text('{}'); self.reject()

    def test_bundle_truncated_archive(self):
        path = self.base/'bundle/payload/shards/part-000001.tar.gz'; path.write_bytes(path.read_bytes()[:-3]); self.reject()

    def test_wrong_external_index(self):
        self.reject(lambda: self.run_assembly(index_sha='0'*64))

    def test_duplicate_control_in_shards(self):
        self.reject(lambda: a.assemble(self.fixture/'duplicate/payload/INDEX.json', self.duplicate_sha,
                                      self.fixture/'duplicate-restored', self.control, self.output))

    def test_concurrent_destination_one_winner(self):
        def attempt(_number):
            try:
                return self.run_assembly()['passed']
            except Exception:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(attempt, [0, 1]))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual((self.output/'payload'/a.CONTROL_TARGET).read_bytes(), self.control_bytes)


if __name__ == '__main__':
    unittest.main(verbosity=2)
