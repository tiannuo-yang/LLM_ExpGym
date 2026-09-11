"""Bounded metadata/template/parser checks; never loads model tensors or serves."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise SystemExit("Set CUDA_VISIBLE_DEVICES='' for this CPU-only check")

    import torch
    import sglang
    from transformers import AutoConfig, AutoTokenizer
    from sglang.srt.entrypoints.openai.protocol import Tool
    from sglang.srt.function_call.qwen3_coder_detector import Qwen3CoderDetector
    from sglang.srt.parser.reasoning_parser import ReasoningParser

    config = AutoConfig.from_pretrained(args.checkpoint, local_files_only=True)
    assert config.architectures == ["Qwen3_5MoeForCausalLM"]
    assert config.quantization_config["quant_method"] == "fp8"
    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint, local_files_only=True)
    messages = [{"role": "user", "content": "Reply with the number two."}]
    rendered = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, reasoning_effort="xhigh"
    )
    assert "Reasoning effort is set to xhigh." in rendered
    assert "<|im_start|>assistant" in rendered
    for effort in ("medium", "low"):
        assert tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            reasoning_effort=effort
        )
    rejected = []
    for kwargs in ({"reasoning_effort": "max"}, {"enable_thinking": False}):
        try:
            tokenizer.apply_chat_template(messages, tokenize=False, **kwargs)
        except Exception as exc:
            rejected.append({"input": kwargs, "error": str(exc)})
        else:
            raise AssertionError(f"Expected unsupported template setting: {kwargs}")

    tool_spec = {
        "type": "function",
        "function": {
            "name": "observe",
            "description": "Return a test observation.",
            "parameters": {
                "type": "object",
                "properties": {"trial": {"type": "integer"}},
                "required": ["trial"],
            },
        },
    }
    with_tools = tokenizer.apply_chat_template(
        messages, tools=[tool_spec], tokenize=False, add_generation_prompt=True,
        reasoning_effort="xhigh"
    )
    assert "<function=example_function_name>" in with_tools
    parsed = Qwen3CoderDetector().detect_and_parse(
        "<tool_call>\n<function=observe>\n<parameter=trial>\n2\n"
        "</parameter>\n</function>\n</tool_call>",
        [Tool(**tool_spec)],
    )
    assert len(parsed.calls) == 1
    assert parsed.calls[0].name == "observe"
    assert json.loads(parsed.calls[0].parameters) == {"trial": 2}
    reasoning, final = ReasoningParser(model_type="qwen3").parse_non_stream(
        "<think>Compute one plus one.</think>2"
    )
    assert reasoning.strip() == "Compute one plus one."
    assert final.strip() == "2"
    assert not torch.cuda.is_initialized(), "CPU checks initialized CUDA unexpectedly"

    root = Path(__file__).resolve().parent
    result = {
        "status": "cpu_checks_passed_not_gpu_validation",
        "python": sys.version,
        "sglang": sglang.__version__,
        "sglang_source_tag_commit": "29481685462732237d80d86076d6563e1f658102",
        "torch": torch.__version__,
        "torch_cuda_wheel": torch.version.cuda,
        "cuda_initialized": torch.cuda.is_initialized(),
        "uv_lock_sha256": hashlib.sha256((root / "uv.lock").read_bytes()).hexdigest(),
        "checkpoint": str(args.checkpoint),
        "architecture": config.architectures,
        "model_type": config.model_type,
        "native_quantization": config.quantization_config["quant_method"],
        "checks": [
            "torch_and_sglang_import", "autoconfig_local_metadata", "local_tokenizer",
            "xhigh_medium_low_templates", "unsupported_template_settings_rejected",
            "native_xml_tool_template", "qwen3_coder_typed_tool_parse",
            "qwen3_reasoning_final_split", "no_cuda_context_initialized",
        ],
        "rejected_template_settings": rejected,
        "distributions": dict(sorted(
            (dist.metadata["Name"], dist.version)
            for dist in importlib.metadata.distributions()
        )),
    }
    (root / "versions.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "distributions"}, indent=2))


if __name__ == "__main__":
    main()
