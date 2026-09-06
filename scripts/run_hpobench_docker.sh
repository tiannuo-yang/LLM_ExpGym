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

IMAGE="${EXPGYM_HPOBENCH_IMAGE:-expgym-hpobench:py37}"
PLATFORM="${EXPGYM_HPOBENCH_PLATFORM:-linux/amd64}"
DOCKER_BIN="${DOCKER:-}"
BUILD_IMAGE=1
POOLACT_MODE=0
RUNNER_ARGS=()

usage() {
  cat <<'EOF'
Usage: bash scripts/run_hpobench_docker.sh [wrapper options] [runner options]

Builds/runs a linux/amd64 Python 3.7 image for the pinned HPOBench ParamNet
models. NASBench101/201 use verified compact tables generated during setup.

Wrapper options:
  --no-build       Use the existing Docker image instead of building first.
  --image NAME     Docker image tag (default: expgym-hpobench:py37).
  --poolact        Run scripts/run_poolact.py instead of the sequential sweep.
  -h, --help       Show this help.

If no runner options are provided, this runs one ParamNet smoke:
  --models openai/gpt-4.1-nano
  --scenarios tuning
  --tuning-tasks hpobench:paramnet:adult:steps
  --cost-regimes cost_tight

With --poolact, the default smoke instead uses:
  --model openai/gpt-4.1-nano
  --scenario tuning
  --tuning-task hpobench:paramnet:adult:steps
  --cost-regime cost_tight
  --agents 2 --strategies poolact

The container stores verified HPOBench data under:
  data/hpo_tuning/hpobench_data/
  data/hpo_tuning/hpobench_cache/

Docker setup:
  Linux: install/start Docker Engine.
  macOS: install/start Docker Desktop.
  Windows: install/start Docker Desktop with WSL2, then run this script from WSL.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      BUILD_IMAGE=0
      shift
      ;;
    --image)
      IMAGE="${2:?--image requires a value}"
      shift 2
      ;;
    --poolact)
      POOLACT_MODE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      RUNNER_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ "$POOLACT_MODE" -eq 1 ]]; then
  POOLACT_DEFAULT_ARGS=(
    --backend openrouter
    --model "${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}"
    --scenario tuning
    --tuning-task hpobench:paramnet:adult:steps
    --cost-regime cost_tight
    --agents 2
    --strategies poolact
    --output-dir runs/hpobench_poolact
    --resume
  )
  # User arguments come last, so normal argparse options override defaults.
  RUNNER_ARGS=("${POOLACT_DEFAULT_ARGS[@]}" "${RUNNER_ARGS[@]}")
elif [[ ${#RUNNER_ARGS[@]} -eq 0 ]]; then
  RUNNER_ARGS=(
    --models "${EXPGYM_OPENROUTER_MODEL:-openai/gpt-4.1-nano}"
    --scenarios tuning
    --tuning-tasks hpobench:paramnet:adult:steps
    --cost-regimes cost_tight
    --output-dir budget_sweep_results/hpobench_docker
    --resume
  )
fi

if [[ -z "$DOCKER_BIN" ]]; then
  if [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
    DOCKER_BIN="/Applications/Docker.app/Contents/Resources/bin/docker"
    export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
  elif command -v docker >/dev/null 2>&1; then
    DOCKER_BIN="$(command -v docker)"
  fi
fi

if [[ -z "$DOCKER_BIN" ]]; then
  cat >&2 <<'EOF'
Docker is not installed or not on PATH.

Install/start Docker Engine on Linux, Docker Desktop on macOS, or Docker Desktop
with WSL2 on Windows. On Windows, rerun this script from the WSL shell.
Apple Silicon and Windows-on-Arm are supported through linux/amd64 emulation,
but full NASBench runs will be slower than native Linux/x86_64.
EOF
  exit 1
fi

if ! "$DOCKER_BIN" info >/dev/null 2>&1; then
  echo "Docker is installed but the daemon is not running. Start Docker Desktop and rerun." >&2
  exit 1
fi

if [[ "$BUILD_IMAGE" -eq 1 ]]; then
  "$DOCKER_BIN" build \
    --platform "$PLATFORM" \
    -f "$ROOT_DIR/docker/hpobench/Dockerfile" \
    -t "$IMAGE" \
    "$ROOT_DIR"
fi

mkdir -p "$ROOT_DIR/data/hpo_tuning/hpobench_data" "$ROOT_DIR/data/hpo_tuning/hpobench_cache"

DOCKER_ENV=(
  -e HPOBENCH_ROOT=/opt/HPOBench
  -e PYTHONNOUSERSITE=1
  -e XDG_DATA_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_data
  -e XDG_CACHE_HOME=/workspace/LLM_ExpGym/data/hpo_tuning/hpobench_cache
)
DOCKER_MOUNTS=(
  -v "$ROOT_DIR:/workspace/LLM_ExpGym"
)

RUN_BACKEND="${EXPGYM_BACKEND:-openrouter}"
for ((i = 0; i < ${#RUNNER_ARGS[@]}; i++)); do
  if [[ "${RUNNER_ARGS[$i]}" == "--backend" && $((i + 1)) -lt ${#RUNNER_ARGS[@]} ]]; then
    RUN_BACKEND="${RUNNER_ARGS[$((i + 1))]}"
  fi
done

case "$RUN_BACKEND" in
  sub2api)
    if [[ -z "${SUB2API_API_KEY:-}" ]]; then
      echo "SUB2API_API_KEY is required for --backend sub2api." >&2
      exit 1
    fi
    DOCKER_ENV+=(-e SUB2API_API_KEY)
    if [[ -n "${SUB2API_BASE_URL:-}" ]]; then
      DOCKER_SUB2API_BASE_URL="${SUB2API_BASE_URL/127.0.0.1/host.docker.internal}"
      DOCKER_SUB2API_BASE_URL="${DOCKER_SUB2API_BASE_URL/localhost/host.docker.internal}"
      DOCKER_ENV+=(-e "SUB2API_BASE_URL=$DOCKER_SUB2API_BASE_URL")
    fi
    if [[ -n "${SUB2API_MODEL:-}" ]]; then
      DOCKER_ENV+=(-e SUB2API_MODEL)
    fi
    ;;
  openai)
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
      echo "OPENAI_API_KEY is required for --backend openai." >&2
      exit 1
    fi
    DOCKER_ENV+=(-e OPENAI_API_KEY)
    ;;
  fake)
    ;;
  openrouter)
    if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
      DOCKER_ENV+=(-e OPENROUTER_API_KEY)
    else
      KEY_FILE="${OPENROUTER_API_KEY_FILE:-"$ROOT_DIR/../openrouter.key"}"
      if [[ ! -f "$KEY_FILE" ]]; then
        echo "OPENROUTER_API_KEY is unset and key file was not found: $KEY_FILE" >&2
        echo "Set OPENROUTER_API_KEY or OPENROUTER_API_KEY_FILE." >&2
        exit 1
      fi
      KEY_FILE_ABS="$(cd "$(dirname "$KEY_FILE")" && pwd)/$(basename "$KEY_FILE")"
      DOCKER_MOUNTS+=(-v "$KEY_FILE_ABS:/workspace/openrouter.key:ro")
      DOCKER_ENV+=(-e OPENROUTER_API_KEY_FILE=/workspace/openrouter.key)
    fi
    ;;
  *)
    echo "Docker HPOBench does not support backend: $RUN_BACKEND" >&2
    exit 2
    ;;
esac

if [[ "$POOLACT_MODE" -eq 1 ]]; then
  RUNNER_SCRIPT="scripts/run_poolact.py"
else
  RUNNER_SCRIPT="scripts/run_paper_sweep.py"
fi

"$DOCKER_BIN" run --rm \
  --platform "$PLATFORM" \
  --add-host host.docker.internal:host-gateway \
  "${DOCKER_ENV[@]}" \
  "${DOCKER_MOUNTS[@]}" \
  -w /workspace/LLM_ExpGym \
  "$IMAGE" \
  python "$RUNNER_SCRIPT" "${RUNNER_ARGS[@]}"
