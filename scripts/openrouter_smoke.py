#!/usr/bin/env python3
"""Run a real OpenRouter-backed ExpGym smoke test.

This intentionally uses the built-in tuning scenario so the smoke verifies the
LLM -> tool -> observation -> answer path without requiring external datasets.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from expgym.llm_clients import build_openrouter_client
from expgym.react_loop import build_system_prompt, run_react_loop
from expgym.task_tuning import build_tools, describe_parameter_ranges


def _default_key_file() -> Path:
    return Path(
        os.environ.get("OPENROUTER_API_KEY_FILE", REPO_ROOT.parent / "openrouter.key")
    )


def _load_api_key(path: Optional[Path]) -> str:
    env_key = os.environ.get("OPENROUTER_API_KEY")
    if env_key:
        return env_key.strip()
    if path is not None and path.is_file():
        return path.read_text(encoding="utf-8").strip()
    raise SystemExit(
        "OPENROUTER_API_KEY is not set and no key file was found. "
        "Set OPENROUTER_API_KEY or pass --api-key-file PATH."
    )


def _build_context() -> str:
    return "\n".join(
        [
            "Smoke test: verify the complete ExpGym ReAct path with a real LLM call.",
            "Goal: tune the system for high performance.",
            describe_parameter_ranges(),
            (
                "You must do exactly one tool call, then after the Observation "
                "answer with the exact same JSON configuration you evaluated."
            ),
            'Action format: Action: evaluate_config {"param": value, ...}',
            'Answer format: Answer: {"param": value, ...}',
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=os.environ.get("EXPGYM_OPENROUTER_MODEL", "openai/gpt-4.1-nano"),
        help="OpenRouter model ID.",
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=_default_key_file(),
        help="File containing the OpenRouter API key if OPENROUTER_API_KEY is unset.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1206)
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument(
        "--show-trace",
        action="store_true",
        help="Print the full ReAct trace instead of a compact summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = _load_api_key(args.api_key_file)
    system_prompt = build_system_prompt()
    llm = build_openrouter_client(
        api_key=api_key,
        model=args.model,
        system_prompt=system_prompt,
        temperature=args.temperature,
        seed=args.seed,
        max_tokens=args.max_tokens,
        title="ExpGym smoke",
    )
    result = run_react_loop(
        llm=llm,
        tools=build_tools(tuning_task="neural_network_training"),
        max_steps=3,
        max_evals=2,
        context=_build_context(),
        system_prompt=system_prompt,
        include_cost_in_observation=True,
    )

    ok = (
        not result["aborted"]
        and result["api_calls"] >= 2
        and result["evaluations"] >= 1
        and bool(result["answer"])
        and result["answer_perf"] is not None
    )

    print(f"model: {args.model}")
    print(f"aborted: {result['aborted']}")
    print(f"api_calls: {result['api_calls']}")
    print(f"evaluations: {result['evaluations']}")
    print(f"answer_perf: {result['answer_perf']}")
    print(f"prompt_tokens: {result['prompt_tokens']}")
    print(f"completion_tokens: {result['completion_tokens']}")
    print(f"answer: {result['answer']}")

    if args.show_trace or not ok:
        print("\nTrace:")
        for line in result["steps"]:
            print(line)

    if not ok:
        print(
            "\nOpenRouter smoke failed: expected a non-aborted run with at least "
            "one tool evaluation and a scored answer."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
