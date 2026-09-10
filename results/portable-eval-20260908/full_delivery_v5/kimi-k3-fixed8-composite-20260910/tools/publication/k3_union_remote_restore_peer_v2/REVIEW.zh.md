# K3 union 公共恢复 verifier v2：独立有限工程审阅

结论：**PASS_BOUNDED_ENGINEERING_CANDIDATE_REVIEW，未发现阻断这次最薄适配的逻辑问题。** 这是候选准入审阅，不是实际公开恢复或科学验收。生产 pin 为 `80f35ba87e127d13a73daf958f7fc3d44f0f07a34aab2c512eaedd485b14866e`。

复核者 /root/format_diagnostics 不是本次 K3 union 适配作者；曾参与原 GLM 基线适配及其他审计，故不冒称未接触实现的盲审。全文读原 GLM 209行、新生产216行、测试261行、README78行、两层精确diff及CPU收据。原GLM与新候选的8个辅助函数、完整member loop逐字/AST相同；member loop之后直到成功receipt写入的全部main AST亦相同，CLI AST相同。main仅collection定位、exact IDs、分类门、raw筛选4条语句不同；v1→v2仅2行固定数值变化。候选exact6/50821B与13个明确input pins前后校验通过。

固定范围36包/66643原件/1751137861B，与ROOT公开466/195085429B决定一致。旧33包64188件、旧controls917件、新run1072件均保留；排除的是ROOT明确的一份1292B synthetic CPU收据，不减少实验分母。这里raw包是完整run原件，不是HTTP请求计数。本审阅没有读该排除文件或重新判定scanner，没有将不自包含的私有证明引用链冒称全部公开。

## 三组实际纯合成检查

唯一session10682，`d7b095→3345a6`，自然exit0；3/3通过、0skip，14.732秒。证据在 [CPU_RECEIPT.json](CPU_RECEIPT.json)。

- 独立AST/逐字核上述不变核心、固定counts/maps及无CLI缩小范围入口；从原GLM到新main只有指定4处变化。
- 在36包各1字节的fake中，False退出码、错误newcontrols类别、bool成员数均拒绝且无成功receipt；恢复正确fake元数据后完整通过，各36原件恰hash一次、输入树字节不变，旧默认INDEX不被选用。
- 第一个fake payload读取后修改ROOT proof，最终metadata重哈希拒绝，未提交成功receipt。

为节省重复代码，仅复用作者Fake目录生成器；异常注入、断言、AST检查由本审阅独立编写。mock只发生在测试进程的4个数值集合，类别maps未mock；未把fake36件说成真实66643件验收。真实候选/旧工具未修改，无actual tar/raw/答案/key、restore、模型/API/scorer/Git/network/Slurm。临时synthetic目录已清理。

## 入口与证明边界

新入口固定读共同祖先下 `INDEX.kimi-k3-composite-v1.json`，不存在时不fallback；member的相对路径仍受原canonical/NoFollow/无父目录跳转检查。ROOT需先验证union旧34行仅前缀迁移、最终collection SHA与fresh Git提交语义，再给实际GO；本verifier不独立重做Git。真实CLI退出必须exact-int0并绑定collection/commit，原COMPLETE结构及false历史字段不改。逐文件大小/SHA、完整ownership/pathset、无INCOMPLETE、metadata末次重哈希、fresh输入树外receipt和原100MiB/8MiB限额均保留。

这是对已闭合、无其他writer恢复目录的逐文件读取核验；它不承诺对抗并发payload改写的原子全树快照。只重哈希metadata的尾门不能升级为payload的第二遍全量读。该原机制未改变；实际必须保持ROOT声明的闭合输入。通过也不证明POSIX metadata、科学评分、backend/runtime自包含或原AN2十输出回放，后者均另做。

## 外层放置与收口

本组可原字节复制为 `newleaf/tools/publication/k3_union_remote_restore_peer_v2/`。若希望CPU例子在该布局可运行，其父目录需相邻已有 `k3_union_remote_restore_candidate_v2/`、`k3_union_remote_restore_candidate_v1/`、`glm_full_remote_restore_candidate_v1/`，分别取新的tests/source、旧v1 source、GLM source；不需要real archive或ROOT scope文件来执行fake。CPU收据中的全部历史绝对refs是审计溯源，不承诺公开目录包含它们全部。仅作证据镜像也可，但勿在其他不相邻目录声称原地可执行。

无须修改冻结生产或额外扩大测试。实际restore/verifier与ROOT工程接受仍须单独授权；本报告不签发该GO。STOP-WRITE。

