# DeepSeek-V4-Flash-0731 全量研究

已完成同Qwen流程的Custom study：783项执行、1881个agent槽位、705个分析单元；ExpGym Free/Moderate/Tight和Pool N4 Moderate/Tight × naive/cached/poolact全部覆盖。最高reasoning_effort=max，每请求32768输出上限；4节点×8 H200，四个TP8副本，GPU已正常释放。

- [完整报告：主张、全部设置与资源](report/README.zh.md)
- [全部family/task、绝对值与配对比较](report/TABLES.md)
- [重复/种子块明细](report/REPEATS.md)
- [原始dump与聚合完整存档索引](report/ARCHIVE_INDEX.md) · [机器可读索引](report/ARCHIVE_INDEX.json)
- [成稿后独立数字与逻辑复核](report/review/REVIEW.md) · [检查记录](report/review/REVIEW.json)

推荐分析为`analysis/full_v2`；`full_v1`仅保留首次reasoning用量字段遗漏的成本/身份记录，不是另一轮模型实验。所有负向结果和缺失最终配置保留；本轮支持Search F1与Audit evidence accuracy的预算退化，但Audit label accuracy不是同一方向，也不支持PoolAct在所有场景稳定更好的强结论。
