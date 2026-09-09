# 新 GLM 绑定 CPU 验证补充

此补充记录 ROOT 后续授权的合成测试；不回写旧 README / STATIC_REUSE_RECEIPT 的历史 pending 状态。

生产 `operator.py` 始终保持 SHA
`2124e9929f29531d48960ece983eea10d493660244bfc1dc8938696ebfd79d3d`。
新增 [test_operator.py](test_operator.py) 和 [test_safe_invoke.py](test_safe_invoke.py)，完整差异见 [TEST_DIFF.patch](TEST_DIFF.patch)。
后者与旧 K3 版本逐字相同；原 fixture 和所有生产工具未修改。

原 11 项保留：Wiring 6 项、Lifecycle 5 项。只替 schema/action/临时目录标签；setUp 在原 f.put 写当前 synthetic metadata/inventory.json 时临时将两个完成状态改为 true，随后由原 fixture 自然生成全部 pins。原成功测试两处完成状态断言同步改为 assertTrue；其他原测试方法 AST 不变。

新增 4 项（共 8 个状态/类型负例）：

- receipt false/false、false/true、true/false → `original_scan_not_complete`。
- receipt 1/true、true/1、1/1 → 同规则，整数 1 不冒充 bool true。
- max_parallel_batches=true → `exact_root_delivery_go`，bool 不冒充整数 1。
- 独立、全部 pins 自洽的 false/false seal，receipt 伪称 true/true → **`original_completion_identity`**。

所有新增用例都核精确异常码、load_helper 和 safe_invoke 未被调用、delivery output 不存在。最后一项实际命中了 seal 完成状态检查，不是被早先坏 SHA 意外挡住；fixture 自身的 synthetic metadata/scan 输出当然存在，不将其说成全程零文件。

## 实际运行

每个解释器只运行一次同一 15 项 suite，均通过：

| 控制解释器 | exit / chunk | unittest 报告时间 |
| --- | --- | ---: |
| Python 3.10.12 | 0 / `388ebf` | 0.610 s |
| Python 3.11.15 | 0 / `e547b5` | 0.561 s |

命令与完整日志 pins 见 [CPU_RECEIPT.json](CPU_RECEIPT.json)、[CPU_py310.log](CPU_py310.log)、[CPU_py311.log](CPU_py311.log)。两次通过原 prlimit 设置 core=0 后运行，无新 wrapper 脚本。原合成成功路径实际调用 pack/restore CLI 的子进程固定为 /usr/bin/python3，不能说两种控制解释器代表两种底层 producer 都测试过。

独立 peer `/root/glm_delivery_reuse/archive_contract` 只读确认原 11 项及全部生命周期覆盖保留，新的 false-seal 负例完整派生 pins、精确到达预期检查。实际 CPU 由本 operator 作者单独运行；peer 未运行/import，也没有读取真实 scanner 输出。

## 边界

此次确实 import 了新 candidate 并以 synthetic/mocked 输入调用 execute；因此不再声称“任何形式都未执行新代码”。但全部数据、三份 known-value 文件、归档/恢复路径都在合成临时目录；没有实际 GLM keys/raw/scanner output、真实 scan metadata gate、正式 pack/restore、网络、Git、Slurm 或模型评分。生产 SHA 和旧文档/回执保留。

这些测试验证新完成状态绑定、原控制流和明确负例；不是正式扫描验收、原件交付或发布 GO。仍等待 ROOT 接受 CPU，随后仅在独立授权及真实闭合 scan refs 到位后才做正式 metadata gate / delivery。新增测试与本补充写完后停写。
