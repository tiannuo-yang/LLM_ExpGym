# 公开数据恢复与报告重建

先取得本研究**固定 Git 提交**中的公开文件，并以该可信提交绑定 `ARCHIVE_INDEX.json` 及四份 manifest；只从不可信位置取得 manifest 不能证明归档身份。下面均从研究公开根运行，使用与原 `INPUTS.json` 一致的 CPython 3.11.15，无 API、GPU、模型权重或密钥需求。恢复工具是 `rebuild/` 中 exact-byte 保留的原 `expgym.delivery.v1` 读取器，不产生新归档格式。

## 仅恢复报告需要的原件

为四个模型分别选择一个尚不存在的目标目录。下面示例的 `/absolute/restored-study` 可自行替换；四个子目录都必须是全新的。

```bash
for model in gpt kimi deepseek glm; do
  python -B rebuild/scripts/package_run.py verify \
    --manifest "bundles/$model/payload/manifest.json" \
    --archive-dir "bundles/$model/payload" --require-public-scan \
    --select "restore_selections/$model.json" \
    --restore-dir "/absolute/restored-study/$model"
done
python -B rebuild/aggregate_material.py \
  --spec spec.json --artifact-root /absolute/restored-study \
  --output /absolute/new-rebuilt-report
```

`--select` 只限制恢复到磁盘的成员；原读取器仍按 manifest 流式校验全部归档和成员。上面不是本交付流水线额外执行的恢复步骤。完整 raw 始终在模型包中，没有复制到共享输入。若只查验、不落盘，可省略 `--select` 和 `--restore-dir`。

`spec.json` 的相对引用指向公开根中的原 master plans、GPT recovery plan、oracle、四份固定历史 CSV、用量和尝试元数据；`@study/<model>/<member>` 引用上述恢复目录。原 bound plan/result/summary/生产验证收据来自包内原字节，绝不改写其历史 provenance。聚合器不调用 scorer、不读取 API raw、不补造缺答或失败分数；strict 与 Gap0 仍分别输出。

生成器重建主/详细报告和分析 CSV 等其 `CHECKS.json` 指定文件。独立复核、交付索引、本说明由各自来源冻结，不伪装成聚合器重建产物。`CHECKS.json` 的 `output_sha256` 与 `INPUTS.json` 是重建比较入口；记录的 Python 版本可能影响身份文件，精确复现时使用原记录版本。科学分数不能用已知子集平均替换未知值。

冻结包中 `pending` / `not pushed` 及生成器 `INPUTS.independent_final_review=false` 是各自生成时间或职责范围的状态快照，不代替最后固定发布提交与 [最终独立复核](INDEPENDENT_REVIEW.zh.md)，也不据此修改冻结包。另一个不同限制仍然有效：GPT 的本地 commit 本身不宣称可由远端 fetch；公开源码重建入口是已公开 base `0d3c299f0352ddd53bc012c787d3da81db529d89` 加 [exact patch](bundles/gpt/source_delivery/source-0d3c299-to-7f0fe09.patch)，及其 [source provenance](bundles/gpt/source_delivery/source-provenance.json)。不能把该源码可达性限制统称为过时状态。

## 查找并恢复完整 request/reply

由 `ARCHIVE_INDEX.json` 的模型尝试索引定位科学槽与物理 attempt，再查该模型 `payload/manifest.json` 的 `files`，取得精确 member、SHA256、bytes 及 shard 映射。将所需 member 名称写成一个 JSON 字符串数组，并以上述原工具的 `--select` 恢复至另一个全新目录。不要按成绩筛选，不要用新的成功 attempt 覆盖旧失败 attempt。

GPT 的 27 个有效科学槽有 28 次物理 job 尝试：原基础设施失败的 12 个请求与独立恢复都在包中；恢复没有增加第 370 个科学槽。正常空答与基础设施失败继续使用各自状态，不能统记为零。所有公开 request/reply/result 为原字节；仅模型外层已声明的路径/账户元数据投影发生过变化，具体看对应 MODEL_INDEX / projection_sources。

私有凭据、含凭据源路径的控制文件及其操作配置没有复制到公开根；局部遗漏原因和原件身份由模型的安全投影记录。恢复已有分数和报告不需要这些私有文件。科学源码/部署配置分别由模型源身份、GPT 原补丁和共同已公开版本追溯，不用猜测本机路径。

旧五模型 cohort 固定为 `6c63f1c03c88683fa55be5cafcbb8122ac8fadaa`；Free/Moderate/Tight 与 ranking reshuffle 属于该历史 cohort，不冒充本轮 369 池重新验证。旧诊断固定为 `d2cd3089d1d34a19e9c03dd5d38a7fd01be608cc`，709 原件直接引用、不重复下载/归档。本轮对修复前后差异不能作单一补丁因果归因。
