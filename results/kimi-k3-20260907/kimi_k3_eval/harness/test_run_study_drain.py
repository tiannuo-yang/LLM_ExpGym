"""Exercise real process signals only against isolated, non-API test children."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


HARNESS = Path(__file__).resolve().parent
DRIVER = r'''
import json, pathlib, signal, sys
sys.path.insert(0, sys.argv[1])
import run_study as study
root = pathlib.Path(sys.argv[2])
args = study.parse_args([
    '--stage', 'smoke', '--base-url', 'http://unused.invalid/v1',
    '--output-dir', str(root), '--workers', '2',
])
child = r"""
import json, os, pathlib, signal, sys, time
output, release = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
blocked = signal.pthread_sigmask(signal.SIG_BLOCK, set())
output.with_suffix('.started').write_text(str(os.getpid()))
while not release.exists():
    time.sleep(0.01)
output.write_text(json.dumps({'persisted': True, 'usr1_blocked': signal.SIGUSR1 in blocked}))
"""
jobs = []
for number in range(4):
    output = root / ('job_%d.json' % number)
    jobs.append({
        'id': 'job_%d' % number, 'system': 'expgym', 'agents': 1, 'paper_subset': False,
        'expected_outputs': [{'path': str(output)}], 'summary_path': None,
        'status_path': str(root / ('status_%d.json' % number)),
        'stdout_log': str(root / ('stdout_%d.log' % number)),
        'dump_dir': str(root / ('dumps_%d' % number)),
        'command': [sys.executable, '-u', '-c', child, str(output), str(root / 'release')],
    })
manifest = {'jobs': jobs, 'counts': study.count_jobs(jobs), 'progress_path': str(root / 'progress.json')}
signals = (signal.SIGINT, signal.SIGTERM, signal.SIGUSR1)
before = {number: signal.getsignal(number) for number in signals}
code = study.execute_study(args, manifest)
(root / 'driver_result.json').write_text(json.dumps({
    'exit_code': code,
    'handlers_restored': all(signal.getsignal(number) == before[number] for number in signals),
}))
raise SystemExit(code)
'''


class DrainTests(unittest.TestCase):
    def wait_for(self, condition, process, timeout=8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if condition():
                return
            if process.poll() is not None:
                self.fail("isolated harness exited before the expected state: %s" % process.returncode)
            time.sleep(0.01)
        self.fail("isolated harness did not reach the expected state")

    def launch(self, root):
        log = (root / "driver.log").open("wb")
        process = subprocess.Popen([sys.executable, "-u", "-c", DRIVER, str(HARNESS), str(root)],
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self.addCleanup(log.close)

        def cleanup():
            if process.poll() is None:
                # This PID belongs to this test's Popen instance only.
                process.terminate()
                try:
                    process.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        self.addCleanup(cleanup)
        self.wait_for(lambda: (root / "job_0.started").exists() and (root / "job_1.started").exists(), process)
        return process

    def read_progress(self, root):
        return json.loads((root / "progress.json").read_text())

    def test_usr1_waits_for_inflight_persistence_and_keeps_pending_jobs(self):
        with tempfile.TemporaryDirectory(prefix="kimi-drain-test-") as directory:
            root = Path(directory)
            process = self.launch(root)
            process.send_signal(signal.SIGUSR1)
            self.wait_for(lambda: self.read_progress(root)["status"] == "draining", process)
            process.send_signal(signal.SIGUSR1)  # Repeated requests are idempotent.
            self.assertIsNone(process.poll())
            self.assertEqual(self.read_progress(root)["job_counts"]["pending"], 2)
            self.assertFalse((root / "job_2.started").exists())
            self.assertFalse((root / "job_3.started").exists())
            (root / "release").touch()
            self.assertEqual(process.wait(timeout=10), 75)
            progress = self.read_progress(root)
            self.assertEqual(progress["status"], "drained")
            self.assertEqual(progress["exit_code"], 75)
            self.assertTrue(progress["drain_requested"])
            self.assertFalse(progress["interruption_requested"])
            self.assertFalse(progress["all_selected_jobs_complete"])
            self.assertEqual(progress["job_counts"], {
                "pending": 2, "running": 0, "completed": 2, "failed": 0, "interrupted": 0,
            })
            for number in (0, 1):
                self.assertEqual(json.loads((root / ("job_%d.json" % number)).read_text()),
                                 {"persisted": True, "usr1_blocked": True})
                receipt = json.loads((root / ("status_%d.json" % number)).read_text())
                self.assertEqual((receipt["status"], receipt["returncode"]), ("completed", 0))
            for number in (2, 3):
                self.assertFalse((root / ("job_%d.started" % number)).exists())
                self.assertFalse((root / ("status_%d.json" % number)).exists())
            self.assertTrue(json.loads((root / "driver_result.json").read_text())["handlers_restored"])

    def test_term_after_usr1_retains_existing_interruption_semantics(self):
        with tempfile.TemporaryDirectory(prefix="kimi-drain-term-test-") as directory:
            root = Path(directory)
            process = self.launch(root)
            process.send_signal(signal.SIGUSR1)
            self.wait_for(lambda: self.read_progress(root)["status"] == "draining", process)
            process.terminate()
            self.assertEqual(process.wait(timeout=10), 130)
            progress = self.read_progress(root)
            self.assertEqual(progress["status"], "interrupted")
            self.assertEqual(progress["exit_code"], 130)
            self.assertTrue(progress["interruption_requested"])
            self.assertEqual(progress["job_counts"]["interrupted"], 2)
            self.assertEqual(progress["job_counts"]["pending"], 2)
            self.assertFalse(any(root.glob("job_*.json")))
            self.assertFalse((root / "job_2.started").exists())
            self.assertTrue(json.loads((root / "driver_result.json").read_text())["handlers_restored"])

    def test_without_drain_all_jobs_still_dispatch_and_complete(self):
        with tempfile.TemporaryDirectory(prefix="kimi-no-drain-test-") as directory:
            root = Path(directory)
            process = self.launch(root)
            (root / "release").touch()
            self.assertEqual(process.wait(timeout=10), 0)
            progress = self.read_progress(root)
            self.assertEqual(progress["status"], "completed")
            self.assertEqual(progress["exit_code"], 0)
            self.assertFalse(progress["drain_requested"])
            self.assertTrue(progress["all_selected_jobs_complete"])
            self.assertEqual(progress["job_counts"]["completed"], 4)
            self.assertEqual(progress["job_counts"]["pending"], 0)
            self.assertEqual(len(list(root.glob("job_*.json"))), 4)
            self.assertTrue(json.loads((root / "driver_result.json").read_text())["handlers_restored"])


if __name__ == "__main__":
    unittest.main()
