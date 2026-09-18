# 正式修复补跑 runtime

`../runtime` 已冻结为 117 个源文件（1,537,719 字节），供正式 HPO 修复补跑使用。它以既有 Gemini OpenRouter native runtime 为底，保留 GPT Responses、Gemini/Anthropic native、自托管工具协议和历史上下文准入规则。未执行付费模型调用。

- 既有运行身份算法 source SHA：`cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`。
- [完整文件清单](RUNTIME_SOURCE_MANIFEST.json) 另覆盖 configs、tools、requirements、环境声明及 HPO wrapper，避免误把 source_tree 的覆盖范围说成全目录。
- [逐文件来源映射](SOURCE_MAPPING.json)；[native 基线到最终版本完整补丁](patches/native-baseline-to-final.patch)；[正式 parser 最小移植补丁](patches/parser-from-repair-worktree.patch)。
- parser 采用 `final-answer-boundary-v2`；Audit 包装与字段规则采用 `audit-json-wrapper-v2`、`audit-literal-label-legacy-evidence-v2`；Search 采用 `search-name-set-v2`；PoolAct 图采用历史 `paper-graph-lock-v4`，graph 源文件与历史 v4 字节相同。

正式改变限于答案边界、单体与投票共享接受规则、v4 完整配置图身份，以及恢复历史 Qwen/DeepSeek 的 `cache_salt` 参数传递。4 个 provider adapter 保持原字节，prompt、上下文裁剪/不可变历史、请求重试、预算计算保持历史语义。GLM/Kimi 的 queue 最终参数由运营将 `prompt_cache_key` 维持 `None`；Qwen 使用 `cache_salt`。历史不同 provider 的参数省略也保持原样，不代表所有模型计算预算相同。

验证结果：

- [完整单元/集成日志](final_unittest.log)：801 tests，5 skipped，全部通过。跳过项沿用数据/可选依赖条件。初次系统 Python 环境失败与原 snapshot 缺少 publication scanner 的情况已分别改用既有 venv、补入冻结主树的纯源码依赖；未为测试修改评分逻辑。
- [NAS101 ABC 真实数据检查](NAS101_FAKE_E2E.json)：每个 variant 4 个 native fake agent，经实际工具 schema、v4 图、真实表查询、最终答案解析、独立评分与落盘通过；另 3 个 production queue job 在新进程执行和 `--verify-only` 全部通过。NumPy 严格核验为 2.4.6。为了确保 smoke 确实查询有效架构，离线假代理从固定 seed 样本中选择第一个有效配置；这些输出只是测试产物，不是报告实验。
- [独立 invariants 复核](INDEPENDENT_INVARIANTS.zh.md)：4 clients 字节一致、29 函数组 AST 一致、2 组终答 guard 一致、20 个 dummy-transport wire 请求一致、4 个 cache 字段场景通过。[机器结果](independent_invariants.json)。

本地 `runtime/data` 是指向历史冻结数据的声明软链，**不属于公开源码清单**。源码中不含数据、运行结果、pycache 或密钥。测试原件位于 `runtime_build/test_artifacts`，不进入运行源码；正式队列另在 operations 管理。

本机复验（无需调用模型）：

```bash
cd /lustrefs/users/chufan.shi/codex_space_tn/protocol_repair_20260918/runtime
PHANTOM_WIKI_ROOT=/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym_gemini_schema_20260911/data/phantom-wiki PYTHONDONTWRITEBYTECODE=1 /lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/.venv/bin/python -B -m unittest discover -s tests -q
```

`nas101_fake_e2e.py`、`check_independent_invariants.py` 和 `freeze_runtime.py` 是构建目录中的复验入口。NAS101 检查需要一个新的测试输出目录；正式运行前清除/移走测试生成的 runs、budget_sweep_results、pycache，再核验完整清单。公开移植时 data 路径、Python 与 HPO wrapper 的既有本地依赖需按部署目录绑定；生产 source SHA 与完整清单必须保持一致。
