# HPO 全量终答协议重评分

本目录枚举主实验全部 **486 个单智能体 slot、324 个 N4 slot（1,296 个成员）**，合计 **1,782 个成员终答**。逐文件核对采用来源 SHA256，并从最终模型文本重新执行统一终答解析，不只检查先前发现的异常。

本轮采用原 HPO `legacy` 计分规则：完整配置优先匹配本成员已收到的可见 evaluation；不匹配且有可见评估时，使用可见最佳配置回退；没有可见评估记录时才离线评估模型提交的配置。无有效终答保持缺配置，不从隐藏的超预算反馈挑选更优配置。Gap/Gap0 使用冻结 `oracle3.json` 的原定义；正常缺配置仅 Gap0 记零，不伪造 raw performance。

当前全量结果：**1,782 个实际计分终答及分数均不变**；1,771 个成员有有限分数，11 个 DeepSeek N1 缺配置保留。所有有分数的新旧终答还经原 benchmark 独立复算，去重后实际评估 1,461 个配置。NAS 使用历史 NumPy 2.4.6；ParamNet 使用隔离的历史 Python 3.7 / NumPy 1.18.5 / sklearn 0.23.2 worker，避免改变 NAS101 C 的排序语义。

GLM Tight cached NAS101 C 的一个最终文本修复了标签提取；修复后能完整提取模型配置，但该配置未在本成员可见记录中评估，因此新旧仍按同一 legacy 规则回退到可见最佳配置；实际计分配置、分数和评分来源均不变。所有原始分数均保留。

除终答外，还按逐 slot 真实代码来源的 **8 个 source tree** 扫描 **18,093 个 assistant turn**。3 个历史 slot 的中间回复会被新 parser 更早认定为终答：DeepSeek Tight PoolAct NAS101 B repeat 2、GLM Tight PoolAct NAS101 C repeat 0、Qwen Moderate cached NAS101 A repeat 1。它们的现有轨迹离线末端分数虽然不变，但不能据此宣称新运行行为不变，须进入统一版本补跑。此目录 `existing_trace_rescored` 明确不声称修复了历史图共享或反事实决策。

| 文件 | 内容 |
| --- | --- |
| `agent_rows.csv` | 全部 1,782 成员的旧/新终答、分数、Gap、Gap0、评分来源、可见评估来源及 source SHA |
| `slot_metrics.csv` | 全部 810 slot 的旧/新正式指标，N4 分别保留 MI 与 BoN |
| `affected_agents.csv` / `affected_slots.csv` | 提取、评分来源或控制流认定发生变化的样本；不把“分数不变”当作“完全不受影响” |
| `turn_parser_changes.csv` | 原始 runtime parser 与新 parser 的逐 turn 差异及是否改变终止认定 |
| `SOURCE_INVENTORY.csv` | 所有采用原件的路径、字节数、SHA256 |
| `scoring_inputs.jsonl.gz` | 可公开的最小评分输入：终答文本、可见评估记录、旧分数、oracle、来源/数据身份、benchmark 独立测量证书；不含 API header 或完整请求历史 |
| `CHECKS.json` | 当前全量检查、脚本/parser hash、范围与复算边界 |
| `LIGHTWEIGHT_REPLAY_CHECKS.json` | 最小输入包回放与全量 CSV 的逐字节对照 |
| `evaluator_worker_checks.json` | ParamNet 环境及六个冻结 pickle 的校验 |

`old/new_score_complete` 表示历史计分协议下取得有限评分，**不等于模型提交了有效 JSON 配置**：旧版两条非 JSON 输出依约计零；best-visible fallback 也属于完整评分。`old/new_final_present` 指实际计分终答非空，包括回退配置。`new_extracted_answer` 是回退前模型终答；`new_model_final_json_configuration` 只检查其 JSON 对象/数组形态，不冒充完整参数 schema 合法性。行为分析应分别报告这些字段。

## 复算

在仓库根目录，轻量回放不需要原始 trace、模型 API 或完整 benchmark 数据：

```bash
python3 tools/rescore_hpo_protocol.py \
  --inputs results/protocol-repair-20260918/rescore/hpo/scoring_inputs.jsonl.gz \
  --output /tmp/hpo-protocol-replay --verify-benchmarks
```

输入包中的 benchmark 测量证书已绑定配置 hash 和历史 table/dependency identity。此轻量模式复算 parser、可见配置匹配/回退、全部成员与 slot 聚合，并校验测量证书；它**不重新执行外部 benchmark 表**。完整 benchmark 复验需本地冻结数据与原件，运行：

```bash
HPOBENCH_ROOT=/path/to/hpo_tuning/HPOBench \
XDG_DATA_HOME=/path/to/hpo_tuning/hpobench_data \
/path/to/numpy-2.4.6/python tools/rescore_hpo_protocol.py \
  --archive /path/to/paper-ad03e8c-20260916 \
  --source-map /path/to/resolved_sources.json \
  --versions /path/to/hpo_all_slots.csv \
  --paramnet-python /path/to/python3.7-numpy1.18.5-sklearn0.23.2/python \
  --output /tmp/hpo-full-rescore --verify-benchmarks
```

轻量包只保留终答评分必需的文本；18,093 turn 控制流审计在轻量回放时保留为绑定原件 SHA 的审计结果。要独立重做全部 turn 审计，需使用完整原件模式。两种范围在 `CHECKS.json` 中分别列明。
