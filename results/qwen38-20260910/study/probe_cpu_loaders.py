"""Small offline CPU loader/oracle probe; never a model experiment."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import socket
import sys
from types import SimpleNamespace
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=('main', 'hpo'), required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()

    def forbidden_network(*unused, **kwargs):
        raise AssertionError('Offline CPU probe must not open a network connection')
    urllib.request.urlopen = forbidden_network
    socket.create_connection = forbidden_network
    socket.socket.connect = forbidden_network
    try:
        import requests
        requests.sessions.Session.request = forbidden_network
    except ImportError:
        pass

    from expgym import task_tuning
    from demo_experiment import resolve_base_cost, resolve_cost_regime
    data = Path(os.environ['EXPGYM_DATA_ROOT'])
    repo = Path(os.environ['EXPGYM_SOURCE_REPO'])
    assert Path(task_tuning.__file__).resolve().parent == repo / 'expgym'
    assert Path(task_tuning.HPOBENCH_ROOT).resolve() == data / 'hpo_tuning/HPOBench'
    oracle = json.loads((data / 'hpo_tuning/oracle3.json').read_text())['tasks']
    tasks = (['hpobench:paramnet:' + name + ':steps' for name in ('adult', 'higgs', 'letter')]
             if args.family == 'hpo' else
             ['hpobench:nasbench101:' + name for name in ('A', 'B', 'C')] +
             ['hpobench:nasbench201:' + name for name in ('cifar10-valid', 'cifar100', 'imagenet16-120')])
    result = {'scope': 'Offline CPU data/oracle probe; no model calls or GPU work',
              'family': args.family, 'python_version': platform.python_version(),
              'python_executable': sys.executable, 'source_repo': str(repo),
              'data_root': str(data), 'task_tuning_source': task_tuning.__file__,
              'hpobench_source': task_tuning.HPOBENCH_ROOT,
              'budget_oracle': os.environ['EXPGYM_VERIFIED_BUDGET_ORACLE'],
              'budget_oracle_sha256': os.environ['EXPGYM_VERIFIED_ORACLE_SHA256'],
              'hpo_config': str(Path(os.environ['XDG_CONFIG_HOME']) / '.hpobenchrc'),
              'hpo_table_root': os.environ['XDG_DATA_HOME'], 'tasks': []}
    for name in tasks:
        expected = oracle[name]
        task = task_tuning._load_hpobench(name)
        value, cost = task_tuning._hpobench_evaluate(task, expected['best_config'])
        assert math.isclose(value, expected['best_perf'], rel_tol=1e-10, abs_tol=1e-10), name
        assert math.isclose(cost, expected['best_cost'], rel_tol=1e-8, abs_tol=1e-6), name
        assert task.fidelity == expected['fidelity'], name
        base = resolve_base_cost('tuning', SimpleNamespace(tuning_task=name))
        assert base == float(expected['best_cost']), name
        for regime, multiplier in (('cost_free', None), ('cost_moderate', 10), ('cost_tight', 3)):
            budget, unused = resolve_cost_regime(SimpleNamespace(cost_regime=regime), base)
            assert budget == (None if multiplier is None else multiplier * base), name
        result['tasks'].append({'task': name, 'score': value, 'cost': cost,
                                'fidelity': task.fidelity, 'oracle_and_budgets_match': True})
    if args.family == 'main':
        from expgym import task_restricted_search as search, task_evidence_audit as audit
        import pyarrow.parquet as parquet
        result['search'] = []
        for seed, total in ((2, 36), (3, 37)):
            qa = search._load_qa(seed)
            corpus = search._load_corpus(seed)
            assert len(qa) == total
            # size_5000 is the generator size, not the article row count: the
            # frozen seed2/3 files contain 5029/5039 unique article rows.
            corpus_path = Path(search.CORPUS_DIR) / ('depth_20_size_5000_seed_%d-00000-of-00001.parquet' % seed)
            assert len(corpus) == parquet.read_metadata(str(corpus_path)).num_rows
            assert len(corpus) > 0
            result['search'].append({'seed': seed, 'questions': len(qa), 'articles': len(corpus),
                                     'qa_directory': search.QA_DIR, 'corpus_directory': search.CORPUS_DIR})
        expected_docs = [1, 2, 4, 5, 6, 8, 11, 18, 21, 22, 23, 24, 25]
        docs = [audit._get_doc(index) for index in range(13)]
        assert [doc.doc_id for doc in docs] == expected_docs
        assert all(doc.segments and doc.annotations for doc in docs)
        assert set(expected_docs).issubset(audit._load_hints())
        assert Path(audit.EVIDENCE_PATH).resolve() == data / 'contract-nli/test_segments.json'
        assert Path(audit.HINTS_PATH).resolve() == data / 'contract-nli/test_nda_span_dims.json'
        result['audit'] = {'selected_doc_ids': expected_docs, 'split': 'cc-large',
                           'hypotheses': len(audit._get_labels('cc-large')),
                           'evidence_path': audit.EVIDENCE_PATH, 'hints_path': audit.HINTS_PATH}
    result['passed'] = True
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write('\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
