import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from expgym.scheduling import QueueJob, run_queue, write_json
from scripts.run_study_queue import make_plan, queue_jobs

ROOT = Path(__file__).resolve().parents[1]

FAKE = """
import json, os, pathlib, sys, time
root, delay, code = pathlib.Path(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
root.mkdir()
start = time.time_ns()
time.sleep(delay)
(root / 'result.json').write_text(json.dumps({'start':start, 'end':time.time_ns(),
 'pid':os.getpid(), 'run_id':os.environ['EXPGYM_RUN_ID'],
 'dump':os.environ['EXPGYM_API_DUMP_DIR'], 'endpoint':os.getenv('EXPGYM_QUEUE_ENDPOINT'),
 'terminal_status':'normal_missing_final'}))
raise SystemExit(code)
"""


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def job(self, number, delay=.02, code=0, endpoints=()):
        job_id = 'job_%d' % number
        output = self.root / job_id
        return QueueJob(job_id, {'repeat': number, 'stage': number // 2},
                        [sys.executable, '-c', FAKE, str(output), str(delay), str(code)],
                        [sys.executable, '-c', 'raise SystemExit(0)'], output, ROOT,
                        {'EXPGYM_RUN_ID': job_id, 'EXPGYM_API_DUMP_DIR': str(output / 'dump')}, endpoints)

    def test_slow_first_stage_does_not_block_later_stage_and_bounded(self):
        jobs = [self.job(0, .8)] + [self.job(i, .03) for i in range(1, 8)]
        report = run_queue(jobs, state_dir=self.root / 'state', workers=2)
        self.assertTrue(report['passed'])
        self.assertEqual(report['max_active_workers'], 2)
        values = [json.loads((j.output_dir / 'result.json').read_text()) for j in jobs]
        self.assertLess(values[2]['start'], values[0]['end'])
        self.assertEqual(len({v['pid'] for v in values}), 8)
        self.assertEqual(len({v['run_id'] for v in values}), 8)
        self.assertEqual(len({v['dump'] for v in values}), 8)
        events = [json.loads(line) for line in (Path(report['session_dir']) / 'events.jsonl').read_text().splitlines()]
        self.assertEqual(len([x for x in events if x['event'] == 'queued']), 8)
        self.assertEqual(len([x for x in events if x['event'] == 'start']), 8)
        self.assertEqual(len([x for x in events if x['event'] == 'end']), 8)
        self.assertTrue(all(0 <= x['active'] <= 2 for x in events))

    def test_failure_stops_new_and_drains_keeps_partial(self):
        jobs = [self.job(0, .01, 3), self.job(1, .25), self.job(2)]
        report = run_queue(jobs, state_dir=self.root / 'state', workers=2)
        self.assertFalse(report['passed'])
        self.assertEqual(report['finished'], 2)
        self.assertEqual(report['unstarted'], ['job_2'])
        self.assertTrue((jobs[0].output_dir / 'result.json').exists())
        self.assertTrue((jobs[1].output_dir / 'result.json').exists())
        self.assertFalse(jobs[2].output_dir.exists())

    def test_normal_missing_final_is_not_failure(self):
        report = run_queue([self.job(i) for i in range(3)], state_dir=self.root / 'state', workers=2)
        self.assertTrue(report['passed'])
        self.assertEqual(report['finished'], 3)

    def test_resume_is_readonly_and_identity_bound(self):
        jobs = [self.job(0), self.job(1)]
        first = run_queue(jobs, state_dir=self.root / 'state', workers=2)
        before = [(j.output_dir / 'result.json').read_bytes() for j in jobs]
        second = run_queue(jobs, state_dir=self.root / 'state', workers=2, resume=True)
        self.assertTrue(first['passed'] and second['passed'])
        self.assertTrue(all(r['mode'] == 'verify_resume' for r in second['reports']))
        self.assertEqual(before, [(j.output_dir / 'result.json').read_bytes() for j in jobs])
        changed = QueueJob('job_0', {'repeat': 99}, jobs[0].command, jobs[0].verify_command,
                           jobs[0].output_dir, ROOT, jobs[0].environment)
        with self.assertRaisesRegex(ValueError, 'exact definition'):
            run_queue([changed, jobs[1]], state_dir=self.root / 'state', workers=2, resume=True)

    def test_resume_tamper_or_failed_attempt_never_resamples(self):
        job = self.job(0)
        run_queue([job], state_dir=self.root / 'state', workers=1)
        (job.output_dir / 'result.json').write_text('{}')
        result = run_queue([job], state_dir=self.root / 'state', workers=1, resume=True)
        self.assertFalse(result['passed'])
        self.assertEqual((job.output_dir / 'result.json').read_text(), '{}')
        failed = self.job(1, code=2)
        run_queue([failed], state_dir=self.root / 'failed', workers=1)
        result = run_queue([failed], state_dir=self.root / 'failed', workers=1, resume=True)
        self.assertFalse(result['passed'])
        self.assertIn('explicit recovery required', result['reports'][0]['error'])

    def test_ambiguous_output_and_duplicate_jobs_rejected(self):
        job = self.job(0)
        with self.assertRaises(ValueError):
            run_queue([job, job], state_dir=self.root / 'duplicate', workers=2)
        job.output_dir.mkdir()
        result = run_queue([job], state_dir=self.root / 'state', workers=1)
        self.assertFalse(result['passed'])
        nested = QueueJob('nested', {}, job.command, job.verify_command,
                          job.output_dir / 'nested', ROOT, {})
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            run_queue([job, nested], state_dir=self.root / 'nestedstate', workers=2)

    def test_stop_file_admission_only(self):
        stop = self.root / 'STOP'
        stop.touch()
        result = run_queue([self.job(0)], state_dir=self.root / 'state', workers=1, stop_file=stop)
        self.assertEqual(result['finished'], 0)
        self.assertEqual(result['unstarted'], ['job_0'])
        self.assertFalse(result['passed'])

    def test_free_replica_gets_next_job_without_waiting_slow_replica(self):
        endpoints = ['http://a:1/v1', 'http://b:2/v1']
        jobs = [self.job(0, .5, endpoints=endpoints)] + [self.job(i, .02, endpoints=endpoints) for i in range(1, 4)]
        report = run_queue(jobs, state_dir=self.root / 'state', workers=2)
        self.assertTrue(report['passed'])
        values = [json.loads((j.output_dir / 'result.json').read_text()) for j in jobs]
        self.assertEqual([v['endpoint'] for v in values], [endpoints[0], endpoints[1], endpoints[1], endpoints[1]])

    def matrix(self):
        return {'stages': [
            {'label':'slow-stage', 'runner':'expgym', 'args':[
                '--backend','fake','--models','fake','--scenarios','tuning',
                '--tuning-reps','2','--max-steps','2','--max-evals','1']},
            {'label':'later-stage', 'runner':'poolact', 'args':[
                '--backend','fake','--model','fake','--scenario','tuning',
                '--strategies','naive,cached,poolact','--agents','2','--repeats','2',
                '--max-steps','2','--max-evals','1']}]}

    def test_matrix_uses_existing_selectors_and_repeat_identity(self):
        plan = make_plan(self.matrix(), study_id='fake', output_root=self.root / 'run', default_python=sys.executable)
        self.assertEqual(len(plan['jobs']), 8)
        self.assertEqual(len({j['job_id'] for j in plan['jobs']}), 8)
        self.assertEqual(len({j['args']['prompt_cache_key'] for j in plan['jobs']}), 8)
        self.assertEqual(len({j['args']['output_dir'] for j in plan['jobs']}), 8)
        pools = [j for j in plan['jobs'] if j['runner'] == 'poolact']
        self.assertEqual([j['selection']['repeat_index'] for j in pools], [0,0,0,1,1,1])
        self.assertTrue(all(j['args']['repeats'] == 2 and j['args']['agents'] == 2 for j in pools))
        self.assertEqual(plan, make_plan(self.matrix(), study_id='fake', output_root=self.root / 'run', default_python=sys.executable))
        duplicate = self.matrix()
        duplicate['stages'].append({**duplicate['stages'][0], 'label':'duplicate'})
        with self.assertRaisesRegex(ValueError, 'duplicate logical'):
            make_plan(duplicate, study_id='fake', output_root=self.root, default_python=sys.executable)

    def test_overlapping_stage_selectors_cannot_duplicate_same_job(self):
        matrix = {'stages': [
            {'label':'wide', 'runner':'expgym', 'args':[
                '--backend','fake','--models','fake','--scenarios','tuning,restricted_search']},
            {'label':'overlap', 'runner':'expgym', 'args':[
                '--backend','fake','--models','fake','--scenarios','tuning']}]}
        with self.assertRaisesRegex(ValueError, 'duplicate logical'):
            make_plan(matrix, study_id='overlap', output_root=self.root, default_python=sys.executable)

    def test_overlapping_pool_repeat_counts_cannot_duplicate_same_pool(self):
        base = ['--backend','fake','--model','opaque','--scenario','tuning',
                '--agents','2','--strategies','poolact']
        matrix = {'stages': [
            {'label':'r2', 'runner':'poolact', 'args':base + ['--repeats','2']},
            {'label':'r3', 'runner':'poolact', 'args':base + ['--repeats','3']}]}
        with self.assertRaisesRegex(ValueError, 'duplicate logical'):
            make_plan(matrix, study_id='overlap', output_root=self.root, default_python=sys.executable)
        individual = []
        for stage in matrix['stages']:
            individual.append(make_plan({'stages':[stage]}, study_id='same-study',
                output_root=self.root, default_python=sys.executable))
        self.assertEqual([j['job_id'] for j in individual[0]['jobs']],
                         [j['job_id'] for j in individual[1]['jobs'][:2]])
        self.assertTrue(all(j['args']['repeats'] == 2 for j in individual[0]['jobs']))
        self.assertTrue(all(j['args']['repeats'] == 3 for j in individual[1]['jobs']))
        self.assertEqual([j['selection']['repeat_index'] for j in individual[1]['jobs']], [0,1,2])

    def test_formal_selectors_preserve_audit_orders_and_hpo_repeats_without_data(self):
        matrix = {'stages': [{'label':'formal', 'runner':'expgym', 'args':[
            '--backend','fake','--models','fake',
            '--scenarios','tuning,restricted_search,evidence_audit',
            '--tuning-tasks','all-hpobench','--tuning-reps','3',
            '--search-indices','0:73','--search-reps','1',
            '--audit-indices','0:13','--audit-reps','3',
            '--cost-regimes','cost_free,cost_moderate,cost_tight']}]}
        plan = make_plan(matrix, study_id='formal', output_root=self.root, default_python=sys.executable)
        self.assertEqual(len(plan['jobs']), 417)
        audits = [j['selection'] for j in plan['jobs'] if j['selection']['scenario'] == 'evidence_audit']
        first = [j for j in audits if j['question_index'] == 0 and j['cost_regime'] == 'cost_free']
        self.assertEqual(len(first), 3)
        self.assertEqual([j['rep'] for j in first], [0,1,2])
        self.assertEqual(len({json.dumps(j['hypothesis_order']) for j in first}), 3)

    def test_real_runner_fake_subprocess_execution_and_verified_resume(self):
        plan = make_plan(self.matrix(), study_id='fake-integration', output_root=self.root / 'run', default_python=sys.executable)
        plan_path = self.root / 'plan.json'
        write_json(plan_path, plan)
        checksum = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        jobs = queue_jobs(plan, plan_path, checksum)
        result = run_queue(jobs, state_dir=self.root / 'state', workers=3)
        failures = [r for r in result['reports'] if not r['passed']]
        if failures:
            for failure in failures:
                print((Path(result['session_dir']) / (failure['job_id'] + '.stderr.log')).read_text())
        self.assertTrue(result['passed'], failures)
        self.assertEqual(result['finished'], 8)
        repeated = next(j for j in plan['jobs'] if j['runner'] == 'poolact' and j['selection']['repeat_index'] == 1)
        saved = json.loads((Path(repeated['args']['output_dir']) / 'repeat_1' / repeated['selection']['strategy'] / 'result.json').read_text())
        self.assertEqual(saved['config']['repeat_index'], 1)
        self.assertEqual(saved['config']['base_seed'], 1206)
        self.assertEqual(saved['config']['agent_seeds'], [1208,1209])
        rerun = run_queue(jobs, state_dir=self.root / 'state', workers=3, resume=True)
        self.assertTrue(rerun['passed'], [r for r in rerun['reports'] if not r['passed']])
        self.assertTrue(all(r['mode'] == 'verify_resume' for r in rerun['reports']))

    def test_secret_literals_forbidden_without_reading_files(self):
        matrix = self.matrix()
        matrix['stages'][0]['args'] += ['--api-key','not-a-real-key']
        with self.assertRaisesRegex(ValueError, 'forbidden'):
            make_plan(matrix, study_id='test', output_root=self.root, default_python=sys.executable)

    def test_cli_plan_and_run_read_serving_worker_default(self):
        matrix_path, plan_path = self.root / 'matrix.json', self.root / 'plan.json'
        config_path = self.root / 'serving.json'
        matrix = self.matrix()
        matrix['stages'] = matrix['stages'][:1]
        write_json(matrix_path, matrix)
        write_json(config_path, {'dispatch': {'max_workers': 2}})
        command = [sys.executable, '-B', str(ROOT / 'scripts/run_study_queue.py')]
        created = subprocess.run(command + ['plan', '--matrix', str(matrix_path),
            '--study-id', 'cli-fake', '--output-root', str(self.root / 'run'),
            '--output', str(plan_path)], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        receipt = json.loads(created.stdout)
        self.assertEqual(receipt['jobs'], 2)
        executed = subprocess.run(command + ['run', '--plan', str(plan_path),
            '--sha256', receipt['sha256'], '--serving-config', str(config_path)],
            cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(executed.returncode, 0, executed.stderr + executed.stdout)
        report = json.loads(executed.stdout)
        self.assertEqual(report['workers'], 2)
        self.assertEqual(report['finished'], 2)
        self.assertTrue(report['passed'])


if __name__ == '__main__':
    unittest.main()
