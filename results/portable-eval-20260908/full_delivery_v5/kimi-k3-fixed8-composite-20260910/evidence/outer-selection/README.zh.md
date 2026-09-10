# K3 composite outer metadata：闭合精确复制候选

本目录随最终INDEX生效 STOP-WRITE；candidate/approved=false，不是copy、scan或Git授权。最终使用 MAPPING.candidate.json：55件 /3,605,605 B，SHA 1d3ec7c75a3ae0a77878e428fceca5c5ad1929cbd0f600b963e8e08539dca150（67,541 B）。另列9件既有公开工具复用 /109,558 B，不重复复制这9件。

## 最终有限范围

| copy组 | 件数 | bytes |
|---|---:|---:|
| 最终controls选择及其独立metadata旁证 | 11 | 920799 |
| 原467 scope/prepare与真实失败扫描证据 | 12 | 1060152 |
| ROOT浏览文件copy GO/EXIT | 2 | 24667 |
| 新466公开controls scope/prepare与成功本地pipeline非payload证据 | 13 | 1466783 |
| verifier v1历史467范围 | 6 | 50688 |
| verifier v2最终466范围 | 6 | 50821 |
| 原GLM单文件baseline（供原CPU测试） | 1 | 12412 |
| verifier独立工程peer | 4 | 19283 |
| 合计 | 55 | 3605605 |

普通metadata目标为 `<new leaf>/evidence/workspace/<source workspace-relative path>`，保持原目录层级，不扁平化、不修改字节或原绝对provenance。工具17件按下节放在tools层；source与target均唯一、无文件/目录前缀冲突。

本55不包含本候选自己的文件，不自引用其SHA。ROOT工程准入小文件、ROOT其它outer主文档、flatunion及bundle另由ROOT处理，不递归纳入本映射。bundle的5个metadata及tar、旧34包、新raw1072、恢复payload均不重复copy或读取。

## 原467与公开466分开

原467新controls /195,086,721 B的完整选择和首次scan exit1原样保留；pack/restore当次未调用。ROOT_PUBLIC_SCOPE仅将公开子集减为466 /195,085,429 B，排除明确1292B的合成CPU测试收据。原扫描规则未改；ROOT没有据此断言已证明真实密钥泄漏，没有删实验raw、成绩、unknown或改变科学分母。被拒原收据不读、不进入outer，也不提供公开替换版本。

PUBLIC_SUBSET_IDENTITY.json记录0d71a5实际metadata差集核验：只少该一行，剩余466完整row对象逐字段相同。其“非实验CPU”分类承接ROOT判断，本作者未读取被拒正文。部分保留证据仍引用私有收据身份，所以不是全部私有审计链的自包含副本。

新466的原scan/pack/restore及全字节比对均有已闭合原收据，旧失败不覆盖。新增7个operator/CLI/whole/README/scan/lock/restore-COMPLETE已d39552核SHA/bytes/stat并末尾重hash；这里只选择证明，不重跑这些流程或再次读取source/restored payload。新本地成功不替代最终whole outgoing四来源显式core=0扫描、Git公开、fresh union恢复、post-verifier和AN2回放。

## 工具与相对依赖

9件既有公开原件沿 TOOLS_REUSE.candidate.json 的精确repository路径复用。5个原恢复工具保持旧K3 `payload/tools/publication/` 布局；collection→common/restore/validator，pack→common/restore，restore→common，common→validator。初文件4条edges只是摘要，最终MAPPING列7条相关文件边。validator应显式给正确workspace。

prepare.py直接复用为审计源码；它在旧evidence的位置不满足相对common/validator导入，不能称原地可运行。ROOT决定不为它新增copy/wrapper；如调用者另行运行，必须按原publication兄弟布局取得精确原件。原relocator及README/CPU三件复用GLM已公开导航，只需该三文件，不需要下载GLM全部37包。旧CPU证明不是本次K3实际重放通过。

新增工具17件保留四个相邻目录：

```text
<new leaf>/tools/publication/
  k3_union_remote_restore_candidate_v1/       # 原6件，467历史，非最终入口
  k3_union_remote_restore_candidate_v2/       # 最终6件，466公开范围
  glm_full_remote_restore_candidate_v1/      # 仅verify_restored_files.py
  k3_union_remote_restore_peer_v2/            # 独立peer原4件
```

最终实际入口是v2/verify_restored_files.py，仅stdlib；相邻v1与GLM baseline使原tests/peer的固定源码读取布局可用。源字节不改、没有新wrapper。peer3/3 fake通过、0阻断，但实际restore/verifier仍须ROOT独立GO；本作者未运行这些tests或真实入口。

冻结历史README中的绝对审计refs不保证全部可访问。成功pipeline原README的bundle相对链接也未借复制bundle元数据强行补齐；查bundle请用ROOT新leaf/flatunion正式导航，不改写原README或承诺所有旧链接原地可点击。

## 实际核验与独立范围

a676a4实际exit0核全部55源SHA/bytes、读前后stat，末尾重hash同集合；目标当时全不存在、既有ancestor无symlink，无目标碰撞。另重核9复用文件的原source和当前repo公开路径字节。只是当时只读观测，ROOT真正copy必须再次no-clobber/身份检查。

原5恢复工具有独立peer三方字节/layout核bfee36；初26准备metadata有独立peer a82907，仅读4份候选metadata，不冒称其独立读55全部原件。最后verifier4件peer由format实际3/3纯fake审阅；本作者fdce01全文读及3aeac0全4 pin核。ROOT另主读并接受该工程组，准入文件不在本55里。

本作者仅读明确非secret源/metadata与原工具代码；未递归WS/OP/serving/payload树，未读tar、raw、恢复payload、被拒CPU收据或密钥，也未进行copy、Git、网络、模型、评分、Slurm、scan/pack/restore/verifier。不能把本候选称为公开验收或整项目完成。

## 历史准备保留

PREPARATION_MAPPING.json保留最初19件，CLOSED_ADDITIONS.json保留当时新增7件；其中pending字段不倒写为成功。最终以MAPPING.candidate.json为准。

385d9b的只读工具枚举helper在读取文件前因tuple unpack退出1，后guard阻止任何候选写入；改为字段字典后c2c27f通过。peer曾将FULL_DELIVERY或TOOLS_REUSE简称误作路径，之后用明确原名完成；没有修改原件或重跑实验。最后工程peer因旧范围等待曾处于idle，确认冻结466范围后一次followup恢复审阅，并未重复启动另一审阅者。具体真实工具回执见CHECKS.json。

未来dynamic public scan/Git/restore/AN2证明保持outer独立，不作为本组无限ref依赖。
