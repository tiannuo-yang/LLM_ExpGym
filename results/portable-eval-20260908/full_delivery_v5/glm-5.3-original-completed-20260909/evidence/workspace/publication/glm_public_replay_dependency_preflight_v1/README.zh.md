# GLM 公开数据的 AN2 离线重放依赖预检

结论分两层：**实验分析依赖在指定 union 中闭合；路径迁移工具链尚须外层另行交付。** 本次只核冻结 metadata，不证明实际恢复、迁移或分析已经执行。

两清单：原run70,520件 +公开controls1,114件 =71,634唯一件/3,467,116,893 B，无路径重叠。不纳入已排除的非实验 operator invocation，不改任何清单。

## 已闭合的离线分析输入

- 从已绑定 records.json 仅取source_sha256：783 records、2247次/2247个不同源引用；与source_index恰好同集合，旧绝对路径唯一且规范、均位于原workspace。
- 2247源全部精确映射原run成员，声明SHA均相同；总626,156,977 B，最大4,556,665 B，无成员超过原工具100MiB上限。只比较metadata中的声明字节数/SHA，未读取源内容。
- manifest、records、oracle、input_pins、source_index五份原输入在public controls逐path/bytes/SHA匹配；三input_pins、records→manifest/source_tree、manifest→oracle绑定一致。没有读oracle数值。
- 原AN2三代码都在public controls，按原共同根N保留下面布局及原SHA；源码静态核显示只用标准库与显式分析输入，不调用旧planner.inventory/main、原backend或模型：
  - operations/restart_user_20260909/analysis_candidate_v2/analysis.py，30377 B，5df8525973261d61b5c3c373945129db22979131e6ce3b586c8913efeed256bf。
  - design/formal_export_candidate/converter.py，28464 B，0261660a38d80c9135efc498f11580ef3fea26de00e6061824e9c9380662547f。
  - design/formal_matrix_candidate/planner.py，26895 B，13914a8341765d0c0ed75812d9b79d2281478b7fc82accef64deaa70a5ead68a。

N为 portable_eval_20260908/source_cohorts/v4/portable_eval_20260908。如果三件以后跨bundle分布，须按原相对布局在新分析根复制原bytes，不能扁平化或替换planner。86件v5源文件及source_acceptance引用也在union匹配，但它们不是这条AN2调用路径的额外动态import。

## 尚未自包含的部分

1. 固定relocator v2代码与README不在71,634原件中：这是实际发现的工具交付缺口，不能称该union自带完整迁移入口。ROOT明确后续将原代码、README、CPU receipt三件加入外层公开tools/evidence，保持原pins，**不重封/修改1114 controls，不计入71634包内原件**。本项未执行该补充，也未证明它已scan/公开/freshclone通过。CPU receipt只从既有明确publication metadata行取得9054 B/f3b8fbec…身份，没有读其payload。全部精确pins见RECEIPT.json。
2. manifest声明23个原runtime辅助路径，仅audit.orders与hpo.config两个原路径在union；其余21原路径未入。其中原hpo.oracle路径未入，但五输入中的export/oracle.json已按同bytes/SHA携带；另20项为数据集、NAS/ParamNet表与runtime配置。AN2只核其metadata/使用显式export oracle，不读取这些原路径，所以不阻断上述离线汇总；**不能据此称原backend/模型重跑环境完整**，也不证明数据集或后端真值正确。

## 范围、实际检查与待办

source_index仅提供路径，不能单凭它证明SHA闭包。ROOT在初始范围后明确追加许可：先核固定records.json完整bytes/SHA，仅解释manifest/source_tree/source_sha256结构。未解释或输出telemetry、答案、分数。所有原始raw/恢复件/活动bundle均未读。

实际metadata全核exit0：7f1d56；原五输入/三代码检查ea6afc；独立静态子审三个exit0见收据。早期d5f1e2的membership断言失败保留：它准确暴露了relocator不在union，而不是实验源缺失；随后未改变原范围去伪造通过。

下一步仍需外层原迁移工具交付→真实完整restore验收→固定relocator产生新路径索引→原AN2不改源码离线重放→全原输出逐件比对。此处不实际执行这些步骤、不新建GO、不调用scorer/model/backend/API/Git/Slurm，仅在本新目录写预检记录。

