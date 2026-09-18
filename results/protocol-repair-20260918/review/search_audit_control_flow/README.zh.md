# Search / Audit：25 个中间解析差异的实际控制流核查

结论：**24 个响应会被固定新版 runtime 更早作为自然终答接受，涉及 21 个完整实验槽位；另 1 个响应因 `finish_reason=length` 在进入 parser 之前即被拒绝，不产生真实控制流差异。** 24 个均为原始 API 的完整 `stop`、非 forced、无原生工具调用。

本核查只读取历史原件，绑定正式 `runtime_counterfactual.csv` 的 25 条差异。冻结 parser SHA 是 `6b09495845fa6c1dc324a82ba471bcfba59265aaa4912ff0acf8307239e84bed`。没有修改 parser、评分、原件或运行矩阵，没有调用模型。

## 完整覆盖与来源

- [CONTROL_FLOW.csv](CONTROL_FLOW.csv)：逐项资格、后续工具/新反馈、最终 payload 是否一致及来源 SHA。
- [EVIDENCE.json](EVIDENCE.json)：原始 API 证书、合法提交内容、必要的 payload 诊断、后续环境观察。25 个候选和后续调用共 **55 个原始 dump**，全部 SHA 对齐冻结归档。
- [CHECKS.json](CHECKS.json)：22 个 canonical 槽位、25 个候选和55个原API证据的覆盖检查；25 条旧 parser 结果亦独立复算，与正式 CSV 一致。
- [AFFECTED_WHOLE_SLOTS.csv](AFFECTED_WHOLE_SLOTS.csv)：按控制流差异选取全部21个完整槽位，**2个N1+19个N4=78成员**，不是只选成绩变化的5条。
- [SOURCE_SETTINGS_PUBLIC.json](SOURCE_SETTINGS_PUBLIC.json)：科学设置白名单、source tree / provenance 与 canonical SHA。内部端点仅保留hash。N1 的 hypothesis_order / seed 必须保留，N4必须整池替换。
- [AFFECTED_GROUPS.csv](AFFECTED_GROUPS.csv)：模型/系统/任务/策略/预算分组及全部slot ID。

旧 parser SHA 指的是正式重评分固定的297c3d00比较基线，不冒称它与两批历史运行源码逐字相同；历史运行的实际拒绝由原API响应之后的protocol-error提示及后续请求直接证明。原运行的source tree/provenance另保留在SOURCE_SETTINGS_PUBLIC.json。

逐项定位以 canonical 的 assistant 消息序号和 usage_attempt/request_id（N1另有 output_message_id）联合绑定，响应公开 content 与 native tool_calls 均逐字核对。新旧 parser 比较不读取 reasoning_content，导出不包含 provider reasoning、加密签名或 HTTP 授权头。4个格式无效候选仅公开其JSON前缀诊断及尾部长度/哈希，不发布解释尾文；JSON前缀不当作合法评分输入。

## 真实影响

| 组 | 成员数 | 观察到的后续行为 |
|---|---:|---|
| 更早终答且任务 payload 与实际最终答相同 | 19 | 后面仅重复交付，没有后续工具或新增已完成共享事实；仍多消耗一次模型响应，N4早结束可能改变并发协作时序 |
| 更早提交的 Audit payload 无效，实际后来的终答有效 | 4 | 均Qwen；3条只经重答去掉尾部说明；1条还新增4次验证，其中3次可见、1次超预算隐藏 |
| 更早 Audit payload 有效但与后来的答案不同 | 1 | Qwen PoolAct Tight；后来1次工具超预算隐藏，并收到新的共享反馈；nda-1/nda-2证据改变 |
| length造成的表面parser差异 | 1 | DeepSeek Search；新旧runtime均先拒绝截断响应，不可当作自然提前停答 |

24个真实差异包含 DeepSeek N4 Audit Moderate PoolAct 的11成员/9池，以及 Qwen 的13成员/12槽位（详见分组CSV）。只有两条候选之后还有工具动作，合计 **5次：3次可见、2次隐藏**。收到新已完成共享事实的候选只有1条；共享事实按完整请求内 Already Explored 的工具参数及反馈去重，不把纯agent名单变化误当新验证结果。

## 为什么4个Qwen案例不是“只是重复终答”

通用 final parser 负责判断模型是否已提交最终答案；任务 scorer 负责判断提交是否符合 Audit JSON 契约。当前 runtime 在通用 parser 返回非None后就自然结束（`react_loop.py` 的 natural-answer 分支），随后任务 scorer 独立解析 payload。

这4个候选都有明确 `Answer:`，后面是**裸JSON对象再接解释性段落**。新版通用 parser 忽略前导 prose 中的“final answer:”提及，正确找到真正的Answer行，保留其完整字面后缀。因此模型已经提交，但 Audit 的整对象 parser 拒绝裸JSON后的额外说明，scorer按既有规则返回 LA=0、EA=0、verification_eff=None。此处不把尾部说明删掉后重评分，也不引入新的格式容错规则。

旧 final parser 被更早的 prose “final answer:”提及干扰，没有接受该响应，于是原运行给了 protocol retry。后续模型再次提交单一JSON，或继续调用工具后再交付。这是历史运行的额外纠错机会，不能用其最终有效答案代表新版 runtime 已经提前结束时会得到的答案。

| 旧slot / agent | 更早候选 | 实际后续 |
|---|---|---|
| `d67c769bf1e64fefbbc93e94` / 0 | Qwen Cached Moderate，JSON+尾文，无效 | 4次验证，3可见1隐藏；后来JSON有效，诊断性JSON前缀比较中nda-10/nda-15证据也改变 |
| `f89ad4badf4c758833244ebb` / 2 | Qwen PoolAct Moderate，JSON+尾文，无效 | 无新工具/共享完成事实；去掉尾文后合法，JSON前缀内容相同 |
| `e0d5f2259519e3141c3b434d` / 3 | 同上 | 同上 |
| `c71943652fd8b85b914b258f` / 3 | 同上 | 同上 |
| `efdd63d3b5c0599458713c62` / 3 | Qwen PoolAct Tight，合法JSON | 后续工具结果隐藏，但共享图新增 `nda-1 ev:[16,17]` 为 Evidence Incomplete / Definition core 的反馈；最后nda-1/nda-2证据改变 |

上述“JSON前缀内容”只用于解释历史行为，不是评分时获准的修复操作。当前正式离线重评分保持冻结，它评价的是既有完整运行的终答。

## 需要什么对照

若报告只写“既有轨迹重评分”，保留固定重评分结果即可；若要声称观测新版 parser/runtime 的性能，应在同一固定 runtime / settings 下补跑这21个完整槽位，并依预定规则整槽采用。仅把5条payload差异列成limitation，或仅补跑这5条，会漏掉自然停答时序和PoolAct并发协作变化。21项矩阵及原settings已交ops隔离准备，发布/启动权仍由root掌握；既有HPO97矩阵未改变。

不声称通过固定旧响应完全预测新运行的最终分数：提前结束会改变后续调用、共享状态和调度，尤其N4需要真实整池对照。该边界审核提供必须补对照的确定触发点，而不冒充新模型运行。

## 独立Sweep GLM补充

[SWEEP_GLM_CONTROL_FLOW.json](SWEEP_GLM_CONTROL_FLOW.json) 独立核验 `whois:glm:beta20:phantom_seed2:5:R1`：不是主实验β10复用，也不在上述25条之内。候选和唯一后续响应的2个原API dump均为success/stop、非forced、无工具调用；公开content及展开content_ref后的输入均与canonical对应。新版会更早接受相同6名单，历史后来只多重答一次，无新工具，F1均1。

因此完整补对照资格清单为主实验21个whole slots，加此独立Sweep N1槽位（共22个实验结果/运行槽、79成员）。主21CSV保持独立，Sweep原设置、来源与资格见独立证书；运行是否启动、完成和采用以正式调度/采用记录为准，本审核没有启动任何实验。

## 公开边界和复核条件

仅 [PUBLICATION_INPUTS.json](PUBLICATION_INPUTS.json) 中列出的文件可公开。`SOURCE_CONFIG_REFS.json` 为ops私有准备输入，包含历史内部端点，禁止按整个目录或内部MANIFEST整包公开。本地审核脚本及内部MANIFEST也不在公开白名单。科学设置中的端点仅保留SHA256；没有凭据、HTTP授权头、加密签名、provider reasoning或完整raw request/response。

所有源路径只作为定位证据。重新核对原API/轨迹哈希需要本地保留的原件与归档（requires archives）；这个小型公开sidecar没有复制原始dump，也不声称离开原件即可重新验证其内容。公开终答内容和证书足以审阅本轮分类及补对照范围。
