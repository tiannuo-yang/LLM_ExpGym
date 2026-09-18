# 统一修复实验运行版本

本目录固定了协议修复实验实际运行的 native API 兼容源码。答案协议为 final-answer-boundary-v2，Audit 包装及字段解释与单体评分/池投票共享；图协议为历史 paper-graph-lock-v4 的完整 SHA 身份实现。

`runtime/` 的117个源文件与实际执行快照逐字节相同，源文件清单见 RUNTIME_SOURCE_MANIFEST.json。执行 source_tree SHA 为 `cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`。完整清单额外覆盖现有 source_tree 算法未包含的 configs、tools 和依赖文件。

数据、API凭证、模型权重和完整请求响应不包含在本目录。历史API客户端、提供方参数、不可变历史和上下文语义保留；此版本不代表所有模型的算力相同。新实验结果和复算材料在最终结果目录另行发布。

验证：完整运行801项测试（5项跳过）通过；NAS101 A/B/C 使用真实冻结数据、每池4成员进行无模型native工具端到端及source-bound队列导出核验，全部通过。NumPy 2.4.6。
