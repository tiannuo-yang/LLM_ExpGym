# 提供方、设置与原记录的对应关系

目标模型为 [OpenRouter Google Gemini 3.8 Flash](https://openrouter.ai/google/gemini-3.8-flash)，请求 model 为 `google/gemini-3.8-flash`，Chat Completions 地址为 `https://openrouter.ai/api/v1/chat/completions`。提供方固定为 Google AI Studio 标准端点，禁止 fallback，并要求支持所有显式参数。

| 项目 | 旧 Sub2 API Gemini | 本次 OpenRouter |
|---|---|---|
| 推理强度 | `thinkingLevel=medium` | `reasoning.effort=medium`、`exclude=false` |
| 单独 reasoning token budget | 未设置 | 未设置 |
| 温度 / top-p | 1 / 1 | 1 / 1 |
| 输出上限 | 32,768 | 32,768 |
| 每 agent 最大步数 / 评价次数 | 30 / 30 | 30 / 30 |
| 工具协议 / 协议修复次数 | native / 1 | native / 1 |
| N1 上下文 cap | 无客户端 cap | 无客户端 cap |
| N4 上下文 cap | 131,072 | 131,072 |
| 签名历史 | 不可裁剪 | 保留原始 `reasoning_details` 和工具扩展字段，不可裁剪 |
| HPO 终端政策 | legacy | legacy |
| Prompt、工具定义、评分器 | 原 Gemini 实验版本 | 原内容保持；接口格式转换另行记录 |

[OpenRouter 的 reasoning 文档](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens) 说明该 effort 对应 Gemini 的 `thinkingLevel=medium`。相同参数和 prompt 不证明两个服务批次具有完全相同的内部实现、权重状态或推理 token 分配。历史 β10 与新四档预算来自不同提供方及日期，整条曲线不能视作已证明只改变预算的同部署因果对照。

主实验补跑按原槽位 seed 执行：HPO 第三重复为 2208，N4 的四个 agent 为 2208–2211；缺失 Search 池为 2200–2203。Whois N1 sweep 每项为 2200。seed 标签保留，不能据此保证后端确定性。

Whois 题集为 `phantom_seed2` 的 0…19 和 `phantom_seed3` 的 0…18，共 39 题。每题反馈基准费用 300 模拟秒；β=1、5、10、15、20 对应 300、1,500、3,000、4,500、6,000 模拟秒。真实新文章成本为 280–320 秒，因此 β 不是精确的可读文章数量。这不是 API 金额或实际执行超时。

本次代码基于原 Gemini 有效运行时，独立加入 OpenRouter 适配和自定义 β 传递；没有用轻量 main 的较早运行代码冒充此次执行版本。原 Sub2 运行时基线 SHA256 为 `8a58986195c73f5508a2f5810e38921c86f8141671b1a6972c300aa06815723e`；本轮第一版 OpenRouter 运行时 SHA256 为 `ec52a3371945f22ebd9d896a30b7ac8056dd502dd29998693713c5d08dba5ca6`。Sweep 首批 8 项模型交互与评分已完成，但 trace 导出校验拒绝 `custom` 预算；随后仅修复导出层，形成第二个运行时 SHA256 `4302763da1e11463dc1301304966693088927ef797f03104c429137bd6c04b00`。两版 OpenRouter 运行时的模型客户端、prompt、任务、预算和评分代码相同。首批 8 项从保存的完整终态离线恢复，其余 148 项使用第二版本首次执行；恢复与继续执行均按各自来源核验，不能把导出失败描述为模型调用失败或重复采样。
