# A21 离线传输/用量审计

仅处理已封存的 A21 数据，不发网络请求，不执行 runner，不覆盖原件。
从冻结的 scenario v3 collector 最小适配：A21 的 source 在
`manifest.identity.static_acceptance`，四个 harness 文件逐 SHA 绑定；
`execution.json` 没有顶层 source/harness/failed，使用完整 21 job 集合、
逐 job 成功退出、21 traces 和无 unstarted 验证。
实际计时字段是 `elapsed_seconds_including_preflight_resume`。

独立任务重评分、完整 raw/history/prompt 验收与服务排空观察是另行必需证据。
collector 本身不能授权任何新实验，也不把 pilot 成绩纳入正式效果检验。

当前继承的严格传输 PASS 只覆盖全部首试成功的情况。合法的 HTTP 重试仍按
既定客户端策略保留；如果发生，严格 collector FAIL 不等于语义成绩无效，
需要补充全尝试传输/用量审计，不能删重试或重新抽样。缺失 token 字段明确
报错，不生成把未知量补零的汇总。

CPU 测试使用临时合成请求/响应，只借用冻结 A21 manifest 的任务集合及
源码/harness 绑定；不会运行真实计划或改它。测试中 PASS 不是实测传输证据。
