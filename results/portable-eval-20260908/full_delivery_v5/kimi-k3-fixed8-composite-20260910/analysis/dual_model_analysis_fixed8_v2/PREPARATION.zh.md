# 固定 8 项基础设施恢复后的双模型报告准备

状态：作者准备稿，尚未冻结、未发布、未获得最终 post-report 验收。仅整理已封存报告及元数据；K3 新 composite 的实际 18 输出及 ROOT 外部 pins 尚待提供，不能据正在写入的结果预判终点。本目录不修改旧报告、旧失败、旧费用、原始结果或科学代码。

## 固定口径

- K3 是原 697 个成功 invocation 加用户指定的全部 8 个基础设施失败 invocation 的新 attempt，不是新一轮 705 个独立任务；不是按成绩挑选，也不把新 attempt 当新 seed。原 8 个失败及费用仍保留。Pool 始终恢复整个 N4，不挑其中成员。
- 每模型仍是 705 invocation / 783 logical / 1,881 agents。Search R1；Exp Audit R1 内含三个固定 orders；Pool Audit 原 default order；HPO/NAS 三个预声明 seed blocks。R3 不等于已证明独立同分布，orders、题目和 N4 成员不增加独立重复数。
- K3 新结果只可能改变涉及固定 8 个任务的分组；GLM 全部数值、K3 Search/Audit、非涉及任务及原 31 个负性能比较必须保留。此前静态映射的 173 个可能受影响 comparison / 341 个不受影响 comparison 是验证范围，不是新结果。新负值或 unknown 一律保留。
- 推理 tokens 是 output tokens 的子集，不能额外相加；失败 attempt 用量 unknown 不填 0；有效结果费用与包含原失败的全尝试费用分列。
- 原修正包括一般共享图的时间/预算可见性问题，不仅是 serving 兼容；没有消融可将收益归因于修补。两个模型、最大推理、温度 1 与扩展题集属于 Custom study，不是 paper-exact reproduction 或普遍稳定性证明。

## 已确认 GLM 元数据

正式启动记录为 2026-09-09 05:17:33.061708 UTC，ROOT 核验 execution 完成时间为 18:42:11.600352 UTC；差值 48,278.538644 秒（13:24:38.538644）。这是两记录之间的墙钟区间，不冒称本次直接读取了 execution.elapsed_seconds。

整个 allocation 是 2026-09-08 21:52:40 至 2026-09-09 18:51:24，共 75,524 秒 × 64 GPU = 1,342.648889 GPUh proxy，包含加载、开发/smoke、idle 与正式任务，不是正式任务单独 GPUh、平均利用量或收费，不重复累计服务 steps。

18,403 个已封 attempts 的 input 为 323,702,359，output 为 61,759,454，其中 reasoning 为 59,754,394；三字段 unknown 均为 0。完整 783 logical 的有效子集同值。1,881 个 agent 中 59 个正常 model_no_answer（Search 54 / Audit 5 / HPO 0，分布于 46 logical）。独立原复核确认 59/59 最终 none 调用发出并返回，max_tokens=completion_tokens=32768、finish_reason=length、正文空、reasoning 非空。该近端分类不证明提高预算会答对，也不是独立 tokenizer 重数。

这些 usage 小计表明 reasoning 占 output 的 96.753436%，每个已记录 attempt 平均 output 3,355.944900 / reasoning 3,246.992012 tokens。59 个末次 length 调用的已知 output 共 1,933,312，占该输出总量 3.130390%。这只是分布量化，不是吞吐测量；不能据总 tokens 把所有墙钟归因于 reasoning，排队、并发、工具/验证、模型速度与长尾也没有在这里做因果分解，更没有更小推理预算的反事实实验。

GLM fresh GitHub 原件恢复后的原 AN2，以 /usr/bin/python3 3.10.12 重放已获 ROOT 十文件逐 byte/SHA 验收。先前 3.11 重放的 34 个次要 SD 之 1 ULP 差异及失败对比记录保留；所有主项未变。原历史导出只记裸 python3，不能据 3.10 匹配而断言历史解释器精确版本。

## 等待后再定稿的项目

1. ROOT 指定 K3 composite 18 输出的最终 refs；据原 effects/summary/cost/provenance 元数据抽取，不重新评分或读模型 raw。
2. 复核固定 8 选择、697 原成功不变、341 不受影响 comparison 一致；计算 K3 新 E-H 和受影响次要项，保留新负值/unknown。
3. 新 K3 whole-run、提示审计和实际 allocation 的精确 refs。ROOT 已告知 289 成功请求 / 8 invocation / 26 owner；60 marker observations 来自 51 请求，均为历史（nasbench 41 / nasbench101 19），source+mixed=0；不能写成“全 prompt 0”。ROOT 通知 job1203933 共 11,261 秒、64 GPU，即 200.19555556 GPUh proxy，最终引用仍待原件 pin。
4. 有效费用和两段所有 attempts 的费用分别报告；原 63 个失败请求的 unknown 成本不因补齐而消失。
5. 终稿后独立非作者 post-report 复核，未完成前不得称最终科学验收或新 composite 已公开交付。

## 已核输入身份

路径以本 operations/restart_user_20260909 为根，publication 另注明。

| 文件 | SHA256 |
| --- | --- |
| dual_model_analysis_v1/REPORT.zh.md | 2cb93a26292607c7707bad1e12b4b26dd3064c77e25fe68688370864af7ff70e |
| dual_model_analysis_v1/NUMERICAL_EXTRACT.json | 2a19ba7c0488c3b9cb0639feab47d0ec734fae2eb334af557248eb4b511c5f46 |
| dual_model_analysis_v1/INPUT_REFS.json | d81a1710d53cf2502dba3cbcb3c0152be84fac58b80ef481dc92072dbc282210 |
| dual_model_analysis_addendum_v1/README.zh.md | 685f7f597609e150fb5b4dd98fb4fcdbf399f368e56fe85c48e1909ba0d0d94a |
| actual_formal_export_glm_completed_v2/EXPORT_INDEX.json | e32cab1af07054e76503aab79c66b76bcc216d2021cf0f46cd638340023bbca7 |
| actual_formal_export_glm_completed_v2/effects.csv | 50943f354df56026a1701826b6d7c3fd0a2f5b5a615353374884ee0d90e030a8 |
| glm_formal_terminal_root_v1/ROOT_TERMINAL.json | 7298e516b2171c46085359320138513b6f9f7fb40b2ccd593f57b366f01c261a |
| glm_formal_service_release_v1/operator_finish_v1/final_scheduler_snapshot.json | 99b02ee16a810e5c80ae3530fd5895bd4d3c1d24641d4d896132c4d748d29fb1 |
| glm_post_analysis_usage_review_v1/actual_v1/SUMMARY.json | 79bbee9f499c66810ac5f6fb77eed6f1750469cd7153194664ad83074a81ef20 |
| glm_missing_cause_post_analysis_review_v1/REVIEW_EVIDENCE.json | 3222414d3e2379d35250b1fea1b5a5dbf2f994822be80d3a2b38ed6b539b222a |
| publication/glm_public_analysis_replay_py310_v1/ROOT_ACCEPTANCE.json | a9d7ce0af44c24bf6fdb703106f25217a9bb1be5880a2edd31d91d744d4fe668 |

准备期间仅一次尝试读取不存在的 SUMMARY.json，立即以已索引 effects.csv/EXPORT_INDEX 元数据替代；没有运行 AN2、scorer、模型或改写任何原件。最终还应绑定精确新输入与作者检查，而非把此准备记录当验收。
