# 四模型合报：一次成稿后的独立数字与逻辑复核

结论：**报告层复核通过，未发现阻断项。** 三项 P3 文案问题已修正并作窄复核；冻结输入、科学 CSV、全部明细表未变。本结论不代表重新验证原始评分、不证明没有任何 bug，也不表示四模型均支持 PoolAct 普适改善。

审阅者为 `/root/four_model_postdraft_review`；独立只读文字/索引协作者为其 `prose_index` 子任务。二者未参与合报、适配器或索引的作者工作。适用仓库 `expgym-runner`、full-setting-report、efficient-delivery、portable-study 与 task-abstention 契约已阅读；本次仅审查已经成稿的报告层，未执行作者的 `build_report.py --check` 充作独立证据。

## 1. 实际覆盖与证据

| 检查 | 实际范围 | 结果 |
| --- | ---: | --- |
| 冻结输入快照 | 18 份显式 CSV/JSON；逐份比对固定提交的本地 Git blob、大小、SHA-256、来源 URL | 相同 |
| 规范化绝对聚合 | 4,760 行 | 原输入身份、映射字段、完整/已知/缺失分母一致，无遗漏或重复 |
| 规范化 blocks | 11,208 行 | 原输入及 block/seed 映射一致；Audit 不重复折叠 |
| 旧模型新增描述性差值 | 2,236 行 | 独立枚举全部预算/策略配对，从未舍入完整均值计算，方向和分母一致 |
| 新模型原生配对差值 | 2,454 行 | 全部原生字段逐项保留；完整差值的方向另行计算核对 |
| 完整均值与 SD | 2,886 个有定义的描述 SD | 从完整 blocks 独立重算；R1、缺失端点不生成 SD |
| README 生成数表 | 225 绝对值行、120 重复行、40 对照行、108 资源行 | 全部逐格对应已核对 CSV |
| 四模型可读明细 | 4,760 聚合行、11,208 block 行 | 每个规范化行恰好出现一次 |
| 展示单元格 | 88,092 格，含数值、分母、seed 标签与 unknown | 六位展示值或原标签完全一致 |
| 固定仓库链接 | 140 个唯一 URL，涉及 9 个提交 | 本地 Git 对象路径逐项存在；不宣称本轮远端可达性验证 |

独立数值脚本为 [review/independent_numeric_review.py](review/independent_numeric_review.py)，原始检查输出及实读 31 个文件身份见 [review/numeric.json](review/numeric.json)。脚本未导入作者代码；数值重算容差为 `rel_tol=1e-11, abs_tol=1e-9`，源字段与展示格式采用精确比较。全部 4,690 对照、已定义 SD 及完整均值的另算合计 17,800 次数值检查；脚本未从 raw 重新求分。

成功的全范围数值检查进程耗时 **0.871 秒**。首次运行曾因审阅脚本把 Free 的“不适用”预算利用率当作存在的指标查询而退出；修正审阅脚本后完成上述检查，此事不是报告数值错误。人工阅读、工具交互与协作总耗时没有预先独立计时，故不以这个进程耗时冒充整个复核用时。

可在保留固定本地 Git 源仓库的环境复查，默认只输出检查摘要，不覆盖已保留的检查记录：

```bash
python3 -B review/independent_numeric_review.py --workspace /path/to/codex_space_tn
```

这里的 Git 源仓库布局显式写在脚本中；此独立检查器并非任意研究通用接口，也不同于报告作者支持的快照离线生成。

## 2. 科学主张、设置与成本

- 四模型 Search F1 / Audit EA 的 Free→Tight 下降与表格一致；GLM、DeepSeek 的 Audit LA 反向也保留，未扩大为所有指标均退化。
- Kimi、GLM、Qwen 六组主要展示端点的 PoolAct−naive 为正，以及四模型 Tight Search 改善均与数表一致；DeepSeek Moderate Search / Audit 的负值没有被忽略。Qwen Tight Search 不优于 cached、NAS MI 与 BoN 不等价的限定正确。
- DeepSeek Exp HPO 的 70/81 可评分分母、三档完整 all unknown，以及 Pool 135/216 成员、10/54 完整 N4 池均明确区分。没有以已知子集均值取代完整端点，或为得出结论补零/补配置/重抽样。
- Gap 仅有下界、方向为越高越好。规范化聚合/block 中 12 个大于 100 的 Gap 单元格均保留；这不是 12 个独立原始实验的计数。
- 已区分旧 705 invocation 与新 783 执行槽位、Audit orders 与文档单元、MI 与池内成员、Exp 与 Pool 不同的 all 任务全集。新源 Audit 的 all/family 重复切片保留但不相加；Kimi composite 未再累计一次。
- DeepSeek 正式 workers=32，由固定发布计划及精确正式 session summary 确认；6 jobs / 15 agents 是 smoke，不是正式并发设置。Qwen 自然 drain、同计划续接与拓扑/provider/source 差异均显式记录。
- Qwen / DeepSeek 两份数据清单的 249 项路径、大小与 SHA 声明相同；这是清单对比，不是数据 payload 新验证。
- 从冻结顶层 allocation 的 GPU 数与 elapsed 秒独立重算四模型 GPU-hours：Kimi 1259.235556、GLM 1342.648889、Qwen 468.204444、DeepSeek 98.062222。未重复计入副本或 batch/extern steps。
- 总账的请求数、input/output/reasoning 与展示一致。Kimi 原失败尝试及 63 次 usage unknown 没被抹去；reasoning 已含在 output。旧 pool wall 与新模型缺失 pool wall 不混用，不拿 allocation 或 HTTP wall 总和冒充 formal elapsed / 有效计算效率。

## 3. 索引范围

四模型物理载荷索引合计为 602 个 tar shards、196,107 件原文件、8,040,138,605 原字节、1,551,057,964 压缩字节；其中旧格式 73 bundles、新格式 2 single-manifest collections。外层附件与本次合报不混入该载荷合计，未做跨模型内容去重。

Qwen 历史独立 review 原件未在其固定报告提交中发布，统一索引没有虚构该文件的 GitHub 链接。原件恢复格式与新模型任意路径重定位重放的限制均保留。本轮未下载旧归档、读 tar 成员、恢复 raw 或验证历史远端 payload；固定 URL 存在性只是本地 Git 元数据检查。

## 4. 三项 P3 修正与窄复核

| 项目 | 修正 | 窄复核结果 |
| --- | --- | --- |
| 资源因果措辞 | 将“同时增加模型侧开销”改为“可能增加或改变” | 不再作无条件因果/开销增长断言 |
| budget_utilization 解释 | 补明单 agent 反馈/B、Pool 总反馈/(4B)，已发起的最后调用可越预算，故值可 >1 | 与冻结口径及旧模板一致，不截断数值 |
| GLM 索引 scope | 移除 Kimi composite 专属说明 | GLM scope 不再误套其他模型的恢复流程 |

修正后只做受影响文字/索引的窄检查：将两处 README 文案变化逆转后，其 SHA 与原全范围审阅稿完全一致；其余 30 个实读文件的 SHA 未变。科学 CSV、全部模型明细及已核对的生成数表未改变，因此未重跑整套数字复核。最终主报告 SHA-256 为 `16e30087024feb158e29e640555ad96d5924edff25b4022e459b4219a7aef415`；最终索引等身份见 [REVIEW.json](REVIEW.json)。

## 5. 交付边界

复核完成时，发布扫描和远端确认由作者的后续 [VALIDATION.json](VALIDATION.json) / 发布记录负责，本复核不提前声明它们通过。本次没有模型调用、GPU 申请、评分器执行、原数据扫描/重包/恢复，没有改写原模型研究，也没有增加第二条完整复核链。

阻断项：0。未解决的本报告层问题：0。原研究已有的缺失端点、模板/采样/资源差异及非确认性推断边界继续存在，不能由有限报告复核消除。
