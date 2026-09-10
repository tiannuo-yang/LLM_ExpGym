# K3 fixed8 最终 controls 本地交付：扫描失败并停止

本目录原计划封装 467 个新控制原件（195086721 B），另 7 个旧同路径/同 SHA/同字节文件只复用，不打包。本轮未完成交付，也未发布。

唯一原扫描进程 session 99445（start a4307c）在 completion 213ae2 自然 exit 1。扫描仅登记 466 件 / 195085429 B，safe_to_stage=false、complete_project_publishable=false；4 个已知密钥来源被原工具读取，0 advisories，1 finding：

- artifact: file_000000222
- path: portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/k3_eight_infra_recovery_candidate_v1/test_legacy_helpers_CPU.json
- rule: credential_metadata_field
- 原成员 metadata：1292 B；SHA256 bc9600522bc407fdaafcba68ec4abe9a664967af522fe6170ce125f1edbacd49。selection=new_control_candidate，角色为 fixed_recovery_seal_merge_prompt_cpu_evidence 等原映射理由；操作员没有读取该被拒绝源正文。

按 GO 失败即停止。pack、restore、全 source/restored byte 比较均未调用，bundle_v1 和 local_restore_v1 不存在。原扫描产物、全部原件、GO/spec 以及失败记录均保留；未重试、排除、改写或改工具。lock.json 是 71 B 的失败占位，绝不可用作成功 lock 或传给 pack。

真实扫描 argv 以 /usr/bin/prlimit --core=0:0 -- /usr/bin/python3 -B 开始。前置检查 518266 exit 0 实际读得 RLIMIT_CORE=(0,0) 与 Python 3.10.12；这与旧 raw 的 CPU affinity 历史限定记录不同，不替旧记录追认。四个密钥路径在命令收据中仅用 GO 顺序占位，密钥值只由原工具在内存中读取。操作员未手动读取、stat、hash 或打印密钥。

证据：

- [原授权](ROOT_PIPELINE_GO.json)、[原 scope](ROOT_SCOPE.json)、[原 inventory](inventory.json)、[原 spec](ROOT_SCAN_SPEC.json)
- [真实 CLI/启动/退出/门禁](ACTUAL_CLI_RECORDS.json)
- [失败 metadata 核查](FAILED_SCAN_GATE.json)
- [操作员结论](LOCAL_OPERATOR.json)
- [原扫描 manifest](scan_v1/manifest.json)、[失败 lock](scan_v1/lock.json)

失败 metadata 核查 a3fa0a exit 0 确认 GO/spec/四原工具 SHA 未改变、全部 467 required stages 存在，但被拒成员 passed=false。成员来源 metadata 检查 75e2d9 exit 0。后续任何新版本须 ROOT 另行限定并授权；本目录 STOP-WRITE。
