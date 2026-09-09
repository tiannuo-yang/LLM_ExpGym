# Third-party attribution for this historical supplement

This supplement preserves DEV traces, superseded runs, v5 smoke, source and
control records. It is not a new benchmark dataset or a formal performance
claim. Raw prompts, tool replies and model histories can contain original
dataset text even though no full benchmark database or model weights are
distributed. Model output is retained as unverified experimental evidence.

The existing [study attribution](../ATTRIBUTION.md) retains the author lists,
papers, official sources and transformation descriptions for PhantomWiki and
ContractNLI. [PhantomWiki v1](https://huggingface.co/datasets/kilian-group/phantom-wiki-v1)
is identified as MIT-licensed, including the pinned revision
`9369f9c64655f4e8146afee75ae5d3e3a95d7df5`; its notice is included in
[PhantomWiki-MIT.txt](PhantomWiki-MIT.txt).
[ContractNLI](https://stanfordnlp.github.io/contract-nli/) specifies
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The study selects documents/questions, reorders hypotheses, and adds task
instructions, retrieval/tool feedback and model responses; these are not
revised gold annotations or endorsements by dataset authors.

HPO task definitions and numerical feedback derive from
[HPOBench](https://github.com/automl/HPOBench),
[NAS-Bench-101](https://github.com/google-research/nasbench), and the
[NAS-Bench-201](https://github.com/D-X-Y/NAS-Bench-201) topology space.
The actual NAS201 loader uses NATS-Bench TSS 200-epoch results. ParamNet assets
come from the explicitly pinned `LoneKnightz/HPOlib2` mirror, not asserted to be
official hosting. Exact dependency hashes remain in run/control records.
Code licenses do not automatically cover external tables, surrogate forests,
weights or their underlying datasets.

The separately published source includes two small derived data files; see its
[pinned attribution notice](https://github.com/tiannuo-yang/LLM_ExpGym/blob/8dfea72931d952ad90f1c722a83957ab23afc6bf/ATTRIBUTION.md).
No new license is assigned to the upstream ExpGym/PoolAct code or third-party
content. Original terms continue to apply, and no blanket permission for all
downstream uses or complete privacy clearance is asserted. Official sources
were checked on 2026-09-09 UTC.
