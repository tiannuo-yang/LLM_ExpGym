# 模型无效 final 配置：离线评分修复

状态：补丁已准备，未由本子任务应用到 LLM_ExpGym；所有原始结果与 dump 原字节保留。补丁为 invalid_final_score_fix.patch，暂存源码为 invalid_final_score_stage.uKed6R/。

## 边界

- Unknown keys、根对象类型和列表长度错误抛出专用 InvalidConfigurationError；评分器只将该明确输入异常重算为 0，不包装 backend/data 异常。
- 原有 Invalid JSON payload / Invalid config 观察文本和 0 overhead 保留。评分器只认这些明确前缀及原有 numeric-zero/degenerate 前缀，不再将泛泛 missing、invalid 或 Tool error 视作零分。
- 新增 JSON 标量、有限数值、类型、choices、范围检查。整数超参数和整数类别中的数学整数 1.0 规范为 int 1，保持 ConfigSpace 0.4.21 / 1.2.0 一致；非整数、bool、NaN/Infinity、嵌套结构及错误形状被拒绝。旧实现会忽略过长列表尾部，新版明确拒绝，作为本次输入协议修正记录。
- 真实工具 loop、预算、observations、eval_records 和 fallback 不改。只有原 answer_perf=None 且无已评分 eval_records 的 final，才使用现有 offline_final_answer 补分。非零原分与无效输入冲突仍失败，不能被悄悄覆盖。
- 库内部 ValueError / FileNotFoundError / TypeError、Missing data 文本以及 (None, 1.0) 仍不通过评分审计。

未扩展本次修复：_hpobench_evaluate 旧实现对 backend 缺失 function_value/cost 字段使用默认值；这不是此次输入异常分类的触发路径，已另报 root。

## 证据

invalid_final_score_replay.json 包含真实 NAS101B Free / naive / agent 1 final 的原始 dump 路径、SHA256、原文、runtime 与两份源码指纹。原始请求 6c70310325c443f9a3b79260bfff9c48，dump SHA256 为 dd2798b1930b2d623ecc2ecbbcde5581334a993469eeac44ab91148aa686c242。

| 环境 | 原源码重放 | staged 重放 | staged backend 调用 |
|---|---|---|---|
| Python 3.11 / ConfigSpace 1.2.0 | score_check=false / Unknown hyperparameter | score_check=true / perf=0 | 0 |
| Python 3.7 / ConfigSpace 0.4.21 | score_check=false / Unknown hyperparameter | score_check=true / perf=0 | 0 |

这是已有模型回答的离线程序验证，不是新增 Kimi-K3 测评，不写回旧成绩、不调用 LLM API。

新增 tests/test_invalid_final_configuration.py 的 11 项测试在两个 runtime 都通过。覆盖解析/缺参数/未知参数、短长列表、范围、类型、非有限数、1.0 规范化、观察文本、开销与 fallback 不变、未报告分数、数据/后端异常、旧非零分冲突。暂存源码的既有回归：run_paper_sweep 27/27、react_loop 44/44、HPO 基础 7 通过 + 3 依赖开关 skip。

随后暂存源码全 unit suite 共运行 243 项，239 通过、4 skip、0 failures（2.759 秒）。这是本补丁加当时冻结源码的验证；其他两个协议补丁合并后仍应由 root 重跑最终全 suite。

## 复现

    LLM_ExpGym/.venv/bin/python kimi_k3_eval/patches/replay_invalid_final_score.py \
      --repo kimi_k3_eval/patches/invalid_final_score_stage.uKed6R \
      --dump kimi_k3_eval/dumps/full/poolact__tuning__hpobench_nasbench101_B__cost_free/6c70310325c443f9a3b79260bfff9c48.json

使用 data_runtime/.venv-hpo/bin/python 可复现 legacy；helper 自动指定固定 HPO data/cache/config 与 BLAS 线程环境，不读取 API key。

补丁触及 expgym/task_tuning.py（validation 部分）、scripts/run_paper_sweep.py（score 部分）和新增测试文件；与独立的 NAS101 B/C _task_hints / Answer 行首解析补丁应无语义重叠。git apply --check 已通过；正式应用、全 suite 与统一新 source/full 运行由 root 执行。
