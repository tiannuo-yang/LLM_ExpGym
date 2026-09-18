# HPO 重跑收集器独立审查

独立审查通过。检查源码 SHA256 为 `55e9e8c044d23942827b51eb4ce4f574cced488e611c67f86aeb30f2bd8ecfff`；本报告只覆盖 **97 个 HPO 对照的收集阶段**，不宣称整个实验已正式采用。整体正式采用还须合并额外 Search/Audit 控流对照并通过总验收。

## 实际验证

- 全部 97 个预注册 slot/job 绑定通过，模型数量和四成员设计保持一致。
- 固定快照完整验证 **97 池、388 成员**，每个完成池的成员来自同一个新 invocation，未拼池。全部 97 池通过 HPO 阶段门禁，合并保留 4,601 条非替换结果，形成 4,698 条主结果。
- 0 项未完成指标的新分数及变化量全为空，没有补零。
- **22 个边界测试通过**：错 slot、参数与哈希身份漂移、缺失／重复成员、异 invocation 成员、重复 API client、错 seed／源码树／数据哈希、非终态回复被漏当终答均拒绝；复制完整收据及文件可通过，删除成员文件后收据和运行时磁盘验证均拒绝。
- 正常 1 个或 4 个成员缺终答可接受，保留科学值 None；Gap0 按原协议处理。选择实际可见但更差的配置仍可通过，不按提升幅度筛结果。
- **11 个公式边界场景、8 个答案选择场景通过**；对这 97 池的逐成员选择及六项池指标独立复算一致，含 2 个真实零分和 0 个实际缺失终答。
- 真实结果共检查 2948 个 assistant turns，非终态却应被接受为终答的遗漏为 0。

详见 [CHECKS.json](CHECKS.json)、[BOUNDARY_TESTS.json](BOUNDARY_TESTS.json)、[SCORE_FORMULA_REVIEW.json](SCORE_FORMULA_REVIEW.json)。

## 审查中修复的问题

1. 原收集器将聚合答案中的空字符串和成员原始 None 直接比较，误拒正常无终答。现仅对聚合展示表示做归一，成员值与严格 MI/BoN 仍保留 None。
2. 原绑定验证遗漏有效参数与哈希身份中的 model/backend/base_url/api_protocol 对照。现全字段核对，仅允许明确的输出目录、重复控制和 cache namespace 派生。
3. 原成员检查缺少 invocation/client 身份约束。现每个成员的 api_dump.run_id 必须匹配该 job，且四个 client ID 互异。

严格 MI/BoN 遇任一不可评分成员即为空；Gap0 仅对正常缺终答使用零，基础设施失败和待运行均不赋分。Gap 先对每个成员做下界截断再取均值，真实零分不是缺失。公式验证器保留离线证书原有原因标签；证书回放不冒充重新执行 benchmark。

另审阅了正式输出防陈旧处理、旧来源指针归档、HPO 阶段范围声明和收集期间源码不变检查。最终额外控流对照组合仍需执行总采用验收；本报告不提前替代该环节。

## 复算与范围

[check_collector_boundaries.py](check_collector_boundaries.py) 使用完整本地工作区与隔离临时副本，原运行文件未改。合成内存用例仅为检查收集器自身边界而跳过磁盘结果相等比较；真实回放及隔离删除成员文件用例另行验证收据／磁盘门禁。

[score_formula_review.py](score_formula_review.py) 支持 `--repo /path/to/public-repo --package /path/to/scoring_inputs.jsonl.gz --output /tmp/hpo-formula-review.json`；可另设 `--runtime /path/to/runtime-code`，默认使用 `--repo`。显式传参后只需公开代码与评分包，不依赖原工作区、Git 元数据或私有 benchmark 表；oracle reference 从包内读取。若单独复制该脚本且相邻 collector 源码不存在，公式仍可复核，但 collector 源码表达式检查会明确标为未执行。

本报告使用一次固定的本地 replay/ 快照，避免运行队列持续增长改变分母；该中间目录不属于公开交付。当前评分 helper SHA256 为 `5534e0df2d131e6131af1c82800bc4ee2b7fc4be96472bb72b356a46a33405a9`，公式脚本、评分包和各结果文件的校验值均写入 CHECKS.json。公开评分包和通用回放脚本由上级交付提供。

以上检查未调用模型或 API，未修改生产结果。


## 发布端点投影说明

本目录的CHECKS、公式复核和边界测试保留原始冻结审查身份，指向投影前的科学包和原replayer源码。公开发布随后仅把三个工件中的私有端点变为opaque SHA标识，未修改本目录的原始审查hash。请结合上级PUBLIC_ENDPOINT_PROJECTION.json与ORIGINAL_PUBLIC_REPLAY_CHECKS.json核对原件身份；投影后的实际公开回放结果见上级PUBLIC_REPLAY_CHECKS.json。原审查不冒充新投影脚本的边界测试，投影另有发布阶段的独立字段差异和篡改拒绝检查。
