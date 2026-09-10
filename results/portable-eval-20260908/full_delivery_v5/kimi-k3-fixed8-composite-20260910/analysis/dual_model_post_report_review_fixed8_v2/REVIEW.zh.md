# 固定 8 项恢复后终稿：成稿后的独立有限复核

结论：**PASS_BOUNDED_POST_REPORT_REVIEW；未发现需要阻断该冻结报告的数值或解释逻辑问题。** 这不是全部源码无漏洞、普适结论、ROOT 科学签署或新 K3 公开交付完成证明。被审对象为 [冻结终稿](../dual_model_analysis_fixed8_v2/REPORT.zh.md)，INDEX SHA `aa2f55e3b42d179e505603ce2f4870c56582e5ec7152ad901f355729b43ff854`，exact14 / 294735B；未改任何被审原件。

## 独立性与实际范围

复核者为 /root/format_diagnostics，不是本终稿作者、恢复 runner 作者或 merge/exporter 作者。此前参与 usage/format、恢复 sealer 工程、新26有限科学及不变性检查，故并非从未接触数据的盲审稿人；这些既有工作不自动构成本次报告通过。收到作者 STOP-WRITE 与 ROOT 授权后，重新全文阅读 REPORT 136行和 NEGATIVE_PERFORMANCE 66行，重新核表及解释边界。成本辅助复核者曾独立核新289 usage，但本次未重读 raw，也不是报告/merge 作者。

主实际只读脚本 `review.py` 使用原固定摘要、CSV、manifest、results 中的指标/身份字段，未 import 或执行作者 checker、AN2、scorer、模型或 backend。工具 `8af852` 真实 exit0；115 个明确输入（14报告文件+101声明引用）前后 SHA/stat 一致。文件容器可能包含答案字段，但本次没有解释、打印或输出那些字段；无 HTTP raw、key、表反序列化、Slurm/Git/network。少量明确引用的历史控制补证另列 INPUT_REFS，不递归扫描目录。

## 数值与分母

- 12个主 CSV 行与两份最终 effects.csv 逐字段精确相同，报告六位小数表全部一致。独立从其原 paired_rows 重新核主项方向、每 outer 的描述性平均、总 effect 与样本 SD；CSV/报告映射不设容差，独立浮点算术仅容许2e-13绝对舍入差。Exp 为 Free−Tight，Pool 为同N4/同预算 PoolAct−naive，不反转改善方向。
- K3 E-H 为8.829193357586593 Gap points，outer三值为3.8388051121411433、13.02838114996262、9.620393810656017，样本SD4.645597438051279。报告没有把其余五主项变化或假显著性当作恢复收益。
- 全49个负性能 CSV/Markdown 行逐字段覆盖原定义性能集合的全部负值，K3 41/GLM 8；旧K3 23行精确保留。未省略 GLM Audit label 反向、K3 Tight NAS101A BoN 负值、新 Moderate PoolAct B/C/总体 BoN 负值，以及 cached 负值。all/family/raw/Gap切片明确不是额外独立样本。
- 每模型705 invocation、783 logical、1881 agent、7687 metric cells、5393 pairs、514 effects直接对账；GLM59缺答保留，46 logical和46 invocation只是这次恰相同。每模型28 unknown comparisons和366 null cells都仅为 feedback_visible，未补零。两份manifest均453 mixed_or_unknown、330 previously_inspected，R1/R3策略与报告一致；Gap>100为K3 3格/GLM6格。
- 六主方向均为正只支持指定比较。K3全部效应正190/负239/零57/unknown28，GLM正286/负190/零10/unknown28，不能据六主扩张为所有指标或场景优胜。

## 原始证据边界有没有被“正确汇总”掩盖

报告71/128行如实保留新26中19 natural+1 forced为 matching_tool_call、6 best_evaluated_fallback；6项不是缺答，也不等于全部26都是严格有效final配置。旧61 fallback、6 offline_final_answer、204 matching_tool_call只分类旧271终态HPO agent，不能套到旧1855全agent。新26本地表26/21architecture精确匹配仅承接已冻结有限查询；本次不重新unpickle，也不证明官方转换、图hash独立正确、全库真值或训练未污染。Pool NAS是MI/BoN，不是MV。

GLM59最后强制收尾已发出、length/32768/空正文/非空reasoning的近端机制与原独立缺答复核一致。报告没有把正常模型缺答当作ExpGym损坏、没有剔除或全统一补0，也没有声称增加生成预算一定得到答案。该原始来源核验属于此前独立审查，本次未再次读59原raw或重新评分。

报告73行的两模型格式差异计数重新从group_counts相加吻合：Search agent62/25、边界pool47/23、拆票pool6/7；Audit接受差异agent21/2、边界pool17/2，完整planned分母936/234和312/78保留。没有统一parser的反事实端点、重投票或将MV−MI当作信息共享因果收益。报告116行保留真实通用图事件隔离/扣留反馈回流修复，未宣称旧cache时间门全错；明确无旧新消融、不保证提高PoolAct。这些限制避免用摘要正确掩盖已知下层契约差异。

## 成本、提示、设置及交付

成本辅助实际109项算术/引用检查 `76ae7b` exit0，加原K3 allocation metadata核验 `2881d7` exit0：六行tokens、两段相加、有效/未选尝试分账、63unknown和三个complete_total=null、reasoning包含于output，均与冻结证据一致。两段16609请求不是16387有效请求，未选择旧8的222次消耗仍保留。三顶层allocation合计9366784 GPU秒/2601.884444444444 GPUh proxy；不是formal-only、利用率或收费。GLM时间差与比例算术正确，更多tokens没有被写成13小时耗时的因果分解。此次未重新取得05:17:33.061708的原始启动记录，只核报告沿用时间及结束ROOT记录的差；不将这项算术核对冒称原启动日志的独立复读。

R3只是seed blocks，样本SD不是CI，orders/N4/问题不能冒充IID重复；全部CI/p为空。非盲开发、seed有效性未证、温度/推理profile/任务量与论文差异均披露；论文HPO缺有效performance记0与本研究unknown/infra分列不被伪称完全等价。论文设置段落与固定本地main.tex对应段落一致，不因主项方向相符就称paper数字复现。

新K3提示审计289请求/8 invocation/26owner、60个marker观察/51请求、全历史、source-bound/candidate/mixed零，与ROOT有限输出证明一致；旧K3/GLM coverage及fresh-review字段边界未抹去。字面source零命中不是所有prompt零命中、语义匿名、全reasoning/template审计或无训练污染。Pool context描述为本地chars/3估计，不是实际tokenizer；精确先前静态解释还包括保留reasoning及native schema，不改变参数。

报告126–130行准确承接最终strict341全字段不变、775 records、7588非fixed8格、旧23负/五主不变，173预定允许范围内仅162改变；本次没有改阈值或再次运行merge。旧3.10的18 SD-only 1ULP严格失败仍独立保存。K3显式3.11/GLM公开回放3.10是分析字节兼容配置，不是模型runtime更改；没有凭数学匹配倒推历史裸python身份。GLM既有公开37bundle/71634文件与十AN2字节回放各有ROOT控制证明；新K3联合公开恢复/回放仍pending，本复核不替代发布。

## 收口

全部具体数值检查与真实工具记录见 [CHECKS.json](CHECKS.json)、[EXECUTION.json](EXECUTION.json)、[INPUT_REFS.json](INPUT_REFS.json)。小型只读schema探查 `570187` 曾将format顶层list当dict而exit1，随后 `42e0a9`按真实结构定向汇总；属于本复核显示helper错误，不是实验或报告反例，未改任何冻结工具。

无必须勘误项；允许ROOT结合本报告签有限接受。后续公开交付需另有真实push/freshclone/restore/replay证据，不能将本次通过改写为已完成那些步骤。STOP-WRITE后不再修改。
