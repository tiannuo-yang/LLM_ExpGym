# HPO PoolAct 图身份验收

[`verify_graph.py`](verify_graph.py) 提供纯标准库接口 `verify_graph(result) -> dict`。`result` 为一个 `result.json` 已解析对象；函数不修改输入，不调用模型，不导入被检查的运行时图实现。

返回 `ok`、`status`、`applicable`、`counters`、`error_counts` 和最多 30 个定位样例。`naive` / `cached` 返回 `NOT_APPLICABLE`；HPO PoolAct 出现任何身份或路径错误返回 `ok=false`，供采用收集器拒绝该结果。运行时版本、来源哈希与评分完整性由收集器另外检查；本函数不会把不含碰撞的旧协议自动认定为统一新版运行。

检查读取 **所有 agent_results[].messages 中 user/tool 的实际存储图快照**，不只检查终态 `shared_state`。每个图节点均绑定回该池完整工具／评估 payload 的 canonical JSON 与 SHA256，逐快照检查：

- 节点的完整配置必须存在且唯一；完整 SHA256 身份不得对应两个不同 payload。
- 新协议长配置必须有 `E:h:<至少 12 位 SHA256 前缀>` 等明确标签，标签必须与完整 payload 对应。
- 同一可见快照内，一个显示标识只能对应一个完整配置。允许不同快照因前缀延长而使用不同别名。
- 每条路径的起点和终点必须存在于该快照且唯一，不能通过在全池终态找到节点来放行当时不存在的端点。
- 同配置自环允许存在；如果路径附带 agent 身份，该 agent 的源工具／评估记录中必须确实出现至少两次该配置。不同配置共享同一显示标识直接失败。

旧 v3 的长配置没有显式 hash 标签，诊断时按历史前 80 字符规则计算它实际使用的路径标识。全量 108 个历史 HPO PoolAct 池核验中，**45 个 v4 全部通过；63 个 v3 中 61 个失败、2 个未发现身份碰撞**。相较此前 60 个“实际路径端点歧义”池，额外 1 个失败池是在可见节点中出现身份冲突，即使对应路径尚未出现也不会放行。逐池记录见 [`HISTORICAL_GRAPH_VALIDATION.json`](HISTORICAL_GRAPH_VALIDATION.json)。

独立验证脚本 [`check_verify_graph_independent.py`](check_verify_graph_independent.py) 的 **22 项检查全部通过**，包括旧碰撞／已修复原件、naive/cached、不带路径的新运行时 fake、运行时产生的真实重复配置自环、错误 hash、缺失端点、身份碰撞、缺失源记录以及伪自环等突变用例。全部检查保持输入对象不变；结果与源码哈希见 [`GRAPH_VALIDATION_TESTS.json`](GRAPH_VALIDATION_TESTS.json)。空结果既无配置记录也无图时仅表示“无图可检”，不能代替采用层的执行完整性和评分验收。

本检查验证身份、路径端点和来源绑定，不是对修改信息共享后行动或分数的反事实模拟。原轨迹的消息与实际 HTTP 请求之间是否逐字节一致，需要原始请求记录另行核查；本函数不会把保存的消息冒充提供方输入证明，也不证明时间门控或跨池隔离的全部语义。
