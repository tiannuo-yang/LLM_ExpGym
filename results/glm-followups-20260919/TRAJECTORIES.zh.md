这份材料只解释原定六类任务 first/last 的 12 对同版 Low/Max 轨迹。两侧 source 均为 `88e27ad5963625ccbd3f9269dce0f95412b8d786`，tree 为 `2fa93be36614ecf6c29c3cd22f5283a6694e440493da92106f371fb4dab243b5`。首请求完整 system/user/tools、采样参数与 task/budget/data/order 的既有配对检查全部通过；两层 effort 分别为 low/max，运行身份及隔离缓存键允许不同。数据字段缺少文件 SHA 时仍为 unknown，不能以 null 相等证明文件内容。

本次只汇总已经完成的 24 条审阅和配对小报告，没有读取 raw、API dump 或 owned-cache，没有模型调用、重评分或新增案例。原证据的路径/SHA 从小报告继承，本次实际读过的小报告另列在 INPUTS_INDEX.csv。

固定样本中，Low/Max 分别 104/116 次 API、90/101 次实际工具、5/8 次 forced、2/3 次协议失败、0/1 次 length；两侧均无 model_no_answer。协议失败包含真实 multicall/length，不能并入网络重试；两侧 HTTP 重试为 0。所有 24 条既有机械与评分保存一致性检查通过，不表示模型答案全部正确。

下面的值是原始评分；Search 为 F1，HPO 为原始 performance（不是 Gap），Audit 同列 EA/LA。API/工具/强制列写作 API 次数 / 实际工具次数 / forced 次数。

| 固定案例 | budget | Low 原分数 | Max 原分数 | Low API/工具/强制 | Max API/工具/强制 | Low→Max 协议/length |
|---|---|---:|---:|---:|---:|---:|
| Audit first | cost_free | EA 100.00%; LA 94.12% | EA 100.00%; LA 94.12% | 30/29/0 | 25/24/0 | 0/0 → 0/0 |
| Audit last | cost_tight | EA 41.18%; LA 82.35% | EA 41.18%; LA 94.12% | 5/4/1 | 5/4/1 | 0/0 → 0/0 |
| NAS101 first | cost_free | 0.942374468 | 0.946581205 | 12/11/0 | 31/30/1 | 0/0 → 0/0 |
| NAS101 last | cost_moderate | 0.936631938 | 0.938635131 | 9/8/0 | 5/4/1 | 0/0 → 0/0 |
| NAS201 first | cost_tight | 0.901986667 | 0.901986667 | 4/3/1 | 6/4/1 | 0/0 → 1/0 |
| NAS201 last | cost_tight | 0.731466667 | 0.709066667 | 4/3/1 | 4/3/1 | 0/0 → 0/0 |
| ParamNet first | cost_tight | 0.709884689 | 0.712578417 | 5/4/1 | 5/4/0 | 0/0 → 0/0 |
| ParamNet last | cost_tight | 0.936770689 | 0.709294438 | 8/7/0 | 6/5/1 | 0/0 → 0/0 |
| Whatis first | cost_free | 0.857142857 | 0.400000000 | 11/9/0 | 12/9/1 | 1/0 → 2/1 |
| Whatis last | cost_free | 0.000000000 | 0.166666667 | 7/6/0 | 8/7/0 | 0/0 → 0/0 |
| Whois first | cost_tight | 0.000000000 | 0.000000000 | 4/3/0 | 5/4/0 | 0/0 → 0/0 |
| Whois last | cost_tight | 0.000000000 | 0.000000000 | 5/3/1 | 4/3/1 | 1/0 → 0/0 |

Audit Free 两侧最终相同，Max 少用 5 次核验；Tight 两侧 EA 同为 7/17、Max 的 LA 更高，但均只核验少数假设并超预算。Whatis first 的 Max 查到了相关文章，却收缩到单个候选，且发生真实 length 后 forced；两侧 Whois 都未补齐关系链，零分是保留的错误回答。HPO 两侧都返回了各自可见 best，却走过不同配置与耗时路径：NAS101 first 的 Max 用更多评估略好，ParamNet last 的 Low 用更多较便宜可见试验明显更好。以上差异不证明某 effort 普遍更强，也不解释全部 417 对的差值。

**Audit first**。Low：29 次反馈逐步纠正证据：nda-16 [33]→[]；nda-19 [64]→[17,64]→[16,17,64]；nda-12/13 补齐 Carveout set。最终 17 项证据均对应 correct 反馈。模型知道反馈只核证据，对 nda-8 标签仍犹豫。 Max：24 次反馈完成 17 项证据；nda-7 [17]→[]→[16,19]，nda-16/20 [33]→[]，nda-19 补 [16,17,64]。把标签也称 confirmed 超出了仅核证据的反馈能力。 配对观察：两侧 EA=1、LA=16/17；Max 用较少核验得到相同最终指标。不能将证据全对当作标签全对；未重建未知 gold 标签。 [Low 既有审阅](PROVENANCE.md#ref-4e35e4ee5408870f)；[Max 既有审阅](PROVENANCE.md#ref-4e24543debb4a091)。

**Audit last**。Low：nda-15 [50] 失败后改 [45] 正确；nda-7 [40] irrelevant 后过度推断 NotMentioned。剩余约 13 秒虽说 finalizing，仍调用 nda-3 [25] 并超预算；forced 提交完整 17 项。 Max：仅实际查询 nda-3 与 nda-7；[25] irrelevant 后未验证空证据便推 NotMentioned；nda-7 [38] incomplete→[38,40] irrelevant。约 22 秒仍试 [38,39]，结果隐藏；forced 猜该证据集，其余 15 项未经工具验证。 配对观察：同为 4 次工具、一次隐藏、一次 forced，EA 均 7/17；LA 为 Low14/17、Max16/17。差异来自不同查询和最终判断，不能从本对证明 effort 的一般因果效果。 [Low 既有审阅](PROVENANCE.md#ref-63694de8b915a57b)；[Max 既有审阅](PROVENANCE.md#ref-7b5033e0edf29e4a)。

**NAS101 first**。Low：11 次评估后自然返回 tool0006，0.9423744678497314，为已见最佳；后五次尝试均未胜出。保留边优先级平局及文字计划与 native 参数不一致。 Max：用满 30 次评估后 forced 返回 tool0023，0.9465812047322592；tool0028 改无输入连接节点得到并列。23 个未超越先前最佳的评估保留；call24/26/29 的拓扑描述与实际边参数不一致。 配对观察：Max 进行了更多评估并得到稍高的可见最佳；低效或失败尝试未剔除。两侧最终都对应各自可见 best，不能将架构文字解释直接当已执行网络。 [Low 既有审阅](PROVENANCE.md#ref-ac0464943a685b5f)；[Max 既有审阅](PROVENANCE.md#ref-bfab53c47de643e7)。

**NAS101 last**。Low：8 次评估、自然返回 tool0001，0.9366319378217062，与 tool0003/0008 并列。记录中完整链的文字描述不符实际缺失 1→2 边；五次更差评估保留。 Max：前三个可见结果 0.8458867470→0.9294871688→0.9386351307；仅余约 4944 秒仍发起约 16023 秒评估，第四次隐藏。forced 返回 tool0003，没有使用隐藏的 0.9387353063。 配对观察：Max 用更少评估获得略高的可见最佳，同时以预算越界结束；Low 自然停止。隐藏结果不充作模型已知的更好解。 [Low 既有审阅](PROVENANCE.md#ref-f37390d48ecf7292)；[Max 既有审阅](PROVENANCE.md#ref-4fa6c96cd9db65a2)。

**NAS201 first**。Low：三次评估；第二个可见结果略低于基线，第三个超预算隐藏；forced 返回首次可见最佳 0.9019866665364583。 Max：先提出四个 native 调用，整轮被单调用约束拒绝，再逐个执行四次评估。可见第二/第三次更差，第四次隐藏；forced 仍返回首次最佳 0.9019866665364583。 配对观察：相同最终分数；Max 多一次实际评估及一次被拒绝决策。协议修复成本保留，不把四个未执行提案算成四次评估。 [Low 既有审阅](PROVENANCE.md#ref-80a16b7880edaff5)；[Max 既有审阅](PROVENANCE.md#ref-3facdf45748085b7)。

**NAS201 last**。Low：三个配置依次评估，可见第一项 0.7314666666666666 胜第二项约 0.701333；第三项隐藏。forced 精确返回第一项。 Max：可见首次 0.7090666666666667 胜第二次 0.6682333333333335；第三次隐藏的 0.7158 未被采用。forced 返回首项；关于 batching 的规则回忆无指令支持，但实际仍单调用。 配对观察：相同工具次数与预算停止形态，Low 找到更高的可见 best。均未泄漏隐藏评估结果；此差异不是缺答或评分记录故障。 [Low 既有审阅](PROVENANCE.md#ref-dca422bb8fa6fc35)；[Max 既有审阅](PROVENANCE.md#ref-6c608df7b336cc3e)。

**ParamNet first**。Low：三次可见性能 0.651582115→0.709165131→0.709884689；第四次更高结果被预算隐藏。forced 精确返回第三项。 Max：四次全部可见，第二次 0.712578417 为最佳，后两次下降。剩余约 28 秒自然停止；声称已无法评估过于绝对，未试配置耗时未知。 配对观察：工具数同为 4；Max 稍高且自然停止，Low 第四次被隐藏后 forced。比较以各自可见最佳为准，不能用 Low 隐藏的 0.715096869 替换结果。 [Low 既有审阅](PROVENANCE.md#ref-cdd3a94d298054bd)；[Max 既有审阅](PROVENANCE.md#ref-772fd7c536edaa2f)。

**ParamNet last**。Low：七次全可见，调宽度、批量、dropout、学习率、层数和形状；中途下降保留。最终自然选择第七次 0.936770689，最后剩余约 17 秒；少量短计划与实际 shape 参数不同。 Max：前四次可见 0.475260070→0.684350974→0.700610584→0.709294438。剩余约 49 秒仍试已估约 126 秒的学习率变更，第五项隐藏；forced 返回第四项。 配对观察：Low 以更多且较便宜的可见试验覆盖了不同配置，最终分数明显高于 Max；Max 隐藏的 0.834554501 不能代替返回值。这里只观察到具体搜索路径和预算使用差异。 [Low 既有审阅](PROVENANCE.md#ref-901fc05e14637a95)；[Max 既有审阅](PROVENANCE.md#ref-41afb635f1ae368e)。

**Whatis first**。Low：九次有效搜索后返回 Bart/Hugh/Zachariah 三个有文章支持的生日；省略 son of sister of aunt 中的 sister 层，未把已见的 Darrell 生日纳入集合。先一次双调用被拒后逐次恢复。 Max：同样九次有效搜索，已见四个相关生日，但倾向假定只有一个 intended target，未遵循 ALL 的覆盖要求。call11 外部为空、length 截断；随后 forced 只返回 Zachariah 的生日。 配对观察：Low F1=6/7，Max F1=0.4；两者都未满分。Max 的一次真实 length、forced 和候选集合收缩均保留；长 reasoning 中段未读，不能描述其全部思考过程。 [Low 既有审阅](PROVENANCE.md#ref-eec8ae7d56304491)；[Max 既有审阅](PROVENANCE.md#ref-ed8934ee60b23da6)。

**Whatis last**。Low：将 archivist August 的 sister Maryam 的 children 错当 cousins，查询其父 Jakob 后返回真实文章里的 0942-11-14，并附解释。日期有出处但关系路径错误。 Max：建立 August→母 Luisa→姐妹 Freda→女 Lyndsey→父 Rene 链，生日 0910-07-14 有直接出处。只覆盖首条职业文章，虽想到可能多名 archivist 仍假定单一目标；重复查询同文章为免费。 配对观察：Low F1=0，Max F1=1/6；Max 有一条成立的路径但集合覆盖仍不完整。未重评 Low 附解释格式对零分的贡献，也未从部分分数重建 gold 全集。 [Low 既有审阅](PROVENANCE.md#ref-98daffa4b1ee8369)；[Max 既有审阅](PROVENANCE.md#ref-97e66f73e8bd2d39)。

**Whois first**。Low：只查到 location manager Dollie 及父母 Yasmin/Wallace，未建立 sibling 的 sibling；将未列兄弟姐妹过度推为 only child，仍猜 Dollie。 Max：在相同父母资料之外增加一次 sibling 查询但又取回 Dollie 文章；中间 sibling 仍未建立，却由关系对称性猜回 Dollie。 配对观察：两侧 F1=0、自然给出同一个不受完整关系链支持的名字。Max 多一次搜索和更多已报告 reasoning 并未填补缺证；零分不是拒答。 [Low 既有审阅](PROVENANCE.md#ref-1316109d3b308d19)；[Max 既有审阅](PROVENANCE.md#ref-3a2fa9d0a627f692)。

**Whois last**。Low：Cory→母 Annmarie→祖父母 My/Deangelo；一次双调用被拒后恢复。第三次实际查询 My 超预算隐藏；forced 猜已见的 Cory 兄弟 Irvin/Kendrick/Oren，代际与题目不符。 Max：Cory→妹妹 Bernadine 后再查 Bernadine，重复确认父母；第三次查 Annmarie 已隐藏，完整 great-grandparent 链未建立。forced 明知证据不足仍猜父亲 Dale。 配对观察：均三次实际搜索、最后结果隐藏、F1=0；Low 有一次协议修复而 Max 没有。具体路径不同，均无法把已见亲属替代题目要求的祖辈关系。 [Low 既有审阅](PROVENANCE.md#ref-c7b400cb84c74ec4)；[Max 既有审阅](PROVENANCE.md#ref-3d9ebb76c367b06f)。

已报告 token 与实际阅读范围如下。token 是后端 usage 的逐 attempt 合计，包含 forced 和被拒绝决策；reasoning 字符是既有人工审阅覆盖范围，两者不可换算，更不能当作隐藏思考量。长 reasoning 中段没有被本次或原审阅补读。

| 案例 | Low prompt/completion/reasoning tokens | Max prompt/completion/reasoning tokens | Low reasoning 已读/总字符 | Max reasoning 已读/总字符 |
|---|---:|---:|---:|---:|
| Audit first | 123955/2553/1451 | 1483625/75371/72518 | 5314/5314 | 23350/283556 |
| Audit last | 25012/1154/667 | 133853/42889/41810 | 1910/2432 | 5740/164253 |
| NAS101 first | 61610/4996/1100 | 758886/52785/41962 | 2464/2464 | 31647/94484 |
| NAS101 last | 33861/2992/694 | 20448/4595/3171 | 1884/1884 | 5438/9849 |
| NAS201 first | 4052/373/47 | 14005/3736/2878 | 164/164 | 5260/8895 |
| NAS201 last | 4016/338/21 | 6033/1294/908 | 85/85 | 3010/3010 |
| ParamNet first | 4607/497/41 | 12977/4807/4077 | 138/138 | 5928/13795 |
| ParamNet last | 9820/909/113 | 7014/1116/473 | 300/300 | 1851/1851 |
| Whatis first | 15095/341/174 | 63479/36092/35941 | 614/614 | 6026/134480 |
| Whatis last | 8432/439/285 | 13065/1296/911 | 1069/1069 | 3615/3731 |
| Whois first | 3251/369/256 | 5364/2364/2155 | 1162/1162 | 3511/9390 |
| Whois last | 3970/243/162 | 2993/822/775 | 631/631 | 1809/3211 |

Low reasoning 除 Audit last 第一段 1902 字符只读首 1200 + 尾 180（未读 522）外，其余各段按既有审阅记录全文覆盖；Audit first 的 1264 字符也是原实际全文阅读，未被本次追溯裁切。Max 共 730,505 字符，原实际读 97,185、未读 633,320；短段全文，长段通常首 1200 + 尾 180，重叠只计一次。精确逐例范围及已读 external 范围在 PAIRS.json 中保留。原审阅外部 assistant/native/tool 轨迹全部覆盖，但 Low Audit 不冒称初始全部法律文档段落重新审核。结构检查中的完整串比对不等于人工读完长 reasoning。

INPUT_CONTRACT.md:53 和 METHODS v1/v2:35 已有最大提升/最大退步/近中位差的解释案例规则，但原属新 Low 对历史 Max 的 917 项设计；其数量上限、差值方向和多指标优先级没有在所查新增 Max 计划中补齐。新增 Max PLAN.zh.md:35 明确将原 Low 固定样本投影，不能把这里的 12 对称为依据得分选出的 extreme/median 案例。本次没有扩大样本。完整出处与实际 bytes/SHA 在 SELECTION_RULES.json、INPUTS_INDEX.csv。

旧 v1 Audit 双零的定向诊断仅描述旧版本历史原分数；不拿它解释最新 0e 重评分历史，也不混入当前同版对照。全部 417 对的分数、成本和终态比较由独立 same-version-analysis 输出负责。
