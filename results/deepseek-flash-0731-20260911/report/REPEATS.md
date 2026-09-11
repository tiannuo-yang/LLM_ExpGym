# Tuning R3 明细

outerrep 0/1/2 对应三个独立队列 stage 的 seed block 2200/2204/2208；seed 标签不是独立生成保证。所有 tuning 指标、family/task/all、档位和策略均保留。Search / Pool Audit 是 R1；Exp Audit 三顺序已经按文档平均一次，不再冒充 R3。完整含资源的 block 数据请见主报告链接的 by_outerseed.csv。

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | outerrep | seed 标签 | 完整均值 | known/expected | missing | 已知子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | unknown | 8/9 | 1 | 93.2892 |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 7/9 | 2 | 76.6479 |
| expgym | tuning | all/all | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 5/9 | 4 | 73.3376 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 97.6513 | 3/3 | 0 | 97.6513 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 60.2848 | 3/3 | 0 | 60.2848 |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 67.1165 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 87.9318 | 3/3 | 0 | 87.9318 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 94.5558 | 3/3 | 0 | 94.5558 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 93.56 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | unknown | 2/3 | 1 | 94.782 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 72.0134 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 56.2258 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 99.2833 | 1/1 | 0 | 99.2833 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 94.7989 | 1/1 | 0 | 94.7989 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 98.4934 | 1/1 | 0 | 98.4934 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 67.1165 | 1/1 | 0 | 67.1165 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 98.8717 | 1/1 | 0 | 98.8717 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 82.3612 | 1/1 | 0 | 82.3612 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 85.23 | 1/1 | 0 | 85.23 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 97.5156 | 1/1 | 0 | 97.5156 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 96.2538 | 1/1 | 0 | 96.2538 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 86.1519 | 1/1 | 0 | 86.1519 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 87.12 | 1/1 | 0 | 87.12 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 95.0546 | 1/1 | 0 | 95.0546 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | 72.0134 | 1/1 | 0 | 72.0134 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | 94.5093 | 1/1 | 0 | 94.5093 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 20.1629 | 1/1 | 0 | 20.1629 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 2 | &#91;2208&#93; | 92.2888 | 1/1 | 0 | 92.2888 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | unknown | 8/9 | 1 | 0.808301 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 7/9 | 2 | 0.675919 |
| expgym | tuning | all/all | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 5/9 | 4 | 0.725572 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.938646 | 3/3 | 0 | 0.938646 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.597 | 3/3 | 0 | 0.597 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.865151 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.694162 | 3/3 | 0 | 0.694162 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.699411 | 3/3 | 0 | 0.699411 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 0.593239 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | unknown | 2/3 | 1 | 0.783991 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.842204 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 0.788116 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.941039 | 1/1 | 0 | 0.941039 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.935697 | 1/1 | 0 | 0.935697 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.945112 | 1/1 | 0 | 0.945112 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.865151 | 1/1 | 0 | 0.865151 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.939203 | 1/1 | 0 | 0.939203 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.916067 | 1/1 | 0 | 0.916067 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.717 | 1/1 | 0 | 0.717 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.732 | 1/1 | 0 | 0.732 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.4635 | 1/1 | 0 | 0.4635 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.450167 | 1/1 | 0 | 0.450167 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.451444 | 1/1 | 0 | 0.451444 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.851694 | 1/1 | 0 | 0.851694 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.842204 | 1/1 | 0 | 0.842204 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.716287 | 1/1 | 0 | 0.716287 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.651582 | 1/1 | 0 | 0.651582 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.924649 | 1/1 | 0 | 0.924649 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 82.4178 | 9/9 | 0 | 82.4178 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 8/9 | 1 | 92.5251 |
| expgym | tuning | all/all | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 8/9 | 1 | 64.5719 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 64.1219 | 3/3 | 0 | 64.1219 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 95.3205 | 3/3 | 0 | 95.3205 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 56.189 | 3/3 | 0 | 56.189 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 93.5409 | 3/3 | 0 | 93.5409 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 88.7169 | 3/3 | 0 | 88.7169 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 83.6616 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 89.5906 | 3/3 | 0 | 89.5906 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 94.0442 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 60.2284 | 3/3 | 0 | 60.2284 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 93.1987 | 1/1 | 0 | 93.1987 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 99.2216 | 1/1 | 0 | 99.2216 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 87.3837 | 1/1 | 0 | 87.3837 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 85.6151 | 1/1 | 0 | 85.6151 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 99.1671 | 1/1 | 0 | 99.1671 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 99.3561 | 1/1 | 0 | 99.3561 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 82.9519 | 1/1 | 0 | 82.9519 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 84.9581 | 1/1 | 0 | 84.9581 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 91.1223 | 1/1 | 0 | 91.1223 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 78.7324 | 1/1 | 0 | 78.7324 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 85.0116 | 1/1 | 0 | 85.0116 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 95.6646 | 1/1 | 0 | 95.6646 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 96.2959 | 1/1 | 0 | 96.2959 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 87.9512 | 1/1 | 0 | 87.9512 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 89.5247 | 1/1 | 0 | 89.5247 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 84.6243 | 1/1 | 0 | 84.6243 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 90.031 | 1/1 | 0 | 90.031 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | 98.5637 | 1/1 | 0 | 98.5637 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 89.3791 | 1/1 | 0 | 89.3791 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 0 | &#91;2200&#93; | 90.7897 | 1/1 | 0 | 90.7897 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 2 | &#91;2208&#93; | 6.68176 | 1/1 | 0 | 6.68176 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.713211 | 9/9 | 0 | 0.713211 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 8/9 | 1 | 0.806275 |
| expgym | tuning | all/all | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 8/9 | 1 | 0.67684 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.613036 | 3/3 | 0 | 0.613036 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.933115 | 3/3 | 0 | 0.933115 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.587173 | 3/3 | 0 | 0.587173 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.700616 | 3/3 | 0 | 0.700616 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.693874 | 3/3 | 0 | 0.693874 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 2/3 | 1 | 0.80936 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.825979 | 3/3 | 0 | 0.825979 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 0.784616 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.67816 | 3/3 | 0 | 0.67816 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.898237 | 1/1 | 0 | 0.898237 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.940605 | 1/1 | 0 | 0.940605 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0 | 1/1 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.9168 | 1/1 | 0 | 0.9168 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.912293 | 1/1 | 0 | 0.912293 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.940872 | 1/1 | 0 | 0.940872 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.94194 | 1/1 | 0 | 0.94194 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.849225 | 1/1 | 0 | 0.849225 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.904093 | 1/1 | 0 | 0.904093 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.909 | 1/1 | 0 | 0.909 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.709067 | 1/1 | 0 | 0.709067 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.716733 | 1/1 | 0 | 0.716733 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.462722 | 1/1 | 0 | 0.462722 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.463556 | 1/1 | 0 | 0.463556 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.848769 | 1/1 | 0 | 0.848769 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.849417 | 1/1 | 0 | 0.849417 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.847398 | 1/1 | 0 | 0.847398 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.712389 | 1/1 | 0 | 0.712389 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.719816 | 1/1 | 0 | 0.719816 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.711822 | 1/1 | 0 | 0.711822 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.91678 | 1/1 | 0 | 0.91678 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.47526 | 1/1 | 0 | 0.47526 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 84.4287 | 9/9 | 0 | 84.4287 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 82.7321 | 9/9 | 0 | 82.7321 |
| expgym | tuning | all/all | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 7/9 | 2 | 77.4869 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 87.7612 | 3/3 | 0 | 87.7612 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 88.7111 | 3/3 | 0 | 88.7111 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 84.1208 | 3/3 | 0 | 84.1208 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 79.6243 | 3/3 | 0 | 79.6243 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 72.5351 | 3/3 | 0 | 72.5351 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 77.7041 | 3/3 | 0 | 77.7041 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 85.9005 | 3/3 | 0 | 85.9005 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 86.9502 | 3/3 | 0 | 86.9502 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 56.9337 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 98.8514 | 1/1 | 0 | 98.8514 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 95.1657 | 1/1 | 0 | 95.1657 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 84.9207 | 1/1 | 0 | 84.9207 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 75.4487 | 1/1 | 0 | 75.4487 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 82.3612 | 1/1 | 0 | 82.3612 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 82.3612 | 1/1 | 0 | 82.3612 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 91.157 | 1/1 | 0 | 91.157 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 82.3115 | 1/1 | 0 | 82.3115 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 100 | 1/1 | 0 | 100 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 78.7324 | 1/1 | 0 | 78.7324 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 94.2394 | 1/1 | 0 | 94.2394 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 56.5615 | 1/1 | 0 | 56.5615 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 56.5615 | 1/1 | 0 | 56.5615 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 56.5615 | 1/1 | 0 | 56.5615 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 72.0134 | 1/1 | 0 | 72.0134 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 72.0134 | 1/1 | 0 | 72.0134 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 86.7821 | 1/1 | 0 | 86.7821 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 97.578 | 1/1 | 0 | 97.578 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 0 | &#91;2200&#93; | 98.9058 | 1/1 | 0 | 98.9058 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 1 | &#91;2204&#93; | 91.2592 | 1/1 | 0 | 91.2592 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 2 | &#91;2208&#93; | 56.9337 | 1/1 | 0 | 56.9337 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.798632 | 9/9 | 0 | 0.798632 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.799665 | 9/9 | 0 | 0.799665 |
| expgym | tuning | all/all | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 7/9 | 2 | 0.772575 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.876135 | 3/3 | 0 | 0.876135 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.898137 | 3/3 | 0 | 0.898137 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.875957 | 3/3 | 0 | 0.875957 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.68271 | 3/3 | 0 | 0.68271 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.674055 | 3/3 | 0 | 0.674055 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.680366 | 3/3 | 0 | 0.680366 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.83705 | 3/3 | 0 | 0.83705 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.826802 | 3/3 | 0 | 0.826802 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.739055 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.938001 | 1/1 | 0 | 0.938001 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.936632 | 1/1 | 0 | 0.936632 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.910524 | 1/1 | 0 | 0.910524 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.886385 | 1/1 | 0 | 0.886385 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.8956 | 1/1 | 0 | 0.8956 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.901987 | 1/1 | 0 | 0.901987 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.735033 | 1/1 | 0 | 0.735033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.709067 | 1/1 | 0 | 0.709067 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.728 | 1/1 | 0 | 0.728 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.411111 | 1/1 | 0 | 0.411111 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.411111 | 1/1 | 0 | 0.411111 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.411111 | 1/1 | 0 | 0.411111 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.842204 | 1/1 | 0 | 0.842204 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.842204 | 1/1 | 0 | 0.842204 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.709562 | 1/1 | 0 | 0.709562 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.718958 | 1/1 | 0 | 0.718958 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 0 | &#91;2200&#93; | 0.959385 | 1/1 | 0 | 0.959385 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 1 | &#91;2204&#93; | 0.919245 | 1/1 | 0 | 0.919245 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 2 | &#91;2208&#93; | 0.739055 | 1/1 | 0 | 0.739055 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 97.3279 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 99.4624 |
| poolact | tuning | all/all | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 98.6236 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 97.3279 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 99.4624 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 98.6236 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | 97.3279 | 1/1 | 0 | 97.3279 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 98.6236 | 1/1 | 0 | 98.6236 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | 99.4624 | 1/1 | 0 | 99.4624 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 71.4866 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 98.5335 |
| poolact | tuning | all/all | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 94.8789 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 71.4866 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 98.5335 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 94.8789 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | 71.4866 | 1/1 | 0 | 71.4866 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 94.8789 | 1/1 | 0 | 94.8789 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | 98.5335 | 1/1 | 0 | 98.5335 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.927284 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.942541 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.936398 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.927284 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.942541 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.936398 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.927284 | 1/1 | 0 | 0.927284 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.936398 | 1/1 | 0 | 0.936398 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.942541 | 1/1 | 0 | 0.942541 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.684846 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.937291 |
| poolact | tuning | all/all | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.910056 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.684846 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.937291 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.910056 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.684846 | 1/1 | 0 | 0.684846 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.910056 | 1/1 | 0 | 0.910056 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.937291 | 1/1 | 0 | 0.937291 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 10.8189 |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 10.8189 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | 10.8189 | 1/1 | 0 | 10.8189 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 2.70472 |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 2.70472 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | 2.70472 | 1/1 | 0 | 2.70472 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.318743 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.318743 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.318743 | 1/1 | 0 | 0.318743 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.0796858 |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.0796858 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.0796858 | 1/1 | 0 | 0.0796858 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 97.8974 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 97.8974 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 97.8974 | 1/1 | 0 | 97.8974 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 72.4394 |
| poolact | tuning | all/all | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 72.4394 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 72.4394 | 1/1 | 0 | 72.4394 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.93129 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.93129 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.93129 | 1/1 | 0 | 0.93129 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.691548 |
| poolact | tuning | all/all | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.691548 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.691548 | 1/1 | 0 | 0.691548 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 85.7566 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 85.7566 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 21.4392 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 21.4392 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | 21.4392 | 1/1 | 0 | 21.4392 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.845887 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.845887 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.211472 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 1/3 | 2 | 0.211472 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | 0.211472 | 1/1 | 0 | 0.211472 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 86.5374 |
| poolact | tuning | all/all | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 86.5374 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 85.7566 | 1/1 | 0 | 85.7566 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | 87.3182 | 1/1 | 0 | 87.3182 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 46.8368 |
| poolact | tuning | all/all | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 46.8368 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 26.8486 | 1/1 | 0 | 26.8486 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | 66.825 | 1/1 | 0 | 66.825 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 0.88126 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 0.88126 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.845887 | 1/1 | 0 | 0.845887 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.916633 | 1/1 | 0 | 0.916633 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 0.617626 |
| poolact | tuning | all/all | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 2/3 | 1 | 0.617626 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.370843 | 1/1 | 0 | 0.370843 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.864408 | 1/1 | 0 | 0.864408 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 83.008 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 87.3751 |
| poolact | tuning | all/all | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 83.008 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 87.3751 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | 87.3751 | 1/1 | 0 | 87.3751 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | 83.008 | 1/1 | 0 | 83.008 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 75.5044 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 67.4268 |
| poolact | tuning | all/all | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 75.5044 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 67.4268 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | 67.4268 | 1/1 | 0 | 67.4268 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | 75.5044 | 1/1 | 0 | 75.5044 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.905649 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.857272 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.905649 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.857272 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | 0.857272 | 1/1 | 0 | 0.857272 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | 0.905649 | 1/1 | 0 | 0.905649 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.886527 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.716947 |
| poolact | tuning | all/all | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 1/3 | 2 | 0.886527 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 1/3 | 2 | 0.716947 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | 0.716947 | 1/1 | 0 | 0.716947 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | 0.886527 | 1/1 | 0 | 0.886527 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 0 | &#91;2200&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 1 | &#91;2204&#93; | unknown | 0/1 | 1 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 2 | &#91;2208&#93; | unknown | 0/1 | 1 | unknown |

