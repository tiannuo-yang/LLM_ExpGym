# 本次 run 的通用性与 bug 修复复盘

范围：**Static/fake validation**。审查上游 `703719150e8d44712ace50d6439686423dcd1328`
到实际实验源码 `8dfea72931d952ad90f1c722a83957ab23afc6bf` 的核心差异，
并对本次复盘发现的两处残留协议漏洞做前瞻性修补。没有调用模型、申请 GPU、
重跑实验、修改已发布结果，或为期望的性能方向改分。

## 结论

此次主要修复没有依赖 Kimi/GLM 名称来选择解析、重试、计分或成功样本；
触发条件是协议结构、返回状态、任务定义、模拟时间和执行身份。
但不能把所有改动称为“纯兼容性修补”：其中还包含通用正确性修复、
显式的协议/缺失值处理扩展，以及本次 Custom study 的配置选择。
它们都需要版本化，不能与旧结果无差别合并。

**有限复核又找到了两处真实的通用漏洞**，见下文。模型无关不等于没有 bug，
更不等于所有模型都已真实验证；目前真实实验结论只覆盖已运行的两个模型和设置。

## 原修复的分类与证据

| 项目与触发条件 | 分类、是否依赖模型名 | 实现与回归证据 | 保留的限制 |
|---|---|---|---|
| API 返回 `content=null/[]`，同时有原生 tool calls、reasoning 或 length stop | 通用 Chat Completions 兼容；不按模型名判断 | [llm_clients.py](../expgym/llm_clients.py)；[native client tests](../tests/test_native_llm_clients.py) | 支持声明的接口形状，不保证任意供应商扩展。原消息、call ID 和 reasoning 保留；真正畸形的 envelope 显式失败。 |
| 原生 tools 已启用，但 system/user task context 仍要求文本 `Action:` | 通用提示/协议一致性；由能力声明和显式 `tool_protocol` 决定 | [tool_protocol.py](../expgym/tool_protocol.py)；[task-context integration](../tests/test_native_task_context.py) | 仅修改源代码拥有的指令，不全局替换任务数据。自定义 task builder 仍需使用已解析协议；fake auto 为 text，不能代替 native smoke。 |
| 空正文、length、错误模型参数被当作 HTTP 失败免费重采样 | 通用实验正确性；不读取模型名、答案正误或分数 | [react_loop.py](../expgym/react_loop.py)；[native loop tests](../tests/test_native_react_loop.py)、[provider abort tests](../tests/test_provider_abort.py) | 仅配置的暂时性 HTTP/连接错误可重试；协议修复占正常步数。历史唯一 forced-final 调用仍记录。`abort` 是基础设施终止，不是正常弃答。 |
| PoolAct 早完成节点后来合并未来分数/访问者/边，或预算边界反馈通过图重新进入 final | 通用模拟时间正确性；与 LLM 完全解耦 | [parallel_cache.py](../expgym/extras/parallel_cache.py)；[visibility tests](../tests/test_poolact_visibility.py)、[execution-contract tests](../tests/test_execution_contract.py) | 基于可见完成事件重建图；严格预算外反馈不发布。旧 cache 已有未来时间过滤，不能误称所有旧 cache 都失效。无时钟 legacy ledger 只支持明确无限预算。 |
| NAS101 B/C 提示误用 A 的二进制边语义；ConfigSpace/NumPy 标量、整值浮点及坏 backend 返回处理不一致 | 任务/运行时兼容与正确性；task-specific，**不是 model-specific** | [task_tuning.py](../expgym/task_tuning.py)；[schema tests](../tests/test_task_schemas.py)、[tuning validation](../tests/test_tuning_validation.py) | B 为 edge-ID，C 为 priority/top-k；不修补模型提出的非法架构。当前只承诺 flat scalar、无条件/forbidden/量化的既有空间，其他空间显式报错。 |
| Search prompt 读隐藏 gold 数量；HPO 自有指令携带 benchmark 身份名称 | 源指令信息边界修复；不选择模型或有利题目 | [prompt identity tests](../tests/test_prompt_identity_blinding.py)；三个 task context builders | 去掉源代码注入的身份/答案数，不抹掉模型自产历史或数据中的同名词。结构仍可能被识别，不能称为语义盲测或排除训练污染。 |
| loop 正常返回但没有最终答案，随后被当作整个框架失败 | 显式 `task-abstention-v1` 处理扩展；按终止状态和 scenario 分类，不按 GLM 名称 | [missing_final.py](../expgym/missing_final.py)；[missing-final tests](../tests/test_missing_final_policy.py) | `answer` 保持 `None`；Search/Audit 用原 evaluator 评估空预测，非硬编码零。HPO 无配置则未评分/null；保留全体 agent 分母。异常不转换为弃答、不触发额外模型调用。 |
| 重试/异常使用量、正常终止原始值、重算分数或 resume 身份记录不足 | 通用可查验性；与模型名无关 | [terminal_evidence.py](../expgym/terminal_evidence.py)、[evaluation_identity.py](../expgym/evaluation_identity.py)、[trace_v2.py](../expgym/trace_v2.py)；[dump tests](../tests/test_api_dump_provenance.py)、[identity tests](../tests/test_evaluation_identity.py) | 未知 usage 为 unknown，不补零；终止证据不是完成/计分权威。源码、数据、依赖或配置不同不得冒充同一次可 resume 实验。 |

历史已存在的模型适配不能归因于此次修复：`llm_clients.py` 的 Qwen `/nothink`
条件由显式 `nothink_prefix` 开启，默认关闭，`git blame` 归属初始 `aa135b1`。
它没有替 Kimi/GLM 选择答案或救活失败。OpenRouter 的 provider/reasoning 参数、
不同服务的认证/URL 也是 provider adapter，不是通用评分算法。

## 复盘新增修复：解析器的否定不能被最终兜底绕过

旧 native 普通终止与 forced-final 使用：

```python
extract_text_answer(text) or structured_final_answer(text) or text
```

前两个解析器已明确拒绝推理区和引用示例，但最后的 `or text` 又把原文当答案。
这不是只影响日志的错误：在旧源码的内存复现中，用虚构模型、mock transport、
原 Search evaluator、唯一 synthetic gold `Ada Lovelace`，以下文本分别得到
F1 `0.5`、`2/3`、`0.5`；普通/强制两条路径均只有一次模型交付：

```text
<think>
Ada Lovelace
</think>
```

```text
<think>
Ada Lovelace
```

```text
Thought: Example:
Answer:
Ada Lovelace
```

现在 [unlabelled_final_answer](../expgym/tool_protocol.py) 仅接受不含协议/推理
标记的普通裸文本作为兜底。明确 `Answer:` 和完整合法 JSON 仍优先；
正常裸名、带引号的裸名仍可提交。推理块、未闭合推理、含协议标签的引用/代码示例不再进入 scorer；
普通步骤可走原本已有的有界协议修复/forced-final，强制最终失败不再生成。
**闭合推理后接无标签正文也要求明确 `Answer:`**，这是公开的保守协议边界，
没有猜测思考结束位置、提取 gold 名字或新增 model ID 特判。
字面正文确实需要包含 `Action:` 等标记时，使用明确 `Answer:` 或任务的完整 JSON。

没有改变 Search/Audit evaluator、PoolAct voting、HPO `legacy` 最佳已观测回退规则。
该修补会改变今后这些畸形交付的最终答案判定，因此属于新源码身份；
**没有审查全部历史 raw，也不能报告本次正式 run 的发生次数或分数影响**。
旧发布数据保持不可变；若需量化历史影响，应另做索引限定、无模型调用的审计，
而不是把新解析结果覆写成当时的实际 run。

## 复盘新增修复：坏 content part 不是正常空回答

旧 client 对 `[42]`、`[None]`、`[{}]`、`[{"type":"text"}]` 都会跳过/补空文本，
导致畸形 API envelope 被误分类为“成功交付、模型没回答”。
现在列表成员必须是含非空字符串 `type` 的对象，`text` part 必须含字符串正文。
违规只有一次交付，抛 `APIClientError`，保留已知 usage，**不 HTTP 重采样**。
合法 `[]`、空 text、带非空字符串 type 的未知扩展仍完整保留，不猜测其内容语义；
没有其他可读正文时仍按正常空回答处理，不代表验证了该扩展的私有 schema，
也不是对所有未知扩展的支持承诺。

## 不应包装成 bug 的设置或限制

- 两模型的 temperature、top-p、reasoning、max tokens、上下文裁剪、真实 checkpoint/
  template/TP 配置属于显式 study/serving 参数；它们会改变耗时和结果，不是模型通用性修补。
- 本次 GLM 的正常 length/reasoning-only 终止应保留；没有证据表明“不给答案”本身
  是 ExpGym 丢弃了已交付答案。新发现的畸形 part/正文推理兜底是不同触发条件。
- `legacy` HPO final policy、Audit 的 int evidence coercion 与 EA/LA 独立定义是
  历史 endpoint。改为严格 submitted/不同投票可以研究，但必须另立设置，不能追认成原实验。
- PoolAct 的 prompt-cache namespace 原先未纳入完整 model/backend/item/task/regime/seed
  身份；这是本轮调度审查发现的另一个通用隔离缺口，归调度修复处理。
  缺失 namespace 区分不等于已证明存在跨实验的物理 KV、工具状态或答案泄漏。
- 两模型主比较方向一致，不支持所有模型/场景都稳定改善；49 行负向性能比较不删除。
  这些修复是按协议与执行不变量验收，不以产生预期正号验收。

## 本轮验证与下一次真实运行要求

新增 [test_model_agnostic_regressions.py](../tests/test_model_agnostic_regressions.py)
使用三个不在任何模型别名表中的虚构 ID，贯穿真实 client 与 loop：原生 tool/history、
显式 text、不同 reasoning 字段、length、未知 usage、abstention、provider abort、
无效 content parts，以及本轮两处回归。没有真实网络、外部数据或 GPU。

实际 CPython 3.11.15 执行以下组合：**201 tests，200 通过、1 项按条件跳过**。
跳过的是需要隔离 legacy ParamNet 环境且须显式开启的真实 ParamNet schema 测试。
测试初稿曾把 evaluator 的实际双参数调用误写成单参数断言；仅修正测试断言后通过。

```bash
python -B -m unittest \
  tests.test_model_agnostic_regressions tests.test_native_llm_clients \
  tests.test_native_react_loop tests.test_tool_protocol \
  tests.test_missing_final_policy tests.test_provider_abort \
  tests.test_poolact_visibility tests.test_execution_contract \
  tests.test_audit_tool_schema tests.test_task_schemas \
  tests.test_tuning_validation tests.test_prompt_identity_blinding \
  tests.test_native_task_context
```

此结果证明所测协议不变量，不证明未运行供应商/模型的实际兼容。
下一次正式研究必须冻结新源码/环境身份；对每个模型先做一次获授权、
覆盖原生多轮 tool 和 forced-final 的 real smoke，再跑预先确定的完整矩阵。
本轮不额外申请 GPU 来重复已经完成的历史实验。
