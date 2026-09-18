# 公开运营与资源账本

状态：**FINAL — 已完成**。登记 **97 个 HPO 槽 + 22 个辅助控制槽 = 119 槽、467 个智能体成员**；本次快照已有 **119 槽**通过生产完成校验。辅助控制含主实验 21 槽与独立 GLM β20 sweep 1 槽，不能把后者并入主 β10。

账本只描述实际运行的请求、用量、费用、设置、版本与资源，不定义正式采用分数、排名或评分修正。历史分数和新正式分数由实验分析交付管理。

## 内容与复算

- `main/`：HPO 97 槽的 6 个公开账本文件。
- `aux/`：辅助 22 槽的 6 个公开账本文件。
- `resource_usage/`：4 个固定服务 allocation 的 5 个资源文件。
- `audit/`：独立原件审查和重复导出凭据的安全投影。
- `ALLOWLIST.json`：每个 payload 的来源相对位置、原件/投影 SHA、字节数及转换方式。
- `MANIFEST.json`：封闭文件清单；包含 ALLOWLIST，只有 manifest 自身不自哈希。

在任意 Python 3 环境，从本包目录运行：

```bash
python3 tools/verify_public_ledgers.py --root .
```

它只读取包内 CSV/JSON，复算槽数与成员数、attempt/profile 关联、逐槽和逐模型用量/费用/错误次数，并验证所有文件 SHA；无需网络、GPU 或私有原件。用 `--require-complete` 可拒绝 partial 包。

当前导出的 HTTP error attempts 为 **2**，来自全部尝试记录动态统计；其中 **2** 条按原 will_retry/max_attempts 标记重试，且同一 generation 随后成功。重试身份和费用字段全部保留，不等于 whole-slot 重跑。生产层允许的 HTTP 传输重试和 whole-slot 重新采样须分开解释。

USD 仅汇总 provider 实际报告的 usage.cost，未知费用保持 null，不填 0。GPU hours 是分配数乘 scheduler 记账时长，包含部署、加载、生成、空闲和等待验收，不是纯模型计算，也不换算美元。资源是否最终结束见 DELIVERY_STATUS 的独立 gate。

`source_scripts/` 保留实际 exporter/packager 源码便于审计。运行这些原导出器需要原项目完整本地 archive、队列与（资源查询时）Slurm 布局；公开包不包含这些材料，也不能单靠该目录重读私有 API 原件。资源目录原 README 中的刷新命令同样属于原运行环境；公开独立复算入口只有上述 verifier。

未发布原 plans、BINDINGS、API dumps、prompt、答案、工具内容、endpoint、凭证或绝对本地路径。`--allow-partial` 构建始终标记 complete=false；最终构建要求生产完成、独审覆盖、receipt 链和资源记账全部通过。
