# DeepSeek Audit 的历史提示保留版本

`runtime-deepseek-audit/` 用于九个 DeepSeek Audit 中间终答接受时刻发生变化的控制对照。它采用与其他补跑相同的正式终答解析、投票规则和 v4 图身份修复；其原生 Audit 初始提示保留这些旧运行实际使用的内容。

DeepSeek 这批历史 v4 运行已移除固定 `nda-11`／`[3,7]` 的首调用示例，而通用补跑运行目录沿用另一批实验的旧提示。直接套用该默认提示，会把任务提示变化混入终答规则对照。因此，此目录仅恢复历史 `_build_context` 函数；不向 DeepSeek 重新加入固定示例，也不替其他模型移除它们当时使用的提示。

相对 `runtime/` 的 117 个源码文件，只有 `expgym/task_evidence_audit.py` 的 `_build_context` 改变，其余 116 文件完全相同。该函数与历史来源逐字节相同，所在模块的其他函数及前后字节均保持原样。终答 parser、运行循环、投票、图实现和三个运行入口保持与已冻结修复版本相同。

- 通用运行目录的 source tree：`cb2fe024256e8f2e7eaf882cd34af2fd7217ba1af21e6f7d9f23243f50a09f02`。
- DeepSeek Audit 运行目录的 source tree：`4f28d240bfbb6e38d68a1db3466b8c78b8cdbb0b13962b99509a66f713cc0765`。
- 历史 `_build_context` 函数 SHA256：`05500a2a2165f488bef95a47241baaa7f6896398abbe844f3313aae0ba0d4edd`。
- [完整源码、函数差异与身份检查](RUNTIME_DEEPSEEK_AUDIT_MANIFEST.json)。

公开目录只包含源码。实际运行的外部 `data` 挂载、完整请求与结果归档不在其中；输入数据身份、逐槽 prompt 对照和正式采用状态由结果交付包单独记录。本目录不替换正在运行的 HPO 97 池所使用的通用冻结版本。
