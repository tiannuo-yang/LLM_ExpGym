"""Quota pauses and pending-generation retries; no network or real clock waits."""
from email.message import Message
from io import BytesIO
import json
import multiprocessing
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import urllib.error

from expgym.llm_clients import APIClientError, OpenAICompatibleLLM, PartialAPIResponseError
from expgym.quota_gate import QuotaGate, _atomic_json, _utc


def process_wait(directory, signal):
    gate = QuotaGate(directory, "gemini", "opaque-model", poll_seconds=.01)
    signal.put(gate.before_attempt())


class FakeClock:
    def __init__(self):
        self.now, self.sleeps, self.callback = 1000.0, [], None

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.sleeps.append(seconds)
        if len(self.sleeps) > 100:
            raise AssertionError("unexpected unbounded test wait")
        if self.callback:
            self.callback()


class QuotaGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clock = FakeClock()
        self.gate = QuotaGate(self.root / "quota", "gemini", "opaque-model",
                              clock=self.clock.time, sleep=self.clock.sleep, poll_seconds=1)
        self.snapshot(False)

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self, blocked, reset=None, observed=None, reason=None):
        _atomic_json(self.gate.directory / "snapshot.json", {
            "schema": "expgym.quota-snapshot.v1", "provider": self.gate.provider,
            "model": self.gate.model, "observed_at": _utc(self.clock.now if observed is None else observed),
            "blocked": blocked, "reset_at": _utc(reset) if reset is not None else None,
            "reason": reason or ("window_quota" if blocked else "available"),
        })

    def failure(self, status, message="Too many requests", code=None, headers=None):
        error = {"message": message}
        if code is not None:
            error["type"] = code
        return urllib.error.HTTPError("http://fake/v1", status, "fixture", headers or Message(),
                                      BytesIO(json.dumps({"error": error}).encode()))

    def client(self, outcomes, max_retries=0):
        captured = []

        def transport(request, timeout):
            captured.append(request.data)
            value = outcomes.pop(0)
            if isinstance(value, Exception):
                raise value
            if isinstance(value, bytes):
                return value
            return json.dumps(value).encode()

        with patch.dict(os.environ, {}, clear=True):
            client = OpenAICompatibleLLM(api_key="fixture-secret", model="opaque-model",
                                         transport=transport, max_retries=max_retries,
                                         retry_base_seconds=0, retry_max_seconds=0)
        client._quota_gate = self.gate
        client._dump_directory = self.root / "dump"
        return client, captured

    @staticmethod
    def success():
        return {"choices": [{"message": {"role": "assistant", "content": "done"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2}}

    def test_reset_requires_new_available_snapshot_and_records_wait(self):
        self.snapshot(True, reset=1003)
        def update():
            if self.clock.now == 1002:
                self.snapshot(False)  # Before reset: cannot release later by itself.
            if self.clock.now == 1004:
                self.snapshot(False)
        self.clock.callback = update
        self.assertEqual(self.gate.before_attempt(), 4)
        state = json.loads((self.gate.directory / "gate.json").read_text())
        self.assertFalse(state["paused"])
        self.assertEqual(state["paused_until"], _utc(1003))
        events = (self.gate.directory / "events.jsonl").read_text()
        self.assertIn("wait_complete", events)
        self.assertIn("quota_wait_seconds", events)

    def test_quota429_does_not_consume_short_retry_budget_and_preserves_payload(self):
        client, captured = self.client([
            self.failure(429, "Your hourly usage limit has been reached"),
            self.failure(429, "Quota exhausted for this model"), self.success()], max_retries=0)
        self.clock.callback = lambda: self.snapshot(False)
        result = client.generate("same pending decision")
        self.assertEqual(result.text, "done")
        self.assertEqual(result.request_attempts, 3)
        self.assertEqual(len(set(captured)), 1)
        self.assertEqual([r["state"] for r in result.attempt_usage], ["error", "error", "success"])
        self.assertEqual([r["quota_wait_seconds"] for r in result.attempt_usage], [0, 1, 1])
        self.assertEqual(len({r["generation_id"] for r in result.attempt_usage}), 1)
        self.assertEqual(len({r["request_id"] for r in result.attempt_usage}), 3)
        self.assertIsNone(result.attempt_usage[0]["usage"])
        dumps = [json.loads(p.read_text()) for p in client._dump_directory.glob("*.json")]
        self.assertEqual(len(dumps), 3)
        self.assertTrue(all("fixture-secret" not in json.dumps(x) for x in dumps))
        self.assertEqual(sum(x.get("retry_classification") == "quota_pause" for x in dumps), 2)

    def test_quota_then_ordinary_failures_keep_original_bounded_policy(self):
        client, captured = self.client([
            self.failure(429, "Your weekly usage limit has been reached"),
            self.failure(503, "Backend unavailable"), TimeoutError("fixture timeout"),
            self.failure(429, "Too many requests"), self.success()], max_retries=2)
        self.clock.callback = lambda: self.snapshot(False)
        with self.assertRaises(APIClientError) as caught:
            client.generate("pending")
        self.assertEqual(len(captured), 4)
        self.assertEqual(len(caught.exception.attempt_usage), 4)

    def test_masked503_requires_fresh_model_evidence(self):
        raw = b'{"error":{"message":"No available Gemini accounts"}}'
        self.clock.callback = lambda: self.snapshot(True, reset=1010, reason="model_throttle")
        classified = self.gate.classify_http(503, raw)
        self.assertEqual(classified["reason"], "model_throttle")
        self.assertTrue((self.gate.directory / "refresh-request.json").exists())
        self.clock.callback = None
        self.snapshot(False)
        self.assertIsNone(self.gate.classify_http(503, b'{"error":{"message":"ordinary capacity failure"}}'))
        self.snapshot(True, reset=1010, observed=700)
        self.assertIsNone(self.gate.classify_http(503, b'{"error":{"message":"ordinary failure"}}'))

    def test_masked503_without_evidence_probe_is_bounded(self):
        self.clock.callback = lambda: self.snapshot(None, reason="unknown")
        raw = b'{"error":{"message":"No available Gemini accounts"}}'
        self.assertIsNone(self.gate.classify_http(503, raw))
        self.assertEqual(self.clock.now, 1015)

    def test_masked503_persists_error_before_probe_then_retries_pending_request(self):
        client, captured = self.client([
            self.failure(503, "No available Gemini accounts"), self.success()])
        def update():
            records = [json.loads(path.read_text()) for path in client._dump_directory.glob("*.json")]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["state"], "error")
            self.assertEqual(records[0]["http_status"], 503)
            self.assertEqual(records[0]["response_json"]["error"]["message"], "No available Gemini accounts")
            self.snapshot(self.clock.now < 1003, reset=1003 if self.clock.now < 1003 else None,
                          reason="model_throttle" if self.clock.now < 1003 else "available")
        self.clock.callback = update
        output = client.generate("same payload")
        self.assertEqual(output.request_attempts, 2)
        self.assertEqual(len(set(captured)), 1)
        self.assertEqual(output.attempt_usage[1]["quota_wait_seconds"], 2)
        self.assertIn("transport_wall_time_seconds", output.attempt_usage[0])
        self.assertIn("quota_evidence_wait_seconds", output.attempt_usage[0])

    def test_401_and_permission403_are_not_quota(self):
        self.snapshot(True, reset=1010)
        raw = b'{"error":{"message":"Invalid token"}}'
        self.assertIsNone(self.gate.classify_http(401, raw))
        self.assertIsNone(self.gate.classify_http(403, raw))
        self.snapshot(False)
        client, captured = self.client([self.failure(401, "Invalid token"), self.success()], max_retries=2)
        with self.assertRaises(APIClientError):
            client.generate("pending")
        self.assertEqual(len(captured), 1)

    def test_claude403_quota_and_retry_headers(self):
        self.gate.provider = "claude"
        self.snapshot(False)
        header = Message()
        header["Retry-After"] = "30"
        raw = b'{"error":{"message":"You have reached your specified API usage limits"}}'
        self.assertEqual(self.gate.classify_http(403, raw, header)["reset_at"], 1030)
        header.replace_header("Retry-After", "Thu, 01 Jan 1970 00:17:20 GMT")
        self.assertEqual(self.gate.classify_http(403, raw, header)["reset_at"], 1040)

    def test_no_reset_and_stale_available_stay_paused_until_fresh_available(self):
        self.gate.pause({"reason": "weekly_quota", "reset_at": None}, request_id="fixture")
        def update():
            if self.clock.now < 1003:
                self.snapshot(False, observed=700)
            else:
                self.snapshot(False)
        self.clock.callback = update
        self.assertEqual(self.gate.before_attempt(), 3)

    def test_rpc_retryinfo_only_with_explicit_quota_evidence(self):
        body = {"error": {"status": "RESOURCE_EXHAUSTED", "message": "Quota exhausted for model",
            "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3.5s"}]}}
        self.assertEqual(self.gate.classify_http(429, json.dumps(body).encode())["reset_at"], 1003.5)
        body["error"]["message"] = "Too many requests"
        self.assertIsNone(self.gate.classify_http(429, json.dumps(body).encode()))
        body["error"]["details"].append({"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                            "reason": "QUOTA_EXHAUSTED"})
        self.assertEqual(self.gate.classify_http(429, json.dumps(body).encode())["reset_at"], 1003.5)

    def test_success_status_error_hook_keeps_original_bytes_and_one_attempt_ledger_row(self):
        error_json = b'{"error":{"code":429,"message":"Quota exhausted"}}'
        original = b'event: error\ndata: ' + error_json + b'\n\n'
        client, captured = self.client([original, self.success()])
        client._quota_error_response = lambda raw: (429, error_json) if raw == original else None
        self.clock.callback = lambda: self.snapshot(False)
        output = client.generate("pending")
        self.assertEqual(output.request_attempts, 2)
        self.assertEqual(len(set(captured)), 1)
        self.assertEqual(len(output.attempt_usage), 2)
        first = output.attempt_usage[0]
        self.assertIsNone(first["http_status"])
        self.assertEqual(first["quota_error_response_status"], 429)
        saved = json.loads((client._dump_directory / (first["request_id"] + ".json")).read_text())
        self.assertEqual(saved["response_raw"].encode(), original)
        self.assertEqual(saved["state"], "error")

    def test_unconfirmed_error_hook_and_delivered_decision_never_resample(self):
        original = b'event: error\ndata: {"error":{"code":429,"message":"Too many requests"}}\n\n'
        client, captured = self.client([original, self.success()], max_retries=2)
        client._quota_error_response = lambda raw: (429, b'{"error":{"message":"Too many requests"}}')
        with self.assertRaises(APIClientError) as caught:
            client.generate("pending")
        self.assertEqual(len(captured), 1)
        self.assertEqual(len(caught.exception.attempt_usage), 1)
        client, captured = self.client([{"choices": [{"message": {"content": "Quota exhausted"}}]},
                                        self.success()], max_retries=2)
        self.assertEqual(client.generate("pending").text, "Quota exhausted")
        self.assertEqual(len(captured), 1)

    def test_partial_transport_bytes_and_known_usage_are_terminal_and_retained(self):
        partial = json.dumps(self.success()).encode()
        client, captured = self.client([PartialAPIResponseError("fixture stream interrupted", partial),
                                        self.success()], max_retries=2)
        with self.assertRaises(PartialAPIResponseError) as caught:
            client.generate("pending")
        self.assertEqual(len(captured), 1)
        attempts = caught.exception.attempt_usage
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["usage"], {"prompt_tokens": 3, "completion_tokens": 2})
        self.assertTrue(attempts[0]["usage_partial"])
        saved = json.loads((client._dump_directory / (attempts[0]["request_id"] + ".json")).read_text())
        self.assertEqual(saved["response_raw"].encode(), partial)
        self.assertTrue(saved["response_partial"])
        self.assertFalse(saved["will_retry"])

    def test_two_processes_share_one_pause_and_resume_after_recreation(self):
        current = time.time()
        _atomic_json(self.gate.directory / "snapshot.json", {
            "schema": "expgym.quota-snapshot.v1", "provider": "gemini", "model": "opaque-model",
            "observed_at": _utc(current), "blocked": True, "reset_at": _utc(current + .05),
            "reason": "window_quota"})
        signal = multiprocessing.Queue()
        children = [multiprocessing.Process(target=process_wait, args=(str(self.gate.directory), signal)) for _ in range(2)]
        try:
            for child in children:
                child.start()
            deadline = time.time() + 2
            while not (self.gate.directory / "gate.json").exists() and time.time() < deadline:
                time.sleep(.005)
            self.assertTrue(json.loads((self.gate.directory / "gate.json").read_text())["paused"])
            time.sleep(.08)
            _atomic_json(self.gate.directory / "snapshot.json", {
                "schema": "expgym.quota-snapshot.v1", "provider": "gemini", "model": "opaque-model",
                "observed_at": _utc(time.time()), "blocked": False, "reset_at": None, "reason": "available"})
            self.assertGreater(signal.get(timeout=2), 0)
            self.assertGreater(signal.get(timeout=2), 0)
            for child in children:
                child.join(2)
                self.assertEqual(child.exitcode, 0)
            recreated = QuotaGate(self.gate.directory, "gemini", "opaque-model")
            self.assertEqual(recreated.before_attempt(), 0)
            events = [json.loads(x) for x in (self.gate.directory / "events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(x["event"] == "paused" for x in events), 1)
            self.assertEqual(sum(x["event"] == "resumed" for x in events), 1)
        finally:
            for child in children:
                if child.is_alive():
                    child.terminate()
                    child.join(2)
            signal.close()

    def test_partial_error_itself_carries_prior_attempts_before_outer_generate_guard(self):
        for prior in (self.failure(429, "Quota exhausted"), self.failure(503, "Unavailable")):
            with self.subTest(prior_http_status=prior.code):
                partial = json.dumps(self.success()).encode()
                original_error = PartialAPIResponseError("fixture stream interrupted", partial)
                client, captured = self.client([prior, original_error, self.success()], max_retries=2)
                self.clock.callback = lambda: self.snapshot(False)
                ledger = []
                with self.assertRaises(PartialAPIResponseError) as caught:
                    client._generate("pending", tools=None, tool_choice=None, attempt_usage=ledger)
                self.assertIs(caught.exception, original_error)
                self.assertEqual(caught.exception.partial_response, partial)
                self.assertEqual(len(captured), 2)
                self.assertEqual(len(set(captured)), 1)
                self.assertEqual(len(caught.exception.attempt_usage), 2)
                self.assertEqual(caught.exception.attempt_usage[0]["http_status"], prior.code)
                self.assertEqual(caught.exception.attempt_usage[1]["usage"],
                                 {"prompt_tokens": 3, "completion_tokens": 2})
                self.assertTrue(caught.exception.attempt_usage[1]["usage_partial"])
                ledger[0]["state"] = "mutated-after-raise"
                self.assertEqual(caught.exception.attempt_usage[0]["state"], "error")

    def test_environment_is_opt_in_and_model_bound(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(QuotaGate.from_environment("opaque-model"))
        with patch.dict(os.environ, {"EXPGYM_QUOTA_STATE_DIR": str(self.gate.directory),
                "EXPGYM_QUOTA_PROVIDER": "gemini", "EXPGYM_QUOTA_MODEL": "different"}, clear=True):
            with self.assertRaisesRegex(ValueError, "differs"):
                QuotaGate.from_environment("opaque-model")


if __name__ == "__main__":
    unittest.main()
