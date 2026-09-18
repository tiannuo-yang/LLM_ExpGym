# Native runtime 独立一致性检查

检查对象：`protocol_repair_20260918/runtime`；历史基线：`gemini_openrouter_20260917/runtime-sweep-v2`。采用逐字节、AST 与离线 dummy transport 检查，没有模型调用、网络请求或真实凭据读取。

当前源码树 SHA-256：`cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`。最终机器结果见 `independent_invariants.json`。

| 检查 | 结果 |
|---|---|
| Native Gemini、OpenRouter Gemini、Responses、Anthropic 4 客户端 | 全文件逐字节相同 |
| Prompt、工具 schema、budget、采样/effort 构建、上下文与 cache namespace | 29 个命名函数组 AST 相同 |
| 自然回答 finish/tool guards、强制回答 tool/finish guards | 对应代码段逐字节相同 |
| Native immutable history | 保留原 admission cap；未转为截断 signed/encrypted history |
| 5 类 client × 2 cache key 状态 × 2 tool_choice 状态 | 20 个实际构造请求的 URL/body 与历史基线全等 |
| 兼容 Chat transport 的 cache 字段 | 4 case：None 两种字段均不发；非空只发指定字段 |
| 数据与凭据 | 源目录无数据文件、凭据命名文件或真实 token 形状；只允许已声明固定 data 外部挂载 |

本轮有意变更的最终答案提取、Audit/Search 接受规则和 graph v4 不属于“保持不变”的断言。`react_loop.py` 的 native 自然终答和强制终答均转入 `parse_final_answer`，原先先判截断/工具调用的 guard 顺序保留。文本自然终答继续使用 `allow_unlabelled=False`。

OpenRouter Gemini 的固定 provider 路由、medium 默认 thinking 映射、原始 reasoning_details 保留、无 prompt transforms，以及 Responses 原有参数省略语义均保留。这证明与所选历史运行协议相同，不表示所有模型拥有相同 provider 计算预算。

外部 `data` 软链是正式本地运行挂载，目标固定为 `LLM_ExpGym_gemini_schema_20260911/data`，不得随公开源码复制。测试输出/pycache 的最终清理状态以 JSON 为准，`--require-clean` 会拒绝这类文件。凭据检测结合白名单源复制、文件名及常见 token 形状检查，不声称能证明任意伪装内容均不存在。

`source_tree_sha256` 沿用项目定义，覆盖 expgym/scripts/schemas/tests 与入口；configs、requirements、tools/publication 等须由完整交付 manifest 另外覆盖。

可复验：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B protocol_repair_20260918/runtime_build/independent_wire_capture.py gemini_openrouter_20260917/runtime-sweep-v2 > protocol_repair_20260918/runtime_build/independent_wire_baseline.json
PYTHONDONTWRITEBYTECODE=1 python3 -B protocol_repair_20260918/runtime_build/independent_wire_capture.py protocol_repair_20260918/runtime repair > protocol_repair_20260918/runtime_build/independent_wire_repaired.json
PYTHONDONTWRITEBYTECODE=1 python3 -B protocol_repair_20260918/runtime_build/check_independent_invariants.py --require-clean
```
