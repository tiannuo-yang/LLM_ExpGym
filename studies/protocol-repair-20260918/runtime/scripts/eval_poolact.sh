#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ``scripts/setup.sh`` creates this environment. Prefer it automatically so
# readers do not have to remember to activate the venv in every new shell.
VENV_DIR="${EXPGYM_VENV:-$ROOT_DIR/.venv}"
if [[ -x "$VENV_DIR/bin/python" ]]; then
  export PATH="$VENV_DIR/bin:$PATH"
fi

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

if [[ -n "${SUB2API_API_KEY:-}" && -n "${SUB2API_BASE_URL:-}" ]]; then
  DEFAULT_BACKEND="sub2api"
else
  DEFAULT_BACKEND="openrouter"
fi

BACKEND="${EXPGYM_BACKEND:-$DEFAULT_BACKEND}"
MODEL="${EXPGYM_MODEL:-}"
SCENARIO="tuning"
TASK="neural_network_training"
QUESTION_INDEX="0"
QUESTION_INDEX_SET=0
QUESTIONS=""
BUDGET="cost_tight"
STRATEGIES="poolact"
AGENTS="2"
OUTPUT_DIR=""
WITH_AUTO_DATA=0
DRY_RUN=0
EXTRA_ARGS=()

usage() {
  cat <<'EOF'
Usage: bash scripts/eval_poolact.sh [options]

Run PoolAct on one item or a batch. The default is a small real two-agent
built-in tuning run. Existing results are resumed automatically.

Common options:
  --backend NAME            openrouter | openai | sub2api | vllm | fake
  --model MODEL             Model or endpoint model ID
  --scenario NAME           tuning | restricted_search | evidence_audit
  --task TASK               Tuning task (default: neural_network_training)
  --question-index N        One search question or audit document index
  --questions INDICES       Batch selector: 0, 0,2,7, or range 0:5
  --budget REGIME           cost_tight | cost_moderate | cost_free
  --strategies LIST         poolact, or naive,cached,poolact
  --agents N                Number of parallel agents (paper default: 4)
  --output-dir DIR          Output directory
  --with-auto-data          Download missing datasets before running
  --dry-run                 Print the resolved run without model calls

Any unrecognized option is forwarded to scripts/run_poolact.py.

Examples:
  bash scripts/eval_poolact.sh --backend fake --agents 2
  OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh
  bash scripts/eval_poolact.sh --with-auto-data \
    --scenario restricted_search --questions 0:5 --agents 4 \
    --strategies naive,cached,poolact
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend) BACKEND="${2:?--backend requires a value}"; shift 2 ;;
    --model) MODEL="${2:?--model requires a value}"; shift 2 ;;
    --scenario) SCENARIO="${2:?--scenario requires a value}"; shift 2 ;;
    --task|--tuning-task) TASK="${2:?--task requires a value}"; shift 2 ;;
    --question-index|--question)
      if [[ -n "$QUESTIONS" ]]; then
        echo "Use either --question-index or --questions, not both." >&2
        exit 2
      fi
      QUESTION_INDEX="${2:?--question-index requires a value}"
      QUESTION_INDEX_SET=1
      shift 2
      ;;
    --questions)
      if [[ "$QUESTION_INDEX_SET" -eq 1 ]]; then
        echo "Use either --question-index or --questions, not both." >&2
        exit 2
      fi
      QUESTIONS="${2:?--questions requires a value}"
      shift 2
      ;;
    --budget|--cost-regime) BUDGET="${2:?--budget requires a value}"; shift 2 ;;
    --strategies) STRATEGIES="${2:?--strategies requires a value}"; shift 2 ;;
    --agents) AGENTS="${2:?--agents requires a value}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:?--output-dir requires a value}"; shift 2 ;;
    --with-auto-data) WITH_AUTO_DATA=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  EXPGYM_VENV="$VENV_DIR" bash scripts/setup.sh
  export PATH="$VENV_DIR/bin:$PATH"
fi
PYTHON_BIN="$VENV_DIR/bin/python"

if [[ -z "$MODEL" ]]; then
  case "$BACKEND" in
    sub2api) MODEL="${SUB2API_MODEL:-gpt-5.4}" ;;
    openai) MODEL="${EXPGYM_OPENAI_MODEL:-gpt-4o-mini}" ;;
    gemini) MODEL="${EXPGYM_GEMINI_MODEL:-gemini-2.5-flash}" ;;
    vllm) MODEL="${EXPGYM_VLLM_MODEL:-local-model}" ;;
    fake) MODEL="fake" ;;
    *) MODEL="${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}" ;;
  esac
fi

if [[ "$WITH_AUTO_DATA" -eq 1 && "$DRY_RUN" -eq 0 ]]; then
  "$PYTHON_BIN" -m pip install --disable-pip-version-check --quiet \
    -r requirements-data.txt
  case "$SCENARIO" in
    restricted_search) "$PYTHON_BIN" scripts/download_data.py --only phantom-wiki ;;
    evidence_audit) "$PYTHON_BIN" scripts/download_data.py --only contract-nli ;;
    tuning)
      if [[ "$TASK" == hpobench:* ]]; then
        "$PYTHON_BIN" scripts/download_data.py --only hpobench
      fi
      ;;
  esac
fi

if [[ -z "$OUTPUT_DIR" ]]; then
  SAFE_MODEL="${MODEL//\//_}"
  ITEM_SUFFIX=""
  if [[ "$SCENARIO" == "tuning" ]]; then
    SAFE_TASK="${TASK//[^[:alnum:]_.-]/_}"
    ITEM_SUFFIX="_${SAFE_TASK}"
  elif [[ -z "$QUESTIONS" ]]; then
    ITEM_SUFFIX="_item${QUESTION_INDEX}"
  fi
  OUTPUT_DIR="runs/${SAFE_MODEL}/poolact_${SCENARIO}${ITEM_SUFFIX}_${BUDGET}"
fi

CMD=(
  "$PYTHON_BIN" scripts/run_poolact.py
  --backend "$BACKEND"
  --model "$MODEL"
  --scenario "$SCENARIO"
  --tuning-task "$TASK"
  --cost-regime "$BUDGET"
  --strategies "$STRATEGIES"
  --agents "$AGENTS"
  --output-dir "$OUTPUT_DIR"
  --resume
)
if [[ -n "$QUESTIONS" ]]; then
  CMD+=(--questions "$QUESTIONS")
else
  CMD+=(--question-index "$QUESTION_INDEX")
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  CMD+=(--dry-run)
fi
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

printf '[poolact] output: %s\n' "$OUTPUT_DIR"
exec "${CMD[@]}"
