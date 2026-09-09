# 修订附件的独立有限复核

结论：**原 post-report 审阅的 F1、F2 均由新附件关闭；可选 prompt 补充的有限边界正确。** 原报告应与附件合读；本结论不是整项目完成或所有模型普适性的验收，也不补齐 K3 八项失败。

审阅者 /root/format_diagnostics 是原 F1/F2 独立审阅者，不是报告或附件作者。本次仅审已停写的 dual_model_analysis_addendum_v1 exact 三文件，并核其 11 个有限引用；不重复大规模分析，不读 raw、不执行模型、scorer、backend、Slurm 或网络，不改任何既有文件。

## 关闭结果

- **F1 已关闭（附件第 7–13 行）**：明确替换原报告第 40 行“独立”为“预定外层 seed-block 重复”；服务端 seed 生效和统计独立性未独立证明，三个 outer-bundle effects 的 sample SD 不是 CI。保留 Search/Audit R1、orders/N4 不扩充 iid 样本及 CI/p 为 null，没有改任何数值或增强显著性/稳定性结论。
- **F2 已关闭（第 17–32 行）**：分别说明旧共享图未来合并状态泄漏、被预算扣留反馈经 graph 回流 forced-final；新实现以不可变完成事件、观察者时钟和严格 completion_time<budget 隔离，保留原 loop 的 cost≥budget 扣留政策。说明旧 cache 完成时间门控原本正确、通用问题与 K3 serving 适配不同、并非已证明某次整理代码引入。未声称补丁保证提高 PoolAct，未量化旧真实影响，历史 parser/vote 边界和 GLM 59 缺答解释均未改写。
- **可选 prompt 补充正确（第 36–38 行）**：18,403 请求、126 次 model-generated history 命中（oracle 102、nasbench101 11、contractnli 13）、指定字段 HPOBench 0 和 source-controlled/mixed 0，与固定 ROOT 元数据一致。明确不是 fresh 原 payload 来源审阅，不覆盖全部 assistant reasoning、其他未审字段/JSON keys 和服务端模板；零字面命中不证明任务不可识别或没有训练污染。
- **原报告保持不变**：原目录 exact 六文件，逐件 bytes/SHA 与原 INDEX 和此前冻结值相同。新附件仅文字勘误，不产生新评分或替代原数值；K3 697+8 NODE_FAIL、GLM 705 完成，12 主项、31 负项、50 性能 unknown 和阶段状态均保留。

图实现与 seed 的事实依据仍是前次真实 post-report 源码核查；本次复 pin 对应源文件和原审阅不变，没有重新执行测试或反事实实验。此处“关闭”仅指两个报告问题已处理，不证明旧轨迹的泄漏发生率或补丁成绩贡献。

## 实际检查记录

- f20076，exit 0：新附件 exact 三文件 pins、fresh 审阅目录检查及三文件全文读取。
- 28dc2c，exit 0：11 个引用的 canonical path/bytes/SHA 核查；ROOT prompt 元数据全文读取。
- 72804c，exit 0：附件逐行复读并定位更正。
- 13e0c9，exit 0：原报告目录 exact 六文件与 INDEX 复核；收集 14 个有限输入引用。
- d85efa，exit 0：非附件作者 usage_contract_static 独立窄核 prompt 段与 ROOT 回执一致，两个 pins 均匹配。

完整输入 refs 见 INPUT_REFS.json；无失败、重试或新增执行授权。写入仅限本新审阅目录。于 2026-09-09 19:38:53 UTC 完成实质审阅，文件冻结后停止写入。

