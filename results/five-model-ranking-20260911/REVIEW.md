# 五模型成稿独立复核

结论：**本轮报告数字与逻辑验收通过，无未关闭阻断项。** 这是一轮成稿后的独立复核，不是旧实验的重新评分，也不是发布安全或远端上传验收。

## 范围与方法

由非作者审阅者 `five_model_postdraft_review` 执行，配置/资源/索引由同轮只读子任务 `prose_index_check` 并行检查。按 `expgym-runner` 的冻结输入报告流程审阅：不调用作者生成器作为独立证明，不读 raw/tar，不执行模型、scorer 或 GPU 作业。

[独立 checker](review/independent_check.py) 不导入作者报告模块，使用标准库从冻结 GPT 已评分指标另算 item 内重复均值、item 等权聚合、完整配对差及排名。执行环境为 CPython 3.11.15；实际输出、检查计数与已读文件 SHA 见 [REVIEW.json](REVIEW.json)。正文、配置、资源和索引的补充只读检查范围在该记录中另列，不冒称由 checker 自动生成。

该独立 checker 另需 INPUTS 指向的一份本地原始请求范围 metadata，以核对公开派生的两字段变化；这是metadata而非HTTP载荷。正文的离线生成/字节检查命令只需本报告快照，不要求这份本地原件。

## 已完成检查

| 检查 | 结果 |
| --- | --- |
| 13 份冻结输入 | 字节数与 SHA 一致；请求范围公开派生的两字段变换另核对 |
| 旧四模型 CSV | 4,760 绝对值、11,208 blocks、4,690 对照行的所有原字段值原样保留，没有重评分 |
| GPT 新聚合 | 从 1,611 已评分指标行折叠到 1,455 行；另算 291 绝对值、687 blocks、291 配对差，一致 |
| Audit 顺序 | 78 个文档×指标×预算组各含三固定顺序，只折叠一次；不是39个独立文档 |
| GPT 原生导出 | 165 绝对值、333 repeat 行（含全部36个 Audit 顺序视图）、165 对照逐项另算，一致 |
| GPT 完整性 | 783 完成 / 782 评分完整；唯一 NAS C/Moderate/poolact/seed2208 不完整池的四指标保持 unknown，不读已知成员子集补分 |
| 排名 | 270 行、18 转移；固定三档完整候选、并列、competition rank、runner-up margin 与排除原因一致 |
| 展示表 | 16,946 详情行；正文1,125质量、150差值、750重复/SD单元；排名90模型行、54概览/排序/margin行一致 |
| GPT 资源 | 27 setting、270正文单元；21可加总字段与 model_total 一致，13次未知 usage 不补零 |
| 配置与覆盖 | 705 queue stages 的 steps/evals=30、medium、legacy、task-abstention、Pool N4/context131072一致；Claude完整性单列且不入五模型排名 |
| 索引 | 五份metadata SHA、31,222原件metadata、41分片metadata、38分析/控制器映射、101 browse来源身份一致；未读取载荷 |

聚合数值容差为绝对 `1e-10`、相对 `1e-11`；并列规则独立按绝对 `1e-12`、相对0以及分组最高分 anchor 验证。Markdown以CSV原值六位格式核对，不从已舍入正文计算新差值。

## 三项主张的核对

1. 预算退化：五模型 Search F1 与 Audit EA 的 Free→Tight 均下降；四个完整 HPO 总体均值下降。DeepSeek HPO 不完整、Audit LA 非单调等边界仍在相关表旁，不扩张为所有指标一致退化。
2. PoolAct：五模型 Tight Search F1-MV 均高于 naive；GPT 六组主要对照为4正、1负、1未知，保留 cached、MI/MV/BoN 和完整分母，未写成普遍严格优越或等实际成本优越。
3. 排名重排：六家族固定候选中2/6换位；严格五模型完整家族子集1/3。九个 HPO task 中7/9换位；严格五模型完整任务子集1/2。whatis为GPT→DeepSeek，NAS101为GLM→GPT；不换位家族与三档候选排除同时展示。没有跨指标总榜，也没有显著性或纯模型能力因果结论。

## 发现及关闭

仅发现两处低优先级表述澄清，作者已窄修并核对关闭，未改任何科学分数：

- R1：正文现在明确 `max_tokens` 与 Responses `max_output_tokens` 都未发送，不能把 nominal32768当作GPT有效输出上限。
- R2：离线字节检查命令旁现在明确原解释器 CPython3.11.15及跨版本末位差异。

发布检查期间，作者把请求范围 metadata 中两处描述性 Authorization 模板改为公开占位值，并在 INPUTS 记录原件/派生身份。独立对照确认恰好两字段变化、其余 metadata及原件不变；这不是修改实验，也不等于凭据扫描通过。

## 验收边界

本轮沿用旧四模型已发布冻结导出，不重审旧 raw；GPT聚合从保存的评分值重组，不验证评分器对原回复的正确性。索引检查只读metadata，不重读归档载荷；GPT/API raw继续为本地封存，`public_scan_passed=false`不被报告发布改写。

API与自部署的 effort、采样、输出限制、工具编码、服务拓扑和成本口径不同，排名仅描述本次列明部署设置及候选范围。种子标签和有限任务不建立独立采样、确认性推断或跨模型总体保证。

独立复核已结束；安全扫描、staged字节及远端身份由主任务另在VALIDATION/发布记录如实确认，不在本记录预先宣称通过。
