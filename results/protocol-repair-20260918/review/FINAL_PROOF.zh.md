# 公开离线复算最终验收

最终 endpoint 脱敏投影版已在独立无 `.git`、无私有完整数据的副本中实际执行 **1 次** `tools/verify_protocol_repair.py --full` 并通过。25个子命令、202个产物逐字节一致，其中190张科学CSV和三篇最终报告与脱敏前保持原字节。

此前2次完整验收属于脱敏前历史版本，单独保留，不计为最终投影版的验收次数。

本次覆盖全部既有终答重评分、97个新HPO池、21个新Search/Audit位置（78成员）、独立Whois控制1项，重建最终4,698行来源／评分／差表、行为与主分析表、四层评分对照，以及三篇最终报告。主表118处使用新运行，其中109处至少一个数值指标变化。

HPO公开包仅将48个池、3处元数据中的144个私有endpoint字段替换为不透明SHA身份；49个公开endpoint池保留。原运行、配置、结果与FAIRNESS身份保持不变；公开配置和文件投影有单独哈希与代码固定的转换见证。独立逐字段核查及9个篡改负例通过，实际重放使用最终投影包。

在公开仓库根目录复验：

```bash
python3 -B tools/verify_protocol_repair.py --full --output /tmp/protocol-repair-final-check
```

只需Python3.10+标准库、公开包、公开源码capsule和仓库中小型 `data/hpo_tuning/oracle3.json`。没有模型调用或数据下载。HPO实际重做终答解析／可见配置匹配／回退／聚合，默认读取哈希绑定的测量证书；本次未再次运行完整benchmark表。完整HTTP／历史图决策／原件导出等私有证据不在公开重放范围内。

`FULL_REPLAY_SUMMARY.json` 给出覆盖、源码／gate／公开投影身份及各组件比对数量；`FULL_PORTABLE_CHECK.json` 保留本次实际命令、输入源码哈希和逐产物比对结果。临时工作目录仅是验收位置，不是复算依赖。
