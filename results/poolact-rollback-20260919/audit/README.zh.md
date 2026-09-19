# Audit：保留单智能体，回退全部 N4 对照

当前采用层是 **hybrid official**：702 条 N1 轨迹、11,934 次假设展示保留提交 `7776f70` 的正式来源、评分和行为；468 个 N4 池、1,872 个成员（naive、cached、POOLACT 全部策略）恢复到修复前的完整池来源和旧评分。没有拼接成员，没有重新调用模型。

`old/` 的 10 张表完整保留历史基线。当前 `n1/` 的 7 张表与 7776f70 逐字节相同；`coordination/` 的成员、池及 36 组统计由历史 N4 叶表生成。`changes/` 全部重新计算，比较历史全旧层与本次混合采用层。因此 N4 的 changes 为空；N1 修复带来的证据质量及配对变化继续保留。

`score_version=new` 在本包中只是当前采用层的兼容标签，不表示 N4 使用新评分器。所有 N4 行显式标注 `source_origin=historical_n4_rollback`。修复版仍完整保存在 [20260918 历史交付](../../protocol-repair-20260918/README.zh.md)。

复算入口（在仓库根目录运行，输出到新目录）：

```bash
python3 results/poolact-rollback-20260919/tools/build_audit_rollback.py \
  --repo . --output /tmp/audit-rollback-rebuilt \
  --main-scalars results/poolact-rollback-20260919/main/slot_scalars.csv \
  --main-selection results/poolact-rollback-20260919/main/SOURCE_SELECTION.csv
```

该命令校验冻结输入，重建 31 张 CSV，并在独立进程中再次从导出叶表重建，逐字节比较全部 CSV。另逐项核对 1,170 个主表来源 SHA、1,872 个成员来源和 3,276 个 LA/EA 数值（包含 N4 的 MI 与 MV）。此处复算的是公开叶表及聚合，未重新读取完整私有轨迹或重新执行科学评分器；完整私有轨迹的历史核验保留在原包。

证据复用和固定案例基于对应采用来源，不能将修复版的运行时动作归给本次恢复的旧池。VE 沿用历史定义，包含实际尝试但未收到结果的反馈调用；N1 的可见反馈 VE 单独保留。
