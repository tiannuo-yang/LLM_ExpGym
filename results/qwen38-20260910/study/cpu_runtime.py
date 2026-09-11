"""Study-local CPU launch policy; immutable evaluator data, per-job HPO state."""
import hashlib
import json
import os
from pathlib import Path
import sys

WORKSPACE = Path('/lustrefs/users/chufan.shi/codex_space_tn')
RUN_ROOT = WORKSPACE / 'qwen38_eval_20260910'
SOURCE_REPO = WORKSPACE / 'LLM_ExpGym-qwen38-20260910'
DATA_ROOT = RUN_ROOT / 'data'
ORACLE_SHA256 = 'f6a38069eb6d376a045562e8a17e67e600150c7a7b0ee994e46837679fcdb69e'
PYTHONS = {
    'main': WORKSPACE / 'LLM_ExpGym/.venv/bin/python',
    'hpo': WORKSPACE / 'kimi_k3_eval/data_runtime/.venv-hpo/bin/python',
}
IDENTITY_CODE = ('import json,os,platform,sys; '
                 'print(json.dumps({"executable":sys.executable,'
                 '"version":platform.python_version(),"cwd":os.getcwd(),'
                 '"source_repo":os.environ["EXPGYM_SOURCE_REPO"],'
                 '"data_root":os.environ["EXPGYM_DATA_ROOT"],'
                 '"budget_oracle":os.environ["EXPGYM_VERIFIED_BUDGET_ORACLE"],'
                 '"budget_oracle_sha256":os.environ["EXPGYM_VERIFIED_ORACLE_SHA256"]},sort_keys=True))')


def read_only_probe(arguments):
    reduced = list(arguments)
    while reduced and reduced[0] in ('-B', '-s'):
        reduced = reduced[1:]
    if reduced in (['-h'], ['--help'], ['-V'], ['--version'], ['-VV']):
        return True
    if reduced == ['-c', IDENTITY_CODE]:
        return True
    # Only these known CLIs parse help before loading a scorer. Avoid a generic
    # Python-option parser: -W/-S/-X before -c must not bypass the dump guard.
    if not reduced or reduced[0].startswith('-') or reduced[-1] not in ('-h', '--help'):
        return False
    script = Path(reduced[0])
    if not script.is_absolute():
        script = SOURCE_REPO / script
    return script in {SOURCE_REPO / 'scripts' / name for name in
                      ('run_study_queue.py', 'run_paper_sweep.py', 'run_poolact.py')}


def no_symlinks(path):
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise ValueError('Study runtime paths must not contain symlinks')


def configure_state(dump_value):
    dump = Path(dump_value)
    if not dump.is_absolute() or '..' in dump.parts:
        raise ValueError('EXPGYM_API_DUMP_DIR must be an absolute invocation path')
    try:
        dump.relative_to(RUN_ROOT)
    except ValueError:
        raise ValueError('EXPGYM_API_DUMP_DIR must belong to this Qwen study')
    if dump.parent == RUN_ROOT or dump == RUN_ROOT:
        raise ValueError('EXPGYM_API_DUMP_DIR must identify a per-job namespace')
    no_symlinks(dump)
    state = dump.parent / 'runtime/hpobench'
    config_dir, cache_dir, socket_dir = (state / name for name in ('config', 'cache', 'sockets'))
    for path in (config_dir, cache_dir, socket_dir):
        no_symlinks(path)
        path.mkdir(parents=True, exist_ok=True)
    config = {
        'version': '0.0.10', 'verbosity': 0,
        'cache_dir': str(cache_dir),
        'data_dir': str(DATA_ROOT / 'hpo_tuning/hpobench_data'),
        'socket_dir': str(socket_dir),
        'container_dir': str(cache_dir / ('hpobench-' + str(os.getuid()))),
        'container_source': 'oras://gitlab.tf.uni-freiburg.de:5050/muelleph/hpobench-registry',
        'pyro_connect_max_wait': 400,
    }
    body = json.dumps(config, indent=2, sort_keys=True) + '\n'
    config_path = config_dir / '.hpobenchrc'
    if config_path.is_symlink():
        raise ValueError('Study HPOBench configuration must not be a symlink')
    try:
        with config_path.open('x', encoding='utf-8') as handle:
            handle.write(body)
    except FileExistsError:
        if config_path.read_text(encoding='utf-8') != body:
            raise ValueError('Invocation HPOBench configuration changed; refusing to overwrite it')
    return {'XDG_CONFIG_HOME': str(config_dir), 'XDG_CACHE_HOME': str(cache_dir),
            'TMPDIR': str(socket_dir)}


def main(kind):
    python = PYTHONS[kind]
    arguments = list(sys.argv[1:])
    if not python.is_file() or not SOURCE_REPO.is_dir() or not DATA_ROOT.is_dir():
        raise SystemExit('Pinned CPU interpreter, study source, and data must already exist')
    # The current tracked budget loader and evaluator identity deliberately read
    # repo/data. Verify it equals the frozen external input; never silently use
    # the loader's missing-oracle fallback. This is only a 28 KiB read per job.
    budget_oracle = SOURCE_REPO / 'data/hpo_tuning/oracle3.json'
    for oracle in (budget_oracle, DATA_ROOT / 'hpo_tuning/oracle3.json'):
        if not oracle.is_file() or hashlib.sha256(oracle.read_bytes()).hexdigest() != ORACLE_SHA256:
            raise SystemExit('Required budget oracle is missing or differs from the frozen study input')
    dedicated_probe = arguments == ['--expgym-runtime-identity']
    if dedicated_probe:
        arguments = ['-c', IDENTITY_CODE]
    environment = {
        'EXPGYM_SOURCE_REPO': str(SOURCE_REPO), 'EXPGYM_DATA_ROOT': str(DATA_ROOT),
        'EXPGYM_VERIFIED_BUDGET_ORACLE': str(budget_oracle.resolve()),
        'EXPGYM_VERIFIED_ORACLE_SHA256': ORACLE_SHA256,
        'PHANTOM_WIKI_ROOT': str(DATA_ROOT / 'phantom-wiki'),
        'HPOBENCH_ROOT': str(DATA_ROOT / 'hpo_tuning/HPOBench'),
        'XDG_DATA_HOME': str(DATA_ROOT / 'hpo_tuning/hpobench_data'),
        'PYTHONPATH': os.pathsep.join((str(SOURCE_REPO), str(DATA_ROOT / 'hpo_tuning/HPOBench'))),
        'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
        'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
        'HF_HUB_OFFLINE': '1', 'HF_DATASETS_OFFLINE': '1',
        # This local unauthenticated service must never inherit another study's
        # ambient API credential. This wrapper is intentionally no-auth-only:
        # these runners prefer the environment over --api-key-file.
        'OPENAI_API_KEY': 'EXPGYM_LOCAL_NOAUTH_PLACEHOLDER_20260907',
    }
    dump = os.environ.get('EXPGYM_API_DUMP_DIR')
    probe = read_only_probe(arguments)
    try:
        if dump and not probe:
            environment.update(configure_state(dump))
        elif kind == 'hpo' and not probe:
            raise ValueError('EXPGYM_API_DUMP_DIR must identify this invocation\'s absolute dump directory')
        else:
            # Help, planning and stdlib identity have no mutable global fallback.
            # Accidentally loading HPOBench without a job namespace fails against
            # the frozen data tree rather than writing into another study's state.
            disabled = DATA_ROOT / '__runtime_requires_job_dump__'
            environment.update({'XDG_CONFIG_HOME': str(disabled / 'config'),
                                'XDG_CACHE_HOME': str(disabled / 'cache'),
                                'TMPDIR': str(disabled / 'sockets')})
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc))
    os.environ.update(environment)
    os.chdir(str(SOURCE_REPO))
    os.execv(str(python), [str(python)] + arguments)
