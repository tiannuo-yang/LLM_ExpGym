# 历史参照更正：采用用户指定的paper-analysis发布快照

本版本更正历史参照，采用用户指定的paper-analysis-20260916在2026-09-18发布的既有轨迹重评分。原917条的新实验分数、费用、scaling和消融全部保持不变；v1报告和旧历史分数保留。新增同版本Max417另行完成主对照，继续使用本轮冻结88评分契约，不暗中迁移到0e评分。其中Low与历史Max的比较是跨执行版本、跨终答提取/评分版本的描述性次级比较；本轮scaling和消融仍是同88版本内部比较。报告尚待统一独立复核。

历史实际执行仍是 `8dfea729…` / `glm_original`；重提取与评分代码是 `0e6c51b6d86f42437038518c2fc8adc510901c0b`；本报告采用用户指定的发布快照 `2a78fc8ef0d0882d0e94080f0bbfec1fc789946a`。本轮Low、scaling、消融以及新增同版Max仍使用 `88e27ad5963625ccbd3f9269dce0f95412b8d786`。历史执行源码没有被改写成评分代码版本。

417个历史N1 result SHA与旧trace SHA一一匹配，仍是原417次执行；13条指标改变来自既有轨迹的重提取/评分。原logical_id与新slot_id并不相同，桥接以原件SHA和任务／预算／order／repeat／seed等共同身份核对。新表保留原评分与原执行终态，不把重评分状态冒充原运行终态。

上游新版本identity为`existing-trace-rescore-v1`，adoption_state仍是`candidate`。这是用户明确指定的报告参照，不表示本研究修改了上游版本状态或重新运行了其评分代码。

旧v1曾按旧原分描述Audit117条中的22个非空格式无效和2个forced-length缺答；那是旧评分/旧提取记录的诊断，不可继续拿来解释最新重评分差值。尤其Free的旧双零11条贡献+27.30pp、其余28条−4.98pp，是按旧结果筛选的事后分解；它被保留为旧版本历史说明，不作为v2当前比较结论。此次实际改变的历史分数不等于“所有22个旧格式问题都被同一种bug修好”。

此前“评分器AST不变”的结论只针对旧4b/8d执行代码与88历史调查，不能扩展到这里的0e重新提取/评分契约。EA/LA定义不变不等于完整评分实现不变：0e更改了终答提取、Audit JSON wrapper接受及vote字段规范。本轮917和新增同版Max不做隐式重评分，因此跨版本历史对照仍不构成纯effort因果结论。

本轮Audit prompt相对于旧执行仍存在已核实的两处差异；重评分不改变历史模型实际接收的消息、动作、共享状态或已消耗费用。GLM历史81条HPO的Gap/Gap0/RawPerf scalar全部齐备，发布表Gap0与本研究用的Gap逐条相同；本次未重新读取或解析final config，不能将此等价性泛化到其他模型或指标缺失的记录。

本轮88已经包含完整HPO graph identity修复：完整payload SHA256及快照内无碰撞显示别名；静态对比的88与0e/current2a共享graph实现一致，相关差异仅是本研究peer_context段。因此，历史报告中97个HPO pool需要补控制运行的旧图碰撞限制不能直接套到本轮NAS101。这个静态事实不表示本轮已经以0e统一运行，也不消除88仍有的终答解析边界。见[既有静态口径审核](PROVENANCE.md#ref-b9c26f5b571842ef)。

[用户指定的精确发布快照](https://github.com/tiannuo-yang/LLM_ExpGym/blob/2a78fc8ef0d0882d0e94080f0bbfec1fc789946a/results/paper-analysis-20260916/README.zh.md) · [冻结参考包](PROVENANCE.md#ref-a08f1c61b2a4def0) · [417新版历史绑定](PROVENANCE.md#ref-b918c287cf7daf97) · [旧v1指标与结论](PROVENANCE.md#ref-2467e8d17600e7ac)
