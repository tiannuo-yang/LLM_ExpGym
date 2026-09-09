# Attribution and scope of this Kimi-K3 interim report

This directory currently publishes closed Kimi-K3 v5 analysis, audit summaries,
CSV tables and failure indexes. It is a partial formal cohort with eight
infrastructure failures, not a completed two-model study. The 29 controls
mirrors and two additional failure-index originals are identified separately
in BROWSER_FILES.candidate.json; convenience copies are not new samples.

The existing [study attribution](../../ATTRIBUTION.md) preserves dataset author
lists, primary sources, licenses and transformations. In particular, the
[PhantomWiki MIT notice](../../PhantomWiki-MIT.txt) remains part of this study,
and ContractNLI material remains subject to its original CC BY 4.0 terms.
HPO/NAS numerical results and task identities follow the study's pinned local
evaluators; code licenses do not automatically cover external benchmark
assets or surrogate forests. No model weights, credentials, virtual
environments or full benchmark databases are included in this interim leaf.

The exact v5 runtime source is on the separately verified
[source commit](https://github.com/tiannuo-yang/LLM_ExpGym/tree/8dfea72931d952ad90f1c722a83957ab23afc6bf),
with its own attribution. The root code of the results branch is not a
substitute for that source snapshot. The historical supplement's
[additional attribution](../../closed_history_v5_20260909/ATTRIBUTION.md)
records the NATS-Bench/ParamNet provenance caveats that also apply here.

Full raw prompts and tool histories will be delivered separately as original
experimental evidence, including failures. Such material can contain dataset
text and is not endorsed by dataset authors. This notice assigns no new
blanket license or guarantee of suitability to third-party data or upstream
ExpGym/PoolAct code; original terms continue to apply.
