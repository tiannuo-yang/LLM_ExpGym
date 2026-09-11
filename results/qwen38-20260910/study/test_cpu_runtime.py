"""Focused CPU launcher checks; all temporary state belongs to this study."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import cpu_runtime

from cpu_runtime import DATA_ROOT, RUN_ROOT, SOURCE_REPO

STUDY = RUN_ROOT / 'study'
ENV_CODE = ('import json,os,sys; print(json.dumps({"cwd":os.getcwd(),'
            '"version":list(sys.version_info[:2]),"config":os.environ["XDG_CONFIG_HOME"],'
            '"cache":os.environ["XDG_CACHE_HOME"],"socket":os.environ["TMPDIR"],'
            '"data":os.environ["XDG_DATA_HOME"],"repo":os.environ["EXPGYM_SOURCE_REPO"],'
            '"noauth_placeholder":os.environ["OPENAI_API_KEY"]=="EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907",'
            '"run_id":os.environ.get("EXPGYM_RUN_ID"),"argv":sys.argv[1:]}))')


class CpuRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='cpu_runtime_test_', dir=str(STUDY))
        cls.root = Path(cls.temporary.name)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def invoke(self, kind, arguments, dump=None, **extra):
        env = dict(os.environ)
        env.pop('EXPGYM_API_DUMP_DIR', None)
        env.pop('EXPGYM_RUN_ID', None)
        if dump is not None:
            env['EXPGYM_API_DUMP_DIR'] = str(dump)
        env.update(extra)
        return subprocess.run([str(STUDY / ('python_' + kind))] + arguments,
                              env=env, cwd='/', text=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=90)

    def test_identity_probes_without_state(self):
        for kind, version in (('main', '3.11.15'), ('hpo', '3.7.12')):
            process = self.invoke(kind, ['--expgym-runtime-identity'])
            self.assertEqual(process.returncode, 0, process.stderr)
            row = json.loads(process.stdout)
            self.assertEqual(row['version'], version)
            self.assertEqual(row['cwd'], str(SOURCE_REPO))
            self.assertEqual(row['data_root'], str(DATA_ROOT))
        self.assertFalse((DATA_ROOT / '__runtime_requires_job_dump__').exists())

    def test_help_and_versions_without_dump(self):
        for kind in ('main', 'hpo'):
            for arguments in (['--help'], ['--version']):
                process = self.invoke(kind, arguments)
                self.assertEqual(process.returncode, 0, process.stderr)
            for script in ('run_study_queue.py', 'run_paper_sweep.py', 'run_poolact.py'):
                process = self.invoke(kind, ['-B', str(SOURCE_REPO / 'scripts' / script), '--help'])
                self.assertEqual(process.returncode, 0, process.stderr)

    def test_hpo_execution_requires_absolute_study_dump(self):
        for dump in (None, 'relative/api_dump', '/tmp/other-study/api_dump'):
            process = self.invoke('hpo', ['-c', 'print("must not run")'], dump)
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn('must not run', process.stdout)

    def test_help_never_initializes_inherited_dump_state(self):
        parent = self.root / 'help_only'
        for kind in ('main', 'hpo'):
            for dump in ('invalid-relative/api_dump', parent / 'api_dump'):
                process = self.invoke(kind, ['--help'], dump)
                self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse(parent.exists())

    def test_help_does_not_bypass_arbitrary_code_namespace(self):
        for prefix in ([], ['-S'], ['-W', 'ignore'], ['-X', 'dev']):
            process = self.invoke('hpo', prefix + ['-c', 'print("must not run")', '--help'])
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn('must not run', process.stdout)

    def test_namespaces_argv_and_stable_config(self):
        rows = []
        for name in ('a', 'b'):
            process = self.invoke('hpo', ['-B', '-c', ENV_CODE, 'argument with spaces'],
                                  self.root / name / 'api_dump', EXPGYM_RUN_ID=name)
            self.assertEqual(process.returncode, 0, process.stderr)
            row = json.loads(process.stdout)
            self.assertEqual(row['cwd'], str(SOURCE_REPO))
            self.assertEqual(row['repo'], str(SOURCE_REPO))
            self.assertEqual(row['data'], str(DATA_ROOT / 'hpo_tuning/hpobench_data'))
            self.assertEqual(row['argv'], ['argument with spaces'])
            self.assertEqual(row['run_id'], name)
            self.assertTrue(row['noauth_placeholder'])
            rows.append(row)
        for field in ('config', 'cache', 'socket'):
            self.assertNotEqual(rows[0][field], rows[1][field])
        config = Path(rows[0]['config']) / '.hpobenchrc'
        before = config.read_bytes(), config.stat().st_mtime_ns
        process = self.invoke('hpo', ['-c', ENV_CODE], self.root / 'a/api_dump')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(before, (config.read_bytes(), config.stat().st_mtime_ns))

    def test_incompatible_configuration_is_not_overwritten(self):
        dump = self.root / 'tampered/api_dump'
        process = self.invoke('hpo', ['-c', ENV_CODE], dump)
        self.assertEqual(process.returncode, 0, process.stderr)
        config = dump.parent / 'runtime/hpobench/config/.hpobenchrc'
        config.write_text('{"incorrect":"negative test fixture"}\n')
        before = config.read_bytes(), config.stat().st_mtime_ns
        process = self.invoke('hpo', ['-c', ENV_CODE], dump)
        self.assertNotEqual(process.returncode, 0)
        self.assertIn('refusing to overwrite', process.stderr)
        self.assertEqual(before, (config.read_bytes(), config.stat().st_mtime_ns))

    def test_symlink_namespace_rejected(self):
        target = self.root / 'real'
        target.mkdir()
        link = self.root / 'linked'
        link.symlink_to(target, target_is_directory=True)
        process = self.invoke('hpo', ['-c', ENV_CODE], link / 'api_dump')
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse((target / 'runtime').exists())

    def test_missing_or_modified_budget_oracle_refuses_fallback(self):
        fake_repo = self.root / 'fake_repo'
        fake_repo.mkdir()
        with mock.patch.object(cpu_runtime, 'SOURCE_REPO', fake_repo), \
                mock.patch.object(cpu_runtime.os, 'execv') as execute:
            with self.assertRaisesRegex(SystemExit, 'budget oracle'):
                cpu_runtime.main('main')
            bad_oracle = fake_repo / 'data/hpo_tuning/oracle3.json'
            bad_oracle.parent.mkdir(parents=True)
            bad_oracle.write_text('{}\n')
            with self.assertRaisesRegex(SystemExit, 'budget oracle'):
                cpu_runtime.main('main')
            execute.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
