# Gemini OpenRouter 补充实验

[主实验补齐报告](main/README.zh.md) · [六模型 Whois 预算报告](whois/README.zh.md) · [主实验独立复核](review/main/README.zh.md) · [Sweep 独立复核](whois/REVIEW_ADOPTION.zh.md) · [执行证据审核](review/FINAL_EXECUTION_REVIEW.json) · [接口和设置](SETTINGS.zh.md)

本目录为独立补充版本。原 [ad03e8c 主报告](../paper-analysis-20260916/README.zh.md)、原分析表和原采用来源索引保留原字节。主实验新增 Gemini 的 16 个缺项，得到 4,698/4,698 个执行完成结果，其中严格评分完整 4,687 项；原 4,682 个完成结果保持不变。

主实验缺项为 N1 HPO 6 项、N4 HPO 9 池，以及 N4 Search Moderate/naive 1 池，共 46 条 agent trajectory。新结果经 OpenRouter 获得，原 Gemini 完成结果来自 Sub2 API；混合来源已在报告和逐项 CSV 中明确标记。

Whois N1 sweep 新增的同一组 39 题 × β=1、5、15、20 共 **156/156** 项已完成。β=10 的 39 份原 Gemini 结果直接复用；[β10 原数据定位及逐份哈希](provenance/gemini_beta10_reuse.csv) 记录旧 v3 批次 5 项、recovery_v1 批次 34 项，以及完整本地交付中的采用副本。六模型报告保留原五模型的 975 个位置，共 1,170 个完整报告位置。

| Gemini Whois N1 | β1 | β5 | β10（历史复用） | β15 | β20 |
|---|---:|---:|---:|---:|---:|
| F1 × 100 | 8.72 | 40.09 | 62.77 | 67.09 | 72.43 |

β10 的精确 F1 均值为 62.7665%；它是 Whois 子集，不是主报告全部 73 题 Search 的 55.0189%。原五模型报告包括 GPT、Kimi、GLM、Qwen、DeepSeek；本版完整保留这些基线。

首批 8 个 sweep 实验在模型交互和评分后遇到自定义预算的导出校验错误，已依据原终态离线恢复，新增模型调用为零。其余 148 项用仅修复导出层的版本首次执行；两版执行与导出身份逐项保留。恢复的 8 项完整运行 wall time 原先未保存，保持空值；实际 LLM 延迟和模拟工具费用保留。

本轮共新增 **172 个实验、202 条 agent trajectory**，产生 2,052 次客户端 OpenRouter 请求，报告的 API 费用合计 **$9.448475775**。另有不计分接口探针 2 次、$0.000579，合计 **$9.449054775**；历史 β10 的 API 费用保持未知，没有当作零。详见 [费用汇总](provenance/ACCOUNTING.json)。客户端记录不能单独观察提供方内部重试。

公开文件包含数值表、逐项来源和哈希、复核收据及只读数值重建工具。完整请求响应、原始 trajectory 和本地归档不随轻量发布上传。文件中的历史本地路径用于定位原始证据，不代表 GitHub 含这些文件。

在仓库根目录校验全部发布字节和原冻结数据：

```bash
python3 tools/verify_lightweight.py
```

仅使用公开的 4,698 项保存分数重算聚合、比较和排名，不需要 API 或原始 trajectory：

```bash
python3 -B results/gemini-openrouter-20260917/tools/replay_public_tables.py \
  --report results/gemini-openrouter-20260917/main
python3 -B results/gemini-openrouter-20260917/whois/replay_whois.py --check
```

两套公开回放均已在工作区外的临时导出中通过：读取权限仅限公开副本和 Python 标准库，访问原工作区被拒绝，见 [隔离复验收据](provenance/ISOLATED_PUBLIC_REPLAY.json)。这些命令验证保存分数到报告数值的映射，不重新运行任务评分器，也不鉴定提供方模型权重。`tools/merge_main.py` 保留完整合并实现，其从原件开始的入口还需要本地绑定输入；公开验证通过同目录的 `replay_public_tables.py` 使用已发布标量投影。

[复制来源清单](provenance/COPIED_FILES.json) 记录公开副本的原始文件 SHA256。独立复核文档保留审核时的目录名称；其中 `main-final-v2/` 对应本目录 `main/`，本地 `partial_actual/` 与 `main-final/` 是未发布的历史检查材料。
