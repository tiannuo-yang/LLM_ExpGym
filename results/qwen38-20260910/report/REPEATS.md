# Tuning R3 明细

outerrep 0/1/2 对应同一 flat plan 中三个 R1 stage 的 seed block 2200/2204/2208；seed 标签不是独立生成保证。所有 tuning 指标、family/task/all、档位和策略均保留。Search / Pool Audit 是 R1；Exp Audit 三顺序已经按文档平均一次，不再冒充 R3。完整含资源的 block 数据请见主报告链接的 by_outerseed.csv。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | outerrep | seed 标签 | 完整均值 | known/expected | missing | 已知子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 97.2185 | 9/9 | 0 | 97.2185 |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 97.4237 | 9/9 | 0 | 97.4237 |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 97.7534 | 9/9 | 0 | 97.7534 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 98.2176 | 3/3 | 0 | 98.2176 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 99.0667 | 3/3 | 0 | 99.0667 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 98.701 | 3/3 | 0 | 98.701 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 97.4276 | 3/3 | 0 | 97.4276 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 99.3125 | 3/3 | 0 | 99.3125 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 98.6146 | 3/3 | 0 | 98.6146 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 96.0101 | 3/3 | 0 | 96.0101 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 93.892 | 3/3 | 0 | 93.892 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 95.9447 | 3/3 | 0 | 95.9447 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 99.6108 | 1/1 | 0 | 99.6108 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 99.9288 | 1/1 | 0 | 99.9288 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 99.2026 | 1/1 | 0 | 99.2026 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 95.9518 | 1/1 | 0 | 95.9518 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 98.1397 | 1/1 | 0 | 98.1397 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 97.2488 | 1/1 | 0 | 97.2488 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 99.0903 | 1/1 | 0 | 99.0903 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 99.1316 | 1/1 | 0 | 99.1316 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 99.6515 | 1/1 | 0 | 99.6515 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 97.9062 | 1/1 | 0 | 97.9062 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 92.9563 | 1/1 | 0 | 92.9563 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 99.3265 | 1/1 | 0 | 99.3265 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 97.9375 | 1/1 | 0 | 97.9375 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 97.9375 | 1/1 | 0 | 97.9375 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 92.9865 | 1/1 | 0 | 92.9865 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 94.9422 | 1/1 | 0 | 94.9422 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 95.8414 | 1/1 | 0 | 95.8414 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 95.3626 | 1/1 | 0 | 95.3626 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 93.6826 | 1/1 | 0 | 93.6826 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 92.9406 | 1/1 | 0 | 92.9406 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 99.6812 | 1/1 | 0 | 99.6812 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 93.0513 | 1/1 | 0 | 93.0513 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 99.0523 | 1/1 | 0 | 99.0523 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.829311 | 9/9 | 0 | 0.829311 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.827017 | 9/9 | 0 | 0.827017 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.829808 | 9/9 | 0 | 0.829808 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.940805 | 3/3 | 0 | 0.940805 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.943487 | 3/3 | 0 | 0.943487 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.942007 | 3/3 | 0 | 0.942007 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.703352 | 3/3 | 0 | 0.703352 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.705607 | 3/3 | 0 | 0.705607 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.705052 | 3/3 | 0 | 0.705052 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.843776 | 3/3 | 0 | 0.843776 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.831956 | 3/3 | 0 | 0.831956 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.842365 | 3/3 | 0 | 0.842365 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.943343 | 1/1 | 0 | 0.943343 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.94558 | 1/1 | 0 | 0.94558 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.940471 | 1/1 | 0 | 0.940471 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.938635 | 1/1 | 0 | 0.938635 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.944211 | 1/1 | 0 | 0.944211 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.94194 | 1/1 | 0 | 0.94194 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.940438 | 1/1 | 0 | 0.940438 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.940672 | 1/1 | 0 | 0.940672 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.94361 | 1/1 | 0 | 0.94361 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.916067 | 1/1 | 0 | 0.916067 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.916067 | 1/1 | 0 | 0.916067 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.9144 | 1/1 | 0 | 0.9144 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.726433 | 1/1 | 0 | 0.726433 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.467556 | 1/1 | 0 | 0.467556 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.465722 | 1/1 | 0 | 0.465722 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.465722 | 1/1 | 0 | 0.465722 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.850843 | 1/1 | 0 | 0.850843 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.851648 | 1/1 | 0 | 0.851648 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.852019 | 1/1 | 0 | 0.852019 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.71703 | 1/1 | 0 | 0.71703 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.715567 | 1/1 | 0 | 0.715567 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.714922 | 1/1 | 0 | 0.714922 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.963455 | 1/1 | 0 | 0.963455 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.928652 | 1/1 | 0 | 0.928652 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.960154 | 1/1 | 0 | 0.960154 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 96.9503 | 9/9 | 0 | 96.9503 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 95.5733 | 9/9 | 0 | 95.5733 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 92.8765 | 9/9 | 0 | 92.8765 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 98.0143 | 3/3 | 0 | 98.0143 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 97.26 | 3/3 | 0 | 97.26 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 94.2586 | 3/3 | 0 | 94.2586 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 98.6542 | 3/3 | 0 | 98.6542 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 94.8458 | 3/3 | 0 | 94.8458 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 88.3092 | 3/3 | 0 | 88.3092 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 94.1824 | 3/3 | 0 | 94.1824 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 94.614 | 3/3 | 0 | 94.614 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 96.0617 | 3/3 | 0 | 96.0617 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 98.7992 | 1/1 | 0 | 98.7992 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 96.597 | 1/1 | 0 | 96.597 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 99.1742 | 1/1 | 0 | 99.1742 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 97.5239 | 1/1 | 0 | 97.5239 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 96.3055 | 1/1 | 0 | 96.3055 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 84.1216 | 1/1 | 0 | 84.1216 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 97.7198 | 1/1 | 0 | 97.7198 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 98.8776 | 1/1 | 0 | 98.8776 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 99.4802 | 1/1 | 0 | 99.4802 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 99.33 | 1/1 | 0 | 99.33 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 98.0067 | 1/1 | 0 | 98.0067 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 96.6327 | 1/1 | 0 | 96.6327 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 86.5307 | 1/1 | 0 | 86.5307 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 82.6162 | 1/1 | 0 | 82.6162 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 92.0649 | 1/1 | 0 | 92.0649 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 92.0649 | 1/1 | 0 | 92.0649 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 91.8176 | 1/1 | 0 | 91.8176 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 91.7746 | 1/1 | 0 | 91.7746 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 92.6173 | 1/1 | 0 | 92.6173 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 97.578 | 1/1 | 0 | 97.578 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 98.7076 | 1/1 | 0 | 98.7076 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 99.16 | 1/1 | 0 | 99.16 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 98.7895 | 1/1 | 0 | 98.7895 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.827805 | 9/9 | 0 | 0.827805 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.825213 | 9/9 | 0 | 0.825213 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.822446 | 9/9 | 0 | 0.822446 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.937656 | 3/3 | 0 | 0.937656 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.933638 | 3/3 | 0 | 0.933638 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.930467 | 3/3 | 0 | 0.930467 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.704856 | 3/3 | 0 | 0.704856 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.70006 | 3/3 | 0 | 0.70006 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.694173 | 3/3 | 0 | 0.694173 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.840905 | 3/3 | 0 | 0.840905 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.841941 | 3/3 | 0 | 0.841941 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.842698 | 3/3 | 0 | 0.842698 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.937634 | 1/1 | 0 | 0.937634 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.922142 | 1/1 | 0 | 0.922142 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.940271 | 1/1 | 0 | 0.940271 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.942642 | 1/1 | 0 | 0.942642 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.939537 | 1/1 | 0 | 0.939537 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.908487 | 1/1 | 0 | 0.908487 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.932692 | 1/1 | 0 | 0.932692 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.939236 | 1/1 | 0 | 0.939236 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.942642 | 1/1 | 0 | 0.942642 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.915533 | 1/1 | 0 | 0.915533 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.91448 | 1/1 | 0 | 0.91448 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.464 | 1/1 | 0 | 0.464 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.450667 | 1/1 | 0 | 0.450667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.4455 | 1/1 | 0 | 0.4455 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.850463 | 1/1 | 0 | 0.850463 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.850463 | 1/1 | 0 | 0.850463 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.850361 | 1/1 | 0 | 0.850361 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.713907 | 1/1 | 0 | 0.713907 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.71464 | 1/1 | 0 | 0.71464 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.718958 | 1/1 | 0 | 0.718958 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.958345 | 1/1 | 0 | 0.958345 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.960719 | 1/1 | 0 | 0.960719 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.958774 | 1/1 | 0 | 0.958774 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 86.408 | 9/9 | 0 | 86.408 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 85.1395 | 9/9 | 0 | 85.1395 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 85.5825 | 9/9 | 0 | 85.5825 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 95.6356 | 3/3 | 0 | 95.6356 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 93.9101 | 3/3 | 0 | 93.9101 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 91.8998 | 3/3 | 0 | 91.8998 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 77.4311 | 3/3 | 0 | 77.4311 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 80.3738 | 3/3 | 0 | 80.3738 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 98.542 | 3/3 | 0 | 98.542 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 86.1572 | 3/3 | 0 | 86.1572 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 81.1345 | 3/3 | 0 | 81.1345 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 66.3059 | 3/3 | 0 | 66.3059 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 97.513 | 1/1 | 0 | 97.513 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 92.5717 | 1/1 | 0 | 92.5717 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 96.7772 | 1/1 | 0 | 96.7772 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 90.4625 | 1/1 | 0 | 90.4625 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 96.8219 | 1/1 | 0 | 96.8219 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 99.1966 | 1/1 | 0 | 99.1966 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 99.4802 | 1/1 | 0 | 99.4802 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 90.7203 | 1/1 | 0 | 90.7203 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 99.33 | 1/1 | 0 | 99.33 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 99.33 | 1/1 | 0 | 99.33 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 85.0116 | 1/1 | 0 | 85.0116 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 85.23 | 1/1 | 0 | 85.23 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 56.5615 | 1/1 | 0 | 56.5615 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 56.5615 | 1/1 | 0 | 56.5615 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 96.2959 | 1/1 | 0 | 96.2959 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 72.0134 | 1/1 | 0 | 72.0134 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 72.0134 | 1/1 | 0 | 72.0134 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 86.7373 | 1/1 | 0 | 86.7373 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 89.6547 | 1/1 | 0 | 89.6547 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 86.7821 | 1/1 | 0 | 86.7821 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 20.1629 | 1/1 | 0 | 20.1629 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 96.8035 | 1/1 | 0 | 96.8035 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 84.6078 | 1/1 | 0 | 84.6078 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 92.0174 | 1/1 | 0 | 92.0174 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.813929 | 9/9 | 0 | 0.813929 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.800823 | 9/9 | 0 | 0.800823 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.805597 | 9/9 | 0 | 0.805597 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.928742 | 3/3 | 0 | 0.928742 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.909221 | 3/3 | 0 | 0.909221 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.904391 | 3/3 | 0 | 0.904391 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.678841 | 3/3 | 0 | 0.678841 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.681215 | 3/3 | 0 | 0.681215 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.704707 | 3/3 | 0 | 0.704707 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.834205 | 3/3 | 0 | 0.834205 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.812031 | 3/3 | 0 | 0.812031 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.807692 | 3/3 | 0 | 0.807692 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.928586 | 1/1 | 0 | 0.928586 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.930021 | 1/1 | 0 | 0.930021 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.940739 | 1/1 | 0 | 0.940739 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.924646 | 1/1 | 0 | 0.924646 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.927618 | 1/1 | 0 | 0.927618 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.941039 | 1/1 | 0 | 0.941039 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.942642 | 1/1 | 0 | 0.942642 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.90868 | 1/1 | 0 | 0.90868 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.915533 | 1/1 | 0 | 0.915533 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.915533 | 1/1 | 0 | 0.915533 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.716733 | 1/1 | 0 | 0.716733 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.717 | 1/1 | 0 | 0.717 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.411111 | 1/1 | 0 | 0.411111 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.411111 | 1/1 | 0 | 0.411111 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.463556 | 1/1 | 0 | 0.463556 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.842204 | 1/1 | 0 | 0.842204 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.842204 | 1/1 | 0 | 0.842204 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.848269 | 1/1 | 0 | 0.848269 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.712062 | 1/1 | 0 | 0.712062 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.709562 | 1/1 | 0 | 0.709562 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.651582 | 1/1 | 0 | 0.651582 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.948349 | 1/1 | 0 | 0.948349 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.884328 | 1/1 | 0 | 0.884328 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.923225 | 1/1 | 0 | 0.923225 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.3164 | 3/3 | 0 | 98.3164 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.339 | 3/3 | 0 | 99.339 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.3552 | 3/3 | 0 | 99.3552 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.3164 | 3/3 | 0 | 98.3164 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.339 | 3/3 | 0 | 99.339 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.3552 | 3/3 | 0 | 99.3552 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.2216 | 1/1 | 0 | 99.2216 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.3782 | 1/1 | 0 | 99.3782 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.4684 | 1/1 | 0 | 99.4684 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 96.1352 | 1/1 | 0 | 96.1352 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.0698 | 1/1 | 0 | 99.0698 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.0698 | 1/1 | 0 | 99.0698 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.5924 | 1/1 | 0 | 99.5924 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.5688 | 1/1 | 0 | 99.5688 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.5274 | 1/1 | 0 | 99.5274 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 96.8273 | 3/3 | 0 | 96.8273 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.3031 | 3/3 | 0 | 98.3031 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 98.0396 | 3/3 | 0 | 98.0396 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 96.8273 | 3/3 | 0 | 96.8273 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.3031 | 3/3 | 0 | 98.3031 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 98.0396 | 3/3 | 0 | 98.0396 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.5951 | 1/1 | 0 | 98.5951 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.2273 | 1/1 | 0 | 98.2273 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 98.1953 | 1/1 | 0 | 98.1953 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 93.0565 | 1/1 | 0 | 93.0565 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.989 | 1/1 | 0 | 97.989 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 97.4977 | 1/1 | 0 | 97.4977 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.8304 | 1/1 | 0 | 98.8304 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.693 | 1/1 | 0 | 98.693 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 98.4257 | 1/1 | 0 | 98.4257 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.940994 | 3/3 | 0 | 0.940994 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.94381 | 3/3 | 0 | 0.94381 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.943944 | 3/3 | 0 | 0.943944 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.940994 | 3/3 | 0 | 0.940994 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.94381 | 3/3 | 0 | 0.94381 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.943944 | 3/3 | 0 | 0.943944 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.940605 | 1/1 | 0 | 0.940605 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.941707 | 1/1 | 0 | 0.941707 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942341 | 1/1 | 0 | 0.942341 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.939103 | 1/1 | 0 | 0.939103 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.946581 | 1/1 | 0 | 0.946581 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.946581 | 1/1 | 0 | 0.946581 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943276 | 1/1 | 0 | 0.943276 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.943142 | 1/1 | 0 | 0.943142 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942909 | 1/1 | 0 | 0.942909 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.935475 | 3/3 | 0 | 0.935475 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.938543 | 3/3 | 0 | 0.938543 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.937547 | 3/3 | 0 | 0.937547 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.935475 | 3/3 | 0 | 0.935475 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.938543 | 3/3 | 0 | 0.938543 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.937547 | 3/3 | 0 | 0.937547 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.936198 | 1/1 | 0 | 0.936198 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.93361 | 1/1 | 0 | 0.93361 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.933385 | 1/1 | 0 | 0.933385 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.931257 | 1/1 | 0 | 0.931257 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.943827 | 1/1 | 0 | 0.943827 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.942575 | 1/1 | 0 | 0.942575 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.938969 | 1/1 | 0 | 0.938969 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.938193 | 1/1 | 0 | 0.938193 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.936682 | 1/1 | 0 | 0.936682 |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.8961 | 3/3 | 0 | 98.8961 |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.8121 | 3/3 | 0 | 98.8121 |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.3944 | 3/3 | 0 | 98.3944 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.8961 | 3/3 | 0 | 98.8961 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.8121 | 3/3 | 0 | 98.8121 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.3944 | 3/3 | 0 | 98.3944 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.1789 | 1/1 | 0 | 99.1789 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.8244 | 1/1 | 0 | 99.8244 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.7992 | 1/1 | 0 | 98.7992 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.9169 | 1/1 | 0 | 97.9169 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.3798 | 1/1 | 0 | 97.3798 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 96.3841 | 1/1 | 0 | 96.3841 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.5924 | 1/1 | 0 | 99.5924 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.2321 | 1/1 | 0 | 99.2321 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 100 | 1/1 | 0 | 100 |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 97.2635 | 3/3 | 0 | 97.2635 |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.4062 | 3/3 | 0 | 97.4062 |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 96.0991 | 3/3 | 0 | 96.0991 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 97.2635 | 3/3 | 0 | 97.2635 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.4062 | 3/3 | 0 | 97.4062 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 96.0991 | 3/3 | 0 | 96.0991 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 97.462 | 1/1 | 0 | 97.462 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.9024 | 1/1 | 0 | 98.9024 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 95.8257 | 1/1 | 0 | 95.8257 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 95.5293 | 1/1 | 0 | 95.5293 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 94.1668 | 1/1 | 0 | 94.1668 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 94.0489 | 1/1 | 0 | 94.0489 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.7994 | 1/1 | 0 | 98.7994 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 99.1494 | 1/1 | 0 | 99.1494 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 98.4228 | 1/1 | 0 | 98.4228 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942408 | 3/3 | 0 | 0.942408 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942786 | 3/3 | 0 | 0.942786 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940983 | 3/3 | 0 | 0.940983 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942408 | 3/3 | 0 | 0.942408 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942786 | 3/3 | 0 | 0.942786 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940983 | 3/3 | 0 | 0.940983 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.940304 | 1/1 | 0 | 0.940304 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.944845 | 1/1 | 0 | 0.944845 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.937634 | 1/1 | 0 | 0.937634 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943643 | 1/1 | 0 | 0.943643 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942274 | 1/1 | 0 | 0.942274 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.939737 | 1/1 | 0 | 0.939737 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943276 | 1/1 | 0 | 0.943276 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.941239 | 1/1 | 0 | 0.941239 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.94558 | 1/1 | 0 | 0.94558 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.93486 | 3/3 | 0 | 0.93486 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.937739 | 3/3 | 0 | 0.937739 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.929056 | 3/3 | 0 | 0.929056 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.93486 | 3/3 | 0 | 0.93486 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.937739 | 3/3 | 0 | 0.937739 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.929056 | 3/3 | 0 | 0.929056 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.928227 | 1/1 | 0 | 0.928227 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.93836 | 1/1 | 0 | 0.93836 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.916717 | 1/1 | 0 | 0.916717 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.937558 | 1/1 | 0 | 0.937558 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.934086 | 1/1 | 0 | 0.934086 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.933786 | 1/1 | 0 | 0.933786 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.938794 | 1/1 | 0 | 0.938794 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.940772 | 1/1 | 0 | 0.940772 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.936665 | 1/1 | 0 | 0.936665 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.9029 | 3/3 | 0 | 98.9029 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.1083 | 3/3 | 0 | 99.1083 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.4326 | 3/3 | 0 | 99.4326 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.9029 | 3/3 | 0 | 98.9029 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.1083 | 3/3 | 0 | 99.1083 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.4326 | 3/3 | 0 | 99.4326 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.6108 | 1/1 | 0 | 99.6108 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.008 | 1/1 | 0 | 99.008 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.682 | 1/1 | 0 | 99.682 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.5763 | 1/1 | 0 | 97.5763 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.1397 | 1/1 | 0 | 98.1397 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.5982 | 1/1 | 0 | 98.5982 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.5215 | 1/1 | 0 | 99.5215 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 100.177 | 1/1 | 0 | 100.177 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 100.018 | 1/1 | 0 | 100.018 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.5703 | 3/3 | 0 | 98.5703 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.9654 | 3/3 | 0 | 98.9654 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 99.0727 | 3/3 | 0 | 99.0727 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.5703 | 3/3 | 0 | 98.5703 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.9654 | 3/3 | 0 | 98.9654 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 99.0727 | 3/3 | 0 | 99.0727 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 99.3521 | 1/1 | 0 | 99.3521 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.925 | 1/1 | 0 | 98.925 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 99.5705 | 1/1 | 0 | 99.5705 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 96.954 | 1/1 | 0 | 96.954 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.9726 | 1/1 | 0 | 97.9726 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 97.7925 | 1/1 | 0 | 97.7925 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 99.4049 | 1/1 | 0 | 99.4049 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 99.9985 | 1/1 | 0 | 99.9985 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 99.8553 | 1/1 | 0 | 99.8553 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942998 | 3/3 | 0 | 0.942998 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.943298 | 3/3 | 0 | 0.943298 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.944967 | 3/3 | 0 | 0.944967 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942998 | 3/3 | 0 | 0.942998 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.943298 | 3/3 | 0 | 0.943298 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.944967 | 3/3 | 0 | 0.944967 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943343 | 1/1 | 0 | 0.943343 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.939103 | 1/1 | 0 | 0.939103 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.943843 | 1/1 | 0 | 0.943843 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942775 | 1/1 | 0 | 0.942775 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.944211 | 1/1 | 0 | 0.944211 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.945379 | 1/1 | 0 | 0.945379 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942875 | 1/1 | 0 | 0.942875 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.946581 | 1/1 | 0 | 0.946581 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.94568 | 1/1 | 0 | 0.94568 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.941643 | 3/3 | 0 | 0.941643 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.942625 | 3/3 | 0 | 0.942625 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.943716 | 3/3 | 0 | 0.943716 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.941643 | 3/3 | 0 | 0.941643 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.942625 | 3/3 | 0 | 0.942625 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.943716 | 3/3 | 0 | 0.943716 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.941523 | 1/1 | 0 | 0.941523 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.938518 | 1/1 | 0 | 0.938518 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.943059 | 1/1 | 0 | 0.943059 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.941189 | 1/1 | 0 | 0.941189 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.943785 | 1/1 | 0 | 0.943785 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.943326 | 1/1 | 0 | 0.943326 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.942216 | 1/1 | 0 | 0.942216 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.945571 | 1/1 | 0 | 0.945571 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.944762 | 1/1 | 0 | 0.944762 |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.1809 | 3/3 | 0 | 98.1809 |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.8198 | 3/3 | 0 | 97.8198 |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.4506 | 3/3 | 0 | 98.4506 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.1809 | 3/3 | 0 | 98.1809 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.8198 | 3/3 | 0 | 97.8198 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.4506 | 3/3 | 0 | 98.4506 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.3469 | 1/1 | 0 | 97.3469 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 96.597 | 1/1 | 0 | 96.597 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.3165 | 1/1 | 0 | 99.3165 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.8514 | 1/1 | 0 | 97.8514 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.5239 | 1/1 | 0 | 97.5239 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 97.2226 | 1/1 | 0 | 97.2226 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.3443 | 1/1 | 0 | 99.3443 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.3384 | 1/1 | 0 | 99.3384 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.8127 | 1/1 | 0 | 98.8127 |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 92.5108 | 3/3 | 0 | 92.5108 |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 85.8212 | 3/3 | 0 | 85.8212 |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 93.9409 | 3/3 | 0 | 93.9409 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 92.5108 | 3/3 | 0 | 92.5108 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 85.8212 | 3/3 | 0 | 85.8212 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 93.9409 | 3/3 | 0 | 93.9409 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 91.5031 | 1/1 | 0 | 91.5031 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 73.1282 | 1/1 | 0 | 73.1282 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 93.8288 | 1/1 | 0 | 93.8288 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 88.0126 | 1/1 | 0 | 88.0126 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 86.7942 | 1/1 | 0 | 86.7942 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 92.0018 | 1/1 | 0 | 92.0018 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.0167 | 1/1 | 0 | 98.0167 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.5411 | 1/1 | 0 | 97.5411 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 95.992 | 1/1 | 0 | 95.992 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.937589 | 3/3 | 0 | 0.937589 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.935541 | 3/3 | 0 | 0.935541 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940672 | 3/3 | 0 | 0.940672 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.937589 | 3/3 | 0 | 0.937589 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.935541 | 3/3 | 0 | 0.935541 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940672 | 3/3 | 0 | 0.940672 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.927417 | 1/1 | 0 | 0.927417 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.922142 | 1/1 | 0 | 0.922142 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.941273 | 1/1 | 0 | 0.941273 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943476 | 1/1 | 0 | 0.943476 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942642 | 1/1 | 0 | 0.942642 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.941874 | 1/1 | 0 | 0.941874 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.941874 | 1/1 | 0 | 0.941874 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.94184 | 1/1 | 0 | 0.94184 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.938869 | 1/1 | 0 | 0.938869 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.913028 | 3/3 | 0 | 0.913028 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.868011 | 3/3 | 0 | 0.868011 |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.918055 | 3/3 | 0 | 0.918055 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.913028 | 3/3 | 0 | 0.913028 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.868011 | 3/3 | 0 | 0.868011 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.918055 | 3/3 | 0 | 0.918055 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.88631 | 1/1 | 0 | 0.88631 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.757053 | 1/1 | 0 | 0.757053 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.902669 | 1/1 | 0 | 0.902669 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.918403 | 1/1 | 0 | 0.918403 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.915298 | 1/1 | 0 | 0.915298 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.928569 | 1/1 | 0 | 0.928569 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.93437 | 1/1 | 0 | 0.93437 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.931682 | 1/1 | 0 | 0.931682 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.922927 | 1/1 | 0 | 0.922927 |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.6909 | 3/3 | 0 | 98.6909 |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.9666 | 3/3 | 0 | 97.9666 |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.9153 | 3/3 | 0 | 98.9153 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.6909 | 3/3 | 0 | 98.6909 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.9666 | 3/3 | 0 | 97.9666 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.9153 | 3/3 | 0 | 98.9153 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.8799 | 1/1 | 0 | 98.8799 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.9653 | 1/1 | 0 | 98.9653 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.8054 | 1/1 | 0 | 99.8054 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.3405 | 1/1 | 0 | 97.3405 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 96.24 | 1/1 | 0 | 96.24 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 97.4191 | 1/1 | 0 | 97.4191 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 99.8523 | 1/1 | 0 | 99.8523 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.6945 | 1/1 | 0 | 98.6945 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.5215 | 1/1 | 0 | 99.5215 |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 93.25 | 3/3 | 0 | 93.25 |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 86.2711 | 3/3 | 0 | 86.2711 |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 92.3422 | 3/3 | 0 | 92.3422 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 93.25 | 3/3 | 0 | 93.25 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 86.2711 | 3/3 | 0 | 86.2711 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 92.3422 | 3/3 | 0 | 92.3422 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 93.1584 | 1/1 | 0 | 93.1584 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 72.1463 | 1/1 | 0 | 72.1463 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 91.3928 | 1/1 | 0 | 91.3928 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 87.3772 | 1/1 | 0 | 87.3772 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 89.7386 | 1/1 | 0 | 89.7386 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 90.1677 | 1/1 | 0 | 90.1677 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 99.2143 | 1/1 | 0 | 99.2143 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 96.9283 | 1/1 | 0 | 96.9283 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | 95.4662 | 1/1 | 0 | 95.4662 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.941707 | 3/3 | 0 | 0.941707 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.938791 | 3/3 | 0 | 0.938791 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.94332 | 3/3 | 0 | 0.94332 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.941707 | 3/3 | 0 | 0.941707 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.938791 | 3/3 | 0 | 0.938791 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.94332 | 3/3 | 0 | 0.94332 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.938201 | 1/1 | 0 | 0.938201 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.938802 | 1/1 | 0 | 0.938802 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.944712 | 1/1 | 0 | 0.944712 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.942174 | 1/1 | 0 | 0.942174 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.93937 | 1/1 | 0 | 0.93937 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942374 | 1/1 | 0 | 0.942374 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.944745 | 1/1 | 0 | 0.944745 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.938201 | 1/1 | 0 | 0.938201 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942875 | 1/1 | 0 | 0.942875 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.918625 | 3/3 | 0 | 0.918625 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.846835 | 3/3 | 0 | 0.846835 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.909795 | 3/3 | 0 | 0.909795 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.918625 | 3/3 | 0 | 0.918625 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.846835 | 3/3 | 0 | 0.846835 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.909795 | 3/3 | 0 | 0.909795 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.897953 | 1/1 | 0 | 0.897953 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.689487 | 1/1 | 0 | 0.689487 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.885534 | 1/1 | 0 | 0.885534 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.916784 | 1/1 | 0 | 0.916784 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.922801 | 1/1 | 0 | 0.922801 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.923895 | 1/1 | 0 | 0.923895 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.941139 | 1/1 | 0 | 0.941139 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.928218 | 1/1 | 0 | 0.928218 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.919955 | 1/1 | 0 | 0.919955 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.1119 | 3/3 | 0 | 98.1119 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.3217 | 3/3 | 0 | 98.3217 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.4397 | 3/3 | 0 | 98.4397 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.1119 | 3/3 | 0 | 98.1119 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.3217 | 3/3 | 0 | 98.3217 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.4397 | 3/3 | 0 | 98.4397 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.5984 | 1/1 | 0 | 97.5984 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.6995 | 1/1 | 0 | 98.6995 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.5477 | 1/1 | 0 | 98.5477 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.9955 | 1/1 | 0 | 97.9955 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.5239 | 1/1 | 0 | 97.5239 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 97.3798 | 1/1 | 0 | 97.3798 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 98.7418 | 1/1 | 0 | 98.7418 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 98.7418 | 1/1 | 0 | 98.7418 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | 99.3916 | 1/1 | 0 | 99.3916 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 96.6486 | 3/3 | 0 | 96.6486 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 95.2788 | 3/3 | 0 | 95.2788 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 96.8846 | 3/3 | 0 | 96.8846 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 96.6486 | 3/3 | 0 | 96.6486 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 95.2788 | 3/3 | 0 | 95.2788 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 96.8846 | 3/3 | 0 | 96.8846 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 97.3338 | 1/1 | 0 | 97.3338 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.0351 | 1/1 | 0 | 98.0351 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 94.6392 | 1/1 | 0 | 94.6392 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 94.1995 | 1/1 | 0 | 94.1995 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 90.1317 | 1/1 | 0 | 90.1317 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 96.8034 | 1/1 | 0 | 96.8034 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 98.4124 | 1/1 | 0 | 98.4124 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 97.6696 | 1/1 | 0 | 97.6696 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | 99.2114 | 1/1 | 0 | 99.2114 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.937166 | 3/3 | 0 | 0.937166 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.939347 | 3/3 | 0 | 0.939347 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940093 | 3/3 | 0 | 0.940093 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.937166 | 3/3 | 0 | 0.937166 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.939347 | 3/3 | 0 | 0.939347 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.940093 | 3/3 | 0 | 0.940093 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.929187 | 1/1 | 0 | 0.929187 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.936932 | 1/1 | 0 | 0.936932 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.935864 | 1/1 | 0 | 0.935864 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.943843 | 1/1 | 0 | 0.943843 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942642 | 1/1 | 0 | 0.942642 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942274 | 1/1 | 0 | 0.942274 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.938468 | 1/1 | 0 | 0.938468 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.938468 | 1/1 | 0 | 0.938468 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.942141 | 1/1 | 0 | 0.942141 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.932701 | 3/3 | 0 | 0.932701 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.92949 | 3/3 | 0 | 0.92949 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.930099 | 3/3 | 0 | 0.930099 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.932701 | 3/3 | 0 | 0.932701 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.92949 | 3/3 | 0 | 0.92949 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.930099 | 3/3 | 0 | 0.930099 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.927325 | 1/1 | 0 | 0.927325 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.932258 | 1/1 | 0 | 0.932258 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.90837 | 1/1 | 0 | 0.90837 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.93417 | 1/1 | 0 | 0.93417 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.923803 | 1/1 | 0 | 0.923803 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.940805 | 1/1 | 0 | 0.940805 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.936607 | 1/1 | 0 | 0.936607 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.932409 | 1/1 | 0 | 0.932409 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.941122 | 1/1 | 0 | 0.941122 |

