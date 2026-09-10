#!/usr/bin/env python3
"""Fixed recovery eight: independent metadata-only usage accounting.

No project imports, exporter calls, scoring, raw answer/history interpretation,
network, or old-run payload reads. Invalid token values are never counted as
integers; a missing/invalid field is unknown, not zero. Conflicting valid aliases
and an individual reasoning count above completion are hard failures.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import stat
import sys

HERE = Path(__file__).resolve().parent
OP = HERE.parent.parent
RUN_ID = 'restart-20260909-v5-kimi-k3-infra8-recovery'
RUN = OP.parent.parent / 'formal_runs' / RUN_ID
SEAL_PATH = OP / 'k3_recovery_root_v1/SEAL_V2_ACCEPTANCE.json'
SEAL_SHA = 'd4b3cf79b91d9d3ac41bc8d1c33272bc4404f8035538c08fca8e1679d2bae219'
INVENTORY_SHA = 'b1d1dd3f17b4eb6ccd9cda4026e02f3423674a84b2af15d58db263921794a5ce'
CLOSURE_SHA = '5b53d7acc67a4460bda1da11de2e32ebdfcf5b483cbd4ee61226ba19dbd3fc34'
FIELDS = ('input_tokens', 'output_tokens', 'reasoning_tokens')


class Invalid(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Invalid(code)


def strict_json(body):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate_json_key')
            out[key] = value
        return out
    def bad_number(_):
        raise Invalid('nonfinite_json_number')
    return json.loads(body, object_pairs_hook=pairs, parse_constant=bad_number)


def count(value):
    return value if type(value) is int and value >= 0 else None


def decode(usage):
    u = usage if type(usage) is dict else {}
    p, c = count(u.get('prompt_tokens')), count(u.get('completion_tokens'))
    details = u.get('completion_tokens_details')
    flat = count(u.get('reasoning_tokens'))
    nested = count(details.get('reasoning_tokens')) if type(details) is dict else None
    candidates = [x for x in (flat, nested) if x is not None]
    require(len(set(candidates)) <= 1, 'conflicting_valid_reasoning_aliases')
    r = candidates[0] if candidates else None
    require(r is None or c is None or r <= c, 'attempt_reasoning_exceeds_completion')
    source = ('both_equal' if len(candidates) == 2 else 'flat_only_valid' if flat is not None
              else 'nested_only_valid' if nested is not None else 'unknown')
    return dict(zip(FIELDS, (p, c, r))), source


def aggregate(rows):
    result = {}
    for name in FIELDS:
        values = [row[name] for row in rows]
        unknown = sum(value is None for value in values)
        total = sum(value for value in values if value is not None)
        result[name] = dict(known_sum=total, unknown_attempts=unknown,
                            attempts=len(rows), complete_total=None if unknown else total)
    return result


def add_identity(seen, run_id, request_id):
    require(type(run_id) is str and bool(run_id), 'missing_raw_run_id')
    require(type(request_id) is str and re.fullmatch('[0-9a-f]{32}', request_id), 'invalid_request_id')
    identity = (run_id, request_id)
    require(identity not in seen, 'duplicate_run_request_identity')
    seen.add(identity)


def selftest():
    tests = 0
    def check(condition):
        nonlocal tests
        require(condition, 'selftest_failed')
        tests += 1
    def rejected(fn, code):
        try:
            fn()
        except Invalid as exc:
            check(str(exc) == code)
        else:
            raise Invalid('selftest_expected_rejection')
    values, source = decode(dict(prompt_tokens=2, completion_tokens=0, reasoning_tokens=0))
    check(values == dict(input_tokens=2, output_tokens=0, reasoning_tokens=0) and source == 'flat_only_valid')
    values, source = decode(dict(completion_tokens=9, completion_tokens_details=dict(reasoning_tokens=7)))
    check(values['reasoning_tokens'] == 7 and source == 'nested_only_valid')
    values, source = decode(dict(completion_tokens=5, reasoning_tokens=5, completion_tokens_details=dict(reasoning_tokens=5)))
    check(values['reasoning_tokens'] == 5 and source == 'both_equal')
    for bad in (True, False, -1, 3.0, '3', None, [], {}):
        values, _ = decode(dict(prompt_tokens=bad, completion_tokens=bad, reasoning_tokens=bad))
        check(values == dict.fromkeys(FIELDS))
        for flat, nested in ((bad, 3), (3, bad)):
            values, _ = decode(dict(completion_tokens=3, reasoning_tokens=flat, completion_tokens_details=dict(reasoning_tokens=nested)))
            check(values['reasoning_tokens'] == 3)
    rejected(lambda: decode(dict(reasoning_tokens=2, completion_tokens_details=dict(reasoning_tokens=3))), 'conflicting_valid_reasoning_aliases')
    rejected(lambda: decode(dict(completion_tokens=1, reasoning_tokens=2)), 'attempt_reasoning_exceeds_completion')
    # A large separate completion cannot offset a bad individual attempt.
    decode(dict(completion_tokens=1000, reasoning_tokens=0))
    rejected(lambda: decode(dict(completion_tokens=1, reasoning_tokens=2)), 'attempt_reasoning_exceeds_completion')
    check(decode(dict(reasoning_tokens=7))[0] == dict(input_tokens=None, output_tokens=None, reasoning_tokens=7))
    rows = [decode(u)[0] for u in (dict(prompt_tokens=2, completion_tokens=3, reasoning_tokens=1),
                                  dict(prompt_tokens=4, completion_tokens=5))]
    out = aggregate(rows)
    check([out[f]['complete_total'] for f in FIELDS] == [6, 8, None])
    check(out['reasoning_tokens']['known_sum'] == 1 and out['reasoning_tokens']['unknown_attempts'] == 1)
    check(aggregate([decode(None)[0]])['input_tokens']['complete_total'] is None)
    check(aggregate([])['input_tokens']['complete_total'] == 0)
    seen = set()
    add_identity(seen, 'new', 'a' * 32)
    rejected(lambda: add_identity(seen, 'new', 'a' * 32), 'duplicate_run_request_identity')
    add_identity(seen, 'other', 'a' * 32)
    check(len(seen) == 2)
    rejected(lambda: strict_json('{"x":1,"x":2}'), 'duplicate_json_key')
    rejected(lambda: strict_json('{"x":NaN}'), 'nonfinite_json_number')
    return dict(passed=True, checks=tests, actual_raw_reads=0)


def stamp(s):
    return tuple(getattr(s, 'st_' + name) for name in ('dev', 'ino', 'mode', 'size', 'mtime_ns', 'ctime_ns'))


class Reader:
    def __init__(self):
        self.refs, self.stamps = {}, {}

    def read(self, ref):
        path = Path(ref['path'])
        require(path.is_absolute() and path.resolve() == path and '..' not in path.parts, 'noncanonical_input')
        require(str(path) not in self.refs, 'input_read_twice')
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 128 * 1024 * 1024, 'input_not_regular_or_too_large')
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as handle:
            require(stamp(before) == stamp(os.fstat(handle.fileno())), 'input_changed_before_read')
            body = handle.read(128 * 1024 * 1024 + 1)
            require(stamp(before) == stamp(os.fstat(handle.fileno())) == stamp(path.lstat()), 'input_changed_during_read')
        require(len(body) == before.st_size and ('bytes' not in ref or len(body) == ref['bytes']), 'input_size_mismatch')
        require(hashlib.sha256(body).hexdigest() == ref['sha256'], 'input_sha_mismatch')
        for key, attr in (('mode','st_mode'), ('device','st_dev'), ('inode','st_ino'), ('mtime_ns','st_mtime_ns'), ('ctime_ns','st_ctime_ns')):
            require(key not in ref or ref[key] == getattr(before, attr), 'sealed_stat_mismatch_' + key)
        self.refs[str(path)] = dict(path=str(path), sha256=ref['sha256'], bytes=len(body))
        self.stamps[str(path)] = stamp(before)
        return strict_json(body)

    def stable(self):
        require(all(stamp(Path(path).lstat()) == original for path, original in self.stamps.items()), 'input_changed_after_read')


def same_ref(a, b):
    return all(a.get(key) == b.get(key) for key in ('path', 'sha256')) and ('bytes' not in a or a['bytes'] == b['bytes'])


def actual():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    require(not (HERE / 'ACTUAL_STARTED.json').exists(), 'actual_already_started')
    save('ACTUAL_STARTED.json', dict(run_id=RUN_ID, mode='one_actual_read', selftest=selftest()))
    reader = Reader()
    root = reader.read(dict(path=str(SEAL_PATH), sha256=SEAL_SHA))
    require(root['passed'] is True and root['inventory_ref']['sha256'] == INVENTORY_SHA
            and root['closure_ref']['sha256'] == CLOSURE_SHA, 'root_seal_pins')
    inventory = reader.read(root['inventory_ref'])
    require(inventory['run_root'] == str(RUN) and inventory['closure_ref']['sha256'] == CLOSURE_SHA, 'inventory_scope')
    closure = reader.read(inventory['closure_ref'])
    require(closure['run_id'] == RUN_ID and closure['expected_invocations'] == 8 and closure['raw_count'] == 289
            and closure['local_workers'] == 0, 'closure_scope')
    files = {}
    for part in inventory['file_parts']:
        page = reader.read(part)
        require(len(page) == part['file_count'] and sum(row['bytes'] for row in page) == part['total_bytes'], 'inventory_page_totals')
        for ref in page:
            p = Path(ref['path'])
            require(RUN in p.parents and str(p) not in files and p.relative_to(RUN).as_posix() == ref['relative_path'], 'inventory_path_scope')
            files[str(p)] = ref
    require(len(files) == inventory['file_count'] == 1072 and sum(r['bytes'] for r in files.values()) == inventory['total_bytes'], 'inventory_totals')
    for field, expected in (('execution_ref', RUN / 'execution.json'), ('plan_ref', OP / ('compiled_' + RUN_ID) / 'plan.json')):
        ref = closure[field]
        require(ref['path'] == str(expected) and any(same_ref(ref, candidate) for candidate in inventory['control_refs']), 'control_ref_binding')
    require(same_ref(closure['execution_ref'], files[str(RUN / 'execution.json')]), 'sealed_execution_binding')
    execution = reader.read(closure['execution_ref'])
    plan = reader.read(closure['plan_ref'])
    require(execution['run_id'] == plan['config']['run_id'] == RUN_ID and execution['local_workers'] == 0, 'run_metadata_scope')
    jobs = {j['invocation_id']: j for j in plan['jobs']}
    require(len(jobs) == len(plan['jobs']) == len(execution['reports']) == 8, 'eight_jobs')
    require(set(execution['started_invocation_ids']) == set(jobs) and execution['unstarted_invocation_ids'] == [], 'started_scope')
    selected, reports_seen = {}, set()
    for report in execution['reports']:
        iid = report['invocation_id']
        require(iid in jobs and iid not in reports_seen, 'report_owner')
        reports_seen.add(iid)
        ref = report['report']['raw_audit_ref']
        expected = RUN / 'logs' / iid / 'raw_audit.json'
        require(ref['path'] == str(expected) and same_ref(ref, files[str(expected)]), 'sealed_raw_audit')
        audit = reader.read(files[str(expected)])
        raw_refs = [r for r in audit['inventory'] if r['kind'] == 'raw']
        require(len(raw_refs) == audit['counts']['raw_files'], 'raw_audit_count')
        for raw_ref in raw_refs:
            path = raw_ref['path']
            require(path in files and same_ref(raw_ref, files[path]) and path not in selected, 'raw_ref_binding_duplicate')
            require(Path(path).parent == Path(jobs[iid]['dump_dir']) and RUN / 'dumps' in Path(path).parents, 'raw_job_path_owner')
            selected[path] = iid
    sealed_raw = {name for name in files if RUN / 'dumps' in Path(name).parents}
    require(set(selected) == sealed_raw and len(selected) == 289, 'exact_289_sealed_raw')
    attempts, seen = [], set()
    states, run_ids, representations = collections.Counter(), collections.Counter(), collections.Counter()
    for path, iid in sorted(selected.items()):
        raw = reader.read(files[path])
        rid, raw_run, state = raw.get('request_id'), raw.get('run_id'), raw.get('state')
        require(raw_run == plan['config']['run_id'], 'raw_run_id_differs_from_pinned_new_plan')
        require(raw.get('schema_version') == 'expgym.api_attempt.v1' and state in ('success', 'error', 'malformed_response'), 'raw_schema_or_state')
        require(Path(path).name == str(rid) + '.json', 'request_filename_binding')
        add_identity(seen, raw_run, rid)
        # Only usage metadata is selected from response_json. No choices,
        # content, reasoning body, request messages, or context is inspected.
        response = raw.get('response_json')
        usage = response.get('usage') if type(response) is dict else None
        values, representation = decode(usage)
        attempts.append(dict(invocation_id=iid, run_id=raw_run, request_id=rid, state=state,
                             usage=values, reasoning_source=representation, raw_ref=reader.refs[path]))
        states[state] += 1
        run_ids[raw_run] += 1
        representations[representation] += 1
        del raw, response, usage
    require(dict(states) == closure['raw_states'], 'closure_raw_states_match')
    reader.stable()
    per_iid = {iid: dict(raw_count=sum(a['invocation_id'] == iid for a in attempts),
                        usage=aggregate([a['usage'] for a in attempts if a['invocation_id'] == iid]))
               for iid in sorted(jobs)}
    result = dict(schema='fixed8-independent-usage-peer-v1', passed=True, run_id=RUN_ID,
                  raw_count=len(attempts), unique_run_request_count=len(seen), iid_count=len(per_iid),
                  states=dict(states), raw_run_ids=dict(run_ids), reasoning_sources=dict(representations),
                  usage=aggregate([a['usage'] for a in attempts]), by_invocation=per_iid,
                  pins=dict(root_seal=SEAL_SHA, inventory=INVENTORY_SHA, closure=CLOSURE_SHA),
                  source_ref=dict(path=str(Path(__file__).resolve()), sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                  verified_input_count=len(reader.refs), input_refs=list(reader.refs.values()),
                  boundaries=dict(raw_reads=289, model_calls=0, scoring_calls=0, old_raw_reads=0,
                                  response_body_interpreted=False, reasoning_body_interpreted=False,
                                  exporter_imported=False, original_review_imported=False),
                  accounting='Completion includes reasoning; do not add reasoning again. Unknown is not zero.')
    save('attempts.json', attempts)
    save('summary.json', result)
    print(json.dumps({k: result[k] for k in ('passed','raw_count','unique_run_request_count','iid_count','states','raw_run_ids','reasoning_sources','usage','source_ref')}, sort_keys=True))


def save(name, value):
    body = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    with (HERE / name).open('xb') as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())


if __name__ == '__main__':
    if sys.argv[1:] == ['--selftest']:
        print(json.dumps(selftest(), sort_keys=True))
    elif sys.argv[1:] == ['--actual']:
        actual()
    else:
        raise SystemExit('usage: independent_usage.py --selftest | --actual')
