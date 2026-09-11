"""Small synthetic metadata fixtures; no raw/archive/network access."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import build_archive_index as subject


def fixture():
    sha = 'a' * 64
    models = []
    for name in sorted(subject.OLD_MODELS):
        models.append({'model': name, 'counts': dict(original_files=1, original_bytes=2, tar_shards=1, compressed_bytes=1),
                       'navigation': {'report': subject.FOUR_URL + '/README.zh.md'},
                       'raw_entry': {'url': subject.FOUR_URL + '/ARCHIVE_INDEX.json'}})
    four = {'schema': 'four-model.archive-navigation.v1', 'models': models,
            'tar_payload_totals': dict(original_files=4, original_bytes=8, tar_shards=4, compressed_bytes=4)}
    packages, files, out, verification = [], [], [], []
    for name in subject.PACKAGES:
        archive = {'path': name + '/part-000001.tar.gz', 'bytes': 1, 'sha256': sha}
        manifest = {'path': name + '/manifest.json', 'bytes': 3, 'sha256': sha}
        packages.append({'id': name, 'manifest': manifest, 'archives': [archive], 'compressed_bytes': 1,
                         'file_count': 1, 'original_bytes': 2, 'public_scan_passed': False})
        files.append({'path': 'studies/' + name + '/example.json', 'archive': archive['path'],
                      'package': name, 'bytes': 2, 'sha256': sha})
        out.extend([archive, manifest])
        verification.append({'package': name, 'verification': {'passed': True, 'public_scan_declaration': False,
                                                               'restored_files': 0, 'files': 1, 'archives': 1, 'original_bytes': 2}})
    api = {'schema': 'expgym.api-full-archive-index.v1', 'publication': 'local-only; no public clearance or upload',
           'packages': packages, 'files': files, 'browse_copies': [], 'external_immutable_inputs': []}
    outer = {'files': out, 'self_excluded': 'OUTER_FILES.json'}
    spec = {'schema': 'expgym.api-archive-spec.v1', 'packages': [{'id': name} for name in subject.PACKAGES]}
    return four, api, outer, verification, spec


class ArchiveMetadataTests(unittest.TestCase):
    def test_valid_fixture(self):
        files, out = subject.validate_metadata(*fixture())
        self.assertEqual((len(files), len(out)), (3, 6))

    def test_changed_input_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'small.json'
            raw = b'{"safe": true}\n'
            path.write_bytes(raw)
            identity = (len(raw), hashlib.sha256(raw).hexdigest())
            self.assertEqual(subject.read_bound(path, identity), {'safe': True})
            path.write_bytes(b'{"safe":false}\n')
            with self.assertRaisesRegex(ValueError, 'input_identity_mismatch'):
                subject.read_bound(path, identity)

    def test_bad_count(self):
        data = fixture()
        data[1]['packages'][0]['file_count'] += 1
        with self.assertRaisesRegex(ValueError, 'member_count_mismatch'):
            subject.validate_metadata(*data)

    def test_duplicate_member(self):
        data = fixture()
        data[1]['files'].append(copy.deepcopy(data[1]['files'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate_member_path'):
            subject.validate_metadata(*data)

    def test_duplicate_old_model(self):
        data = fixture()
        data[0]['models'][1] = copy.deepcopy(data[0]['models'][0])
        with self.assertRaisesRegex(ValueError, 'old_model_set_or_duplicate'):
            subject.validate_metadata(*data)

    def test_moving_public_url(self):
        data = fixture()
        data[0]['models'][0]['navigation']['report'] = 'https://github.com/tiannuo-yang/LLM_ExpGym/blob/main/report.md'
        with self.assertRaisesRegex(ValueError, 'nonimmutable_url'):
            subject.validate_metadata(*data)

    def test_no_false_api_public_clearance(self):
        data = fixture()
        data[1]['packages'][0]['public_scan_passed'] = True
        with self.assertRaisesRegex(ValueError, 'api_public_scan_status_changed'):
            subject.validate_metadata(*data)

    def test_bad_member_shard_mapping(self):
        data = fixture()
        data[1]['files'][0]['archive'] = 'claude/part-000001.tar.gz'
        with self.assertRaisesRegex(ValueError, 'member_package_mismatch'):
            subject.validate_metadata(*data)

    def test_browse_mismatch(self):
        data = fixture()
        data[1]['browse_copies'] = [{'path': 'browse/example.json', 'source_member': data[1]['files'][0]['path'],
                                    'bytes': 2, 'sha256': 'b' * 64}]
        with self.assertRaisesRegex(ValueError, 'browse_source_mismatch'):
            subject.validate_metadata(*data)

    def test_preserve_local_only_restore_evidence(self):
        data = fixture()
        data[3][0]['verification']['restored_files'] = 1
        with self.assertRaisesRegex(ValueError, 'verification_scope_changed'):
            subject.validate_metadata(*data)


if __name__ == '__main__':
    unittest.main()
