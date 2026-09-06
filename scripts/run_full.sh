#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

PART="all"
BACKEND="${EXPGYM_BACKEND:-}"
MODEL="${EXPGYM_MODEL:-}"
OUTPUT_DIR=""
AGENTS=4
STRATEGIES="naive,cached,poolact"
DRY_RUN=0
NO_BUILD=0
VENV_DIR="${EXPGYM_VENV:-$ROOT_DIR/.venv}"

usage() {
  cat <<'EOF'
Usage: bash scripts/run_full.sh [options]

Run every published task and all three cost regimes for one model. ExpGym and
PoolAct resume verified outputs automatically.

Options:
  --part NAME          all (default) | expgym | poolact
  --backend NAME       sub2api | openrouter | openai | fake
  --model MODEL        One model ID (defaults from the selected backend)
  --output-dir DIR     Repo-relative output root (default: runs/full_<model>)
  --agents N           PoolAct agents (default: 4)
  --strategies LIST    PoolAct strategies (default: naive,cached,poolact)
  --no-build           Reuse the existing HPOBench Docker image
  --dry-run            Print/validate the complete plan; no data/API/Docker calls
  -h, --help           Show this help

The full ExpGym slice for one model is 303 traces:
  9 HPOBench tasks x 3 reps, 35 Search items, 13 Audit items x 3 reps,
  all repeated across cost_free, cost_moderate, and cost_tight.

PoolAct runs the same 9 + 35 + 13 items under all three strategies/regimes;
the N agents are the repeated parallel samples.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --part) PART="${2:?--part requires a value}"; shift 2 ;;
    --backend) BACKEND="${2:?--backend requires a value}"; shift 2 ;;
    --model) MODEL="${2:?--model requires a value}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:?--output-dir requires a value}"; shift 2 ;;
    --agents) AGENTS="${2:?--agents requires a value}"; shift 2 ;;
    --strategies) STRATEGIES="${2:?--strategies requires a value}"; shift 2 ;;
    --no-build) NO_BUILD=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "$PART" in
  all|expgym|poolact) ;;
  *) echo "--part must be all, expgym, or poolact" >&2; exit 2 ;;
esac

case "$BACKEND" in
  ""|sub2api|openrouter|openai|fake) ;;
  *) echo "--backend must be sub2api, openrouter, openai, or fake" >&2; exit 2 ;;
esac

if [[ ! "$AGENTS" =~ ^[1-9][0-9]*$ ]]; then
  echo "--agents must be a positive integer" >&2
  exit 2
fi

if [[ -z "$BACKEND" ]]; then
  if [[ -n "${SUB2API_API_KEY:-}" && -n "${SUB2API_BASE_URL:-}" ]]; then
    BACKEND="sub2api"
  else
    BACKEND="openrouter"
  fi
fi
if [[ -z "$MODEL" ]]; then
  case "$BACKEND" in
    sub2api) MODEL="${SUB2API_MODEL:-gpt-5.3-codex-spark}" ;;
    openai) MODEL="${EXPGYM_OPENAI_MODEL:-gpt-4o-mini}" ;;
    openrouter) MODEL="${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}" ;;
    fake) MODEL="fake" ;;
    *) echo "Unsupported full-run backend: $BACKEND" >&2; exit 2 ;;
  esac
fi

SAFE_MODEL="${MODEL//\//_}"
SAFE_MODEL="${SAFE_MODEL//[^[:alnum:]_.-]/_}"
OUTPUT_DIR="${OUTPUT_DIR:-runs/full_${SAFE_MODEL}}"
if [[ "$OUTPUT_DIR" = /* || "$OUTPUT_DIR" == "." || "$OUTPUT_DIR" == ".." \
      || "$OUTPUT_DIR" == ../* || "$OUTPUT_DIR" == */../* || "$OUTPUT_DIR" == */.. ]]; then
  echo "--output-dir must stay below the repository (Docker shares this path)." >&2
  exit 2
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  EXPGYM_VENV="$VENV_DIR" bash scripts/setup.sh
fi
PY="$VENV_DIR/bin/python"

HPO_TASKS=(
  hpobench:paramnet:adult:steps
  hpobench:paramnet:higgs:steps
  hpobench:paramnet:letter:steps
  hpobench:nasbench101:A
  hpobench:nasbench101:B
  hpobench:nasbench101:C
  hpobench:nasbench201:cifar10-valid
  hpobench:nasbench201:cifar100
  hpobench:nasbench201:imagenet16-120
)
REGIMES=(cost_free cost_moderate cost_tight)

if [[ "$DRY_RUN" -eq 0 ]]; then
  "$PY" -m pip install --disable-pip-version-check --quiet -r requirements-data.txt
  "$PY" scripts/download_data.py
fi

run_expgym() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    "$PY" scripts/run_paper_sweep.py \
      --backend "$BACKEND" --models "$MODEL" \
      --scenarios tuning,restricted_search,evidence_audit \
      --tuning-tasks all-hpobench --search-indices 0:35 --audit-indices 0:13 \
      --cost-regimes cost_free,cost_moderate,cost_tight \
      --tuning-reps 3 --search-reps 1 --audit-reps 3 \
      --output-dir "$OUTPUT_DIR/expgym" --dry-run
    return
  fi

  "$PY" scripts/run_paper_sweep.py \
    --backend "$BACKEND" --models "$MODEL" \
    --scenarios restricted_search,evidence_audit \
    --search-indices 0:35 --audit-indices 0:13 \
    --cost-regimes cost_free,cost_moderate,cost_tight \
    --search-reps 1 --audit-reps 3 \
    --output-dir "$OUTPUT_DIR/expgym" --resume

  docker_args=()
  if [[ "$NO_BUILD" -eq 1 ]]; then
    docker_args+=(--no-build)
  fi
  bash scripts/run_hpobench_docker.sh "${docker_args[@]}" \
    --backend "$BACKEND" --models "$MODEL" \
    --scenarios tuning --tuning-tasks all-hpobench \
    --cost-regimes cost_free,cost_moderate,cost_tight \
    --tuning-reps 3 --output-dir "$OUTPUT_DIR/expgym" --resume
  NO_BUILD=1
}

run_poolact() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'PoolAct full plan: 3 regimes x (9 HPO tasks + 35 Search + 13 Audit), '
    printf 'strategies=%s, agents=%s\n' "$STRATEGIES" "$AGENTS"
  fi

  docker_built=0
  for regime in "${REGIMES[@]}"; do
    common=(
      --backend "$BACKEND" --model "$MODEL" --cost-regime "$regime"
      --strategies "$STRATEGIES" --agents "$AGENTS" --resume
    )
    if [[ "$DRY_RUN" -eq 1 ]]; then
      common+=(--dry-run)
    fi

    "$PY" scripts/run_poolact.py "${common[@]}" \
      --scenario restricted_search --questions 0:35 \
      --output-dir "$OUTPUT_DIR/poolact/$regime/search"
    "$PY" scripts/run_poolact.py "${common[@]}" \
      --scenario evidence_audit --questions 0:13 \
      --output-dir "$OUTPUT_DIR/poolact/$regime/audit"

    for task in "${HPO_TASKS[@]}"; do
      safe_task="${task//:/_}"
      if [[ "$DRY_RUN" -eq 1 ]]; then
        "$PY" scripts/run_poolact.py "${common[@]}" \
          --scenario tuning --tuning-task "$task" \
          --output-dir "$OUTPUT_DIR/poolact/$regime/$safe_task"
        continue
      fi
      docker_args=(--poolact)
      if [[ "$NO_BUILD" -eq 1 || "$docker_built" -eq 1 ]]; then
        docker_args+=(--no-build)
      fi
      bash scripts/run_hpobench_docker.sh "${docker_args[@]}" \
        --backend "$BACKEND" --model "$MODEL" --scenario tuning \
        --tuning-task "$task" --cost-regime "$regime" \
        --strategies "$STRATEGIES" --agents "$AGENTS" \
        --output-dir "$OUTPUT_DIR/poolact/$regime/$safe_task" --resume
      docker_built=1
    done
  done
}

if [[ "$PART" == "all" || "$PART" == "expgym" ]]; then
  run_expgym
fi
if [[ "$PART" == "all" || "$PART" == "poolact" ]]; then
  run_poolact
fi
