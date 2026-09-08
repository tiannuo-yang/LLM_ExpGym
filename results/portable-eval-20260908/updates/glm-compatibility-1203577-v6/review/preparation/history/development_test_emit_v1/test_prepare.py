"""Metadata-only synthetic tests; no real payload/key reads or pack execution."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('glm_prepare', Path(__file__).with_name('prepare.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='glm-metadata-fixture-')
        self.root = Path(self.temp.name)
        (self.root / 'closed').mkdir()
        (self.root / 'closed/empty.log').touch()
        (self.root / 'closed/raw.json').write_bytes(b'not-read-even-if-invalid-json')

    def tearDown(self):
        self.temp.cleanup()

    def rows(self):
        return p.metadata_rows(self.root, ['closed'], [])

    def test_payload_not_read(self):
        p.c.scanner()  # Load code before intercepting arbitrary data reads.
        with patch.object(p.c.scanner(), 'stable_read', side_effect=AssertionError('payload read')):
            rows = self.rows()
        self.assertEqual([r['path'] for r in rows], ['closed/empty.log', 'closed/raw.json'])
        self.assertEqual(rows[0]['bytes'], 0)
        self.assertNotIn('sha256', rows[1])

    def test_added_file_changes_set(self):
        old = self.rows()
        (self.root / 'closed/new.log').touch()
        self.assertNotEqual(old, self.rows())

    def test_missing_file_changes_set(self):
        old = self.rows()
        (self.root / 'closed/empty.log').unlink()
        self.assertNotEqual(old, self.rows())

    def test_changed_bytes_changes_stat(self):
        old = self.rows()
        (self.root / 'closed/raw.json').write_bytes(b'changed')
        self.assertNotEqual(old, self.rows())

    def test_duplicate_rejected(self):
        with self.assertRaises(p.c.DeliveryError):
            p.metadata_rows(self.root, ['closed'], ['closed/empty.log'])

    def test_absolute_rejected(self):
        with self.assertRaises(Exception):
            p.metadata_rows(self.root, [], ['/tmp/elsewhere'])

    def test_parent_rejected(self):
        with self.assertRaises(Exception):
            p.metadata_rows(self.root, [], ['closed/../outside'])

    def test_symlink_rejected(self):
        (self.root / 'closed/link').symlink_to('raw.json')
        with self.assertRaises(p.c.DeliveryError):
            self.rows()

    def test_private_directory_rejected(self):
        (self.root / 'closed/private').mkdir()
        with self.assertRaises(Exception):
            self.rows()

    def test_pins_and_tool_hashes_well_formed(self):
        for value in list(p.ROOT_PINS.values()) + list(p.TOOLS.values()):
            self.assertEqual(p.c.checksum(value), value)

    def test_no_live_controller_or_future_k3(self):
        files = p.fixed_files()
        self.assertNotIn(p.RUN + '/events.jsonl', files)
        self.assertNotIn(p.KEY, files)
        self.assertEqual(sum(name.startswith(p.SERVING + '/') for name in files), 80)
        self.assertTrue(all('kimi' not in name.lower() and 'k3_' not in name.lower() for name in files))

    def test_invalid_go_cannot_read_key(self):
        scope = {'files': []}
        with patch.object(p, 'verify_tools'), patch.object(p.c, 'load_json', side_effect=[(scope, b''), ({}, b'')]), \
                patch.object(p.c, 'stream_hash', return_value=(0, '1' * 64)), \
                patch.object(p.c.scanner(), 'load_secrets', side_effect=AssertionError('key read')):
            with self.assertRaises(p.c.DeliveryError):
                p.seal(Path('scope'), '2' * 64, Path('go'), '3' * 64, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())


    def test_key_parent_symlink_rejected_before_secret_reader(self):
        actual = self.root / 'synthetic_private'
        actual.mkdir()
        (actual / 'router_api_key').touch()  # Empty fixture; never read.
        (self.root / 'key_parent').symlink_to(actual, target_is_directory=True)
        fixture_key = 'key_parent/router_api_key'
        scope_sha, prepare_sha = '2' * 64, '1' * 64
        scope = {'files': [], 'directories': p.DIRECTORIES, 'single_files': p.fixed_files(),
                 'external_root_pins': p.ROOT_PINS, 'tools': p.TOOLS}
        go = {'schema': 'glm-local-scan-go-v1', 'local_scan_authorized': True,
              'publication_authorized': False, 'scope_sha256': scope_sha,
              'prepare_sha256': prepare_sha, 'workspace': str(self.root),
              'secret_source_path': str(self.root / fixture_key)}
        scanner = p.c.scanner()
        with patch.object(p, 'WORKSPACE', self.root), patch.object(p, 'KEY', fixture_key), \
                patch.object(p, 'verify_tools'), patch.object(p, 'metadata_rows', return_value=[]), \
                patch.object(p.c, 'load_json', side_effect=[(scope, b''), (go, b'')]), \
                patch.object(p.c, 'stream_hash', return_value=(0, prepare_sha)), \
                patch.object(scanner, 'load_secrets', side_effect=AssertionError('secret reader called')) as reader:
            with self.assertRaisesRegex(p.c.DeliveryError, '^symlink_path
    unittest.main(verbosity=2)
):
                p.seal(Path('scope'), scope_sha, Path('go'), '3' * 64, self.root / 'out')
            reader.assert_not_called()
        self.assertFalse((self.root / 'out').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
