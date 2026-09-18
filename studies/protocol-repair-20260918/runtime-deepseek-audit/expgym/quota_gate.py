"""Opt-in, cross-process quota pauses; never re-execute an agent decision.

The supervisor atomically writes snapshot.json. This module only reads that
sanitized evidence: it cannot access credentials or contact a provider. Pauses
retain live worker state; they are deliberately not process-crash checkpoints.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import fcntl
import json
import math
import os
from pathlib import Path
import re
import tempfile
import threading
import time


def _timestamp(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("invalid quota timestamp")
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("quota timestamp requires an explicit timezone")
        number = parsed.timestamp()
    if not math.isfinite(number):
        raise ValueError("invalid quota timestamp")
    return number


def _utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()


def _atomic_json(path, value):
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(path.parent),
                                         prefix=".quota-", delete=False)
    try:
        with handle:
            os.chmod(handle.name, 0o600)
            json.dump(value, handle, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, str(path))
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)


class QuotaGate:
    """One directory/lock per provider account and requested model.

    Snapshot schema: expgym.quota-snapshot.v1, provider, model, observed_at
    (UTC ISO timestamp), blocked (bool or null), reset_at (timestamp or null),
    reason (window_quota/weekly_quota/model_throttle/available/unknown).
    Unknown/stale snapshots cannot release an existing pause. A fresh available
    snapshot obtained after the pause, and after any known reset, releases it.
    """

    def __init__(self, directory, provider, model, *, clock=time.time, sleep=time.sleep,
                 poll_seconds=5.0, snapshot_max_age_seconds=120.0):
        if provider not in {"gemini", "claude"} or not isinstance(model, str) or not model.strip():
            raise ValueError("quota gate needs an explicit supported provider and model")
        for value in (poll_seconds, snapshot_max_age_seconds):
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError("quota polling intervals must be positive and finite")
        self.directory, self.provider, self.model = Path(directory), provider, model
        self.clock, self.sleep = clock, sleep
        self.poll_seconds, self.snapshot_max_age_seconds = poll_seconds, snapshot_max_age_seconds
        self.directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_environment(cls, model):
        directory = os.getenv("EXPGYM_QUOTA_STATE_DIR")
        if not directory:
            return None
        configured_model = os.getenv("EXPGYM_QUOTA_MODEL")
        if model != configured_model:
            raise ValueError("quota gate model differs from requested model")
        return cls(directory, os.getenv("EXPGYM_QUOTA_PROVIDER"), configured_model,
                   poll_seconds=float(os.getenv("EXPGYM_QUOTA_POLL_SECONDS", "5")),
                   snapshot_max_age_seconds=float(os.getenv("EXPGYM_QUOTA_SNAPSHOT_MAX_AGE_SECONDS", "120")))

    @contextmanager
    def _locked(self):
        with (self.directory / "gate.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def _state(self):
        path = self.directory / "gate.json"
        if path.exists():
            value = json.loads(path.read_text())
            if (value.get("schema") != "expgym.quota-gate.v1" or
                    value.get("provider") != self.provider or value.get("model") != self.model):
                raise ValueError("quota gate identity mismatch")
            return value
        return {"schema": "expgym.quota-gate.v1", "provider": self.provider,
                "model": self.model, "paused": False}

    def _snapshot(self, now):
        try:
            value = json.loads((self.directory / "snapshot.json").read_text())
            if (value.get("schema") != "expgym.quota-snapshot.v1" or
                    value.get("provider") != self.provider or value.get("model") != self.model):
                raise ValueError("quota snapshot identity mismatch")
            observed = _timestamp(value.get("observed_at"))
            reset = _timestamp(value.get("reset_at"))
            if observed is None or not -5 <= now - observed <= self.snapshot_max_age_seconds:
                return None
            blocked = value.get("blocked")
            if blocked is not None and type(blocked) is not bool:
                raise ValueError("quota snapshot blocked must be bool or null")
            return {"observed_at": observed, "reset_at": reset, "blocked": blocked,
                    "reason": value.get("reason") if value.get("reason") in {
                        "window_quota", "weekly_quota", "model_throttle", "available", "unknown"
                    } else "unknown"}
        except (OSError, ValueError, TypeError):
            return None

    def _event(self, kind, **fields):
        with (self.directory / "events.jsonl").open("a") as stream:
            json.dump({"event": kind, "at": _utc(self.clock()), "provider": self.provider,
                       "model": self.model, "pid": os.getpid(),
                       "thread_id": threading.get_ident(), **fields}, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

    def _pause_locked(self, state, evidence, now, request_id=None):
        reset = evidence.get("reset_at")
        prior_reset = _timestamp(state.get("paused_until"))
        if not state.get("paused"):
            state.update(paused=True, paused_at=_utc(now), release_observation_after=_utc(now))
            self._event("paused", reason=evidence["reason"], request_id=request_id)
        # Later HTTP failures must not be cleared by an older available snapshot.
        if request_id is not None:
            state["release_observation_after"] = _utc(now)
        if reset is not None and (prior_reset is None or reset > prior_reset):
            state["paused_until"] = _utc(reset)
        elif "paused_until" not in state:
            state["paused_until"] = None
        state["reason"] = evidence["reason"]
        state["heartbeat_at"] = _utc(now)
        _atomic_json(self.directory / "gate.json", state)

    def pause(self, evidence, request_id=None):
        with self._locked():
            self._pause_locked(self._state(), evidence, self.clock(), request_id)

    def before_attempt(self):
        """Return actual wall seconds waited, without touching simulated clocks."""
        entered = self.clock()
        waited = False
        while True:
            now = self.clock()
            with self._locked():
                state = self._state()
                snapshot = self._snapshot(now)
                if snapshot is not None and snapshot["blocked"] is True:
                    self._pause_locked(state, snapshot, now)
                elif snapshot is None or snapshot["blocked"] is None:
                    if not state.get("paused"):
                        self._pause_locked(state, {"reason": "unknown", "reset_at": None}, now)
                if state.get("paused"):
                    reset = _timestamp(state.get("paused_until"))
                    after = _timestamp(state["release_observation_after"])
                    if (snapshot is not None and snapshot["blocked"] is False and
                            snapshot["observed_at"] > after and
                            (reset is None or snapshot["observed_at"] >= reset) and
                            (reset is None or now >= reset)):
                        state.update(paused=False, resumed_at=_utc(now), heartbeat_at=_utc(now))
                        self._event("resumed", reason="fresh_available_snapshot")
                        _atomic_json(self.directory / "gate.json", state)
                    else:
                        state.update(heartbeat_at=_utc(now), waiter_pid=os.getpid(),
                                     waiter_thread_id=threading.get_ident())
                        _atomic_json(self.directory / "gate.json", state)
                if not state.get("paused"):
                    delay = max(0.0, now - entered) if waited else 0.0
                    if waited:
                        self._event("wait_complete", quota_wait_seconds=delay)
                    return delay
            waited = True
            self.sleep(self.poll_seconds)

    def classify_http(self, status, raw, headers=None):
        """Recognize quota evidence only; unknown 503/401 are never quota."""
        if status == 401 or status not in {403, 429, 503}:
            return None
        now = self.clock()
        snapshot = self._snapshot(now)
        backed = snapshot is not None and snapshot["blocked"] is True and snapshot["reason"] in {
            "window_quota", "weekly_quota", "model_throttle"}
        try:
            body = json.loads(raw.decode("utf-8"))
            error = body.get("error", {}) if isinstance(body, dict) else {}
            error = error if isinstance(error, dict) else {}
        except (ValueError, UnicodeDecodeError):
            error = {}
        code = str(error.get("type") or error.get("code") or "").lower()
        message = str(error.get("message") or "").lower()
        if status == 503:
            if self.provider != "gemini":
                return None
            if backed:
                return snapshot
            # A scheduler-masked response can arrive before the next regular
            # quota poll. Request one coalesced refresh, then wait only a short
            # bounded time for evidence; absence of evidence is ordinary 503.
            if "no available gemini accounts" in message or "no available accounts" in message:
                requested_at = self.clock()
                _atomic_json(self.directory / "refresh-request.json", {
                    "schema": "expgym.quota-refresh-request.v1", "provider": self.provider,
                    "model": self.model, "requested_at": _utc(requested_at),
                    "reason": "masked_no_available_accounts"})
                deadline = requested_at + 15.0
                while self.clock() < deadline:
                    self.sleep(min(self.poll_seconds, deadline - self.clock()))
                    latest = self._snapshot(self.clock())
                    if latest is not None and latest["observed_at"] >= requested_at:
                        if latest["blocked"] is True and latest["reason"] in {
                                "window_quota", "weekly_quota", "model_throttle"}:
                            return latest
                        if latest["blocked"] is False:
                            break
            return None
        explicit = code in {"insufficient_quota", "quota_exhausted", "usage_limit_exceeded",
                            "subscription_limit_exceeded", "billing_hard_limit_reached"}
        details = error.get("details", []) if isinstance(error.get("details"), list) else []
        explicit = explicit or any(isinstance(detail, dict) and
            detail.get("@type") == "type.googleapis.com/google.rpc.ErrorInfo" and
            detail.get("reason") in {"QUOTA_EXHAUSTED", "QUOTA_EXCEEDED", "DAILY_LIMIT_EXCEEDED",
                                     "SUBSCRIPTION_LIMIT_EXCEEDED"} for detail in details)
        explicit = explicit or bool(re.search(
            r"(?:weekly|monthly|subscription|plan|five.hour|5.hour|hourly) (?:usage |credit |spending )?limit.{0,45}(?:exceed|reach|exhaust)|"
            r"(?:hit|reached|exceeded).{0,35}(?:weekly|monthly|subscription|plan|five.hour|5.hour|hourly) (?:usage )?limit|"
            r"reached your specified api usage limits|quota.{0,35}(?:exhausted|depleted)|"
            r"(?:exhausted|depleted).{0,35}quota|your quota (?:will )?reset", message))
        if not explicit and not (status == 429 and backed):
            return None
        reset = snapshot["reset_at"] if backed else None
        if headers:
            try:
                seconds = float(headers.get("Retry-After", ""))
                if math.isfinite(seconds) and seconds > 0:
                    reset = max(reset or now, now + seconds)
            except (ValueError, TypeError):
                try:
                    value = parsedate_to_datetime(headers.get("Retry-After", "")).timestamp()
                    if math.isfinite(value) and value > now:
                        reset = max(reset or now, value)
                except (ValueError, TypeError, OverflowError):
                    pass
        for detail in details:
            if isinstance(detail, dict) and detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                delay = detail.get("retryDelay")
                if isinstance(delay, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?s", delay):
                    seconds = float(delay[:-1])
                    if math.isfinite(seconds) and seconds > 0:
                        reset = max(reset or now, now + seconds)
        reason = snapshot["reason"] if backed else "weekly_quota" if "weekly" in message else "window_quota"
        return {"reason": reason, "reset_at": reset}
