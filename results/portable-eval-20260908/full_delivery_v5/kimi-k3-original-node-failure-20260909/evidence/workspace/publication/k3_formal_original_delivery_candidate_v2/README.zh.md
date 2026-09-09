# K3 原始 run 本地交付候选 v2：有界子进程收尾修复

v1 和旧 helper 原件不改。v1 有已确认逻辑漏洞：旧 `invoke` 在 Popen 成功后先写 `stage.started.json`；此写入抛异常时，没有执行 `child.wait()`，旧 batch_run 却捕获异常返回，而总账仍固定 `local_workers=0`。本轮纯 mock 红例复现 wait 调用数为 0、没有 exit 回执。不能把 v1 的正常成功路径测试当作该异常路径已经安全。

## 唯一生产差异

见 `PRODUCTION_DIFF.patch`。在新加载的旧 helper 模块内显式注册 `safe_invoke`；pack/restore、扫描器、caps、manifest 和原件字节协议不变。新增 `natural_wait`、`safe_invoke`，只改 `execute/main` 的接线、闭合总账和中断出口。`load_helper/identity/collect/recheck/scan_metadata/preflight` 六函数 AST 与冻结 v1 完全相同；固定 33 批、64,188 文件、1,268,512,973 B 的 metadata 范围完全不变。

1. Popen 返回成功后立即登记 PID、stage、work 和 `confirmed_reaped=false`。启动回执写入放在 `try/finally` 内；无论成功还是 OSError/KeyboardInterrupt/SystemExit，先进入自然等待再离开 stdout/stderr 上下文。
2. 最多两次 blocking `child.wait()`；首个 wait 异常即使第二次取得退出码也保留失败，不伪装正常通过。两次均异常后只做一次最终 `poll()`，保留 `closure_evidence=final_poll` 或未知。没有无限忙等、kill、terminate 或自动重启。
3. 能取得退出码则记录真实值，包括非 0；启动回执、日志引用或退出回执写入失败保留固定 `failure_layers`，不输出异常消息。磁盘全部失败可能无法留下这些文件，缺回执不是完成，不能据此承诺可恢复账目。
4. 无法确认闭合时保留 `unresolved_started_pids`、`all_started_children_reaped=false`、`local_workers=null`，停止后续批次并总失败，交由 ROOT 处理；不能说无活子进程。已确认全部回收才允许 `local_workers=0`。只完成有限收尾尝试，不声称持续 wait 失效时仍必然回收。
5. KeyboardInterrupt/SystemExit 先经历相同收尾，停止调度；能写则保存总账，再传播至安全入口。CLI 对 KeyboardInterrupt 返回 130，其他异常返回 2，均只打印固定失败状态。新 SUMMARY schema 为 `k3-original-local-delivery-operator-v2`。

这不是抵御 SIGKILL、断电、解释器崩溃或所有内存故障的进程监督系统。blocking wait 可能自然等待很久，不会为了超时而杀进程；持续异常闭合未知不会继续开新批。最后 poll 的证据类别显式保留，不伪造一次成功的 wait。

## 原本成功路径保持

仍串行每批一次原 pack → 独立 full restore → 全原路径/bytes/SHA 与 COMPLETE 核对；全部批成功后再做跨批原件/恢复件及 metadata 后验。原 execution/score 两个 false，publication/network/remote false 保持。不是科学结果通过、发布或远端恢复验收；不承诺 POSIX mode/owner/mtime 恢复。

新 GO 仍采用 v1 README 中相同的精确 20 字段契约和外部 SHA，但必须绑定 **v2 operator.py 的新 SHA 和新的 fresh output**；不复用 v1 GO，候选不生成真实 GO。`preflight` 保持 AST 相同，也不会复用旧历史 GO。原 helper 的 ROOT/STOP 仍仅绑定本次新输出；不调用旧 preflight/main。

## CPU 证据与边界

`python3 -B -m unittest discover -s publication/k3_formal_original_delivery_candidate_v2 -p 'test_*.py' -v`

两个控制解释器均运行原 6 项假数据 CLI 测试加 5 项纯 mock 回归，共 11 项。原 6 项条件/断言保留，唯一测试接线差异是成功路径调用观测从旧 `helper.invoke` 改为新 `safe_invoke`（一行）；实际假数据 pack/restore 子进程仍固定 `/usr/bin/python3`。不冒称两种 producer 都跑过。

新增五项：旧缺陷红/新收尾绿；首次 wait 异常而第二次回收仍失败；持续 wait 异常/poll 未退出时总账 unknown 且下一批不启动；正常/非 0 退出；KeyboardInterrupt/SystemExit 收尾后传播。纯 mock PID 不代表真的创建进程。新的未知闭合用例验证总账不是固定 local_workers=0，kill/terminate 均未调用。

本轮未重做真实 33 批 metadata gate，也未读真实 payload/key，未实际 pack/restore、评分、模型、Slurm、Git 或网络。只继承 v1 已记录的那次 metadata gate，并用静态 AST 比较证明该逻辑未变。v1 九个冻结候选文件 SHA 再核一致；旧 helper 和底层工具保持原固定 pin。

候选与 CPU 回执停写后交 ROOT/独立 peer 再审；作者不自签 acceptance。先前 HPO gold 暴露记录仍保留，本作者不是最终科学结果的 fresh reviewer。
