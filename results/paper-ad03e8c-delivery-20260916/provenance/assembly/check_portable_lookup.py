#!/usr/bin/env python3
"""Small real-format restore smoke; only selected API files, never inference."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import tempfile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--delivery', type=Path, required=True)
    args = p.parse_args()
    root = args.delivery.resolve()
    spec = importlib.util.spec_from_file_location('portable_record', root/'tools/find_record.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = list(csv.DictReader((root/'index/selected_slots.csv').open()))
    temp = Path(tempfile.mkdtemp(prefix='expgym-ad03-lookup-'))
    tests = []
    for cohort in ('kimi_original', 'deepseek_original', 'gemini_snapshot'):
        candidates = [r for r in rows if r['cohort_id']==cohort and r['execution_complete']=='True' and int(r['dump_member_count']) > 0]
        if cohort == 'gemini_snapshot':
            index = json.loads((root/'raw_archives/gemini_snapshot/INDEX.json').read_text())
            recovery = next(x['original_root'] for x in index['archive_sets'] if x['kind']=='recovery_v1')
            candidates = [r for r in candidates if r['api_dump_root'].startswith(recovery+'/')]
        # Select by smallest file count for inexpensive format coverage, not score.
        row = min(candidates, key=lambda r: (int(r['dump_member_count']), int(r['dump_bytes']), r['slot_id']))
        members = mod.selected_members(root, row)
        result = mod.restore_dumps(root, row, members, temp/cohort)
        assert result['status']=='PASS'
        tests.append(dict(cohort_id=cohort, slot_id=row['slot_id'], restored_files=result['restored_files'], restored_bytes=result['restored_bytes'], member_names_and_sha256='PASS', format='legacy_data_prefix' if cohort=='kimi_original' else 'modern', selection='fewest dump files, then bytes and slot_id; not performance', verification_scope='selected members only'))
    outcome = dict(status='PASS', tests=tests, restored_files=sum(x['restored_files'] for x in tests), restored_bytes=sum(x['restored_bytes'] for x in tests), local_test_output=str(temp), no_model_calls=True, no_score_changes=True)
    (root/'index/LOOKUP_SMOKE.json').write_text(json.dumps(outcome, indent=2)+'\n')
    print(json.dumps(outcome))


if __name__=='__main__':
    main()
