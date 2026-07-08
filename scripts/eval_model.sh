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

MODEL="${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}"
SCENARIO="tuning"
QUESTIONS="0"
TASK="neural_network_training"
BUDGET="cost_tight"
OUTPUT_DIR=""
WITH_AUTO_DATA=0
CONTRACT_NLI_ARCHIVE="${CONTRACT_NLI_ARCHIVE:-}"
MAX_STEPS=""
MAX_EVALS=""
BASE_URL=""
REPS=""
SEED=""
TEMPERATURE=""
LIMIT=""
DRY_RUN=0
SEARCH_DATA_SOURCE="phantom_seed1"
CC_SPLIT="cc-large"

usage() {
  cat <<'EOF'
Usage: bash scripts/eval_model.sh [options] [-- extra run_paper_sweep.py args]

Evaluate one model and write ExpGym traces.

Common options:
  --model MODEL                 OpenRouter/OpenAI-compatible model id.
  --base-url URL                OpenAI-compatible API base URL.
  --scenario NAME               tuning | restricted_search | evidence_audit.
  --task TASK                   Tuning task, e.g. neural_network_training.
  --questions INDICES           Question/doc indices, e.g. 0 or 0:5.
  --budget REGIME               cost_tight | cost_moderate | cost_free.
  --reps N                      Repeat each selected item N times.
  --seed N                      Starting random seed.
  --temperature FLOAT           Sampling temperature.
  --limit N                     Run only the first N planned jobs.
  --output-dir DIR              Trace output directory.
  --with-auto-data              Fetch Phantom Wiki + HPOBench source first.
  --contract-nli-archive PATH   Extract manually downloaded ContractNLI zip.
  --max-steps N                 ReAct step limit.
  --max-evals N                 Tool call limit.
  --dry-run                     Print planned jobs only; no model calls/traces.

Examples:
  OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
  bash scripts/eval_model.sh --model mistralai/mistral-large
  OPENROUTER_API_KEY=dummy bash scripts/eval_model.sh \
    --base-url http://localhost:8000/v1 --model my-local-model
  bash scripts/eval_model.sh --with-auto-data --scenario restricted_search --questions 0:5
EOF
}

EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      MODEL="${2:?--model requires a value}"
      shift 2
      ;;
    --base-url)
      BASE_URL="${2:?--base-url requires a value}"
      shift 2
      ;;
    --scenario)
      SCENARIO="${2:?--scenario requires a value}"
      shift 2
      ;;
    --task)
      TASK="${2:?--task requires a value}"
      shift 2
      ;;
    --questions|--question)
      QUESTIONS="${2:?--questions requires a value}"
      shift 2
      ;;
    --budget|--cost-regime)
      BUDGET="${2:?--budget requires a value}"
      shift 2
      ;;
    --reps)
      REPS="${2:?--reps requires a value}"
      shift 2
      ;;
    --seed)
      SEED="${2:?--seed requires a value}"
      shift 2
      ;;
    --temperature)
      TEMPERATURE="${2:?--temperature requires a value}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:?--limit requires a value}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:?--output-dir requires a value}"
      shift 2
      ;;
    --with-auto-data)
      WITH_AUTO_DATA=1
      shift
      ;;
    --contract-nli-archive)
      CONTRACT_NLI_ARCHIVE="${2:?--contract-nli-archive requires a path}"
      shift 2
      ;;
    --max-steps)
      MAX_STEPS="${2:?--max-steps requires a value}"
      shift 2
      ;;
    --max-evals)
      MAX_EVALS="${2:?--max-evals requires a value}"
      shift 2
      ;;
    --search-data-source)
      SEARCH_DATA_SOURCE="${2:?--search-data-source requires a value}"
      shift 2
      ;;
    --cc-split)
      CC_SPLIT="${2:?--cc-split requires a value}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        EXTRA_ARGS+=("$1")
        shift
      done
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$BASE_URL" ]]; then
  EXTRA_ARGS+=(--base-url "$BASE_URL")
fi

if [[ -z "$OUTPUT_DIR" ]]; then
  MODEL_ALIAS="$(
    MODEL="$MODEL" python - <<'PY'
import os
import re
value = os.environ["MODEL"]
clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "model"
print(clean)
PY
  )"
  OUTPUT_DIR="runs/${MODEL_ALIAS}/${SCENARIO}_${BUDGET}"
fi

CMD=(bash scripts/run_paper_sweep.sh)
if [[ "$WITH_AUTO_DATA" -eq 1 ]]; then
  CMD+=(--with-auto-data)
fi
if [[ -n "$CONTRACT_NLI_ARCHIVE" ]]; then
  CMD+=(--contract-nli-archive "$CONTRACT_NLI_ARCHIVE")
fi

CMD+=(
  --models "$MODEL"
  --scenarios "$SCENARIO"
  --cost-regimes "$BUDGET"
  --output-dir "$OUTPUT_DIR"
  --resume
)

case "$SCENARIO" in
  tuning)
    CMD+=(--tuning-tasks "$TASK")
    if [[ -n "$REPS" ]]; then
      CMD+=(--tuning-reps "$REPS")
    fi
    if [[ -n "$TEMPERATURE" ]]; then
      CMD+=(--temperature-tuning "$TEMPERATURE")
    fi
    ;;
  restricted_search)
    CMD+=(--search-data-source "$SEARCH_DATA_SOURCE" --search-indices "$QUESTIONS")
    if [[ -n "$REPS" ]]; then
      CMD+=(--search-reps "$REPS")
    fi
    if [[ -n "$TEMPERATURE" ]]; then
      CMD+=(--temperature-eval "$TEMPERATURE")
    fi
    ;;
  evidence_audit)
    CMD+=(--cc-split "$CC_SPLIT" --audit-indices "$QUESTIONS")
    if [[ -n "$REPS" ]]; then
      CMD+=(--audit-reps "$REPS")
    fi
    if [[ -n "$TEMPERATURE" ]]; then
      CMD+=(--temperature-eval "$TEMPERATURE")
    fi
    ;;
  *)
    echo "Unknown scenario: $SCENARIO" >&2
    echo "Choose one of: tuning, restricted_search, evidence_audit" >&2
    exit 2
    ;;
esac

if [[ -n "$MAX_STEPS" ]]; then
  CMD+=(--max-steps "$MAX_STEPS")
fi
if [[ -n "$MAX_EVALS" ]]; then
  CMD+=(--max-evals "$MAX_EVALS")
fi
if [[ -n "$SEED" ]]; then
  CMD+=(--seed "$SEED")
fi
if [[ -n "$LIMIT" ]]; then
  CMD+=(--limit "$LIMIT")
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  CMD+=(--dry-run)
fi
if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
  CMD+=("${EXTRA_ARGS[@]}")
fi

printf '[eval] output: %s\n' "$OUTPUT_DIR"
exec "${CMD[@]}"
