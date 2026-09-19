# 回退版独立验收

在仓库根目录运行，输出目录必须不存在或为空：

```bash
python3 tools/verify_poolact_rollback.py --output /tmp/poolact-rollback-verification
```

仅需 Python 3.10 以上的标准库与仓库公开文件；支持没有 Git 历史的浅克隆，不需要私有原始轨迹、API key、模型服务或完整 HPO benchmark。命令会重新选择输入、计算表格、生成报告，并逐字节比较公开产物，生成 `VERIFICATION.json`。

验收范围：

- 4,698 个主实验槽逐行核对：2,502 个 N1 保留 `7776f70` 的分数与来源；2,196 个 N4 恢复 Gemini 补齐后的历史分数与来源。
- 本轮 116 个新 N4 来源退出正式采用；2 个新 N1 来源保留。此前补齐的 6 个 Gemini N1 和 10 个 Gemini N4 都保留。
- HPO 单智能体行为仍为 486 条、每预算 162 条；Whois 单智能体 sweep 仍为 1,170 项，保留独立 GLM β20 对照。
- 854 个历史交付及冻结 runtime 文件与固定提交 `7776f700902db194c69124b1a5f59d985379cfb3` 逐字节相同。历史保留与当前正式采用分开。
- 当前代码的 N1/N4 规则分离；关键 N1 文件仍为 `7776f70`，图、投票及独立 N4 解析源恢复历史版本。

这项验收是**已有分数和来源的选择、分析及报告复算**。它不声称本次调用模型，不声称重新评分全部私有原件，也不使用旧版的 97 池正式采用门槛批准当前结果。

`BASELINE_INPUTS.json` 是从固定 `7776f70` 的 Git 对象逐文件核对后生成的保存清单；运行本入口时无需 Git。`N1_RUNTIME_DIFFERENTIAL.json` 记录了 72 组实际 loop 差分，默认 N1 与 `7776f70` 的完整结果及请求内容相同；`TRACE_POLICY_CHECK.json` 核对实际 trace 序列化的协议标记；`SELECTION_GUARD_CHECKS.json` 记录了 8 个应当失败的选择变异，均被拒绝。生产代码与测试另见 `../review/CODE_SOURCE_MANIFEST.json` 和 `../review/CODE_TESTS.json`。

上一版 `tools/verify_protocol_repair.py --full` 绑定上一版科学代码。检验那一版交付时应检出固定提交 `7776f700902db194c69124b1a5f59d985379cfb3` 后运行；当前回退版使用本入口。
