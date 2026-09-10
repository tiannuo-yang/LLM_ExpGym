# K3 最终公开版本：有限发布解释复核

结论：PASS_BOUNDED_RELEASE_INTERPRETATION_REVIEW，无必须阻断的发布解释或直接导航问题。此结论不是新实验证明、全源码无漏洞保证或联合公开恢复/AN2重放通过证明。

审阅者：/root/glm_delivery_reuse；此前参与交付封装与浏览映射，不是本科学终稿作者，也不是盲审。时间：2026-09-10 01:38:55 UTC 至 2026-09-10 01:40:24 UTC。ROOT 给定 fresh GitHub clone 绑定 commit 1694aa2a1a79a651629055b45fdd02e20aacdc95，并已完成其4822文件核验；本次不再查询Git或重做clone证明。

## 有限发现

- 两模型六主比较（CSV共12行）方向为正，导航12个六位小数值均与公开冻结CSV一致；只支持指定任务、指标、设置中的方向性观察。文案明确否认普遍/所有场景稳定优胜、统计显著、论文逐数字复现以及收益因果归于补丁；R1/R3、seed非IID、CI/p为空与最大推理/温度1等差异未省略。K3 NAS-A MI三block约0.119/0.097/6.015的幅度不稳定也明确保留。
- NEGATIVE_PERFORMANCE.csv完整读取49行，均为负效应：K3 41、GLM 8。导航及报告保留K3 Moderate总体/B/C BoN负例、Tight A BoN负例、GLM Audit label反向及cached反例，并说明切片不是独立样本。本次只核已给CSV行数/展示，不重新评分或证明它穷尽底层实验；其完整性承接已冻结post-report复核。
- README、REPORT与post-report REVIEW一致保留旧63个error/未知用量、全成本total仍null；GLM59/1881正常缺答及明确forced-final/32768/空正文/非空reasoning边界；新26 NAS中6个legacy fallback。未把缺答剔除、unknown补零、6项称为缺答或26项全当严格有效final配置。本次没有重新读取raw来验证这些近端机制。
- 两项公开遗漏没有混淆：包内controls从467到466，仅缺1292 B合成CPU收据；外层另缺10383 B的FINAL474_READBACK.json，候选55件、公开54件。外层ROOT记录明确它不是归档成员/实验结果/AN2输入，联合66643原件、466 controls及联合SHA不因此变化。两处均披露私留原件和失败扫描、保守credential_metadata_field命中不等于已证明密钥泄漏、私有引用链非完全自包含；不能把“包内唯一缺项”扩大为整个发布只缺一件。
- 两份新导航共28个本地直接链接全部存在，中文“公开范围限定”锚点有效；包含新增outer-selection README、union checker README及工程peer REVIEW三个入口。另1个固定代码提交外链未联网核实。没有递归展开深层历史链接或引用链。
- 新导航仍保留候选时态和K3联合公开恢复/十输出重放pending，属于保守的冻结状态，不构成提前成功声明；REPORT里的成稿后审阅pending与后来post-report PASS有明确时间层次。ROOT正在进行的新联合恢复不由本复核轮询或验收，clone已取得不能替代restore/replay完成。

## 精确阅读范围

BASE = /lustrefs/users/chufan.shi/codex_space_tn/publication/k3_composite_full_remote.2xWrw79q/repo/results/portable-eval-20260908/full_delivery_v5/kimi-k3-fixed8-composite-20260910

下列路径均相对BASE，读取时与最终有限核对时bytes/SHA一致；没有改写任何公开文件或冻结分析。

| 相对路径 | bytes | SHA256 |
| --- | ---: | --- |
| README.zh.md | 5617 | 461281bc98cbdfc175c638187cb5de1ed17e79d9fcac5c2a3e614301a5dd54d3 |
| FULL_DELIVERY.zh.md | 5953 | c5acf5f306e17fa0e1e8bd350e73e592c3ba5cdf243736d584d707b181ce0d83 |
| analysis/dual_model_analysis_fixed8_v2/REPORT.zh.md | 20557 | f799007dbcfb1ca7a4a84c3e872332ab0a479362e50f30d9d440e33c5fe6ee88 |
| analysis/dual_model_analysis_fixed8_v2/PRIMARY_RESULTS.csv | 3178 | 29f57a571a797359638394494cf2553a89f08f87980c65cc45bdb91d32d58004 |
| analysis/dual_model_analysis_fixed8_v2/NEGATIVE_PERFORMANCE.csv | 16056 | 560b0659b8235dddde5f67bb3bb04b56f1779b317afa5aa4030f1ec7828c419f |
| analysis/dual_model_post_report_review_fixed8_v2/REVIEW.zh.md | 7399 | 918d281796d87634d1874adda40b5fe5ce0603e7c71e29f642c6f3797792e30f |
| evidence/root/ROOT_PUBLIC_OUTER_OMISSION.json | 2647 | e6ad378563951d5070e2789cfc1fa960d057c667046838b35a16c04132268438 |

实际工具：6c265b（两导航全文）、bdfccd（REPORT/post-review/外层遗漏全文）、11a291（两CSV全文）、4f78ea（有限链接/展示/计数与7 refs回读），均exit0。除声明文档外仅检查导航直接目标是否存在；未读实际恢复目录、tar、模型、keys，未执行Git/network/模型/scorer/AN2/恢复/扫描，无新CPU工程或额外INDEX。

仅此一份复核说明落盘；STOP-WRITE。
