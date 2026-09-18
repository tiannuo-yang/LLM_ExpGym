"""Export safe per-pool/per-attempt costs, settings and version identities.

No prompt, answer, tool content, credential, response body, cluster endpoint, or
absolute local source path is exported. Pending pools have no adopted score.
"""
import collections
import csv
import datetime
import hashlib
import json
from pathlib import Path

OPS = Path(__file__).resolve().parent
ROOT = OPS.parent
MODELS = ('gemini', 'gpt', 'glm', 'kimi', 'qwen', 'deepseek')
OUT = OPS / 'public_ledger'


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def csvwrite(name, rows):
    assert rows
    with (OUT / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def settings(payload):
    return {key: payload.get(key) for key in ('model', 'temperature', 'top_p', 'top_k', 'max_tokens',
            'max_output_tokens', 'seed', 'reasoning', 'reasoning_effort', 'provider', 'chat_template_kwargs') if key in payload}


def usage_details(usage):
    input_detail = usage.get('prompt_tokens_details') or usage.get('input_tokens_details') or {}
    output_detail = usage.get('completion_tokens_details') or usage.get('output_tokens_details') or {}
    cost_detail = usage.get('cost_details') or {}
    return {'reasoning_tokens': usage.get('reasoning_tokens', output_detail.get('reasoning_tokens')),
            'cached_input_tokens': input_detail.get('cached_tokens'),
            'cache_write_tokens': input_detail.get('cache_write_tokens'),
            'reported_upstream_total_cost_usd': cost_detail.get('upstream_inference_cost'),
            'reported_upstream_prompt_cost_usd': cost_detail.get('upstream_inference_prompt_cost'),
            'reported_upstream_completion_cost_usd': cost_detail.get('upstream_inference_completions_cost')}


def main():
    OUT.mkdir(exist_ok=True)
    attempts, pools, profiles, services = [], [], {}, {}
    for model in MODELS:
        directory = OPS / 'queues-v2' / model
        plan = read(directory / 'queue-plan.json')
        binding = read(directory / 'BINDINGS.json')
        by_id = {row['new_job_id']: row for row in binding['jobs']}
        events = {}
        for path in (ROOT / 'runs' / model / 'queue/sessions').glob('*/events.jsonl'):
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
            completion_path = ROOT / 'runs' / model / 'queue/jobs' / jid / 'completion.json'
            completion = read(completion_path)
            strategy = job['selection']['strategy']
            result_path = Path(args['output_dir']) / strategy / 'result.json'
            result = read(result_path)
            pool_attempts = []
            for path in sorted((invocation / 'api_dump').glob('**/*.json')):
                record = read(path)
                if record is None:
                    continue
                response = record.get('response_json') or {}
                if not isinstance(response, dict):
                    response = {}
                usage = response.get('usage') or {}
                payload = record.get('request_payload') or {}
                profile = settings(payload)
                profile_id = hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest()
                profiles[profile_id] = profile
                artifact_name = str(path.relative_to(invocation))
                artifact = (completion or {}).get('artifacts', {}).get(artifact_name)
                checksum = sha(path)
                if artifact:
                    assert artifact['sha256'] == checksum, 'Completed raw request changed'
                context = record.get('context') or {}
                row = {'old_slot_id': source['old_slot_id'], 'job_id': jid, 'model': source['model'],
                    'request_id': record.get('request_id'), 'generation_id': record.get('generation_id'),
                    'context_agent_id': context.get('agent_id'), 'context_seed': context.get('seed'),
                    'wire_seed': payload.get('seed'),
                    'attempt': record.get('attempt'), 'max_attempts': record.get('max_attempts'),
                    'state': record.get('state'), 'http_status': record.get('http_status'),
                    'will_retry': record.get('will_retry'), 'retry_delay_seconds': record.get('retry_delay_seconds'),
                    'started_at_utc': record.get('started_at_utc'), 'finished_at_utc': record.get('finished_at_utc'),
                    'request_wall_seconds': record.get('wall_time_seconds'), 'api_protocol': context.get('api_protocol'),
                    'response_model': response.get('model'), 'response_provider': response.get('provider'),
                    'request_profile_sha256': profile_id, 'prompt_tokens': usage.get('prompt_tokens'),
                    'completion_tokens': usage.get('completion_tokens'), 'input_tokens': usage.get('input_tokens'),
                    'output_tokens': usage.get('output_tokens'), 'total_tokens': usage.get('total_tokens'),
                    'reported_cost_usd': usage.get('cost'), 'raw_record_sha256': checksum,
                    'raw_record_final': record.get('state') != 'in_progress',
                    'queue_artifact_verified': bool(artifact), **usage_details(usage)}
                attempts.append(row)
                pool_attempts.append(row)
            cost_values = [row['reported_cost_usd'] for row in pool_attempts if row['reported_cost_usd'] is not None]
            start, end = events.get(jid, {}).get('start'), events.get(jid, {}).get('end')
            wall = end['elapsed_seconds'] - start['elapsed_seconds'] if start and end else None
            agents = (result or {}).get('agent_results', [])
            status = 'validated_complete' if completion else ('failed_attempt' if end else ('running' if start else 'pending'))
            row = {'old_slot_id': source['old_slot_id'], 'job_id': jid, 'model': source['model'], 'item': args['tuning_task'],
                'regime': args['cost_regime'], 'strategy': strategy, 'outer_repeat': source['outer_repeat'], 'seed': args['seed'],
                'agents': args['agents'], 'status': status, 'whole_pool_attempt': 1,
                'code_commit': 'ffca5704580b75e254f6e52dd4fe9dff104b1be8',
                'core_code_commit': '0e6c51b6d86f42437038518c2fc8adc510901c0b',
                'source_tree_sha256': plan['source_tree_sha256'], 'plan_sha256': binding['plan_sha256'],
                'historical_trajectory_sha256': source['source_trajectory_sha256'],
                'result_sha256': sha(result_path) if completion else None,
                'completion_receipt_sha256': sha(completion_path) if completion else None,
                'pool_wall_seconds_including_validation': wall,
                'sum_agent_wall_seconds': sum(a.get('wall_time_seconds', 0) or 0 for a in agents) if completion else None,
                'http_attempts': len(pool_attempts), 'successful_http_attempts': sum(a['state'] == 'success' for a in pool_attempts),
                'error_http_attempts': sum(a['state'] not in ('success', 'in_progress') for a in pool_attempts),
                'logical_generations': len({a['generation_id'] for a in pool_attempts}),
                'reported_cost_usd': sum(cost_values) if cost_values else None, 'cost_report_count': len(cost_values),
                'requested_backend': args['backend'], 'requested_model': args['model'], 'reasoning_effort': args['reasoning_effort'],
                'temperature': args['temperature'], 'top_p': args['top_p'], 'top_k': args['top_k'],
                'max_tokens_config': args['max_tokens'], 'max_context_tokens': args['max_context_tokens'],
                'max_steps': args['max_steps'], 'max_evals': args['max_evals'], 'tool_protocol': args['tool_protocol'],
                'graph_protocol': (result or {}).get('config', {}).get('poolact_protocol'),
                'response_providers': ';'.join(sorted({a['response_provider'] for a in pool_attempts if a['response_provider']})),
                'response_models': ';'.join(sorted({a['response_model'] for a in pool_attempts if a['response_model']}))}
            pools.append(row)
        if model in ('glm', 'kimi', 'qwen', 'deepseek'):
            deployment_path = OPS / 'serving' / model
            if model != 'qwen':
                deployment_path /= 'replica0'
            deployment_path /= 'deployment.json'
            deployment = read(deployment_path)
            info = {'deployment_sha256': sha(deployment_path), 'plan_sha256': deployment['plan_sha256'],
                    'job_id': deployment['job_id'], 'checkpoint_tensor_payloads_rehashed': False,
                    'gpu_count': {'glm': 16, 'kimi': 16, 'qwen': 32, 'deepseek': 8}[model]}
            command = deployment.get('argv') or deployment['rank_commands'][0]['argv']
            command = command[command.index('--model-path'):]
            safe_arguments = {}
            for index, item in enumerate(command):
                if item.startswith('--') and item not in ('--model-path', '--dist-init-addr', '--port', '--host'):
                    if index + 1 < len(command) and not command[index + 1].startswith('--'):
                        value = command[index + 1]
                        if '/' not in value:
                            safe_arguments[item] = value
                    else:
                        safe_arguments[item] = True
            info['serving_arguments_without_network_or_paths'] = safe_arguments
            if model in ('glm', 'kimi'):
                info['checkpoint_metadata_sha256'] = deployment['checkpoint_metadata_sha256']
                info['runtime_input_sha256'] = [{'file': Path(path).name, 'sha256': checksum}
                    for path, checksum in deployment['runtime_input_sha256'].items()]
            elif model == 'qwen':
                identity = read(OPS / 'serving/qwen/IDENTITY.json')
                info.update({key: identity[key] for key in ('checkpoint_metadata', 'runtime_env_sha256', 'launcher_sha256')})
                versions_path = ROOT.parent / 'qwen38_eval_20260910/runtime/versions.json'
                versions = read(versions_path)
                info['runtime_manifest_sha256'] = sha(versions_path)
                info['runtime_versions'] = {key: versions[key] for key in ('python', 'sglang', 'sglang_source_tag_commit', 'torch', 'uv_lock_sha256')}
            else:
                info.update(runtime_manifest_sha256=deployment['runtime_manifest_sha256'],
                            reference_deployment_sha256=deployment['reference_deployment_sha256'])
                versions = read(Path(deployment['runtime_manifest']))
                info['runtime_versions'] = {key: versions[key] for key in ('python', 'sglang_base_commit', 'upstream_effort_patch_commit', 'fixed_distribution_versions')}
            services[model] = info
    assert len(pools) == 97 and len({row['old_slot_id'] for row in pools}) == 97
    csvwrite('pool_run_ledger.csv', pools)
    if attempts:
        csvwrite('request_attempt_ledger.csv', attempts)
    write('request_profiles.json', profiles)
    write('service_versions.json', services)
    summary = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'pools': len(pools),
        'validated_pools': sum(row['status'] == 'validated_complete' for row in pools), 'attempt_records': len(attempts),
        'all_complete': all(row['status'] == 'validated_complete' for row in pools), 'models': {},
        'cost_policy': 'Only sum provider-reported usage.cost across all attempts, including retries. No inference of missing API prices and no GPU-to-USD conversion.',
        'public_projection': 'No prompts/answers/tool text, credentials, response bodies, cluster endpoints or absolute local paths',
        'whole_pool_resampling': False}
    for model in MODELS:
        bound = read(OPS / 'queues-v2' / model / 'BINDINGS.json')
        ids = {row['new_job_id'] for row in bound['jobs']}
        rows = [row for row in pools if row['job_id'] in ids]
        costs = [row['reported_cost_usd'] for row in rows if row['reported_cost_usd'] is not None]
        summary['models'][model] = {'planned': len(rows), 'validated': sum(row['status'] == 'validated_complete' for row in rows),
            'http_attempts': sum(row['http_attempts'] for row in rows), 'reported_cost_usd': sum(costs) if costs else None,
            'error_http_attempts': sum(row['error_http_attempts'] for row in rows)}
    write('USAGE_SUMMARY.json', summary)
    write('MANIFEST.json', {'files': {path.name: {'bytes': path.stat().st_size, 'sha256': sha(path)}
          for path in sorted(OUT.iterdir()) if path.is_file() and path.name != 'MANIFEST.json'},
          'exporter_sha256': sha(Path(__file__)), 'complete': summary['all_complete']})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
