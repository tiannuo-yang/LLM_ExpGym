"""Append-only execution evidence; never a score or completion authority.

Construction creates no files (enabled scopes obtain an OS-entropy UUID).
Raw returned loop values are copied in memory before
caller/scorer mutations. Durable writes happen on scope exit, after the caller's
original claim/graph cleanup, not in the model-interaction critical path.
Exceptions retain only their type and allowlisted source frame locations.
"""
from __future__ import annotations

import copy
import builtins
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, Optional
from uuid import uuid4


SCHEMA = 'expgym.terminal-evidence.v1'
_SOURCE_FILES = frozenset({
    'demo_experiment.py', 'scripts/run_poolact.py', 'scripts/run_paper_sweep.py',
    'expgym/terminal_evidence.py', 'expgym/react_loop.py', 'expgym/poolact.py',
    'expgym/llm_clients.py', 'expgym/task_tuning.py',
    'expgym/task_restricted_search.py', 'expgym/task_evidence_audit.py',
    'expgym/tool_protocol.py', 'expgym/evaluation_identity.py',
    'expgym/execution_contract.py', 'expgym/extras/parallel_cache.py',
    'expgym/errors.py',
    'expgym/compact_nasbench101.py', 'expgym/compact_nasbench201.py',
    'expgym/missing_final.py',
})
_BUILTIN_ERRORS = frozenset(value for value in vars(builtins).values()
                          if isinstance(value, type) and issubclass(value, BaseException))
_REPOSITORY_ERROR_NAMES = frozenset({
    ('expgym.llm_clients', 'APIClientError'),
    ('expgym.llm_clients', 'APICompletionAbortedError'),
    ('expgym.errors', 'ToolInputError'),
    ('expgym.errors', 'InvalidConfigurationError'),
})


def _exception_type(error: BaseException) -> str:
    kind = type(error)
    if kind in _BUILTIN_ERRORS or (kind.__module__, kind.__name__) in _REPOSITORY_ERROR_NAMES:
        return kind.__name__
    return 'unavailable'


def _safe_name(value: str) -> str:
    return value if re.fullmatch(r'(?:[A-Za-z_][A-Za-z0-9_]{0,127}|<(?:module|lambda|listcomp|dictcomp|setcomp|genexpr)>)', value) else 'unavailable'


def safe_exception(error: BaseException, source_root: Path) -> Dict[str, Any]:
    """No str/repr(error), traceback formatting, locals, source text or chains."""
    frames = []
    omitted = 0
    traceback = error.__traceback__
    root = Path(source_root).absolute()
    while traceback is not None:
        code = traceback.tb_frame.f_code
        try:
            path = Path(code.co_filename).absolute().relative_to(root).as_posix()
        except ValueError:
            path = None
        if path in _SOURCE_FILES:
            frames.append({'path': path, 'function': _safe_name(code.co_name),
                           'line': traceback.tb_lineno})
        else:
            omitted += 1
        traceback = traceback.tb_next
    return {'type': _exception_type(error), 'frames': frames,
            'omitted_frame_count': omitted,
            'message_locals_source_text_and_chain_omitted': True}


def score_projection(check: Any) -> Dict[str, Any]:
    """Preserve ordinary checks; label removal of legacy exception messages.

    The frozen tuning scorer embeds caught exception text in two fields and
    does not expose the corresponding exception object. Its type/stack cannot
    be reconstructed here and is deliberately not guessed.
    """
    projected = copy.deepcopy(check)
    omitted = []
    if isinstance(projected, dict):
        reason = projected.get('reason')
        if isinstance(reason, str) and reason.startswith('tool recompute failed:'):
            projected['reason'] = 'tool recompute failed; exception message omitted'
            omitted.append('/reason/exception_message')
        if 'invalid_configuration' in projected:
            projected.pop('invalid_configuration')
            omitted.append('/invalid_configuration')
    return {'projection': 'safe_projection' if omitted else 'exact',
            'omitted_exception_message_fields': omitted,
            'embedded_exception_type_and_frames_unavailable': bool(omitted),
            'score_check': projected}


def _open_directory(path: Path) -> int:
    """Create only missing components, rejecting symlinks at every step."""
    absolute = path.absolute()
    if '..' in absolute.parts:
        raise ValueError('Terminal evidence path must not contain parent traversal')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            try:
                os.mkdir(component, 0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            else:
                os.fsync(descriptor)
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


class TerminalEvidence:
    """One attempt, with distinct terminal/score/error events and no overwrite.

    root=None is the explicitly disabled console-demo mode. A persistence
    failure propagates. If recording an already active exception also fails,
    only a fixed/type-only diagnostic is emitted and the original is retained.
    Other threads are neither cancelled nor signalled.
    """
    def __init__(self, root: Optional[Path], *, owner: Dict[str, Any], source_root: Path,
                 stage: str = 'prepare'):
        self.root = Path(root) if root is not None else None
        self.owner = copy.deepcopy(owner) if root is not None else {}
        self.source_root = Path(source_root)
        self.attempt = uuid4().hex if root is not None else None
        if stage not in {'prepare', 'run_items', 'runner_finalize', 'demo_run'}:
            raise ValueError('Unknown terminal evidence stage')
        self.stage = stage
        self.pending = []

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if self.root is None:
            return False
        if error is not None:
            try:
                self.pending.append(('exception', {'stage': self.stage,
                                    'exception': safe_exception(error, self.source_root)}))
            except BaseException:
                # Evidence metadata construction must not replace a primary.
                try:
                    sys.stderr.write('TERMINAL_EVIDENCE_EXCEPTION_METADATA_UNAVAILABLE\n')
                except BaseException:
                    pass
        first_write_error = None
        for event, payload in self.pending:
            try:
                self._write(event, payload)
            except BaseException as evidence_error:
                if first_write_error is None:
                    first_write_error = evidence_error
                try:
                    sys.stderr.write('TERMINAL_EVIDENCE_WRITE_ERROR_TYPE=' +
                                     _exception_type(evidence_error) + '\n')
                except BaseException:
                    pass
        if first_write_error is not None and error is None:
            try:
                self._write('exception', {'stage': 'persistence',
                            'exception': safe_exception(first_write_error, self.source_root)})
            except BaseException:
                pass
            raise first_write_error
        # Never replace an active original exception with a write failure.
        return False

    def _write(self, event: str, payload: Any) -> None:
        if self.root is None:
            return
        if event not in {'loop_terminal', 'score_check', 'exception'}:
            raise ValueError('Unknown terminal evidence event')
        envelope = {'schema_version': SCHEMA, 'event': event, 'owner': self.owner,
                    'attempt_id': self.attempt, 'payload': payload,
                    'attempt_id_kind': 'evidence_scope_not_model_resample',
                    'completion_marker': False, 'score_acceptance_authority': False}
        raw = (json.dumps(envelope, sort_keys=True, ensure_ascii=False,
                          allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')
        directory = _open_directory(self.root / ('attempt_' + self.attempt))
        partial = event + '.json.partial_' + uuid4().hex
        descriptor = None
        try:
            descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                 0o600, dir_fd=directory)
            offset = 0
            while offset < len(raw):
                written = os.write(descriptor, raw[offset:])
                if written <= 0:
                    raise OSError('Terminal evidence write made no progress')
                offset += written
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            os.link(partial, event + '.json', src_dir_fd=directory,
                    dst_dir_fd=directory, follow_symlinks=False)
            os.unlink(partial, dir_fd=directory)
            os.fsync(directory)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory)
        # On failure, a partial file is retained under an explicit .partial_
        # name; it is not a complete JSON event. No existing file is replaced.

    def loop(self, function, *args, **kwargs):
        self.stage = 'loop'
        value = function(*args, **kwargs)
        self.stage = 'capture_loop'
        if self.root is not None:
            self.pending.append(('loop_terminal', {'loop_result': copy.deepcopy(value),
                                'capture_point': 'raw_return_before_caller_and_scorer_mutations',
                                'durable_write_point': 'scope_exit_after_original_cleanup'}))
        self.stage = 'after_loop'
        return value

    def score(self, function, result, tools, evaluator):
        self.stage = 'score'
        check = function(result, tools, evaluator)
        self.stage = 'capture_score'
        if self.root is not None:
            payload = score_projection(check)
            fields = ('answer', 'answer_perf', 'answer_overhead', 'answer_metrics',
                      'answer_source', 'answer_score_source', 'missing_final_policy',
                      'terminal_origin', 'terminal_scenario', 'scoring_input', 'score_status', 'terminal_status')
            payload['post_score_fields'] = copy.deepcopy({key: result[key] for key in fields if key in result})
            payload['post_score_field_scope'] = list(fields)
            self.pending.append(('score_check', payload))
        self.stage = 'after_score'
        return check
