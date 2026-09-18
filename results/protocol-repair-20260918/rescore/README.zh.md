# 全量协议修复重评分交付

- `main/`：4698 个采用结果的新旧标量总表。N1 2502；N4 2196 个池、8784 个成员；合计11286个成员。严格可评分结果仍为4687，11个HPO缺配置不伪造分数。
- `search_audit/`：Search/Audit 的全量新旧评分、完整样本对照、原因分解、最小公开评分输入和真实parser/scorer回放。
- `hpo/`：486 N1 + 324 N4/1782成员；可见配置匹配、历史fallback、Gap0口径与独立benchmark检查。
- `sweep/`：全部1170 Whois预算结果，234个beta10与主实验重叠逐项核对；独立增量936，因此去重5634结果、12222个成员。

所有现有轨迹层均标 `existing_trace_rescored`。它与旧正式成绩、先前诊断敏感性分析、统一版本实际补跑的采用层分别保存；仅重新评分不能改变旧运行时图信息或行动选择。

新主表由 `tools/merge_protocol_rescore.py` 按不可变slot_id合并两部分：

```bash
python tools/merge_protocol_rescore.py --search-audit PATH/search_audit --hpo PATH/hpo --output /tmp/main-rescore
```

`main/slot_scalars.legacy.csv` 保留旧表原字节；`main/slot_scalars.csv` 为全4698新评分；`main/sample_diff.csv` 包含所有变化及未变化样本，`main/affected_scores.csv` 只筛分数发生变化者。主成绩、排名、regret及行为分析另由分析脚本从新表计算。

公开输入包只保留重评分必需的终答/可见评估记录/最小冻结评分参考和哈希，完整原始轨迹继续本地留档。HPO轻量回放明确复用独立验证的benchmark测量证书；持有冻结数据的使用者可重新执行benchmark校验。请分别阅读三部分README，避免把“标量重新汇总”“最小包parser/scorer回放”“独立benchmark重算”“实际补跑”混称同一验证。
