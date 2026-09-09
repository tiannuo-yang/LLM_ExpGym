# K3 封存 usage 独立核验

这是非 exporter 作者的一次离线数字核验，不调用或导入 exporter 的 `usage`、AN2、scorer、模型、后端、HTTP、Slurm 或 Git。v1/v2 性能指标比较不在本项范围内；不重跑格式诊断。

输入固定为 ROOT 指定的 K3 plan / execution / seal 与新 v2 EXPORT_INDEX 原字节 SHA。只进一步读取封存 closure / file parts、索引指定的 manifest 和 records、完整 sealed dumps 集合中的请求原件。绝不跟随 gold、oracle、数据集或私钥 refs，也不读取 result/agent/HTTP wire 文件。

原 raw JSON 容器必须整体读取并反序列化，不能声称从磁盘从未读到响应字节；语义检查仅访问身份、state、request seed/model 与 `response_json.usage` 数字字段，不解释或输出 response content、reasoning body、答案或质量。

## 独立规则

- P / C 仅接受原 `prompt_tokens` / `completion_tokens` 的非负严格 int，bool、float、负数、字符串与 null 为 unknown。
- R 接受合法 flat 或 nested reasoning 值：双合法相等只计一次，不同即失败；两者均无合法值为 unknown；有 C 时逐 attempt 要求 R ≤ C。
- 三字段分别保留全部 attempt 分母、known_sum、unknown_attempts、complete_total。任一字段存在 unknown，该字段完整总量为 null。R 是 C 的子集，不与 C 再相加。
- error 也保留原分母；若确有合法 usage 则计入，缺 usage 为 unknown。not_started 的空 sidecar 可以是零，但 record token 端点仍是 null。
- 从 sealed 完整 dumps 路径集、records 明确 path/SHA/request ID、实际文件内部身份和计划唯一 seed owner 建立双射。校验原文件 bytes/SHA、文件名与内部 request ID、client/seed/逻辑归属及 generation attempt 缺口，不以 filename stem 集合代替内容身份核验。
- 全 783 logical 逐字段重算后，对账 sidecar 三字段四项结构和 record 顶层 reasoning、telemetry input/output；不比较 agent ledger 中另存的 token 值。

另独立汇总 AN2 同定义的“完整 record 字段子集”：只求和该字段 complete_total 非 null 的 record。它不等于所有 attempt 的已知部分，也不按质量成功与否筛选；三个字段可以有不同的已知 record 数。本项不读取 AN2 results 的成本或性能值来回填预期。

## 一次执行与产物

生产入口为：

```bash
/lustrefs/users/chufan.shi/codex_space_tn/LLM_ExpGym/.venv/bin/python -B \
  /ABS/k3_post_analysis_usage_review_v1/review_usage.py \
  --actual-output /ABS/k3_post_analysis_usage_review_v1/actual_v1
```

只接受本目录的全新 `actual_v1/`，不重试、resume、删除或覆盖。失败保留已有输出；必须真实 exit 0 且完整 INDEX 对账通过才算本项通过。

四个数据产物：

- `attempts.jsonl`：每次请求的原件 ref、身份、state、三个可空 usage 数和 reasoning 来源分类，无内容正文。
- `logical_usage.json`：每 logical 独立数字、record 端点与匹配状态。
- `SUMMARY.json`：全量分母、状态分账、全部 attempt 已知部分与完整 record 字段子集，以及范围限制。
- `INDEX.json`：另外三个输出的 bytes/SHA。

每原件上限 128 MiB，总读取上限 8 GiB，无自动扩容。每个选定原件只读一次并按 seal SHA/bytes 核对，检查读取前后及最终 stat 稳定；不是恶意并发的原子快照，不证明未封存 HTTP 不存在或今后文件不再变化。所有材料在新目录中，原运行和导出文件不改写。

## 合成验证与验收边界

`test_review_usage.py` 使用手算数据，不读取真实 controls/raw。覆盖合法零、nested、双值去重、单合法候选、各类非法值、冲突、逐请求上限、跨请求不能抵消、字段独立 unknown、error 无 usage、空记录、严格 JSON 与文件/请求身份不一致。

通过仅说明 sealed 请求集合的报告 usage 数字可以独立复算并与 v2 records 一致；不是供应商真实收费、GPU 成本、模型思考质量、服务端 tokenization、性能结论或整个项目最终独立审计的证明。
