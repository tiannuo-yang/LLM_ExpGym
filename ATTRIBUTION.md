# Third-party data and source attribution

This notice supplements the portable v5 source snapshot at commit
`9976ce741fab675435d6588ee1e70e29b14fcaea`. It does not change the frozen
experiment implementation, settings, or results, and does not assign a new
license to ExpGym/PoolAct or third-party assets.

- **ExpGym / PoolAct:** [upstream repository](https://github.com/tiannuo-yang/LLM_ExpGym), initial study revision `703719150e8d44712ace50d6439686423dcd1328`. That revision did not contain a root LICENSE. This branch adds protocol, integrity, prompt-blinding and runtime-portability changes; data licenses below are not licenses for the repository code.
- **PhantomWiki v1:** Albert Gong, Kamilė Stankevičiūtė, Chao Wan, Anmol Kabra, Raphael Thesmar, Johann Lee, Julius Klenke, Carla P. Gomes and Kilian Q. Weinberger, *PhantomWiki: On-Demand Datasets for Reasoning and Retrieval Evaluation*. The [official dataset card](https://huggingface.co/datasets/kilian-group/phantom-wiki-v1) and the pinned revision `9369f9c64655f4e8146afee75ae5d3e3a95d7df5` identify MIT licensing; the original notice is retained in [PhantomWiki-MIT.txt](PhantomWiki-MIT.txt). The study selects fixed question/corpus snapshots and adds instructions, retrieval context and model responses.
- **ContractNLI:** Yuta Koreeda and Christopher D. Manning, *ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts*, Findings of EMNLP 2021. The [official dataset site](https://stanfordnlp.github.io/contract-nli/) specifies [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and links its original license. This source snapshot includes the 5,545-byte derived `data/contract-nli/test_nda_span_dims.json`; experiments select test-document segments, reorder hypotheses, and append tool feedback and model decisions. These transformations are not revised gold annotations, and dataset authors do not endorse this study.
- **HPO / NAS:** [HPOBench](https://github.com/automl/HPOBench), [NAS-Bench-101](https://github.com/google-research/nasbench), and [NAS-Bench-201](https://github.com/D-X-Y/NAS-Bench-201) provide the benchmark interfaces and task definitions. The source includes 28,814 bytes of derived oracle metadata in `data/hpo_tuning/oracle3.json`. The actual NAS201 loader uses [NATS-Bench TSS](https://github.com/D-X-Y/NATS-Bench), with 200-epoch results. The ParamNet downloader uses the explicitly pinned `LoneKnightz/HPOlib2@de88ab3aa2a39a86ccf8c85e9069f3441c1cfc61` mirror; it is not represented as official hosting. Code licenses do not automatically license external tables, surrogate forests, weights, or underlying datasets.

Full benchmark databases, model weights, environments and credentials are not
included in this source snapshot. The two small derived files above are data;
separately published raw prompts and tool replies can also contain dataset
excerpts and remain subject to their original terms. Model outputs are retained
as unverified experimental records, not author-endorsed annotations. No blanket
permission for all downstream uses is asserted. Official attribution sources
were checked on 2026-09-09 UTC.
