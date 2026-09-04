# LLM_ExpGym

This repository has two parts:

1. **ExpGym** evaluates one agent on expensive-world tasks.
2. **PoolAct** evaluates multiple agents with shared exploration state.

## 1. ExpGym

ExpGym runs ReAct agents on tuning, restricted-search, and evidence-audit tasks.
Every run saves a trace and recomputes its final score.

### Install

Python 3.9 or newer is required.

```bash
git clone https://github.com/tiannuo-yang/LLM_ExpGym.git
cd LLM_ExpGym
bash scripts/setup.sh
```

The setup script creates `.venv`. The run scripts use it automatically, so
you do not need to activate it.

### Configure the API

For OpenRouter, pass the key directly:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_model.sh
```

Or save it once:

```bash
cp .env.example .env
# Add OPENROUTER_API_KEY to .env, then run:
bash scripts/eval_model.sh
```

For a local Sub2API deployment:

```bash
set -a
source /path/to/sub2api/.sub2api-client.env
set +a

bash scripts/eval_model.sh --backend sub2api --model gpt-5.4
```

The same API configuration is used by ExpGym and PoolAct.

### Run ExpGym

The shortest run uses the built-in tuning task and needs no dataset:

```bash
bash scripts/eval_model.sh
```

Run five Search questions:

```bash
bash scripts/eval_model.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:5 \
  --budget cost_tight \
  --output-dir runs/search_5q
```

Run three evidence-audit documents:

```bash
bash scripts/eval_model.sh --with-auto-data \
  --scenario evidence_audit \
  --questions 0:3 \
  --budget cost_tight \
  --output-dir runs/audit_3q
```

`--questions` accepts one item (`0`), a list (`0,2,7`), or a half-open range
(`0:5` means items 0 through 4). Use `--dry-run` to inspect a run without model
calls, and `bash scripts/eval_model.sh --help` for all options.

HPOBench and NASBench use Docker because they require the TensorFlow 1.15
stack:

```bash
bash scripts/run_hpobench_docker.sh --resume \
  --models openai/gpt-4.1-nano \
  --scenarios tuning \
  --tuning-tasks hpobench:paramnet:adult:steps \
  --cost-regimes cost_tight \
  --output-dir runs/hpobench_smoke
```

Full NASBench201 runs need at least 16 GB of Docker memory; 24 GB is safer.

### Read the result

A successful job ends with:

```text
EVALUATION RESULT | ... | answer_perf=... | score_check=ok | trace=...
```

Summarize a result directory with:

```bash
python scripts/summarize_traces.py runs/<result-directory>
```

The primary score is:

| Scenario | `answer_perf` |
|---|---|
| `tuning` | final configuration performance |
| `restricted_search` | name-level F1 |
| `evidence_audit` | label accuracy |

`score_check=ok` means ExpGym successfully recomputed the score from the saved
answer and trace.

## 2. PoolAct

PoolAct runs several agents on the same item. They share cached tool results and
an exploration graph. Reasoning is serialized so each agent sees the latest
graph; independent tool calls still run in parallel.

### Run PoolAct

First run the free functional check. It needs no API key or dataset:

```bash
bash scripts/eval_poolact.sh --backend fake --agents 2
```

Run PoolAct with four real agents:

```bash
OPENROUTER_API_KEY=sk-or-... bash scripts/eval_poolact.sh \
  --model openai/gpt-4.1-nano \
  --agents 4
```

With Sub2API already configured as shown above:

```bash
bash scripts/eval_poolact.sh \
  --backend sub2api \
  --model gpt-5.4 \
  --agents 4
```

Compare `naive`, `cached`, and `poolact` on five Search questions:

```bash
bash scripts/eval_poolact.sh --with-auto-data \
  --scenario restricted_search \
  --questions 0:5 \
  --agents 4 \
  --strategies naive,cached,poolact \
  --output-dir runs/poolact_search_5q
```

The first Search run downloads PhantomWiki. Later runs reuse it, and an
interrupted batch resumes completed items automatically. To run all 35 paper
questions, change `--questions 0:5` to `--questions 0:35`.

For HPOBench/NASBench PoolAct:

```bash
bash scripts/run_hpobench_docker.sh --poolact \
  --agents 4 \
  --strategies naive,cached,poolact
```

Use `bash scripts/eval_poolact.sh --help` for all options.

### Read the result

For one item, each strategy writes `result.json` and one trace per agent. For a
batch, each question has an `item_N/` directory and the top-level `summary.json`
contains the mean score for every strategy.

```bash
python -m json.tool runs/poolact_search_5q/summary.json
```

Aggregation follows the PoolAct paper: tuning uses best-of-N, Search uses a
normalized majority vote, and evidence audit votes on labels and evidence.

See [`docs/poolact.md`](docs/poolact.md) for the algorithm-to-code mapping,
library API, output schema, and implementation details.
