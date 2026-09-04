#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ``scripts/setup.sh`` creates this environment. Prefer it automatically so
# readers do not have to remember to activate the venv in every new shell.
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  export PATH="$ROOT_DIR/.venv/bin:$PATH"
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
MODEL="${EXPGYM_MODEL:-${SUB2API_MODEL:-${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}}}"
SCENARIO="tuning"
QUESTIONS="0"
TASK="neural_network_training"
BUDGET="cost_tight"
OUTPUT_DIR=""
WITH_AUTO_DATA=0
CONTRACT_NLI_ARCHIVE="${CONTRACT_NLI_ARCHIVE:-}"
MAX_STEPS=""
MAX_EVALS=""
BASE_URL="${EXPGYM_BASE_URL:-${SUB2API_BASE_URL:-}}"
PROMPT_CACHE_KEY="${EXPGYM_PROMPT_CACHE_KEY:-}"
PROMPT_CACHE_SCOPE="${EXPGYM_PROMPT_CACHE_SCOPE:-job}"
TRACE_FORMAT="${EXPGYM_TRACE_FORMAT:-v2}"
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

Data:
  default tuning smoke needs no data.
  restricted_search/evidence_audit need --with-auto-data on first run.
  --with-auto-data calls scripts/download_data.py automatically.

Common options:
  --backend NAME                openrouter | openai | sub2api.
  --model MODEL                 OpenRouter/OpenAI-compatible model id.
  --base-url URL                OpenAI-compatible API base URL.
  --prompt-cache-key KEY        Cache namespace; derives one stable key per job.
  --prompt-cache-scope SCOPE    job (default) | literal | disabled.
  --trace-format FORMAT         v2 (default, normalized) | v1 (legacy).
  --scenario NAME               tuning | restricted_search | evidence_audit.
  --task TASK                   Tuning task, e.g. neural_network_training.
  --questions INDICES           Question/doc indices, e.g. 0 or 0:5.
  --budget REGIME               cost_tight | cost_moderate | cost_free.
  --reps N                      Repeat each selected item N times.
  --seed N                      Starting random seed.
  --temperature FLOAT           Sampling temperature.
  --limit N                     Run only the first N planned jobs.
  --output-dir DIR              Trace output directory.
  --with-auto-data              Fetch all external datasets first.
  --contract-nli-archive PATH   Optional offline ContractNLI zip override.
  --max-steps N                 ReAct step limit.
  --max-evals N                 Tool call limit.
  --dry-run                     Print planned jobs only; no model calls/traces.

Examples:
  OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
  bash scripts/eval_model.sh --model mistralai/mistral-large
  OPENROUTER_API_KEY=dummy bash scripts/eval_model.sh \
    --base-url http://localhost:8000/v1 --model my-local-model
  source /path/to/sub2api/.sub2api-client.env
  bash scripts/eval_model.sh --backend sub2api \
    --prompt-cache-key expgym-task-v1
  bash scripts/eval_model.sh --with-auto-data --scenario restricted_search --questions 0:5
EOF
}

EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend)
      BACKEND="${2:?--backend requires a value}"
      shift 2
      ;;
    --model)
      MODEL="${2:?--model requires a value}"
      shift 2
      ;;
    --base-url)
      BASE_URL="${2:?--base-url requires a value}"
      shift 2
      ;;
    --prompt-cache-key)
      PROMPT_CACHE_KEY="${2:?--prompt-cache-key requires a value}"
      shift 2
      ;;
    --prompt-cache-scope)
      PROMPT_CACHE_SCOPE="${2:?--prompt-cache-scope requires a value}"
      shift 2
      ;;
    --trace-format)
      TRACE_FORMAT="${2:?--trace-format requires a value}"
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
EXTRA_ARGS+=(--prompt-cache-scope "$PROMPT_CACHE_SCOPE")
if [[ -n "$PROMPT_CACHE_KEY" ]]; then
  EXTRA_ARGS+=(--prompt-cache-key "$PROMPT_CACHE_KEY")
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
  RUN_ALIAS="$(
    RUN_NAME="${SCENARIO}_${BUDGET}" python - <<'PY'
import os
import re
value = os.environ["RUN_NAME"]
clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "run"
print(clean)
PY
  )"
  OUTPUT_DIR="runs/${MODEL_ALIAS}/${RUN_ALIAS}"
fi

CMD=(bash scripts/run_paper_sweep.sh)
if [[ "$WITH_AUTO_DATA" -eq 1 ]]; then
  CMD+=(--with-auto-data)
fi
if [[ -n "$CONTRACT_NLI_ARCHIVE" ]]; then
  CMD+=(--contract-nli-archive "$CONTRACT_NLI_ARCHIVE")
fi

CMD+=(
  --backend "$BACKEND"
  --trace-format "$TRACE_FORMAT"
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
