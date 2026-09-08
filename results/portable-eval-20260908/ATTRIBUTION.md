# Data and source attribution

This checkpoint contains experiment traces, prompts, model responses, metadata,
and accepted source snapshots. It does not redistribute model weights, full
benchmark databases, environments, or credentials. Dataset excerpts in prompts
remain subject to their original terms; no blanket new license is asserted over
third-party content.

- ExpGym / PoolAct source: [tiannuo-yang/LLM_ExpGym](https://github.com/tiannuo-yang/LLM_ExpGym), starting commit `703719150e8d44712ace50d6439686423dcd1328`. The local study includes protocol, integrity, and runtime portability changes. The v3 acceptance receipt hashes each included source file; v2 and v3 are distinct snapshots. This checkpoint does not invent a license for the upstream repository, which had no root LICENSE at that commit.
- PhantomWiki v1: Albert Gong, Kamilė Stankevičiūtė, Chao Wan, Anmol Kabra, Raphael Thesmar, Johann Lee, Julius Klenke, Carla P. Gomes, and Kilian Q. Weinberger. *PhantomWiki: On-Demand Datasets for Reasoning and Retrieval Evaluation*. The [official dataset card](https://huggingface.co/datasets/kilian-group/phantom-wiki-v1) identifies the dataset as MIT-licensed; the [project license](https://github.com/kilian-group/phantom-wiki/blob/main/LICENSE) is reproduced in [PhantomWiki-MIT.txt](PhantomWiki-MIT.txt). Names and events in these generated search tasks are synthetic. This study selects fixed question/corpus snapshots, extracts text, and appends agent instructions and tool results; it does not claim those instructions or model answers are original dataset annotations.
- ContractNLI: Yuta Koreeda and Christopher D. Manning. *ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts*, Findings of EMNLP 2021. The [official dataset site](https://stanfordnlp.github.io/contract-nli/) releases the dataset under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with [original license](https://github.com/stanfordnlp/contract-nli/blob/gh-pages/LICENSE). The study uses ExpGym's test-document segmentation and hypothesis labels, reorders selected hypotheses, and adds task instructions, evaluated tool feedback and model-generated decisions; these are study transformations, not revised gold labels. Dataset authors do not endorse this experiment or its conclusions.
- HPOBench / NASBench numerical feedback and task definitions are used through the study's pinned local evaluators; full surrogate models and benchmark tables are not included. Trace metadata identifies the exact task and input/dependency hashes.

Dataset source/attribution pages were checked on 2026-09-08. Raw model output is
retained as experimental evidence, including errors, and is not an endorsement
or independently verified factual account. License references do not guarantee
that every possible downstream use is permitted.
