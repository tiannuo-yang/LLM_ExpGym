# 修复与独立核验记录

这些记录分别固定代码修复、旧轨迹全量重评分和运行适配的核验时点。记录中的“未调用模型”“尚未推送”描述对应检查本身，不能据此将之后的正式补跑也解释成零调用。最终采用状态另见 [总采用清单](../control_flow_adoption/FAIRNESS_MANIFEST.json)，其中分别核验 HPO 与 Search/Audit 控制对照。

- [终答与投票规则](parser_implementation.zh.md)、[逐文件代码冻结](PARSER_CODE_FREEZE.json)：同一提取器供运行与回放使用，Audit、Search 的个体评分和投票共享接受规则。
- [独立终答检查](PARSER_INDEPENDENT_REVIEW.zh.md)：325 项通过；[最终主代码检查日志](parser_full_check_final.log) 为 712 项通过、33 项按可选依赖条件跳过。
- [图身份修复](graph_implementation.zh.md)、[独立图回放](graph_identity_independent.zh.md)：完整配置身份及无歧义可见别名；图共享的原子快照竞争未在此次修复。
- [全量评分独立核验](FINAL_RESCORE_REVIEW.zh.md)、[机器计数](FINAL_RESCORE_VERSION_COUNTS.json)：4,698 个主实验槽全部核对。57 个槽有任意指标变化，41 个槽有任务端点变化，39 个槽有论文主指标变化。上述计数只覆盖旧轨迹重新评分，不含随后 97 个池的运行变化。
- [运行适配源码与检查](runtime/README.zh.md)：117 个源码文件清单，801 项测试通过、5 项跳过；NAS101 A/B/C 实际冻结数据的离线假代理执行通过。
- [队列独立检查](OPS_INDEPENDENT_CHECK.json)：97 个任务配置、身份绑定、失败保留及服务释放守卫；检查使用模拟进程，不调用模型。

核心修复提交为 `0e6c51b6d86f42437038518c2fc8adc510901c0b`；原生运行源码提交为 `ffca5704580b75e254f6e52dd4fe9dff104b1be8`。正式补跑采用后者所保存的独立运行目录，而非将主目录的旧 provider 客户端与新运行代码混用。

部分原始检查脚本记录本地工作目录及归档路径，以保留检查来源。它们不是可随仓库下载的原始轨迹；公开数据的迁移后复算入口见[交付说明](../README.zh.md)。原始 API 请求和完整轨迹继续在本地留档。
