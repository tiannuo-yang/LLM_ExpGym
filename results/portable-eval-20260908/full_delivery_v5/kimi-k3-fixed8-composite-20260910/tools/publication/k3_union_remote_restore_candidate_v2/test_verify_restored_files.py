"""CPU-only fake K3 union; no original experimental or restored files are read."""
import argparse
import ast
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('k3_union_fake_verifier', HERE / 'verify_restored_files.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

OLD_PREFIX = 'kimi-k3-original-node-failure-20260909/payload/collection'
NEW_RAW = 'recovery-raw-000001'
NEW_CONTROLS = 'recovery-controls-000001'
OLD_BIDS = ['batch-%06d' % i for i in range(1, 34)] + ['controls']
ALL_BIDS = OLD_BIDS + [NEW_RAW, NEW_CONTROLS]


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(m.encoded(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Fake:
    def __init__(self, root):
        self.root, self.release, self.output = root, root/'release', root/'restored'
        self.collection_path = self.release/'INDEX.kimi-k3-composite-v1.json'
        self.bids = list(ALL_BIDS)
        self.counts = {bid: 1 for bid in self.bids if bid not in ('controls', NEW_CONTROLS)}
        self.bindings = [patch.object(m, 'TOTALS', (36, 36, 36)),
                         patch.object(m, 'RAW_COUNTS', self.counts),
                         patch.object(m, 'RAW_TOTALS', (34, 34)),
                         patch.object(m, 'CONTROL_TOTALS', {'controls': (1, 1), NEW_CONTROLS: (1, 1)})]
        for binding in self.bindings:
            binding.start()
        rows, completed, navigation = [], [], []
        for number, bid in enumerate(self.bids):
            original = 'workspace/f%03d.bin' % number
            payload = self.output/bid/'payload'/original
            payload.parent.mkdir(parents=True); payload.write_bytes(b'x')
            item = dict(path=original, bytes=1, sha256=hashlib.sha256(b'x').hexdigest())
            page = dict(files=[item])
            prefix = OLD_PREFIX if bid in OLD_BIDS else 'synthetic-recovery/payload/collection'
            index_name = prefix + '/' + bid + '/payload/INDEX.json'
            index_dir = (self.collection_path.parent/index_name).parent
            page_path = index_dir/'indexes/part-000001.json'
            page_sha = put(page_path, page)
            index = dict(file_count=1, original_bytes=1, shards=[dict(index='indexes/part-000001.json',
                index_sha256=page_sha, index_bytes=page_path.stat().st_size, file_count=1)])
            index_sha = put(index_dir/'INDEX.json', index)
            put(self.output/'metadata'/bid/'INDEX.json', index)
            put(self.output/'metadata'/bid/'indexes/part-000001.json', page)
            categories = m.CONTROL_CATEGORIES if bid in ('controls', NEW_CONTROLS) else m.RAW_CATEGORIES
            row = dict(bundle_id=bid, category=categories[bid], index=index_name,
                       sha256=index_sha, file_count=1, original_bytes=1)
            rows.append(row)
            marker = dict(schema='completed-directory-v1', complete=True, payload='payload',
                binding=dict(kind='restored-originals', input_sha256=index_sha, single_archive=False),
                file_count=1, bytes=1, inventory_sha256=hashlib.sha256(m.encoded(item)).hexdigest())
            completed.append(dict(bundle_id=bid, completion_sha256=put(self.output/bid/'COMPLETE.json', marker)))
            navigation.append({**row, 'restored_payload':bid+'/payload', 'copied_member_index':'metadata/'+bid+'/INDEX.json'})
        self.collection = dict(schema='whole-file-collection-v1', bundle_count=36, file_count=36,
                               original_bytes=36, bundles=rows)
        collection_sha = put(self.collection_path, self.collection)
        put(self.output/'COLLECTION_INDEX.json', self.collection)
        ownership = dict(schema='collection-path-ownership-v1', bundles=navigation,
            lookup='Read copied_member_index then its indexes/*.json; row.path belongs under restored_payload. Copied metadata is not a standalone archive bundle.')
        ownership_sha = put(self.output/'OWNERSHIP_INDEX.json', ownership)
        complete = dict(schema='whole-file-collection-complete-v1', complete=True, input_sha256=collection_sha,
            bundle_count=36, file_count=36, original_bytes=36, bundles=completed, ownership_index_sha256=ownership_sha,
            known_secret_sources_checked=0, modes_timestamps_ownership_preserved=False,
            publication_performed=False, remote_restore_performed=False)
        put(self.output/'COLLECTION_COMPLETE.json', complete)
        cli_path, proof_path = root/'CLI_EXIT.json', root/'ROOT_FAKE_PROOF.json'
        self.exit_record = dict(actual_exit_code=0, collection_index_sha256=collection_sha, remote_commit='a'*40)
        exit_sha = put(cli_path, self.exit_record)
        proof_sha = put(proof_path, dict(synthetic_only=True, note='not an actual Git proof'))
        self.args = argparse.Namespace(release_root=self.release, restored_root=self.output,
            collection_sha256=collection_sha, remote_commit='a'*40, root_remote_proof=proof_path,
            root_remote_proof_sha256=proof_sha, cli_exit=cli_path, cli_exit_sha256=exit_sha,
            output_receipt=root/'POST_RESTORE_VERIFICATION.json')

    def close(self):
        for binding in reversed(self.bindings):
            binding.stop()

    def run(self):
        with contextlib.redirect_stdout(io.StringIO()):
            m.main(self.args)

    def row(self, bid):
        return next(row for row in self.collection['bundles'] if row['bundle_id'] == bid)

    def bind_collection_change(self, copied=False):
        h = put(self.collection_path, self.collection)
        self.args.collection_sha256 = h
        self.exit_record['collection_index_sha256'] = h
        self.args.cli_exit_sha256 = put(self.args.cli_exit, self.exit_record)
        if copied:
            put(self.output/'COLLECTION_INDEX.json', self.collection)


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic_', dir=HERE)
        self.addCleanup(self.temp.cleanup)

    def fake(self):
        f = Fake(Path(self.temp.name)); self.addCleanup(f.close); return f

    def reject(self, f, message):
        with self.assertRaisesRegex(RuntimeError, message):
            f.run()
        self.assertFalse(f.args.output_receipt.exists())

    def test_fixed_production_scope_not_cli_configurable(self):
        self.assertEqual(m.TOTALS, (36, 66643, 1751137861))
        self.assertEqual(m.RAW_TOTALS, (65260, 1303033772))
        self.assertEqual(m.CONTROL_TOTALS, {'controls': (917, 253018660), NEW_CONTROLS: (466, 195085429)})
        self.assertEqual(set(m.RAW_COUNTS), set(OLD_BIDS[:-1]) | {NEW_RAW})
        self.assertEqual(sum(m.RAW_COUNTS.values()), 65260)
        self.assertEqual(m.RAW_COUNTS[NEW_RAW], 1072)
        self.assertEqual(set(m.RAW_CATEGORIES), set(m.RAW_COUNTS))
        self.assertEqual(set(m.CONTROL_CATEGORIES), {'controls', NEW_CONTROLS})
        with patch('sys.argv', ['verify_restored_files.py', '--file-count', '1']), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                m.cli()
        self.assertEqual(error.exception.code, 2)

    def test_full_fake_path_byte_sha_and_originals_unchanged(self):
        f=self.fake(); before={str(p):p.read_bytes() for root in (f.release,f.output) for p in root.rglob('*') if p.is_file()}
        f.run(); result=json.loads(f.args.output_receipt.read_bytes())
        self.assertTrue(result['passed'])
        self.assertEqual((result['bundle_count'],result['file_count'],result['original_bytes']), (36,36,36))
        self.assertEqual(len(result['bundles']),36)
        self.assertEqual(before,{p:Path(p).read_bytes() for p in before})
        self.assertTrue(all(f.row(bid)['index'].startswith(OLD_PREFIX + '/') for bid in OLD_BIDS))

    def test_unpinned_collection_rejected(self):
        f=self.fake(); f.args.collection_sha256='b'*64; self.reject(f,'cli_not_success')

    def test_root_proof_pin_not_merely_copied(self):
        f=self.fake(); f.args.root_remote_proof_sha256='b'*64; self.reject(f,'metadata_sha')

    def test_cli_exit_pin_and_exact_zero(self):
        f=self.fake(); f.args.cli_exit_sha256='b'*64; self.reject(f,'metadata_sha')
        f.exit_record['actual_exit_code']=False; f.args.cli_exit_sha256=put(f.args.cli_exit,f.exit_record)
        self.reject(f,'cli_not_success')

    def test_remote_commit_mismatch(self):
        f=self.fake(); f.args.remote_commit='b'*40; self.reject(f,'cli_not_success')

    def test_wrong_totals_rejected(self):
        f=self.fake(); f.collection['file_count']=35; f.bind_collection_change(); self.reject(f,'collection_totals')

    def test_duplicate_bundle_id_rejected(self):
        f=self.fake(); f.collection['bundles'][1]['bundle_id']=f.collection['bundles'][0]['bundle_id']
        f.bind_collection_change(); self.reject(f,'exact_K3_union_bundle_ids')

    def test_INCOMPLETE_never_success(self):
        f=self.fake(); put(f.output/'COLLECTION_INCOMPLETE.json',{'synthetic':True}); self.reject(f,'collection_incomplete')

    def test_tampered_original_bytes(self):
        f=self.fake(); next((f.output/f.bids[0]/'payload').rglob('*.bin')).write_bytes(b'y')
        self.reject(f,'restored_original_byte_sha')

    def test_extra_restored_file_rejected(self):
        f=self.fake(); (f.output/'unlisted.txt').write_bytes(b'x'); self.reject(f,'complete_or_exact_output_tree')

    def test_wrong_bundle_COMPLETE(self):
        f=self.fake(); put(f.output/f.bids[0]/'COMPLETE.json',{'complete':True}); self.reject(f,'bundle_complete')

    def test_symlink_and_receipt_overlap_rejected(self):
        f=self.fake(); alias=f.root/'alias'; alias.symlink_to(f.output,target_is_directory=True)
        f.args.restored_root=alias; self.reject(f,'absolute_nonalias_binding')
        f.args.restored_root=f.output; f.args.output_receipt=f.output/'new_receipt.json'; self.reject(f,'receipt_input_overlap')

    def test_original_helpers_and_member_loop_AST_identical(self):
        old_bytes=(HERE.parent/'glm_full_remote_restore_candidate_v1/verify_restored_files.py').read_bytes()
        self.assertEqual(hashlib.sha256(old_bytes).hexdigest(), '40e7b3af4e1d4b1e573e60ee192de19f6db9bd223515b32acbe0c8e345bc7d2b')
        old=ast.parse(old_bytes)
        new=ast.parse((HERE/'verify_restored_files.py').read_bytes())
        oldf={n.name:n for n in old.body if isinstance(n,ast.FunctionDef)}
        newf={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
        for name in ('need','encoded','signature','path_safe','digest','load','relative','tree'):
            self.assertEqual(ast.dump(oldf[name]),ast.dump(newf[name]))
        def member_loop(fn):
            return next(node for node in fn.body if isinstance(node, ast.For) and
                        any(isinstance(child, ast.Assign) and
                            any(isinstance(target, ast.Name) and target.id == 'source_index' for target in child.targets)
                            for child in ast.walk(node)))
        self.assertEqual(ast.dump(member_loop(oldf['main'])), ast.dump(member_loop(newf['main'])))

    def test_union_index_selected_with_old_default_present(self):
        f=self.fake()
        put(f.release/'payload/collection/INDEX.json', {'wrong_old_default': True})
        put(f.release/'INDEX.json', {'wrong_flat_default': True})
        f.run()
        result=json.loads(f.args.output_receipt.read_bytes())
        self.assertTrue(result['passed'])
        self.assertEqual(result['collection_index_sha256'], f.args.collection_sha256)

    def test_missing_union_never_falls_back(self):
        f=self.fake()
        put(f.release/'payload/collection/INDEX.json', f.collection)
        f.collection_path.rename(f.release/'INDEX.json')
        with self.assertRaisesRegex(FileNotFoundError, 'INDEX.kimi-k3-composite-v1.json'):
            f.run()
        self.assertFalse(f.args.output_receipt.exists())

    def test_wrong_union_sha_never_uses_valid_old_default(self):
        f=self.fake()
        put(f.release/'payload/collection/INDEX.json', f.collection)
        put(f.release/'INDEX.json', f.collection)
        put(f.collection_path, {'wrong_union': True})
        self.reject(f, 'metadata_sha')

    def test_wrong_newraw_category_and_count_rejected(self):
        f=self.fake(); row=f.row(NEW_RAW); category=row['category']
        row['category']=m.CONTROL_CATEGORIES['controls']
        f.bind_collection_change(); self.reject(f, 'fixed_raw_scope')
        row['category']=category; row['file_count']=2
        f.bind_collection_change(); self.reject(f, 'fixed_raw_scope')

    def test_wrong_newcontrols_category_and_totals_rejected(self):
        f=self.fake(); row=f.row(NEW_CONTROLS); category=row['category']
        row['category']=m.RAW_CATEGORIES[NEW_RAW]
        f.bind_collection_change(); self.reject(f, 'public_controls_scope')
        row['category']=category; row['original_bytes']=2
        f.bind_collection_change(); self.reject(f, 'public_controls_scope')

    def test_missing_newcontrols_rejected(self):
        f=self.fake()
        f.collection['bundles']=[row for row in f.collection['bundles'] if row['bundle_id'] != NEW_CONTROLS]
        f.bind_collection_change(); self.reject(f, 'collection_shape')

    def test_old_new_original_owner_collision_rejected(self):
        f=self.fake(); row=f.row(NEW_RAW)
        source_index=f.release/row['index']
        index=json.loads(source_index.read_bytes()); shard=index['shards'][0]
        source_page=source_index.parent/shard['index']
        page=json.loads(source_page.read_bytes()); page['files'][0]['path']='workspace/f000.bin'
        shard['index_sha256']=put(source_page, page)
        shard['index_bytes']=source_page.stat().st_size
        put(f.output/'metadata'/NEW_RAW/shard['index'], page)
        row['sha256']=put(source_index, index)
        put(f.output/'metadata'/NEW_RAW/'INDEX.json', index)
        f.bind_collection_change(copied=True)
        self.reject(f, 'duplicate_original_path')


if __name__=='__main__':
    unittest.main()
