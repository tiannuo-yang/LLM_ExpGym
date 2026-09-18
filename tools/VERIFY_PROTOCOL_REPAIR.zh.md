# 协议修复交付的统一离线核验

在公开仓库根目录执行，Python 3.10+ 标准库即可：

```bash
python3 -B tools/verify_protocol_repair.py --components --output /tmp/protocol-repair-check
```

输出目录必须不存在或为空。所有重建写入该目录；公开输入、现有 CSV 和科学实现必须在核验前后保持逐字节不变。结果、每条命令、工作目录、实际执行脚本 SHA、日志及逐表比较写入 `VERIFICATION.json`。默认模式也是 `--components`。默认没有模型调用、数据下载或网络请求。

此模式执行：

1. 从公开最小终答包重新调用生产 parser、Search/Audit scorer 和池投票：3,888 结果、9,504 成员。旧 scorer 也重新运行，历史源码来自公开且 SHA 锁定的 `tools/historical_scorers/297c3d00a006f33fc5a8ca799ce91d327d92839e/`，不需要 `.git`、旧 Git 对象或私有原件。
2. HPO 的 810 结果、1,782 成员重新提取终答，执行历史可见配置匹配／最佳可见回退和聚合，并核验配置 hash 绑定的 benchmark 测量证书。**默认不重新执行 benchmark 表，也不重新扫描完整 18,093 个 assistant turn。** 全 turn 审计仍是绑定原件 SHA 的既有检查记录。
3. Whois 全部 1,170 个终答重新解析、重新计算姓名 F1，连接其中 234 个 beta10 主实验重叠项，重新合并 4,698 个既有轨迹评分结果。
4. 重建 HPO 两层公开事件／行为汇总，按刚复算的 HPO 成员结果重建正式 486 条行为；重建 Audit 全部 31 张 CSV，另将 2,574 个成员及 468 个池的终值连接到刚执行的评分器输出；重建 Whois 全部公开 CSV，并核实其 1,170 条评分输入与已核验重评分表相同。

这些结果属于 `existing_trace_rescored` 及其行为分析。它们不把原轨迹改成修复后新运行。组件通过不等于 HPO97、Search/Audit21 与独立 Whois1 的最终采用总 gate 通过。已有轨迹的 Audit 和 Whois 层分别取 `audit_existing_trace/`、`whois_existing_trace/`；组件阶段尚未分层的早期包可使用其原目录。

正式采用全部齐备后，在同一公开仓库执行：

```bash
python3 -B tools/verify_protocol_repair.py --full --output /tmp/protocol-repair-final-check
```

`--full` 先要求 `control_flow_adoption/FAIRNESS_MANIFEST.json` 的总 gate 通过。HPO 单阶段完成不能替代总 gate。然后执行上述全部组件，并继续：

1. 检查 HPO97 和辅助22项的公开预注册与版本声明；这些声明核验不冒充重读私有原始请求。
2. 从 HPO97 新运行的最小评分包重做终答解析、可见配置选择及六项池指标，用配置 SHA 绑定的原测量证书评分；整池替换重算后的主表，并核验 4,601 个保留位置及全部来源字段。重建582行三层运行评分比较，另由公开源码身份输入重建810项、54组实际采用版本矩阵。默认仍不重新读完整 benchmark 表。
3. 从 Search/Audit21 的公开最小包真实重算 78 个成员和池评分，核对预注册位置、历史来源和成员集合，再重建最终 4,698 行正式评分／来源表及三层逐项差表。
4. 重建正式 Audit31张表，将 2,574 个成员及 468 个池连接到已重算评分和正式来源；复算案例保留状态。HPO486行为仍来自已核验的正式成员层。
5. 重新评分 Whois 旧1,170终答和新增独立控制1项，以真实新成本替换对应一项；核对其公开表、正文、来源和总 gate 身份，另将234个 beta10项目连接到最终主表。
6. 从刚重建的正式主表生成 main、display、search、poolact、cases、四层评分对照，以及三篇最终报告。逐字节比较全部约定 CSV 和生成正文，双向检查 CSV 文件清单以拒绝缺表或额外未核验表。

所有输入均来自公开包与仓库冻结源码。全量入口不读取私有工作区路径，也不需要历史 Git 对象。图决策重放、完整原件到最小包的导出过程、逐请求 HTTP／reasoning 审计不属于这一公开终答核验；这些环节的原始来源 SHA 与采集验收记录保留在包中。

HPO 可选的完整原件和 benchmark 检查使用单独开关：

```bash
python3 -B tools/verify_protocol_repair.py --components --verify-benchmarks \
  --archive /path/to/paper-ad03e8c-20260916 \
  --source-map /path/to/resolved_sources.json \
  --versions /path/to/hpo_all_slots.csv \
  --benchmark-python /path/to/numpy-2.4.6/python \
  --paramnet-python /path/to/python3.7-numpy1.18.5-sklearn0.23.2/python \
  --hpobench-root /path/to/hpo_tuning/HPOBench \
  --benchmark-data /path/to/hpo_tuning/hpobench_data \
  --output /tmp/protocol-repair-full-benchmark-check
```

这些额外路径是显式提供的本地冻结资源。没有它们时，普通轻量核验仍可执行，但不能声称 benchmark 已重新测量。底层 HPO 工具历史上用同名 `--verify-benchmarks` 验证轻量证书；统一入口会分别记录 `fresh_benchmark_evaluations=0` 与可选的完整 benchmark 结果，避免混淆。

`tools/rescore_protocol.py` 与 `tools/rescore_hpo_protocol.py` 的公开加载器仅将旧源码读取从 Git 对象改成上述 capsule；旧 scorer 源文件逐字节不变，科学 core 与冻结补跑 runtime 未修改。原组件 `CHECKS.json` 的脚本 SHA 继续表示当时生成结果的实现；发布加载器及本次复验的身份单独记录，不能倒写历史生成身份。

该入口与 `tools/verify_lightweight.py` 的旧轻量交付身份核验分开。图表渲染不在标准库逐字节核验范围内；公开行为重建也不冒充重新读取私有完整 prompt、HTTP 请求或行动轨迹。
