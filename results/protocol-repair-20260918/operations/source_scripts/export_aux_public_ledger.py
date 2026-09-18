"""Publish safe per-slot / per-request identities for separate parser controls."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import export_public_ledger as common

OPS = Path(__file__).resolve().parent
ROOT = OPS.parent
AUX = OPS / 'aux-controls'
OUT = AUX / 'public_ledger'


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def csvwrite(name, rows):
    if rows:
        with (OUT / name).open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    attempts, slots, profiles = [], [], {}
    release = common.read(AUX / 'EXECUTION_RELEASE.json') or {}
    for directory in sorted((AUX / 'queues').iterdir()):
        binding = common.read(directory / 'BINDINGS.json')
        if not binding:
            continue
        plan = common.read(directory / 'queue-plan.json')
        assert common.sha(directory / 'queue-plan.json') == binding['plan_sha256']
        by_id = {row['new_job_id']: row for row in binding['jobs']}
        events = {}
        run_root = Path(plan['output_root'])
        for path in (run_root / 'queue/sessions').glob('*/events.jsonl'):
            for line in path.read_text().splitlines():
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get('job_id') and event.get('event') in ('start', 'end'):
                    events.setdefault(event['job_id'], {})[event['event']] = event
        for job in plan['jobs']:
            jid, args = job['job_id'], job['args']
            source = by_id[jid]
            invocation = Path(args['output_dir']).parent
            result_path = Path(source['result_path'])
            completion_path = run_root / 'queue/jobs' / jid / 'completion.json'
            completion = common.read(completion_path)
            selected_attempts = []
            for path in sorted(Path(source['api_dump_root']).glob('**/*.json')):
                record = common.read(path)
                if not record:
                    continue
                response = record.get('response_json') or {}
                response = response if isinstance(response, dict) else {}
                usage = response.get('usage') or {}
                profile = common.settings(record.get('request_payload') or {})
                profile_id = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
                profiles[profile_id] = profile
                artifact = (completion or {}).get('artifacts', {}).get(str(path.relative_to(invocation)))
                checksum = common.sha(path)
                if artifact:
                    assert artifact['sha256'] == checksum, 'Validated raw request changed'
                row = {'old_slot_id': source['old_slot_id'], 'job_id': jid, 'model': source['model'],
                    'request_id': record.get('request_id'), 'generation_id': record.get('generation_id'),
                    'context_agent_id': (record.get('context') or {}).get('agent_id'),
                    'context_seed': (record.get('context') or {}).get('seed'),
                    'wire_seed': (record.get('request_payload') or {}).get('seed'),
                    'attempt': record.get('attempt'), 'max_attempts': record.get('max_attempts'),
                    'state': record.get('state'), 'http_status': record.get('http_status'),
                    'will_retry': record.get('will_retry'), 'retry_delay_seconds': record.get('retry_delay_seconds'),
                    'started_at_utc': record.get('started_at_utc'), 'finished_at_utc': record.get('finished_at_utc'),
                    'request_wall_seconds': record.get('wall_time_seconds'),
                    'api_protocol': (record.get('context') or {}).get('api_protocol'),
                    'response_model': response.get('model'), 'response_provider': response.get('provider'),
                    'request_profile_sha256': profile_id, 'prompt_tokens': usage.get('prompt_tokens'),
                    'completion_tokens': usage.get('completion_tokens'), 'input_tokens': usage.get('input_tokens'),
                    'output_tokens': usage.get('output_tokens'), 'total_tokens': usage.get('total_tokens'),
                    'reported_cost_usd': usage.get('cost'), 'raw_record_sha256': checksum,
                    'raw_record_final': record.get('state') != 'in_progress', 'queue_artifact_verified': bool(artifact), **common.usage_details(usage)}
                attempts.append(row)
                selected_attempts.append(row)
            start, end = events.get(jid, {}).get('start'), events.get(jid, {}).get('end')
            wall = end['elapsed_seconds'] - start['elapsed_seconds'] if start and end else None
            costs = [row['reported_cost_usd'] for row in selected_attempts if row['reported_cost_usd'] is not None]
            aliases = release.get('code_commit', {})
            slot = {'old_slot_id': source['old_slot_id'], 'job_id': jid, 'model': source['model'],
                'runner': job['runner'], 'scenario': args.get('scenario') or job['selection'].get('scenario'),
                'selection_json': json.dumps(job['selection'], sort_keys=True, separators=(',', ':')),
                'regime': args.get('cost_regime') or job['selection'].get('cost_regime'),
                'beta': args.get('beta') if job['runner'] == 'poolact' else job['selection'].get('beta'), 'agents': args.get('agents', 1),
                'seed': args.get('seed') if job['runner'] == 'poolact' else job['selection'].get('seed'),
                'status': 'validated_complete' if completion else ('failed_attempt' if end else ('running' if start else 'pending')),
                'whole_slot_attempt': 1, 'source_code_commit': aliases.get(directory.name) if isinstance(aliases, dict) else aliases,
                'core_code_commit': '0e6c51b6d86f42437038518c2fc8adc510901c0b',
                'source_tree_sha256': binding['source_tree_sha256'], 'plan_sha256': binding['plan_sha256'],
                'historical_trajectory_sha256': source.get('source_trajectory_sha256') or source.get('source_trace_sha256'),
                'result_sha256': common.sha(result_path) if completion else None,
                'completion_receipt_sha256': common.sha(completion_path) if completion else None,
                'slot_wall_seconds_including_validation': wall, 'http_attempts': len(selected_attempts),
                'successful_http_attempts': sum(r['state'] == 'success' for r in selected_attempts),
                'error_http_attempts': sum(r['state'] not in ('success', 'in_progress') for r in selected_attempts),
                'logical_generations': len({r['generation_id'] for r in selected_attempts}),
                'reported_cost_usd': sum(costs) if costs else None, 'cost_report_count': len(costs),
                'requested_backend': args['backend'], 'requested_model': args.get('model') or job['selection'].get('model_id'),
                'reasoning_effort': args.get('reasoning_effort'),
                'temperature': args.get('temperature') if job['runner'] == 'poolact' else args.get('temperature_eval'),
                'top_p': args.get('top_p'), 'top_k': args.get('top_k'), 'max_tokens_config': args.get('max_tokens'),
                'max_context_tokens': args.get('max_context_tokens'), 'max_steps': args.get('max_steps'),
                'max_evals': args.get('max_evals'),
                'tool_protocol': args.get('tool_protocol')}
            slots.append(slot)
    assert len(slots) == len({r['old_slot_id'] for r in slots}), 'Duplicate source slot'
    csvwrite('slot_run_ledger.csv', slots)
    csvwrite('request_attempt_ledger.csv', attempts)
    dump('request_profiles.json', profiles)
    service_reference = OPS / 'public_ledger/service_versions.json'
    services = common.read(service_reference) or {}
    dump('service_versions.json', {m: services[m] for m in ('deepseek', 'qwen', 'glm') if m in services})
    summary = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'slots': len(slots),
        'validated_slots': sum(r['status'] == 'validated_complete' for r in slots), 'attempt_records': len(attempts),
        'all_complete': bool(slots) and all(r['status'] == 'validated_complete' for r in slots),
        'whole_slot_resampling': False, 'models': {},
        'cost_policy': 'Only provider usage.cost. Missing prices stay null; self-hosted GPU allocations are not converted to dollars.',
        'public_projection': 'No prompts/answers/tool text, credentials, bodies, cluster endpoints or absolute local source paths'}
    for alias in sorted({p.parent.name for p in (AUX / 'queues').glob('*/BINDINGS.json')}):
        ids = {r['new_job_id'] for r in common.read(AUX / 'queues' / alias / 'BINDINGS.json')['jobs']}
        rows = [r for r in slots if r['job_id'] in ids]
        costs = [r['reported_cost_usd'] for r in rows if r['reported_cost_usd'] is not None]
        summary['models'][alias] = {'planned': len(rows), 'validated': sum(r['status'] == 'validated_complete' for r in rows),
             'http_attempts': sum(r['http_attempts'] for r in rows), 'error_http_attempts': sum(r['error_http_attempts'] for r in rows),
             'reported_cost_usd': sum(costs) if costs else None}
    dump('USAGE_SUMMARY.json', summary)
    dump('MANIFEST.json', {'files': {p.name: {'bytes': p.stat().st_size, 'sha256': common.sha(p)}
        for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'MANIFEST.json'},
        'exporter_sha256': common.sha(Path(__file__)), 'common_exporter_sha256': common.sha(Path(common.__file__)),
        'complete': summary['all_complete']})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
