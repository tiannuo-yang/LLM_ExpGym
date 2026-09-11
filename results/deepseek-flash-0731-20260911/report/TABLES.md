# 全部 family / task 与资源表

本附件直接展示冻结聚合表，不重新评分。unknown 与已知子集严格区分；层级 all/family/task 不相加当作额外样本。

## 质量：预定义 family / task

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | evidence_acc | fraction | 0.639517 | 13/13 | 0 | 13 | 0.639517 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | label_acc | fraction | 0.668175 | 13/13 | 0 | 13 | 0.668175 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | evidence_acc | fraction | 0.586727 | 13/13 | 0 | 13 | 0.586727 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | label_acc | fraction | 0.755656 | 13/13 | 0 | 13 | 0.755656 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | evidence_acc | fraction | 0.475113 | 13/13 | 0 | 13 | 0.475113 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | label_acc | fraction | 0.702866 | 13/13 | 0 | 13 | 0.702866 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | f1 | fraction | 0.369073 | 34/34 | 0 | 34 | 0.369073 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | f1 | fraction | 0.498341 | 39/39 | 0 | 39 | 0.498341 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | f1 | fraction | 0.333516 | 34/34 | 0 | 34 | 0.333516 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | f1 | fraction | 0.497486 | 39/39 | 0 | 39 | 0.497486 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | f1 | fraction | 0.159269 | 34/34 | 0 | 34 | 0.159269 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | f1 | fraction | 0.177828 | 39/39 | 0 | 39 | 0.177828 | 1 / unknown |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | unknown | 7/9 | 2 | 3 | 75.687 | 3 / unknown |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | unknown | 8/9 | 1 | 3 | 91.7487 | 3 / unknown |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | unknown | 5/9 | 4 | 3 | 77.7196 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 49.6417 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 86.8029 | 3/3 | 0 | 1 | 86.8029 | 3 / 17.1487 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 90.6164 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 91.1558 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 94.2485 | 3/3 | 0 | 1 | 94.2485 | 3 / 7.90842 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 89.8419 | 3/3 | 0 | 1 | 89.8419 | 3 / 5.57397 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 83.534 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 57.3361 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | unknown | 1/3 | 2 | 1 | 92.2888 | 3 / unknown |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | unknown | 7/9 | 2 | 3 | 0.759461 | 3 / unknown |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | unknown | 8/9 | 1 | 3 | 0.697358 | 3 / unknown |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | unknown | 5/9 | 4 | 3 | 0.818511 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.470519 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 0.91532 | 3/3 | 0 | 1 | 0.91532 | 3 / 0.043702 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.892545 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.909027 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 0.728011 | 3/3 | 0 | 1 | 0.728011 | 3 / 0.00965576 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 0.455037 | 3/3 | 0 | 1 | 0.455037 | 3 / 0.00735693 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.846949 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.683935 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | unknown | 1/3 | 2 | 1 | 0.924649 | 3 / unknown |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 71.8771 | 9/9 | 0 | 3 | 71.8771 | 3 / 20.6864 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | unknown | 8/9 | 1 | 3 | 90.0085 | 3 / unknown |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | unknown | 8/9 | 1 | 3 | 76.2535 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 64.1401 | 3/3 | 0 | 1 | 64.1401 | 3 / 55.6285 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 57.6663 | 3/3 | 0 | 1 | 57.6663 | 3 / 49.9483 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 93.825 | 3/3 | 0 | 1 | 93.825 | 3 / 9.4169 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 86.1306 | 3/3 | 0 | 1 | 86.1306 | 3 / 4.52088 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 87.9147 | 3/3 | 0 | 1 | 87.9147 | 3 / 10.927 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 95.9803 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 87.3667 | 3/3 | 0 | 1 | 87.3667 | 3 / 2.50196 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 92.6579 | 3/3 | 0 | 1 | 92.6579 | 3 / 5.12496 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 48.7357 | 3 / unknown |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 0.711108 | 9/9 | 0 | 3 | 0.711108 | 3 / 0.192698 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | unknown | 8/9 | 1 | 3 | 0.696148 | 3 / unknown |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | unknown | 8/9 | 1 | 3 | 0.753074 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 0.612947 | 3/3 | 0 | 1 | 0.612947 | 3 / 0.531251 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 0.609698 | 3/3 | 0 | 1 | 0.609698 | 3 / 0.528019 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 0.910679 | 3/3 | 0 | 1 | 0.910679 | 3 / 0.0532233 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 0.905027 | 3/3 | 0 | 1 | 0.905027 | 3 / 0.00359862 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 0.720278 | 3/3 | 0 | 1 | 0.720278 | 3 / 0.0133413 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.463139 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 0.848528 | 3/3 | 0 | 1 | 0.848528 | 3 / 0.00103057 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 0.714676 | 3/3 | 0 | 1 | 0.714676 | 3 / 0.00446033 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.69602 | 3 / unknown |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 86.8644 | 9/9 | 0 | 3 | 86.8644 | 3 / 2.42302 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 76.6212 | 9/9 | 0 | 3 | 76.6212 | 3 / 3.66658 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | unknown | 7/9 | 2 | 3 | 82.1866 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 90.1216 | 3/3 | 0 | 1 | 90.1216 | 3 / 7.56027 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 85.1784 | 3/3 | 0 | 1 | 85.1784 | 3 / 9.86103 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 85.2931 | 3/3 | 0 | 1 | 85.2931 | 3 / 5.07825 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 82.3115 | 3/3 | 0 | 1 | 82.3115 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 90.9906 | 3/3 | 0 | 1 | 90.9906 | 3 / 10.9997 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 56.5615 | 3/3 | 0 | 1 | 56.5615 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 72.0134 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | unknown | 2/3 | 1 | 1 | 92.1801 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 82.3662 | 3/3 | 0 | 1 | 82.3662 | 3 / 22.3546 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 0.88341 | 9/9 | 0 | 3 | 0.88341 | 3 / 0.0127545 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 0.679044 | 9/9 | 0 | 3 | 0.679044 | 3 / 0.0044767 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | unknown | 7/9 | 2 | 3 | 0.809675 | 3 / unknown |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 0.876591 | 3/3 | 0 | 1 | 0.876591 | 3 / 0.0531821 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 0.91118 | 3/3 | 0 | 1 | 0.91118 | 3 / 0.02513 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 0.862458 | 3/3 | 0 | 1 | 0.862458 | 3 / 0.0287017 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 0.901987 | 3/3 | 0 | 1 | 0.901987 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 0.724033 | 3/3 | 0 | 1 | 0.724033 | 3 / 0.0134301 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 0.411111 | 3/3 | 0 | 1 | 0.411111 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.842204 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | unknown | 2/3 | 1 | 1 | 0.71426 | 3 / unknown |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 0.872561 | 3/3 | 0 | 1 | 0.872561 | 3 / 0.117349 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | evidence_acc_mi | fraction | 0.364253 | 13/13 | 0 | 13 | 0.364253 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | evidence_acc_mv | fraction | 0.588235 | 13/13 | 0 | 13 | 0.588235 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | label_acc_mi | fraction | 0.447964 | 13/13 | 0 | 13 | 0.447964 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | label_acc_mv | fraction | 0.737557 | 13/13 | 0 | 13 | 0.737557 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | evidence_acc_mi | fraction | 0.322398 | 13/13 | 0 | 13 | 0.322398 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | evidence_acc_mv | fraction | 0.59276 | 13/13 | 0 | 13 | 0.59276 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | label_acc_mi | fraction | 0.400452 | 13/13 | 0 | 13 | 0.400452 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | label_acc_mv | fraction | 0.78733 | 13/13 | 0 | 13 | 0.78733 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | evidence_acc_mi | fraction | 0.109729 | 13/13 | 0 | 13 | 0.109729 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | evidence_acc_mv | fraction | 0.334842 | 13/13 | 0 | 13 | 0.334842 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | label_acc_mi | fraction | 0.149321 | 13/13 | 0 | 13 | 0.149321 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | label_acc_mv | fraction | 0.447964 | 13/13 | 0 | 13 | 0.447964 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | evidence_acc_mi | fraction | 0.128959 | 13/13 | 0 | 13 | 0.128959 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | evidence_acc_mv | fraction | 0.371041 | 13/13 | 0 | 13 | 0.371041 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | label_acc_mi | fraction | 0.171946 | 13/13 | 0 | 13 | 0.171946 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | label_acc_mv | fraction | 0.502262 | 13/13 | 0 | 13 | 0.502262 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | evidence_acc_mi | fraction | 0.18552 | 13/13 | 0 | 13 | 0.18552 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | evidence_acc_mv | fraction | 0.497738 | 13/13 | 0 | 13 | 0.497738 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | label_acc_mi | fraction | 0.236425 | 13/13 | 0 | 13 | 0.236425 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | label_acc_mv | fraction | 0.692308 | 13/13 | 0 | 13 | 0.692308 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | evidence_acc_mi | fraction | 0.0169683 | 13/13 | 0 | 13 | 0.0169683 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | evidence_acc_mv | fraction | 0.0678733 | 13/13 | 0 | 13 | 0.0678733 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | label_acc_mi | fraction | 0.0328054 | 13/13 | 0 | 13 | 0.0328054 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | label_acc_mv | fraction | 0.131222 | 13/13 | 0 | 13 | 0.131222 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | f1_mi | fraction | 0.169872 | 39/39 | 0 | 39 | 0.169872 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | f1_mv | fraction | 0.17094 | 39/39 | 0 | 39 | 0.17094 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | f1_mi | fraction | 0.0907692 | 39/39 | 0 | 39 | 0.0907692 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | f1_mv | fraction | 0.132479 | 39/39 | 0 | 39 | 0.132479 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | f1_mi | fraction | 0.0790598 | 39/39 | 0 | 39 | 0.0790598 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | f1_mv | fraction | 0.119658 | 39/39 | 0 | 39 | 0.119658 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | f1_mi | fraction | 0.0470085 | 39/39 | 0 | 39 | 0.0470085 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | f1_mv | fraction | 0.042735 | 39/39 | 0 | 39 | 0.042735 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | f1_mi | fraction | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | f1_mv | fraction | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | f1_mi | fraction | 0.0549271 | 39/39 | 0 | 39 | 0.0549271 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | f1_mv | fraction | 0.0744093 | 39/39 | 0 | 39 | 0.0744093 | 1 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | unknown | 3/9 | 6 | 3 | 98.7191 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | unknown | 2/3 | 1 | 1 | 97.9757 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 99.4624 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | unknown | 3/9 | 6 | 3 | 90.8581 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | unknown | 2/3 | 1 | 1 | 83.1827 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 98.5335 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | unknown | 3/9 | 6 | 3 | 0.937191 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | unknown | 2/3 | 1 | 1 | 0.931841 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.942541 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | unknown | 3/9 | 6 | 3 | 0.867371 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | unknown | 2/3 | 1 | 1 | 0.797451 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.937291 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 10.8189 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 10.8189 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 2.70472 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 2.70472 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.318743 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.318743 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.0796858 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.0796858 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 97.8974 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 97.8974 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 72.4394 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 72.4394 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.93129 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.93129 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.691548 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.691548 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | unknown | 1/9 | 8 | 3 | 85.7566 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 85.7566 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | unknown | 1/9 | 8 | 3 | 21.4392 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 21.4392 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | unknown | 1/9 | 8 | 3 | 0.845887 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.845887 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | unknown | 1/9 | 8 | 3 | 0.211472 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.211472 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | unknown | 2/9 | 7 | 3 | 86.5374 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 85.7566 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 87.3182 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | unknown | 2/9 | 7 | 3 | 46.8368 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 26.8486 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 66.825 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | unknown | 2/9 | 7 | 3 | 0.88126 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.845887 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.916633 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | unknown | 2/9 | 7 | 3 | 0.617626 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.370843 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.864408 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | unknown | 2/9 | 7 | 3 | 85.1915 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 87.3751 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | unknown | 1/3 | 2 | 1 | 83.008 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | unknown | 2/9 | 7 | 3 | 71.4656 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 67.4268 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | unknown | 1/3 | 2 | 1 | 75.5044 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | unknown | 2/9 | 7 | 3 | 0.88146 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.857272 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | unknown | 1/3 | 2 | 1 | 0.905649 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | unknown | 2/9 | 7 | 3 | 0.801737 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.716947 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | unknown | 1/3 | 2 | 1 | 0.886527 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |


## 质量：全部对应差值

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | family/evidence_audit | cost_free | evidence_acc | cost_free − cost_moderate | +0.0527903 | fraction | +5.27903 | 13/13 | 0 | 0.0527903 |
| expgym | evidence_audit | family/evidence_audit | cost_free | evidence_acc | cost_free − cost_tight | +0.164404 | fraction | +16.4404 | 13/13 | 0 | 0.164404 |
| expgym | evidence_audit | family/evidence_audit | cost_free | label_acc | cost_free − cost_moderate | -0.0874811 | fraction | -8.74811 | 13/13 | 0 | -0.0874811 |
| expgym | evidence_audit | family/evidence_audit | cost_free | label_acc | cost_free − cost_tight | -0.0346908 | fraction | -3.46908 | 13/13 | 0 | -0.0346908 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc | cost_moderate − cost_tight | +0.111614 | fraction | +11.1614 | 13/13 | 0 | 0.111614 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | label_acc | cost_moderate − cost_tight | +0.0527903 | fraction | +5.27903 | 13/13 | 0 | 0.0527903 |
| expgym | restricted_search | family/whatis | cost_free | f1 | cost_free − cost_moderate | +0.0355566 | fraction | +3.55566 | 34/34 | 0 | 0.0355566 |
| expgym | restricted_search | family/whatis | cost_free | f1 | cost_free − cost_tight | +0.209804 | fraction | +20.9804 | 34/34 | 0 | 0.209804 |
| expgym | restricted_search | family/whois | cost_free | f1 | cost_free − cost_moderate | +0.000854701 | fraction | +0.0854701 | 39/39 | 0 | 0.000854701 |
| expgym | restricted_search | family/whois | cost_free | f1 | cost_free − cost_tight | +0.320513 | fraction | +32.0513 | 39/39 | 0 | 0.320513 |
| expgym | restricted_search | family/whatis | cost_moderate | f1 | cost_moderate − cost_tight | +0.174247 | fraction | +17.4247 | 34/34 | 0 | 0.174247 |
| expgym | restricted_search | family/whois | cost_moderate | f1 | cost_moderate − cost_tight | +0.319658 | fraction | +31.9658 | 39/39 | 0 | 0.319658 |
| expgym | tuning | family/nasbench101 | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 7/9 | 2 | -8.69234 |
| expgym | tuning | family/nasbench101 | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 7/9 | 2 | -10.9275 |
| expgym | tuning | family/nasbench201 | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 7/9 | 2 | 1.55735 |
| expgym | tuning | family/nasbench201 | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 8/9 | 1 | 15.1275 |
| expgym | tuning | family/paramnet | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 5/9 | 4 | 16.0114 |
| expgym | tuning | family/paramnet | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 4/9 | 5 | 18.201 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | -46.5685 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | -42.6624 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | gap | cost_free − cost_moderate | +29.1366 | Gap points | 不适用 | 3/3 | 0 | 29.1366 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | gap | cost_free − cost_tight | +1.62452 | Gap points | 不适用 | 3/3 | 0 | 1.62452 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | -8.64516 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 8.25528 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | 3.11558 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 8.84423 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | gap | cost_free − cost_moderate | +6.33388 | Gap points | 不适用 | 3/3 | 0 | 6.33388 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | gap | cost_free − cost_tight | +3.25795 | Gap points | 不适用 | 3/3 | 0 | 3.25795 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | -4.7774 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | gap | cost_free − cost_tight | +33.2804 | Gap points | 不适用 | 3/3 | 0 | 33.2804 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | -5.20394 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 11.5206 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 2/3 | 1 | -32.3689 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 1/3 | 2 | 7.7272 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | gap | cost_free − cost_moderate | unknown | Gap points | 不适用 | 1/3 | 2 | 85.6071 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | gap | cost_free − cost_tight | unknown | Gap points | 不适用 | 1/3 | 2 | 35.3551 |
| expgym | tuning | family/nasbench101 | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 7/9 | 2 | -0.0640469 |
| expgym | tuning | family/nasbench101 | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 7/9 | 2 | -0.123542 |
| expgym | tuning | family/nasbench201 | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 7/9 | 2 | 0.00130259 |
| expgym | tuning | family/nasbench201 | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 8/9 | 1 | 0.0183146 |
| expgym | tuning | family/paramnet | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 5/9 | 4 | 0.139692 |
| expgym | tuning | family/paramnet | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 4/9 | 5 | 0.0656884 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | -0.448902 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 2/3 | 1 | -0.421424 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | raw_perf | cost_free − cost_moderate | +0.305622 | fraction | +30.5622 | 3/3 | 0 | 0.305622 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | raw_perf | cost_free − cost_tight | +0.00413995 | fraction | +0.413995 | 3/3 | 0 | 0.00413995 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | -0.0488615 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.046658 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | 0.00248 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.00704 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | raw_perf | cost_free − cost_moderate | +0.00773333 | fraction | +0.773333 | 3/3 | 0 | 0.00773333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | raw_perf | cost_free − cost_tight | +0.00397778 | fraction | +0.397778 | 3/3 | 0 | 0.00397778 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | -0.00630556 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | raw_perf | cost_free − cost_tight | +0.0439259 | fraction | +4.39259 | 3/3 | 0 | 0.0439259 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | -0.00214352 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.00474537 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 2/3 | 1 | -0.0281711 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 1/3 | 2 | 0.00672509 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | raw_perf | cost_free − cost_moderate | unknown | fraction | unknown | 1/3 | 2 | 0.449389 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | raw_perf | cost_free − cost_tight | unknown | fraction | unknown | 1/3 | 2 | 0.185595 |
| expgym | tuning | family/nasbench101 | cost_moderate | gap | cost_moderate − cost_tight | -14.9872 | Gap points | 不适用 | 9/9 | 0 | -14.9872 |
| expgym | tuning | family/nasbench201 | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 8/9 | 1 | 13.3873 |
| expgym | tuning | family/paramnet | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 6/9 | 3 | -3.44741 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | gap | cost_moderate − cost_tight | -25.9815 | Gap points | 不适用 | 3/3 | 0 | -25.9815 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | gap | cost_moderate − cost_tight | -27.5121 | Gap points | 不适用 | 3/3 | 0 | -27.5121 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | gap | cost_moderate − cost_tight | +8.53194 | Gap points | 不适用 | 3/3 | 0 | 8.53194 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | gap | cost_moderate − cost_tight | +3.8191 | Gap points | 不适用 | 3/3 | 0 | 3.8191 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | gap | cost_moderate − cost_tight | -3.07594 | Gap points | 不适用 | 3/3 | 0 | -3.07594 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 39.4188 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 16.7245 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | 2.1173 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | gap | cost_moderate − cost_tight | unknown | Gap points | 不适用 | 2/3 | 1 | -29.184 |
| expgym | tuning | family/nasbench101 | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.172302 | fraction | -17.2302 | 9/9 | 0 | -0.172302 |
| expgym | tuning | family/nasbench201 | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 8/9 | 1 | 0.0171041 |
| expgym | tuning | family/paramnet | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 6/9 | 3 | -0.0481561 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.263644 | fraction | -26.3644 | 3/3 | 0 | -0.263644 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.301482 | fraction | -30.1482 | 3/3 | 0 | -0.301482 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0482216 | fraction | +4.82216 | 3/3 | 0 | 0.0482216 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.00304 | fraction | +0.304 | 3/3 | 0 | 0.00304 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.00375556 | fraction | -0.375556 | 3/3 | 0 | -0.00375556 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.0520278 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.00688889 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 2/3 | 1 | 0.00184271 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | unknown | fraction | unknown | 2/3 | 1 | -0.1532 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | poolact − cached | -0.254525 | fraction | -25.4525 | 13/13 | 0 | -0.254525 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | poolact − cached | -0.253394 | fraction | -25.3394 | 13/13 | 0 | -0.253394 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | poolact − cached | -0.298643 | fraction | -29.8643 | 13/13 | 0 | -0.298643 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | poolact − cached | -0.289593 | fraction | -28.9593 | 13/13 | 0 | -0.289593 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | cached − naive | +0.0418552 | fraction | +4.18552 | 13/13 | 0 | 0.0418552 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | poolact − naive | -0.21267 | fraction | -21.267 | 13/13 | 0 | -0.21267 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | cached − naive | -0.00452489 | fraction | -0.452489 | 13/13 | 0 | -0.00452489 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | poolact − naive | -0.257919 | fraction | -25.7919 | 13/13 | 0 | -0.257919 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | cached − naive | +0.0475113 | fraction | +4.75113 | 13/13 | 0 | 0.0475113 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | poolact − naive | -0.251131 | fraction | -25.1131 | 13/13 | 0 | -0.251131 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | cached − naive | -0.0497738 | fraction | -4.97738 | 13/13 | 0 | -0.0497738 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | poolact − naive | -0.339367 | fraction | -33.9367 | 13/13 | 0 | -0.339367 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | poolact − cached | -0.111991 | fraction | -11.1991 | 13/13 | 0 | -0.111991 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | poolact − cached | -0.303167 | fraction | -30.3167 | 13/13 | 0 | -0.303167 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | poolact − cached | -0.13914 | fraction | -13.914 | 13/13 | 0 | -0.13914 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | poolact − cached | -0.371041 | fraction | -37.1041 | 13/13 | 0 | -0.371041 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | cached − naive | -0.0565611 | fraction | -5.65611 | 13/13 | 0 | -0.0565611 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | poolact − naive | -0.168552 | fraction | -16.8552 | 13/13 | 0 | -0.168552 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | cached − naive | -0.126697 | fraction | -12.6697 | 13/13 | 0 | -0.126697 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | poolact − naive | -0.429864 | fraction | -42.9864 | 13/13 | 0 | -0.429864 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | cached − naive | -0.0644796 | fraction | -6.44796 | 13/13 | 0 | -0.0644796 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | poolact − naive | -0.20362 | fraction | -20.362 | 13/13 | 0 | -0.20362 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | cached − naive | -0.190045 | fraction | -19.0045 | 13/13 | 0 | -0.190045 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | poolact − naive | -0.561086 | fraction | -56.1086 | 13/13 | 0 | -0.561086 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | poolact − cached | -0.090812 | fraction | -9.0812 | 39/39 | 0 | -0.090812 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | poolact − cached | -0.0512821 | fraction | -5.12821 | 39/39 | 0 | -0.0512821 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | cached − naive | +0.0791026 | fraction | +7.91026 | 39/39 | 0 | 0.0791026 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | poolact − naive | -0.0117094 | fraction | -1.17094 | 39/39 | 0 | -0.0117094 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | cached − naive | +0.0384615 | fraction | +3.84615 | 39/39 | 0 | 0.0384615 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | poolact − naive | -0.0128205 | fraction | -1.28205 | 39/39 | 0 | -0.0128205 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | poolact − cached | +0.00791855 | fraction | +0.791855 | 39/39 | 0 | 0.00791855 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | poolact − cached | +0.0316742 | fraction | +3.16742 | 39/39 | 0 | 0.0316742 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | cached − naive | +0.0213675 | fraction | +2.13675 | 39/39 | 0 | 0.0213675 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | poolact − naive | +0.0292861 | fraction | +2.92861 | 39/39 | 0 | 0.0292861 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | cached − naive | +0.017094 | fraction | +1.7094 | 39/39 | 0 | 0.017094 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | poolact − naive | +0.0487682 | fraction | +4.87682 | 39/39 | 0 | 0.0487682 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | cached − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 86.509 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | cached − naive | unknown | Gap points | 不适用 | 1/3 | 2 | 86.509 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | cached − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 68.7819 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | cached − naive | unknown | Gap points | 不适用 | 1/3 | 2 | 68.7819 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | cached − naive | unknown | fraction | unknown | 1/9 | 8 | 0.60854 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | cached − naive | unknown | fraction | unknown | 1/3 | 2 | 0.60854 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | cached − naive | unknown | fraction | unknown | 1/9 | 8 | 0.60516 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | cached − naive | unknown | fraction | unknown | 1/3 | 2 | 0.60516 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | poolact − cached | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | poolact − cached | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 1.61846 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 1/3 | 2 | 1.61846 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 1/9 | 8 | 40.5782 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 1/3 | 2 | 40.5782 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | cached − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | poolact − naive | unknown | Gap points | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 1/9 | 8 | 0.0113849 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 1/3 | 2 | 0.0113849 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 1/9 | 8 | 0.346104 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 1/3 | 2 | 0.346104 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | cached − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | poolact − naive | unknown | fraction | unknown | 0/3 | 3 | unknown |


## 资源：全部层次

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | duplicate_action_attempts | count | 0.128205 | 13/13 | 0 | 13 | 0.128205 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | duplicate_action_attempts | count | 0.128205 | 13/13 | 0 | 13 | 0.128205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_attempts | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_attempts | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_cost_seconds | seconds | 6914.98 | 13/13 | 0 | 13 | 6914.98 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_cost_seconds | seconds | 6914.98 | 13/13 | 0 | 13 | 6914.98 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_visible | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_visible | count | 23.1282 | 13/13 | 0 | 13 | 23.1282 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | input_tokens | tokens | 366151 | 13/13 | 0 | 13 | 366151 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | input_tokens | tokens | 366151 | 13/13 | 0 | 13 | 366151 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | output_tokens | tokens | 21262.4 | 13/13 | 0 | 13 | 21262.4 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | output_tokens | tokens | 21262.4 | 13/13 | 0 | 13 | 21262.4 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | protocol_failure_rate | fraction | 0.109717 | 13/13 | 0 | 13 | 0.109717 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | protocol_failure_rate | fraction | 0.109717 | 13/13 | 0 | 13 | 0.109717 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | wall_time_seconds | seconds | 241.674 | 13/13 | 0 | 13 | 241.674 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | wall_time_seconds | seconds | 241.674 | 13/13 | 0 | 13 | 241.674 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | budget_utilization | fraction | 0.968122 | 13/13 | 0 | 13 | 0.968122 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | budget_utilization | fraction | 0.968122 | 13/13 | 0 | 13 | 0.968122 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_attempts | count | 9.74359 | 13/13 | 0 | 13 | 9.74359 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_attempts | count | 9.74359 | 13/13 | 0 | 13 | 9.74359 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2904.36 | 13/13 | 0 | 13 | 2904.36 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_cost_seconds | seconds | 2904.36 | 13/13 | 0 | 13 | 2904.36 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_visible | count | 9.17949 | 13/13 | 0 | 13 | 9.17949 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_visible | count | 9.17949 | 13/13 | 0 | 13 | 9.17949 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | input_tokens | tokens | 137147 | 13/13 | 0 | 13 | 137147 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | input_tokens | tokens | 137147 | 13/13 | 0 | 13 | 137147 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | output_tokens | tokens | 17861.6 | 13/13 | 0 | 13 | 17861.6 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | output_tokens | tokens | 17861.6 | 13/13 | 0 | 13 | 17861.6 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.096219 | 13/13 | 0 | 13 | 0.096219 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | protocol_failure_rate | fraction | 0.096219 | 13/13 | 0 | 13 | 0.096219 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | wall_time_seconds | seconds | 192.191 | 13/13 | 0 | 13 | 192.191 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | wall_time_seconds | seconds | 192.191 | 13/13 | 0 | 13 | 192.191 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | budget_utilization | fraction | 0.984812 | 13/13 | 0 | 13 | 0.984812 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | budget_utilization | fraction | 0.984812 | 13/13 | 0 | 13 | 0.984812 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_attempts | count | 3 | 13/13 | 0 | 13 | 3 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_attempts | count | 3 | 13/13 | 0 | 13 | 3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_cost_seconds | seconds | 886.331 | 13/13 | 0 | 13 | 886.331 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_cost_seconds | seconds | 886.331 | 13/13 | 0 | 13 | 886.331 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_visible | count | 2.33333 | 13/13 | 0 | 13 | 2.33333 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_visible | count | 2.33333 | 13/13 | 0 | 13 | 2.33333 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | input_tokens | tokens | 44672.1 | 13/13 | 0 | 13 | 44672.1 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | input_tokens | tokens | 44672.1 | 13/13 | 0 | 13 | 44672.1 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | output_tokens | tokens | 16333.6 | 13/13 | 0 | 13 | 16333.6 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | output_tokens | tokens | 16333.6 | 13/13 | 0 | 13 | 16333.6 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.179548 | 13/13 | 0 | 13 | 0.179548 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | protocol_failure_rate | fraction | 0.179548 | 13/13 | 0 | 13 | 0.179548 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | wall_time_seconds | seconds | 175.489 | 13/13 | 0 | 13 | 175.489 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | wall_time_seconds | seconds | 175.489 | 13/13 | 0 | 13 | 175.489 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | duplicate_action_attempts | count | 0.0273973 | 73/73 | 0 | 73 | 0.0273973 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | duplicate_action_attempts | count | 0.0294118 | 34/34 | 0 | 34 | 0.0294118 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | duplicate_action_attempts | count | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_attempts | count | 17.5479 | 73/73 | 0 | 73 | 17.5479 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_attempts | count | 17.0882 | 34/34 | 0 | 34 | 17.0882 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_attempts | count | 17.9487 | 39/39 | 0 | 39 | 17.9487 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_cost_seconds | seconds | 3387.71 | 73/73 | 0 | 73 | 3387.71 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_cost_seconds | seconds | 3293.57 | 34/34 | 0 | 34 | 3293.57 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_cost_seconds | seconds | 3469.79 | 39/39 | 0 | 39 | 3469.79 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_visible | count | 17.5479 | 73/73 | 0 | 73 | 17.5479 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_visible | count | 17.0882 | 34/34 | 0 | 34 | 17.0882 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_visible | count | 17.9487 | 39/39 | 0 | 39 | 17.9487 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | input_tokens | tokens | 131940 | 73/73 | 0 | 73 | 131940 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | input_tokens | tokens | 129109 | 34/34 | 0 | 34 | 129109 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | input_tokens | tokens | 134409 | 39/39 | 0 | 39 | 134409 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | output_tokens | tokens | 11589.2 | 73/73 | 0 | 73 | 11589.2 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | output_tokens | tokens | 10760.7 | 34/34 | 0 | 34 | 10760.7 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | output_tokens | tokens | 12311.4 | 39/39 | 0 | 39 | 12311.4 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0632559 | 73/73 | 0 | 73 | 0.0632559 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | protocol_failure_rate | fraction | 0.0598111 | 34/34 | 0 | 34 | 0.0598111 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | protocol_failure_rate | fraction | 0.066259 | 39/39 | 0 | 39 | 0.066259 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | wall_time_seconds | seconds | 134.497 | 73/73 | 0 | 73 | 134.497 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | wall_time_seconds | seconds | 126.248 | 34/34 | 0 | 34 | 126.248 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | wall_time_seconds | seconds | 141.688 | 39/39 | 0 | 39 | 141.688 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | budget_utilization | fraction | 0.856117 | 73/73 | 0 | 73 | 0.856117 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | budget_utilization | fraction | 0.848442 | 34/34 | 0 | 34 | 0.848442 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | budget_utilization | fraction | 0.862808 | 39/39 | 0 | 39 | 0.862808 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.0410959 | 73/73 | 0 | 73 | 0.0410959 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | duplicate_action_attempts | count | 0 | 34/34 | 0 | 34 | 0 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | duplicate_action_attempts | count | 0.0769231 | 39/39 | 0 | 39 | 0.0769231 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_attempts | count | 12.7945 | 73/73 | 0 | 73 | 12.7945 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_attempts | count | 12.0588 | 34/34 | 0 | 34 | 12.0588 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_attempts | count | 13.4359 | 39/39 | 0 | 39 | 13.4359 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2568.35 | 73/73 | 0 | 73 | 2568.35 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_cost_seconds | seconds | 2545.32 | 34/34 | 0 | 34 | 2545.32 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_cost_seconds | seconds | 2588.42 | 39/39 | 0 | 39 | 2588.42 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_visible | count | 12.274 | 73/73 | 0 | 73 | 12.274 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_visible | count | 11.5588 | 34/34 | 0 | 34 | 11.5588 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_visible | count | 12.8974 | 39/39 | 0 | 39 | 12.8974 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | input_tokens | tokens | 68977.5 | 73/73 | 0 | 73 | 68977.5 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | input_tokens | tokens | 63977.1 | 34/34 | 0 | 34 | 63977.1 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | input_tokens | tokens | 73336.8 | 39/39 | 0 | 39 | 73336.8 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | output_tokens | tokens | 11360.5 | 73/73 | 0 | 73 | 11360.5 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | output_tokens | tokens | 12299.9 | 34/34 | 0 | 34 | 12299.9 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | output_tokens | tokens | 10541.6 | 39/39 | 0 | 39 | 10541.6 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0764896 | 73/73 | 0 | 73 | 0.0764896 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | protocol_failure_rate | fraction | 0.0776926 | 34/34 | 0 | 34 | 0.0776926 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | protocol_failure_rate | fraction | 0.0754409 | 39/39 | 0 | 39 | 0.0754409 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | wall_time_seconds | seconds | 127.875 | 73/73 | 0 | 73 | 127.875 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | wall_time_seconds | seconds | 135.989 | 34/34 | 0 | 34 | 135.989 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | wall_time_seconds | seconds | 120.801 | 39/39 | 0 | 39 | 120.801 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | budget_utilization | fraction | 1.18245 | 73/73 | 0 | 73 | 1.18245 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | budget_utilization | fraction | 1.16344 | 34/34 | 0 | 34 | 1.16344 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | budget_utilization | fraction | 1.19902 | 39/39 | 0 | 39 | 1.19902 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | duplicate_action_attempts | count | 0.0136986 | 73/73 | 0 | 73 | 0.0136986 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | duplicate_action_attempts | count | 0.0294118 | 34/34 | 0 | 34 | 0.0294118 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | duplicate_action_attempts | count | 0 | 39/39 | 0 | 39 | 0 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_attempts | count | 4.64384 | 73/73 | 0 | 73 | 4.64384 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_attempts | count | 4.29412 | 34/34 | 0 | 34 | 4.29412 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_attempts | count | 4.94872 | 39/39 | 0 | 39 | 4.94872 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_cost_seconds | seconds | 1064.2 | 73/73 | 0 | 73 | 1064.2 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_cost_seconds | seconds | 1047.1 | 34/34 | 0 | 34 | 1047.1 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_cost_seconds | seconds | 1079.12 | 39/39 | 0 | 39 | 1079.12 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_visible | count | 3.73973 | 73/73 | 0 | 73 | 3.73973 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_visible | count | 3.47059 | 34/34 | 0 | 34 | 3.47059 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_visible | count | 3.97436 | 39/39 | 0 | 39 | 3.97436 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | input_tokens | tokens | 12433 | 73/73 | 0 | 73 | 12433 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | input_tokens | tokens | 10652 | 34/34 | 0 | 34 | 10652 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | input_tokens | tokens | 13985.6 | 39/39 | 0 | 39 | 13985.6 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | output_tokens | tokens | 8252.52 | 73/73 | 0 | 73 | 8252.52 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | output_tokens | tokens | 6346.56 | 34/34 | 0 | 34 | 6346.56 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | output_tokens | tokens | 9914.13 | 39/39 | 0 | 39 | 9914.13 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.12133 | 73/73 | 0 | 73 | 0.12133 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | protocol_failure_rate | fraction | 0.13827 | 34/34 | 0 | 34 | 0.13827 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | protocol_failure_rate | fraction | 0.106561 | 39/39 | 0 | 39 | 0.106561 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | wall_time_seconds | seconds | 89.3709 | 73/73 | 0 | 73 | 89.3709 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | wall_time_seconds | seconds | 68.9446 | 34/34 | 0 | 34 | 68.9446 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | wall_time_seconds | seconds | 107.178 | 39/39 | 0 | 39 | 107.178 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | family/nasbench101 | cost_free | single | duplicate_action_attempts | count | 0.111111 | 9/9 | 0 | 3 | 0.111111 | 3 / 0.19245 |
| expgym | tuning | family/nasbench201 | cost_free | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/paramnet | cost_free | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_free | single | feedback_attempts | count | 16.4074 | 27/27 | 0 | 9 | 16.4074 | 3 / 5.1787 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_attempts | count | 15.7778 | 9/9 | 0 | 3 | 15.7778 | 3 / 9.43594 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_attempts | count | 20.3333 | 9/9 | 0 | 3 | 20.3333 | 3 / 7.17248 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_attempts | count | 13.1111 | 9/9 | 0 | 3 | 13.1111 | 3 / 6.07667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_attempts | count | 14.3333 | 3/3 | 0 | 1 | 14.3333 | 3 / 14.5029 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_attempts | count | 22 | 3/3 | 0 | 1 | 22 | 3 / 12.1244 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_attempts | count | 11 | 3/3 | 0 | 1 | 11 | 3 / 10.5357 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_attempts | count | 16.3333 | 3/3 | 0 | 1 | 16.3333 | 3 / 12.0554 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_attempts | count | 19.3333 | 3/3 | 0 | 1 | 19.3333 | 3 / 4.93288 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_attempts | count | 25.3333 | 3/3 | 0 | 1 | 25.3333 | 3 / 6.35085 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_attempts | count | 5.66667 | 3/3 | 0 | 1 | 5.66667 | 3 / 4.50925 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_attempts | count | 13.3333 | 3/3 | 0 | 1 | 13.3333 | 3 / 14.2945 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_attempts | count | 20.3333 | 3/3 | 0 | 1 | 20.3333 | 3 / 8.5049 |
| expgym | tuning | all/all | cost_free | single | feedback_cost_seconds | seconds | 216690 | 27/27 | 0 | 9 | 216690 | 3 / 61675.2 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_cost_seconds | seconds | 122674 | 9/9 | 0 | 3 | 122674 | 3 / 57519.5 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_cost_seconds | seconds | 524384 | 9/9 | 0 | 3 | 524384 | 3 / 158792 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_cost_seconds | seconds | 3011.06 | 9/9 | 0 | 3 | 3011.06 | 3 / 3134.95 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_cost_seconds | seconds | 80605.6 | 3/3 | 0 | 1 | 80605.6 | 3 / 72939.9 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_cost_seconds | seconds | 193014 | 3/3 | 0 | 1 | 193014 | 3 / 109141 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_cost_seconds | seconds | 94402.2 | 3/3 | 0 | 1 | 94402.2 | 3 / 107060 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_cost_seconds | seconds | 159973 | 3/3 | 0 | 1 | 159973 | 3 / 127575 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_cost_seconds | seconds | 301123 | 3/3 | 0 | 1 | 301123 | 3 / 99519.7 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_cost_seconds | seconds | 1.11206e+06 | 3/3 | 0 | 1 | 1.11206e+06 | 3 / 293965 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_cost_seconds | seconds | 818.089 | 3/3 | 0 | 1 | 818.089 | 3 / 828.042 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_cost_seconds | seconds | 6673.74 | 3/3 | 0 | 1 | 6673.74 | 3 / 8276.33 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_cost_seconds | seconds | 1541.35 | 3/3 | 0 | 1 | 1541.35 | 3 / 545.882 |
| expgym | tuning | all/all | cost_free | single | feedback_visible | count | 16.4074 | 27/27 | 0 | 9 | 16.4074 | 3 / 5.1787 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_visible | count | 15.7778 | 9/9 | 0 | 3 | 15.7778 | 3 / 9.43594 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_visible | count | 20.3333 | 9/9 | 0 | 3 | 20.3333 | 3 / 7.17248 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_visible | count | 13.1111 | 9/9 | 0 | 3 | 13.1111 | 3 / 6.07667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_visible | count | 14.3333 | 3/3 | 0 | 1 | 14.3333 | 3 / 14.5029 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_visible | count | 22 | 3/3 | 0 | 1 | 22 | 3 / 12.1244 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_visible | count | 11 | 3/3 | 0 | 1 | 11 | 3 / 10.5357 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_visible | count | 16.3333 | 3/3 | 0 | 1 | 16.3333 | 3 / 12.0554 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_visible | count | 19.3333 | 3/3 | 0 | 1 | 19.3333 | 3 / 4.93288 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_visible | count | 25.3333 | 3/3 | 0 | 1 | 25.3333 | 3 / 6.35085 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_visible | count | 5.66667 | 3/3 | 0 | 1 | 5.66667 | 3 / 4.50925 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_visible | count | 13.3333 | 3/3 | 0 | 1 | 13.3333 | 3 / 14.2945 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_visible | count | 20.3333 | 3/3 | 0 | 1 | 20.3333 | 3 / 8.5049 |
| expgym | tuning | all/all | cost_free | single | input_tokens | tokens | 148797 | 27/27 | 0 | 9 | 148797 | 3 / 64728.1 |
| expgym | tuning | family/nasbench101 | cost_free | single | input_tokens | tokens | 242898 | 9/9 | 0 | 3 | 242898 | 3 / 162191 |
| expgym | tuning | family/nasbench201 | cost_free | single | input_tokens | tokens | 128628 | 9/9 | 0 | 3 | 128628 | 3 / 45355.9 |
| expgym | tuning | family/paramnet | cost_free | single | input_tokens | tokens | 74864.4 | 9/9 | 0 | 3 | 74864.4 | 3 / 36921.8 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | input_tokens | tokens | 212697 | 3/3 | 0 | 1 | 212697 | 3 / 233183 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | input_tokens | tokens | 318283 | 3/3 | 0 | 1 | 318283 | 3 / 169811 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | input_tokens | tokens | 197714 | 3/3 | 0 | 1 | 197714 | 3 / 196649 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | input_tokens | tokens | 91826.7 | 3/3 | 0 | 1 | 91826.7 | 3 / 80609.4 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | input_tokens | tokens | 121193 | 3/3 | 0 | 1 | 121193 | 3 / 32616 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | input_tokens | tokens | 172864 | 3/3 | 0 | 1 | 172864 | 3 / 61259.6 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | input_tokens | tokens | 25799.3 | 3/3 | 0 | 1 | 25799.3 | 3 / 20621.5 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | input_tokens | tokens | 77145 | 3/3 | 0 | 1 | 77145 | 3 / 82632.1 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | input_tokens | tokens | 121649 | 3/3 | 0 | 1 | 121649 | 3 / 58123 |
| expgym | tuning | all/all | cost_free | single | output_tokens | tokens | 12851.2 | 27/27 | 0 | 9 | 12851.2 | 3 / 6707.51 |
| expgym | tuning | family/nasbench101 | cost_free | single | output_tokens | tokens | 22921.8 | 9/9 | 0 | 3 | 22921.8 | 3 / 14813.7 |
| expgym | tuning | family/nasbench201 | cost_free | single | output_tokens | tokens | 10226.6 | 9/9 | 0 | 3 | 10226.6 | 3 / 5482.48 |
| expgym | tuning | family/paramnet | cost_free | single | output_tokens | tokens | 5405.33 | 9/9 | 0 | 3 | 5405.33 | 3 / 1146.09 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | output_tokens | tokens | 28021.3 | 3/3 | 0 | 1 | 28021.3 | 3 / 29661.9 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | output_tokens | tokens | 25166.7 | 3/3 | 0 | 1 | 25166.7 | 3 / 13995.7 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | output_tokens | tokens | 15577.3 | 3/3 | 0 | 1 | 15577.3 | 3 / 8404.9 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | output_tokens | tokens | 15973 | 3/3 | 0 | 1 | 15973 | 3 / 16697.6 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | output_tokens | tokens | 6728.33 | 3/3 | 0 | 1 | 6728.33 | 3 / 1396.95 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | output_tokens | tokens | 7978.33 | 3/3 | 0 | 1 | 7978.33 | 3 / 1575.62 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | output_tokens | tokens | 3052.33 | 3/3 | 0 | 1 | 3052.33 | 3 / 1251.89 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | output_tokens | tokens | 5858.67 | 3/3 | 0 | 1 | 5858.67 | 3 / 1934.11 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | output_tokens | tokens | 7305 | 3/3 | 0 | 1 | 7305 | 3 / 1402.46 |
| expgym | tuning | all/all | cost_free | single | protocol_failure_rate | fraction | 0.159228 | 27/27 | 0 | 9 | 0.159228 | 3 / 0.0741547 |
| expgym | tuning | family/nasbench101 | cost_free | single | protocol_failure_rate | fraction | 0.140648 | 9/9 | 0 | 3 | 0.140648 | 3 / 0.0806441 |
| expgym | tuning | family/nasbench201 | cost_free | single | protocol_failure_rate | fraction | 0.102269 | 9/9 | 0 | 3 | 0.102269 | 3 / 0.079899 |
| expgym | tuning | family/paramnet | cost_free | single | protocol_failure_rate | fraction | 0.234767 | 9/9 | 0 | 3 | 0.234767 | 3 / 0.112463 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | protocol_failure_rate | fraction | 0.0695762 | 3/3 | 0 | 1 | 0.0695762 | 3 / 0.0939678 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | protocol_failure_rate | fraction | 0.0821114 | 3/3 | 0 | 1 | 0.0821114 | 3 / 0.0863486 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | protocol_failure_rate | fraction | 0.270256 | 3/3 | 0 | 1 | 0.270256 | 3 / 0.212766 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | protocol_failure_rate | fraction | 0.17279 | 3/3 | 0 | 1 | 0.17279 | 3 / 0.179503 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | protocol_failure_rate | fraction | 0.0807667 | 3/3 | 0 | 1 | 0.0807667 | 3 / 0.0379623 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | protocol_failure_rate | fraction | 0.0532514 | 3/3 | 0 | 1 | 0.0532514 | 3 / 0.0363615 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | protocol_failure_rate | fraction | 0.32906 | 3/3 | 0 | 1 | 0.32906 | 3 / 0.173116 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | protocol_failure_rate | fraction | 0.254342 | 3/3 | 0 | 1 | 0.254342 | 3 / 0.23476 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | protocol_failure_rate | fraction | 0.120898 | 3/3 | 0 | 1 | 0.120898 | 3 / 0.0842767 |
| expgym | tuning | all/all | cost_free | single | wall_time_seconds | seconds | 152.04 | 27/27 | 0 | 9 | 152.04 | 3 / 80.6081 |
| expgym | tuning | family/nasbench101 | cost_free | single | wall_time_seconds | seconds | 267.455 | 9/9 | 0 | 3 | 267.455 | 3 / 175.351 |
| expgym | tuning | family/nasbench201 | cost_free | single | wall_time_seconds | seconds | 119.99 | 9/9 | 0 | 3 | 119.99 | 3 / 65.1929 |
| expgym | tuning | family/paramnet | cost_free | single | wall_time_seconds | seconds | 68.6747 | 9/9 | 0 | 3 | 68.6747 | 3 / 14.4082 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | wall_time_seconds | seconds | 331.322 | 3/3 | 0 | 1 | 331.322 | 3 / 354.798 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | wall_time_seconds | seconds | 292.425 | 3/3 | 0 | 1 | 292.425 | 3 / 164.383 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | wall_time_seconds | seconds | 178.619 | 3/3 | 0 | 1 | 178.619 | 3 / 96.6703 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | wall_time_seconds | seconds | 188.529 | 3/3 | 0 | 1 | 188.529 | 3 / 195.44 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | wall_time_seconds | seconds | 77.2005 | 3/3 | 0 | 1 | 77.2005 | 3 / 17.7384 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | wall_time_seconds | seconds | 94.2414 | 3/3 | 0 | 1 | 94.2414 | 3 / 16.0851 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | wall_time_seconds | seconds | 38.4054 | 3/3 | 0 | 1 | 38.4054 | 3 / 16.0622 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | wall_time_seconds | seconds | 74.4672 | 3/3 | 0 | 1 | 74.4672 | 3 / 22.2367 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | wall_time_seconds | seconds | 93.1515 | 3/3 | 0 | 1 | 93.1515 | 3 / 23.9543 |
| expgym | tuning | all/all | cost_moderate | single | budget_utilization | fraction | 0.805942 | 27/27 | 0 | 9 | 0.805942 | 3 / 0.162412 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | budget_utilization | fraction | 0.646425 | 9/9 | 0 | 3 | 0.646425 | 3 / 0.174178 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | budget_utilization | fraction | 1.02726 | 9/9 | 0 | 3 | 1.02726 | 3 / 0.0115121 |
| expgym | tuning | family/paramnet | cost_moderate | single | budget_utilization | fraction | 0.744146 | 9/9 | 0 | 3 | 0.744146 | 3 / 0.333182 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | budget_utilization | fraction | 0.776059 | 3/3 | 0 | 1 | 0.776059 | 3 / 0.674264 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | budget_utilization | fraction | 0.612184 | 3/3 | 0 | 1 | 0.612184 | 3 / 0.551774 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | budget_utilization | fraction | 0.551031 | 3/3 | 0 | 1 | 0.551031 | 3 / 0.28252 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | budget_utilization | fraction | 1.02203 | 3/3 | 0 | 1 | 1.02203 | 3 / 0.0401813 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | budget_utilization | fraction | 1.04267 | 3/3 | 0 | 1 | 1.04267 | 3 / 0.0347679 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | budget_utilization | fraction | 1.01708 | 3/3 | 0 | 1 | 1.01708 | 3 / 0.0221443 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | budget_utilization | fraction | 0.914214 | 3/3 | 0 | 1 | 0.914214 | 3 / 0.0637414 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | budget_utilization | fraction | 0.681823 | 3/3 | 0 | 1 | 0.681823 | 3 / 0.517579 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | budget_utilization | fraction | 0.6364 | 3/3 | 0 | 1 | 0.6364 | 3 / 0.529995 |
| expgym | tuning | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | duplicate_action_attempts | count | 0.111111 | 9/9 | 0 | 3 | 0.111111 | 3 / 0.19245 |
| expgym | tuning | family/paramnet | cost_moderate | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_moderate | single | feedback_attempts | count | 9.74074 | 27/27 | 0 | 9 | 9.74074 | 3 / 2.42501 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_attempts | count | 7.11111 | 9/9 | 0 | 3 | 7.11111 | 3 / 1.64429 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_attempts | count | 12.7778 | 9/9 | 0 | 3 | 12.7778 | 3 / 0.693889 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_attempts | count | 9.33333 | 9/9 | 0 | 3 | 9.33333 | 3 / 6.38575 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_attempts | count | 3.66667 | 3/3 | 0 | 1 | 3.66667 | 3 / 3.21455 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_attempts | count | 6 | 3/3 | 0 | 1 | 6 | 3 / 5 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_attempts | count | 11.6667 | 3/3 | 0 | 1 | 11.6667 | 3 / 7.23418 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_attempts | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 1 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_attempts | count | 12.3333 | 3/3 | 0 | 1 | 12.3333 | 3 / 1.1547 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_attempts | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_attempts | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 1.73205 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_attempts | count | 11 | 3/3 | 0 | 1 | 11 | 3 / 9.53939 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_attempts | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 13.7477 |
| expgym | tuning | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 109647 | 27/27 | 0 | 9 | 109647 | 3 / 2020.72 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_cost_seconds | seconds | 54392.3 | 9/9 | 0 | 3 | 54392.3 | 3 / 7890.54 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_cost_seconds | seconds | 273721 | 9/9 | 0 | 3 | 273721 | 3 / 4669.98 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_cost_seconds | seconds | 828.067 | 9/9 | 0 | 3 | 828.067 | 3 / 573.04 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_cost_seconds | seconds | 38369.5 | 3/3 | 0 | 1 | 38369.5 | 3 / 33336.6 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_cost_seconds | seconds | 63070.6 | 3/3 | 0 | 1 | 63070.6 | 3 / 56846.9 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_cost_seconds | seconds | 61736.7 | 3/3 | 0 | 1 | 61736.7 | 3 / 31653.1 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_cost_seconds | seconds | 115592 | 3/3 | 0 | 1 | 115592 | 3 / 4544.53 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_cost_seconds | seconds | 194346 | 3/3 | 0 | 1 | 194346 | 3 / 6480.53 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_cost_seconds | seconds | 511225 | 3/3 | 0 | 1 | 511225 | 3 / 11130.7 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_cost_seconds | seconds | 260.906 | 3/3 | 0 | 1 | 260.906 | 3 / 18.1911 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_cost_seconds | seconds | 1597.9 | 3/3 | 0 | 1 | 1597.9 | 3 / 1212.98 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_cost_seconds | seconds | 625.393 | 3/3 | 0 | 1 | 625.393 | 3 / 520.829 |
| expgym | tuning | all/all | cost_moderate | single | feedback_visible | count | 9.37037 | 27/27 | 0 | 9 | 9.37037 | 3 / 2.48535 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_visible | count | 6.77778 | 9/9 | 0 | 3 | 6.77778 | 3 / 1.64429 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_visible | count | 12 | 9/9 | 0 | 3 | 12 | 3 / 0.57735 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_visible | count | 9.33333 | 9/9 | 0 | 3 | 9.33333 | 3 / 6.38575 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_visible | count | 3 | 3/3 | 0 | 1 | 3 | 3 / 2.64575 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_visible | count | 5.66667 | 3/3 | 0 | 1 | 5.66667 | 3 / 4.50925 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_visible | count | 11.6667 | 3/3 | 0 | 1 | 11.6667 | 3 / 7.23418 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_visible | count | 12.3333 | 3/3 | 0 | 1 | 12.3333 | 3 / 1.1547 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_visible | count | 11.3333 | 3/3 | 0 | 1 | 11.3333 | 3 / 1.1547 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_visible | count | 12.3333 | 3/3 | 0 | 1 | 12.3333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_visible | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 1.73205 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_visible | count | 11 | 3/3 | 0 | 1 | 11 | 3 / 9.53939 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_visible | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 13.7477 |
| expgym | tuning | all/all | cost_moderate | single | input_tokens | tokens | 74453 | 27/27 | 0 | 9 | 74453 | 3 / 22573.9 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | input_tokens | tokens | 106743 | 9/9 | 0 | 3 | 106743 | 3 / 35205.5 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | input_tokens | tokens | 62312.9 | 9/9 | 0 | 3 | 62312.9 | 3 / 3811.87 |
| expgym | tuning | family/paramnet | cost_moderate | single | input_tokens | tokens | 54303.4 | 9/9 | 0 | 3 | 54303.4 | 3 / 34115.3 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | input_tokens | tokens | 42807.3 | 3/3 | 0 | 1 | 42807.3 | 3 / 34838.8 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | input_tokens | tokens | 90089 | 3/3 | 0 | 1 | 90089 | 3 / 71535 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | input_tokens | tokens | 187332 | 3/3 | 0 | 1 | 187332 | 3 / 138173 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | input_tokens | tokens | 67201.3 | 3/3 | 0 | 1 | 67201.3 | 3 / 11320.6 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | input_tokens | tokens | 56414 | 3/3 | 0 | 1 | 56414 | 3 / 5198.37 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | input_tokens | tokens | 63323.3 | 3/3 | 0 | 1 | 63323.3 | 3 / 7185.51 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | input_tokens | tokens | 20180.7 | 3/3 | 0 | 1 | 20180.7 | 3 / 7736.38 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | input_tokens | tokens | 65013.3 | 3/3 | 0 | 1 | 65013.3 | 3 / 67412.5 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | input_tokens | tokens | 77716.3 | 3/3 | 0 | 1 | 77716.3 | 3 / 89548.8 |
| expgym | tuning | all/all | cost_moderate | single | output_tokens | tokens | 9823.41 | 27/27 | 0 | 9 | 9823.41 | 3 / 2586.18 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | output_tokens | tokens | 15919.8 | 9/9 | 0 | 3 | 15919.8 | 3 / 8524.03 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | output_tokens | tokens | 6053.11 | 9/9 | 0 | 3 | 6053.11 | 3 / 765.655 |
| expgym | tuning | family/paramnet | cost_moderate | single | output_tokens | tokens | 7497.33 | 9/9 | 0 | 3 | 7497.33 | 3 / 1350.18 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | output_tokens | tokens | 18076.7 | 3/3 | 0 | 1 | 18076.7 | 3 / 20932 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | output_tokens | tokens | 13752.3 | 3/3 | 0 | 1 | 13752.3 | 3 / 13607.2 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | output_tokens | tokens | 15930.3 | 3/3 | 0 | 1 | 15930.3 | 3 / 7020.69 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | output_tokens | tokens | 7058.33 | 3/3 | 0 | 1 | 7058.33 | 3 / 2217.52 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | output_tokens | tokens | 4830.33 | 3/3 | 0 | 1 | 4830.33 | 3 / 471.816 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | output_tokens | tokens | 6270.67 | 3/3 | 0 | 1 | 6270.67 | 3 / 1354.46 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | output_tokens | tokens | 7542 | 3/3 | 0 | 1 | 7542 | 3 / 7504.92 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | output_tokens | tokens | 5983 | 3/3 | 0 | 1 | 5983 | 3 / 2608.06 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | output_tokens | tokens | 8967 | 3/3 | 0 | 1 | 8967 | 3 / 6189.13 |
| expgym | tuning | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.127625 | 27/27 | 0 | 9 | 0.127625 | 3 / 0.0552428 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | protocol_failure_rate | fraction | 0.115086 | 9/9 | 0 | 3 | 0.115086 | 3 / 0.0592065 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | protocol_failure_rate | fraction | 0.0752798 | 9/9 | 0 | 3 | 0.0752798 | 3 / 0.010875 |
| expgym | tuning | family/paramnet | cost_moderate | single | protocol_failure_rate | fraction | 0.192509 | 9/9 | 0 | 3 | 0.192509 | 3 / 0.153339 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | protocol_failure_rate | fraction | 0.0892857 | 3/3 | 0 | 1 | 0.0892857 | 3 / 0.0778375 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | protocol_failure_rate | fraction | 0.0997151 | 3/3 | 0 | 1 | 0.0997151 | 3 / 0.112851 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | protocol_failure_rate | fraction | 0.156258 | 3/3 | 0 | 1 | 0.156258 | 3 / 0.0607016 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | protocol_failure_rate | fraction | 0.0668651 | 3/3 | 0 | 1 | 0.0668651 | 3 / 0.00446759 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | protocol_failure_rate | fraction | 0.0700855 | 3/3 | 0 | 1 | 0.0700855 | 3 / 0.00592154 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | protocol_failure_rate | fraction | 0.0888889 | 3/3 | 0 | 1 | 0.0888889 | 3 / 0.03849 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | protocol_failure_rate | fraction | 0.175 | 3/3 | 0 | 1 | 0.175 | 3 / 0.0433013 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | protocol_failure_rate | fraction | 0.147826 | 3/3 | 0 | 1 | 0.147826 | 3 / 0.219468 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | protocol_failure_rate | fraction | 0.254701 | 3/3 | 0 | 1 | 0.254701 | 3 / 0.234252 |
| expgym | tuning | all/all | cost_moderate | single | wall_time_seconds | seconds | 118.364 | 27/27 | 0 | 9 | 118.364 | 3 / 30.6877 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | wall_time_seconds | seconds | 187.027 | 9/9 | 0 | 3 | 187.027 | 3 / 101.69 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | wall_time_seconds | seconds | 71.5567 | 9/9 | 0 | 3 | 71.5567 | 3 / 10.1547 |
| expgym | tuning | family/paramnet | cost_moderate | single | wall_time_seconds | seconds | 96.5093 | 9/9 | 0 | 3 | 96.5093 | 3 / 18.1503 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | wall_time_seconds | seconds | 213.402 | 3/3 | 0 | 1 | 213.402 | 3 / 251.623 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | wall_time_seconds | seconds | 160.966 | 3/3 | 0 | 1 | 160.966 | 3 / 165.536 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | wall_time_seconds | seconds | 186.712 | 3/3 | 0 | 1 | 186.712 | 3 / 81.0248 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | wall_time_seconds | seconds | 84.2377 | 3/3 | 0 | 1 | 84.2377 | 3 / 26.0955 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | wall_time_seconds | seconds | 58.2182 | 3/3 | 0 | 1 | 58.2182 | 3 / 7.26774 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | wall_time_seconds | seconds | 72.2143 | 3/3 | 0 | 1 | 72.2143 | 3 / 13.8273 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | wall_time_seconds | seconds | 96.0534 | 3/3 | 0 | 1 | 96.0534 | 3 / 95.7262 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | wall_time_seconds | seconds | 77.2376 | 3/3 | 0 | 1 | 77.2376 | 3 / 36.1319 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | wall_time_seconds | seconds | 116.237 | 3/3 | 0 | 1 | 116.237 | 3 / 79.2493 |
| expgym | tuning | all/all | cost_tight | single | budget_utilization | fraction | 0.939236 | 27/27 | 0 | 9 | 0.939236 | 3 / 0.126418 |
| expgym | tuning | family/nasbench101 | cost_tight | single | budget_utilization | fraction | 0.808931 | 9/9 | 0 | 3 | 0.808931 | 3 / 0.165851 |
| expgym | tuning | family/nasbench201 | cost_tight | single | budget_utilization | fraction | 1.02071 | 9/9 | 0 | 3 | 1.02071 | 3 / 0.0519215 |
| expgym | tuning | family/paramnet | cost_tight | single | budget_utilization | fraction | 0.988066 | 9/9 | 0 | 3 | 0.988066 | 3 / 0.37033 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | budget_utilization | fraction | 1.06473 | 3/3 | 0 | 1 | 1.06473 | 3 / 0.197849 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | budget_utilization | fraction | 0.6192 | 3/3 | 0 | 1 | 0.6192 | 3 / 0.538716 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | budget_utilization | fraction | 0.742863 | 3/3 | 0 | 1 | 0.742863 | 3 / 0.652138 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | budget_utilization | fraction | 0.973751 | 3/3 | 0 | 1 | 0.973751 | 3 / 0.164033 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | budget_utilization | fraction | 1.04295 | 3/3 | 0 | 1 | 1.04295 | 3 / 0.0229396 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | budget_utilization | fraction | 1.04544 | 3/3 | 0 | 1 | 1.04544 | 3 / 0.103678 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | budget_utilization | fraction | 1.29317 | 3/3 | 0 | 1 | 1.29317 | 3 / 0.643149 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | budget_utilization | fraction | 0.688295 | 3/3 | 0 | 1 | 0.688295 | 3 / 0.47695 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | budget_utilization | fraction | 0.982728 | 3/3 | 0 | 1 | 0.982728 | 3 / 0.00909274 |
| expgym | tuning | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 27/27 | 0 | 9 | 0 | 3 / 0 |
| expgym | tuning | family/nasbench101 | cost_tight | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/nasbench201 | cost_tight | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/paramnet | cost_tight | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_tight | single | feedback_attempts | count | 4.07407 | 27/27 | 0 | 9 | 4.07407 | 3 / 0.42066 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_attempts | count | 3.22222 | 9/9 | 0 | 3 | 3.22222 | 3 / 0.96225 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_attempts | count | 4.22222 | 9/9 | 0 | 3 | 4.22222 | 3 / 0.693889 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_attempts | count | 4.77778 | 9/9 | 0 | 3 | 4.77778 | 3 / 1.9245 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_attempts | count | 3.66667 | 3/3 | 0 | 1 | 3.66667 | 3 / 1.1547 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_attempts | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 3.51188 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_attempts | count | 2.66667 | 3/3 | 0 | 1 | 2.66667 | 3 / 2.51661 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_attempts | count | 4.33333 | 3/3 | 0 | 1 | 4.33333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_attempts | count | 3.66667 | 3/3 | 0 | 1 | 3.66667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_attempts | count | 4.66667 | 3/3 | 0 | 1 | 4.66667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_attempts | count | 1.66667 | 3/3 | 0 | 1 | 1.66667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_attempts | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 3 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_attempts | count | 8.66667 | 3/3 | 0 | 1 | 8.66667 | 3 / 3.51188 |
| expgym | tuning | all/all | cost_tight | single | feedback_cost_seconds | seconds | 34420.8 | 27/27 | 0 | 9 | 34420.8 | 3 / 2127.6 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_cost_seconds | seconds | 19966.5 | 9/9 | 0 | 3 | 19966.5 | 3 / 5311.99 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_cost_seconds | seconds | 83001.2 | 9/9 | 0 | 3 | 83001.2 | 3 / 4493.24 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_cost_seconds | seconds | 294.786 | 9/9 | 0 | 3 | 294.786 | 3 / 129.596 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_cost_seconds | seconds | 15792.5 | 3/3 | 0 | 1 | 15792.5 | 3 / 2934.58 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_cost_seconds | seconds | 19138 | 3/3 | 0 | 1 | 19138 | 3 / 16650.5 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_cost_seconds | seconds | 24968.8 | 3/3 | 0 | 1 | 24968.8 | 3 / 21919.4 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_cost_seconds | seconds | 33039.5 | 3/3 | 0 | 1 | 33039.5 | 3 / 5565.65 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_cost_seconds | seconds | 58319.7 | 3/3 | 0 | 1 | 58319.7 | 3 / 1282.74 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_cost_seconds | seconds | 157644 | 3/3 | 0 | 1 | 157644 | 3 / 15633.8 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_cost_seconds | seconds | 110.717 | 3/3 | 0 | 1 | 110.717 | 3 / 55.0643 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_cost_seconds | seconds | 483.92 | 3/3 | 0 | 1 | 483.92 | 3 / 335.33 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_cost_seconds | seconds | 289.719 | 3/3 | 0 | 1 | 289.719 | 3 / 2.68064 |
| expgym | tuning | all/all | cost_tight | single | feedback_visible | count | 3.62963 | 27/27 | 0 | 9 | 3.62963 | 3 / 0.42066 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_visible | count | 2.88889 | 9/9 | 0 | 3 | 2.88889 | 3 / 1.01835 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_visible | count | 3.55556 | 9/9 | 0 | 3 | 3.55556 | 3 / 0.693889 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_visible | count | 4.44444 | 9/9 | 0 | 3 | 4.44444 | 3 / 1.64429 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_visible | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_visible | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 3.51188 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_visible | count | 2 | 3/3 | 0 | 1 | 2 | 3 / 2 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_visible | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 1.73205 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_visible | count | 2.66667 | 3/3 | 0 | 1 | 2.66667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_visible | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_visible | count | 1 | 3/3 | 0 | 1 | 1 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_visible | count | 3.66667 | 3/3 | 0 | 1 | 3.66667 | 3 / 2.51661 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_visible | count | 8.66667 | 3/3 | 0 | 1 | 8.66667 | 3 / 3.51188 |
| expgym | tuning | all/all | cost_tight | single | input_tokens | tokens | 24947.7 | 27/27 | 0 | 9 | 24947.7 | 3 / 33.143 |
| expgym | tuning | family/nasbench101 | cost_tight | single | input_tokens | tokens | 35051.6 | 9/9 | 0 | 3 | 35051.6 | 3 / 5471.11 |
| expgym | tuning | family/nasbench201 | cost_tight | single | input_tokens | tokens | 20059.1 | 9/9 | 0 | 3 | 20059.1 | 3 / 3818.58 |
| expgym | tuning | family/paramnet | cost_tight | single | input_tokens | tokens | 19732.3 | 9/9 | 0 | 3 | 19732.3 | 3 / 3647.43 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | input_tokens | tokens | 33225.7 | 3/3 | 0 | 1 | 33225.7 | 3 / 12985.1 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | input_tokens | tokens | 39359.3 | 3/3 | 0 | 1 | 39359.3 | 3 / 28227.6 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | input_tokens | tokens | 32569.7 | 3/3 | 0 | 1 | 32569.7 | 3 / 19009 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | input_tokens | tokens | 19907.3 | 3/3 | 0 | 1 | 19907.3 | 3 / 12402.6 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | input_tokens | tokens | 21119.7 | 3/3 | 0 | 1 | 21119.7 | 3 / 1702.49 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | input_tokens | tokens | 19150.3 | 3/3 | 0 | 1 | 19150.3 | 3 / 682.983 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | input_tokens | tokens | 8498 | 3/3 | 0 | 1 | 8498 | 3 / 798.906 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | input_tokens | tokens | 13701 | 3/3 | 0 | 1 | 13701 | 3 / 6285.15 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | input_tokens | tokens | 36998 | 3/3 | 0 | 1 | 36998 | 3 / 11187.3 |
| expgym | tuning | all/all | cost_tight | single | output_tokens | tokens | 6140.74 | 27/27 | 0 | 9 | 6140.74 | 3 / 1014.88 |
| expgym | tuning | family/nasbench101 | cost_tight | single | output_tokens | tokens | 7281.11 | 9/9 | 0 | 3 | 7281.11 | 3 / 1893.41 |
| expgym | tuning | family/nasbench201 | cost_tight | single | output_tokens | tokens | 4186.78 | 9/9 | 0 | 3 | 4186.78 | 3 / 1102.23 |
| expgym | tuning | family/paramnet | cost_tight | single | output_tokens | tokens | 6954.33 | 9/9 | 0 | 3 | 6954.33 | 3 / 3460.64 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | output_tokens | tokens | 8131 | 3/3 | 0 | 1 | 8131 | 3 / 3713.86 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | output_tokens | tokens | 6795 | 3/3 | 0 | 1 | 6795 | 3 / 2067.53 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | output_tokens | tokens | 6917.33 | 3/3 | 0 | 1 | 6917.33 | 3 / 1224.47 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | output_tokens | tokens | 3445.67 | 3/3 | 0 | 1 | 3445.67 | 3 / 2576.61 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | output_tokens | tokens | 5437.67 | 3/3 | 0 | 1 | 5437.67 | 3 / 1952 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | output_tokens | tokens | 3677 | 3/3 | 0 | 1 | 3677 | 3 / 2494.8 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | output_tokens | tokens | 9390.33 | 3/3 | 0 | 1 | 9390.33 | 3 / 12145.2 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | output_tokens | tokens | 2488.67 | 3/3 | 0 | 1 | 2488.67 | 3 / 521.07 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | output_tokens | tokens | 8984 | 3/3 | 0 | 1 | 8984 | 3 / 6810.52 |
| expgym | tuning | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.23939 | 27/27 | 0 | 9 | 0.23939 | 3 / 0.0872608 |
| expgym | tuning | family/nasbench101 | cost_tight | single | protocol_failure_rate | fraction | 0.291005 | 9/9 | 0 | 3 | 0.291005 | 3 / 0.0788129 |
| expgym | tuning | family/nasbench201 | cost_tight | single | protocol_failure_rate | fraction | 0.16045 | 9/9 | 0 | 3 | 0.16045 | 3 / 0.0479754 |
| expgym | tuning | family/paramnet | cost_tight | single | protocol_failure_rate | fraction | 0.266715 | 9/9 | 0 | 3 | 0.266715 | 3 / 0.234031 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | protocol_failure_rate | fraction | 0.180952 | 3/3 | 0 | 1 | 0.180952 | 3 / 0.0329914 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | protocol_failure_rate | fraction | 0.355556 | 3/3 | 0 | 1 | 0.355556 | 3 / 0.26943 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | protocol_failure_rate | fraction | 0.336508 | 3/3 | 0 | 1 | 0.336508 | 3 / 0.28735 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | protocol_failure_rate | fraction | 0.152778 | 3/3 | 0 | 1 | 0.152778 | 3 / 0.168394 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | protocol_failure_rate | fraction | 0.177778 | 3/3 | 0 | 1 | 0.177778 | 3 / 0.019245 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | protocol_failure_rate | fraction | 0.150794 | 3/3 | 0 | 1 | 0.150794 | 3 / 0.0137464 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | protocol_failure_rate | fraction | 0.416667 | 3/3 | 0 | 1 | 0.416667 | 3 / 0.288675 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | protocol_failure_rate | fraction | 0.305556 | 3/3 | 0 | 1 | 0.305556 | 3 / 0.393818 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | protocol_failure_rate | fraction | 0.0779221 | 3/3 | 0 | 1 | 0.0779221 | 3 / 0.0723086 |
| expgym | tuning | all/all | cost_tight | single | wall_time_seconds | seconds | 72.6696 | 27/27 | 0 | 9 | 72.6696 | 3 / 13.3471 |
| expgym | tuning | family/nasbench101 | cost_tight | single | wall_time_seconds | seconds | 82.4581 | 9/9 | 0 | 3 | 82.4581 | 3 / 22.4043 |
| expgym | tuning | family/nasbench201 | cost_tight | single | wall_time_seconds | seconds | 48.8623 | 9/9 | 0 | 3 | 48.8623 | 3 / 13.1228 |
| expgym | tuning | family/paramnet | cost_tight | single | wall_time_seconds | seconds | 86.6882 | 9/9 | 0 | 3 | 86.6882 | 3 / 43.6681 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | wall_time_seconds | seconds | 90.6217 | 3/3 | 0 | 1 | 90.6217 | 3 / 42.6802 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | wall_time_seconds | seconds | 78.2653 | 3/3 | 0 | 1 | 78.2653 | 3 / 25.1599 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | wall_time_seconds | seconds | 78.4874 | 3/3 | 0 | 1 | 78.4874 | 3 / 11.2983 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | wall_time_seconds | seconds | 40.4682 | 3/3 | 0 | 1 | 40.4682 | 3 / 31.039 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | wall_time_seconds | seconds | 61.8816 | 3/3 | 0 | 1 | 61.8816 | 3 / 22.4252 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | wall_time_seconds | seconds | 44.2373 | 3/3 | 0 | 1 | 44.2373 | 3 / 29.1205 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | wall_time_seconds | seconds | 113.846 | 3/3 | 0 | 1 | 113.846 | 3 / 145.112 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | wall_time_seconds | seconds | 31.3393 | 3/3 | 0 | 1 | 31.3393 | 3 / 4.77497 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | wall_time_seconds | seconds | 114.879 | 3/3 | 0 | 1 | 114.879 | 3 / 86.898 |
| poolact | evidence_audit | all/all | cost_moderate | cached | budget_utilization | fraction | 0.626227 | 13/13 | 0 | 13 | 0.626227 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | budget_utilization | fraction | 0.626227 | 13/13 | 0 | 13 | 0.626227 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | duplicate_action_attempts | count | 9.84615 | 13/13 | 0 | 13 | 9.84615 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | duplicate_action_attempts | count | 9.84615 | 13/13 | 0 | 13 | 9.84615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_attempts | count | 32.1538 | 13/13 | 0 | 13 | 32.1538 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_attempts | count | 32.1538 | 13/13 | 0 | 13 | 32.1538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 7514.72 | 13/13 | 0 | 13 | 7514.72 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_cost_seconds | seconds | 7514.72 | 13/13 | 0 | 13 | 7514.72 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | input_tokens | tokens | 473478 | 13/13 | 0 | 13 | 473478 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | input_tokens | tokens | 473478 | 13/13 | 0 | 13 | 473478 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | output_tokens | tokens | 82999.1 | 13/13 | 0 | 13 | 82999.1 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | output_tokens | tokens | 82999.1 | 13/13 | 0 | 13 | 82999.1 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.235076 | 13/13 | 0 | 13 | 0.235076 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | protocol_failure_rate | fraction | 0.235076 | 13/13 | 0 | 13 | 0.235076 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | budget_utilization | fraction | 0.466278 | 13/13 | 0 | 13 | 0.466278 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | budget_utilization | fraction | 0.466278 | 13/13 | 0 | 13 | 0.466278 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | duplicate_action_attempts | count | 4.61538 | 13/13 | 0 | 13 | 4.61538 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | duplicate_action_attempts | count | 4.61538 | 13/13 | 0 | 13 | 4.61538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_attempts | count | 18.8462 | 13/13 | 0 | 13 | 18.8462 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_attempts | count | 18.8462 | 13/13 | 0 | 13 | 18.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 5595.33 | 13/13 | 0 | 13 | 5595.33 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_cost_seconds | seconds | 5595.33 | 13/13 | 0 | 13 | 5595.33 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | input_tokens | tokens | 376722 | 13/13 | 0 | 13 | 376722 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | input_tokens | tokens | 376722 | 13/13 | 0 | 13 | 376722 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | output_tokens | tokens | 109929 | 13/13 | 0 | 13 | 109929 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | output_tokens | tokens | 109929 | 13/13 | 0 | 13 | 109929 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.35335 | 13/13 | 0 | 13 | 0.35335 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | protocol_failure_rate | fraction | 0.35335 | 13/13 | 0 | 13 | 0.35335 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.246636 | 13/13 | 0 | 13 | 0.246636 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | budget_utilization | fraction | 0.246636 | 13/13 | 0 | 13 | 0.246636 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 1.61538 | 13/13 | 0 | 13 | 1.61538 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | duplicate_action_attempts | count | 1.61538 | 13/13 | 0 | 13 | 1.61538 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_attempts | count | 10.4615 | 13/13 | 0 | 13 | 10.4615 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_attempts | count | 10.4615 | 13/13 | 0 | 13 | 10.4615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 2959.63 | 13/13 | 0 | 13 | 2959.63 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_cost_seconds | seconds | 2959.63 | 13/13 | 0 | 13 | 2959.63 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | input_tokens | tokens | 302074 | 13/13 | 0 | 13 | 302074 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | input_tokens | tokens | 302074 | 13/13 | 0 | 13 | 302074 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | output_tokens | tokens | 84832.4 | 13/13 | 0 | 13 | 84832.4 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | output_tokens | tokens | 84832.4 | 13/13 | 0 | 13 | 84832.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.447477 | 13/13 | 0 | 13 | 0.447477 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | protocol_failure_rate | fraction | 0.447477 | 13/13 | 0 | 13 | 0.447477 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | budget_utilization | fraction | 0.531552 | 13/13 | 0 | 13 | 0.531552 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | budget_utilization | fraction | 0.531552 | 13/13 | 0 | 13 | 0.531552 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | duplicate_action_attempts | count | 2.15385 | 13/13 | 0 | 13 | 2.15385 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | duplicate_action_attempts | count | 2.15385 | 13/13 | 0 | 13 | 2.15385 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 1913.59 | 13/13 | 0 | 13 | 1913.59 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_cost_seconds | seconds | 1913.59 | 13/13 | 0 | 13 | 1913.59 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | input_tokens | tokens | 194021 | 13/13 | 0 | 13 | 194021 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | input_tokens | tokens | 194021 | 13/13 | 0 | 13 | 194021 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | output_tokens | tokens | 82773.8 | 13/13 | 0 | 13 | 82773.8 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | output_tokens | tokens | 82773.8 | 13/13 | 0 | 13 | 82773.8 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.453801 | 13/13 | 0 | 13 | 0.453801 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | protocol_failure_rate | fraction | 0.453801 | 13/13 | 0 | 13 | 0.453801 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | budget_utilization | fraction | 0.572016 | 13/13 | 0 | 13 | 0.572016 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | budget_utilization | fraction | 0.572016 | 13/13 | 0 | 13 | 0.572016 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | duplicate_action_attempts | count | 2.53846 | 13/13 | 0 | 13 | 2.53846 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | duplicate_action_attempts | count | 2.53846 | 13/13 | 0 | 13 | 2.53846 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_attempts | count | 7 | 13/13 | 0 | 13 | 7 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 2059.26 | 13/13 | 0 | 13 | 2059.26 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_cost_seconds | seconds | 2059.26 | 13/13 | 0 | 13 | 2059.26 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_visible | count | unknown | 1/13 | 12 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | input_tokens | tokens | 249212 | 13/13 | 0 | 13 | 249212 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | input_tokens | tokens | 249212 | 13/13 | 0 | 13 | 249212 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | output_tokens | tokens | 104834 | 13/13 | 0 | 13 | 104834 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | output_tokens | tokens | 104834 | 13/13 | 0 | 13 | 104834 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.459612 | 13/13 | 0 | 13 | 0.459612 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | protocol_failure_rate | fraction | 0.459612 | 13/13 | 0 | 13 | 0.459612 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | budget_utilization | fraction | 0.173411 | 13/13 | 0 | 13 | 0.173411 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | budget_utilization | fraction | 0.173411 | 13/13 | 0 | 13 | 0.173411 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.692308 | 13/13 | 0 | 13 | 0.692308 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | duplicate_action_attempts | count | 0.692308 | 13/13 | 0 | 13 | 0.692308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_attempts | count | 2.23077 | 13/13 | 0 | 13 | 2.23077 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_attempts | count | 2.23077 | 13/13 | 0 | 13 | 2.23077 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 624.278 | 13/13 | 0 | 13 | 624.278 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_cost_seconds | seconds | 624.278 | 13/13 | 0 | 13 | 624.278 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_visible | count | unknown | 2/13 | 11 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | input_tokens | tokens | 132751 | 13/13 | 0 | 13 | 132751 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | input_tokens | tokens | 132751 | 13/13 | 0 | 13 | 132751 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | output_tokens | tokens | 61874 | 13/13 | 0 | 13 | 61874 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | output_tokens | tokens | 61874 | 13/13 | 0 | 13 | 61874 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.63138 | 13/13 | 0 | 13 | 0.63138 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | protocol_failure_rate | fraction | 0.63138 | 13/13 | 0 | 13 | 0.63138 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | budget_utilization | fraction | 0.390728 | 39/39 | 0 | 39 | 0.390728 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | budget_utilization | fraction | 0.390728 | 39/39 | 0 | 39 | 0.390728 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | duplicate_action_attempts | count | 13.3077 | 39/39 | 0 | 39 | 13.3077 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | duplicate_action_attempts | count | 13.3077 | 39/39 | 0 | 39 | 13.3077 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_attempts | count | 25.0769 | 39/39 | 0 | 39 | 25.0769 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_attempts | count | 25.0769 | 39/39 | 0 | 39 | 25.0769 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 4688.74 | 39/39 | 0 | 39 | 4688.74 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_cost_seconds | seconds | 4688.74 | 39/39 | 0 | 39 | 4688.74 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_visible | count | unknown | 1/39 | 38 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_visible | count | unknown | 1/39 | 38 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | input_tokens | tokens | 169259 | 39/39 | 0 | 39 | 169259 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | input_tokens | tokens | 169259 | 39/39 | 0 | 39 | 169259 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | output_tokens | tokens | 31060.7 | 39/39 | 0 | 39 | 31060.7 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | output_tokens | tokens | 31060.7 | 39/39 | 0 | 39 | 31060.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.323588 | 39/39 | 0 | 39 | 0.323588 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | protocol_failure_rate | fraction | 0.323588 | 39/39 | 0 | 39 | 0.323588 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | budget_utilization | fraction | 0.412121 | 39/39 | 0 | 39 | 0.412121 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | budget_utilization | fraction | 0.412121 | 39/39 | 0 | 39 | 0.412121 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | duplicate_action_attempts | count | 11.9487 | 39/39 | 0 | 39 | 11.9487 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | duplicate_action_attempts | count | 11.9487 | 39/39 | 0 | 39 | 11.9487 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_attempts | count | 24.9231 | 39/39 | 0 | 39 | 24.9231 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_attempts | count | 24.9231 | 39/39 | 0 | 39 | 24.9231 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 4945.46 | 39/39 | 0 | 39 | 4945.46 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_cost_seconds | seconds | 4945.46 | 39/39 | 0 | 39 | 4945.46 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | input_tokens | tokens | 186091 | 39/39 | 0 | 39 | 186091 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | input_tokens | tokens | 186091 | 39/39 | 0 | 39 | 186091 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | output_tokens | tokens | 35566 | 39/39 | 0 | 39 | 35566 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | output_tokens | tokens | 35566 | 39/39 | 0 | 39 | 35566 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.308474 | 39/39 | 0 | 39 | 0.308474 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | protocol_failure_rate | fraction | 0.308474 | 39/39 | 0 | 39 | 0.308474 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.203611 | 39/39 | 0 | 39 | 0.203611 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | budget_utilization | fraction | 0.203611 | 39/39 | 0 | 39 | 0.203611 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 4.46154 | 39/39 | 0 | 39 | 4.46154 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | duplicate_action_attempts | count | 4.46154 | 39/39 | 0 | 39 | 4.46154 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_attempts | count | 10.9231 | 39/39 | 0 | 39 | 10.9231 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_attempts | count | 10.9231 | 39/39 | 0 | 39 | 10.9231 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 2443.33 | 39/39 | 0 | 39 | 2443.33 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_cost_seconds | seconds | 2443.33 | 39/39 | 0 | 39 | 2443.33 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | input_tokens | tokens | 126466 | 39/39 | 0 | 39 | 126466 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | input_tokens | tokens | 126466 | 39/39 | 0 | 39 | 126466 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | output_tokens | tokens | 32022.8 | 39/39 | 0 | 39 | 32022.8 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | output_tokens | tokens | 32022.8 | 39/39 | 0 | 39 | 32022.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.417162 | 39/39 | 0 | 39 | 0.417162 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | protocol_failure_rate | fraction | 0.417162 | 39/39 | 0 | 39 | 0.417162 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | budget_utilization | fraction | 0.815309 | 39/39 | 0 | 39 | 0.815309 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | budget_utilization | fraction | 0.815309 | 39/39 | 0 | 39 | 0.815309 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | duplicate_action_attempts | count | 7.4359 | 39/39 | 0 | 39 | 7.4359 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | duplicate_action_attempts | count | 7.4359 | 39/39 | 0 | 39 | 7.4359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_attempts | count | 13.4359 | 39/39 | 0 | 39 | 13.4359 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_attempts | count | 13.4359 | 39/39 | 0 | 39 | 13.4359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 2935.11 | 39/39 | 0 | 39 | 2935.11 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_cost_seconds | seconds | 2935.11 | 39/39 | 0 | 39 | 2935.11 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_visible | count | unknown | 2/39 | 37 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_visible | count | unknown | 2/39 | 37 | 39 | 0 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | input_tokens | tokens | 54360.4 | 39/39 | 0 | 39 | 54360.4 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | input_tokens | tokens | 54360.4 | 39/39 | 0 | 39 | 54360.4 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | output_tokens | tokens | 26575.7 | 39/39 | 0 | 39 | 26575.7 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | output_tokens | tokens | 26575.7 | 39/39 | 0 | 39 | 26575.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.309256 | 39/39 | 0 | 39 | 0.309256 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | protocol_failure_rate | fraction | 0.309256 | 39/39 | 0 | 39 | 0.309256 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | budget_utilization | fraction | 0.648249 | 39/39 | 0 | 39 | 0.648249 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | budget_utilization | fraction | 0.648249 | 39/39 | 0 | 39 | 0.648249 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | duplicate_action_attempts | count | 5.94872 | 39/39 | 0 | 39 | 5.94872 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | duplicate_action_attempts | count | 5.94872 | 39/39 | 0 | 39 | 5.94872 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_attempts | count | 11.5385 | 39/39 | 0 | 39 | 11.5385 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_attempts | count | 11.5385 | 39/39 | 0 | 39 | 11.5385 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 2333.7 | 39/39 | 0 | 39 | 2333.7 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_cost_seconds | seconds | 2333.7 | 39/39 | 0 | 39 | 2333.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | input_tokens | tokens | 66929.1 | 39/39 | 0 | 39 | 66929.1 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | input_tokens | tokens | 66929.1 | 39/39 | 0 | 39 | 66929.1 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | output_tokens | tokens | 26096 | 39/39 | 0 | 39 | 26096 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | output_tokens | tokens | 26096 | 39/39 | 0 | 39 | 26096 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.37 | 39/39 | 0 | 39 | 0.37 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | protocol_failure_rate | fraction | 0.37 | 39/39 | 0 | 39 | 0.37 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | budget_utilization | fraction | 0.629807 | 39/39 | 0 | 39 | 0.629807 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | budget_utilization | fraction | 0.629807 | 39/39 | 0 | 39 | 0.629807 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | duplicate_action_attempts | count | 4.84615 | 39/39 | 0 | 39 | 4.84615 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | duplicate_action_attempts | count | 4.84615 | 39/39 | 0 | 39 | 4.84615 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_attempts | count | 9.71795 | 39/39 | 0 | 39 | 9.71795 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_attempts | count | 9.71795 | 39/39 | 0 | 39 | 9.71795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 2267.31 | 39/39 | 0 | 39 | 2267.31 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_cost_seconds | seconds | 2267.31 | 39/39 | 0 | 39 | 2267.31 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | input_tokens | tokens | 80792.7 | 39/39 | 0 | 39 | 80792.7 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | input_tokens | tokens | 80792.7 | 39/39 | 0 | 39 | 80792.7 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | output_tokens | tokens | 33809.6 | 39/39 | 0 | 39 | 33809.6 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | output_tokens | tokens | 33809.6 | 39/39 | 0 | 39 | 33809.6 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.402962 | 39/39 | 0 | 39 | 0.402962 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | protocol_failure_rate | fraction | 0.402962 | 39/39 | 0 | 39 | 0.402962 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | budget_utilization | fraction | 0.336466 | 9/9 | 0 | 3 | 0.336466 | 3 / 0.0775656 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | budget_utilization | fraction | 0.336466 | 9/9 | 0 | 3 | 0.336466 | 3 / 0.0775656 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | budget_utilization | fraction | 0.674108 | 3/3 | 0 | 1 | 0.674108 | 3 / 0.411084 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | budget_utilization | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | budget_utilization | fraction | 0.33529 | 3/3 | 0 | 1 | 0.33529 | 3 / 0.365415 |
| poolact | tuning | all/all | cost_moderate | cached | duplicate_action_attempts | count | 1.66667 | 9/9 | 0 | 3 | 1.66667 | 3 / 1.1547 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | duplicate_action_attempts | count | 1.66667 | 9/9 | 0 | 3 | 1.66667 | 3 / 1.1547 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | duplicate_action_attempts | count | 2.33333 | 3/3 | 0 | 1 | 2.33333 | 3 / 2.08167 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | duplicate_action_attempts | count | 2.66667 | 3/3 | 0 | 1 | 2.66667 | 3 / 2.51661 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_attempts | count | 15.2222 | 9/9 | 0 | 3 | 15.2222 | 3 / 8.28206 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_attempts | count | 15.2222 | 9/9 | 0 | 3 | 15.2222 | 3 / 8.28206 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_attempts | count | 18.3333 | 3/3 | 0 | 1 | 18.3333 | 3 / 10.0664 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_attempts | count | 27 | 3/3 | 0 | 1 | 27 | 3 / 25.632 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 94525.8 | 9/9 | 0 | 3 | 94525.8 | 3 / 35612.9 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_cost_seconds | seconds | 94525.8 | 9/9 | 0 | 3 | 94525.8 | 3 / 35612.9 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_cost_seconds | seconds | 133316 | 3/3 | 0 | 1 | 133316 | 3 / 81298.4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_cost_seconds | seconds | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_cost_seconds | seconds | 150262 | 3/3 | 0 | 1 | 150262 | 3 / 163762 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_visible | count | unknown | 2/3 | 1 | 1 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_visible | count | unknown | 1/3 | 2 | 1 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | input_tokens | tokens | 278340 | 9/9 | 0 | 3 | 278340 | 3 / 168429 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | input_tokens | tokens | 278340 | 9/9 | 0 | 3 | 278340 | 3 / 168429 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | input_tokens | tokens | 239019 | 3/3 | 0 | 1 | 239019 | 3 / 63819.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | input_tokens | tokens | 132507 | 3/3 | 0 | 1 | 132507 | 3 / 100938 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | input_tokens | tokens | 463494 | 3/3 | 0 | 1 | 463494 | 3 / 366259 |
| poolact | tuning | all/all | cost_moderate | cached | output_tokens | tokens | 77948.2 | 9/9 | 0 | 3 | 77948.2 | 3 / 40631.6 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | output_tokens | tokens | 77948.2 | 9/9 | 0 | 3 | 77948.2 | 3 / 40631.6 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | output_tokens | tokens | 67691.7 | 3/3 | 0 | 1 | 67691.7 | 3 / 23335.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | output_tokens | tokens | 62480 | 3/3 | 0 | 1 | 62480 | 3 / 56899.2 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | output_tokens | tokens | 103673 | 3/3 | 0 | 1 | 103673 | 3 / 78125.6 |
| poolact | tuning | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.453267 | 9/9 | 0 | 3 | 0.453267 | 3 / 0.120559 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | protocol_failure_rate | fraction | 0.453267 | 9/9 | 0 | 3 | 0.453267 | 3 / 0.120559 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | protocol_failure_rate | fraction | 0.222946 | 3/3 | 0 | 1 | 0.222946 | 3 / 0.132833 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | protocol_failure_rate | fraction | 0.75 | 3/3 | 0 | 1 | 0.75 | 3 / 0.0833333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | protocol_failure_rate | fraction | 0.386856 | 3/3 | 0 | 1 | 0.386856 | 3 / 0.394907 |
| poolact | tuning | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | budget_utilization | fraction | 0.188325 | 9/9 | 0 | 3 | 0.188325 | 3 / 0.117837 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | budget_utilization | fraction | 0.188325 | 9/9 | 0 | 3 | 0.188325 | 3 / 0.117837 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | budget_utilization | fraction | 0.202305 | 3/3 | 0 | 1 | 0.202305 | 3 / 0.310963 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | budget_utilization | fraction | 0.0933723 | 3/3 | 0 | 1 | 0.0933723 | 3 / 0.096383 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | budget_utilization | fraction | 0.269297 | 3/3 | 0 | 1 | 0.269297 | 3 / 0.466436 |
| poolact | tuning | all/all | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.881917 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.881917 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | duplicate_action_attempts | count | 1.66667 | 3/3 | 0 | 1 | 1.66667 | 3 / 2.88675 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_attempts | count | 9.88889 | 9/9 | 0 | 3 | 9.88889 | 3 / 8.77074 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_attempts | count | 9.88889 | 9/9 | 0 | 3 | 9.88889 | 3 / 8.77074 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_attempts | count | 6.33333 | 3/3 | 0 | 1 | 6.33333 | 3 / 6.65833 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_attempts | count | 7 | 3/3 | 0 | 1 | 7 | 3 / 5.2915 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_attempts | count | 16.3333 | 3/3 | 0 | 1 | 16.3333 | 3 / 27.4287 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 66391.6 | 9/9 | 0 | 3 | 66391.6 | 3 / 59036.9 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_cost_seconds | seconds | 66391.6 | 9/9 | 0 | 3 | 66391.6 | 3 / 59036.9 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_cost_seconds | seconds | 40009 | 3/3 | 0 | 1 | 40009 | 3 / 61497.9 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_cost_seconds | seconds | 38479 | 3/3 | 0 | 1 | 38479 | 3 / 39719.7 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_cost_seconds | seconds | 120687 | 3/3 | 0 | 1 | 120687 | 3 / 209036 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_visible | count | unknown | 1/3 | 2 | 1 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | input_tokens | tokens | 269754 | 9/9 | 0 | 3 | 269754 | 3 / 161062 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | input_tokens | tokens | 269754 | 9/9 | 0 | 3 | 269754 | 3 / 161062 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | input_tokens | tokens | 159527 | 3/3 | 0 | 1 | 159527 | 3 / 129772 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | input_tokens | tokens | 246012 | 3/3 | 0 | 1 | 246012 | 3 / 181959 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | input_tokens | tokens | 403725 | 3/3 | 0 | 1 | 403725 | 3 / 481240 |
| poolact | tuning | all/all | cost_moderate | naive | output_tokens | tokens | 72492.4 | 9/9 | 0 | 3 | 72492.4 | 3 / 31099 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | output_tokens | tokens | 72492.4 | 9/9 | 0 | 3 | 72492.4 | 3 / 31099 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | output_tokens | tokens | 52578 | 3/3 | 0 | 1 | 52578 | 3 / 27469.5 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | output_tokens | tokens | 69541 | 3/3 | 0 | 1 | 69541 | 3 / 65817.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | output_tokens | tokens | 95358.3 | 3/3 | 0 | 1 | 95358.3 | 3 / 74765.7 |
| poolact | tuning | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.505538 | 9/9 | 0 | 3 | 0.505538 | 3 / 0.0894579 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | protocol_failure_rate | fraction | 0.505538 | 9/9 | 0 | 3 | 0.505538 | 3 / 0.0894579 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | protocol_failure_rate | fraction | 0.459452 | 3/3 | 0 | 1 | 0.459452 | 3 / 0.271462 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | protocol_failure_rate | fraction | 0.498997 | 3/3 | 0 | 1 | 0.498997 | 3 / 0.176652 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | protocol_failure_rate | fraction | 0.558165 | 3/3 | 0 | 1 | 0.558165 | 3 / 0.392526 |
| poolact | tuning | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.12028 | 9/9 | 0 | 3 | 0.12028 | 3 / 0.103462 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | budget_utilization | fraction | 0.12028 | 9/9 | 0 | 3 | 0.12028 | 3 / 0.103462 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | budget_utilization | fraction | 0.249694 | 3/3 | 0 | 1 | 0.249694 | 3 / 0.181891 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | budget_utilization | fraction | 0.111145 | 3/3 | 0 | 1 | 0.111145 | 3 / 0.192508 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | budget_utilization | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 0.444444 | 9/9 | 0 | 3 | 0.444444 | 3 / 0.19245 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | duplicate_action_attempts | count | 0.444444 | 9/9 | 0 | 3 | 0.444444 | 3 / 0.19245 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | duplicate_action_attempts | count | 0.666667 | 3/3 | 0 | 1 | 0.666667 | 3 / 1.1547 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_attempts | count | 5.11111 | 9/9 | 0 | 3 | 5.11111 | 3 / 3.16813 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_attempts | count | 5.11111 | 9/9 | 0 | 3 | 5.11111 | 3 / 3.16813 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_attempts | count | 8.66667 | 3/3 | 0 | 1 | 8.66667 | 3 / 6.1101 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_attempts | count | 5 | 3/3 | 0 | 1 | 5 | 3 / 8.66025 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_attempts | count | 1.66667 | 3/3 | 0 | 1 | 1.66667 | 3 / 2.08167 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 31728 | 9/9 | 0 | 3 | 31728 | 3 / 32867.9 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_cost_seconds | seconds | 31728 | 9/9 | 0 | 3 | 31728 | 3 / 32867.9 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_cost_seconds | seconds | 49381.1 | 3/3 | 0 | 1 | 49381.1 | 3 / 35971.8 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_cost_seconds | seconds | 45803 | 3/3 | 0 | 1 | 45803 | 3 / 79333.1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_cost_seconds | seconds | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_visible | count | unknown | 3/9 | 6 | 3 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_visible | count | unknown | 2/3 | 1 | 1 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_visible | count | unknown | 1/3 | 2 | 1 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | input_tokens | tokens | 212592 | 9/9 | 0 | 3 | 212592 | 3 / 111745 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | input_tokens | tokens | 212592 | 9/9 | 0 | 3 | 212592 | 3 / 111745 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | input_tokens | tokens | 342342 | 3/3 | 0 | 1 | 342342 | 3 / 306682 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | input_tokens | tokens | 217560 | 3/3 | 0 | 1 | 217560 | 3 / 192978 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | input_tokens | tokens | 77875 | 3/3 | 0 | 1 | 77875 | 3 / 62038.9 |
| poolact | tuning | all/all | cost_moderate | poolact | output_tokens | tokens | 55006.7 | 9/9 | 0 | 3 | 55006.7 | 3 / 30640.3 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | output_tokens | tokens | 55006.7 | 9/9 | 0 | 3 | 55006.7 | 3 / 30640.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | output_tokens | tokens | 75576.3 | 3/3 | 0 | 1 | 75576.3 | 3 / 57931.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | output_tokens | tokens | 57535.7 | 3/3 | 0 | 1 | 57535.7 | 3 / 40788.5 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | output_tokens | tokens | 31908 | 3/3 | 0 | 1 | 31908 | 3 / 20092.5 |
| poolact | tuning | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.586604 | 9/9 | 0 | 3 | 0.586604 | 3 / 0.202288 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | protocol_failure_rate | fraction | 0.586604 | 9/9 | 0 | 3 | 0.586604 | 3 / 0.202288 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | protocol_failure_rate | fraction | 0.370618 | 3/3 | 0 | 1 | 0.370618 | 3 / 0.223792 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | protocol_failure_rate | fraction | 0.726496 | 3/3 | 0 | 1 | 0.726496 | 3 / 0.329386 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | protocol_failure_rate | fraction | 0.662698 | 3/3 | 0 | 1 | 0.662698 | 3 / 0.0893518 |
| poolact | tuning | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | budget_utilization | fraction | 0.389056 | 9/9 | 0 | 3 | 0.389056 | 3 / 0.0466743 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | budget_utilization | fraction | 0.389056 | 9/9 | 0 | 3 | 0.389056 | 3 / 0.0466743 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | budget_utilization | fraction | 0.391573 | 3/3 | 0 | 1 | 0.391573 | 3 / 0.273505 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | budget_utilization | fraction | 0.5097 | 3/3 | 0 | 1 | 0.5097 | 3 / 0.489189 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | budget_utilization | fraction | 0.265895 | 3/3 | 0 | 1 | 0.265895 | 3 / 0.250502 |
| poolact | tuning | all/all | cost_tight | cached | duplicate_action_attempts | count | 0.777778 | 9/9 | 0 | 3 | 0.777778 | 3 / 0.83887 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | duplicate_action_attempts | count | 0.777778 | 9/9 | 0 | 3 | 0.777778 | 3 / 0.83887 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | duplicate_action_attempts | count | 0.666667 | 3/3 | 0 | 1 | 0.666667 | 3 / 1.1547 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | duplicate_action_attempts | count | 1.66667 | 3/3 | 0 | 1 | 1.66667 | 3 / 2.88675 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | cached | feedback_attempts | count | 6.66667 | 9/9 | 0 | 3 | 6.66667 | 3 / 2.96273 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_attempts | count | 6.66667 | 9/9 | 0 | 3 | 6.66667 | 3 / 2.96273 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_attempts | count | 4.66667 | 3/3 | 0 | 1 | 4.66667 | 3 / 1.52753 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_attempts | count | 9.66667 | 3/3 | 0 | 1 | 9.66667 | 3 / 7.37111 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_attempts | count | 5.66667 | 3/3 | 0 | 1 | 5.66667 | 3 / 6.4291 |
| poolact | tuning | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 40665.1 | 9/9 | 0 | 3 | 40665.1 | 3 / 11356 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_cost_seconds | seconds | 40665.1 | 9/9 | 0 | 3 | 40665.1 | 3 / 11356 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_cost_seconds | seconds | 23232 | 3/3 | 0 | 1 | 23232 | 3 / 16227 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_cost_seconds | seconds | 63014.6 | 3/3 | 0 | 1 | 63014.6 | 3 / 60478.9 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_cost_seconds | seconds | 35748.6 | 3/3 | 0 | 1 | 35748.6 | 3 / 33679 |
| poolact | tuning | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | input_tokens | tokens | 168160 | 9/9 | 0 | 3 | 168160 | 3 / 78093.8 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | input_tokens | tokens | 168160 | 9/9 | 0 | 3 | 168160 | 3 / 78093.8 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | input_tokens | tokens | 173457 | 3/3 | 0 | 1 | 173457 | 3 / 77855 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | input_tokens | tokens | 188558 | 3/3 | 0 | 1 | 188558 | 3 / 86093 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | input_tokens | tokens | 142466 | 3/3 | 0 | 1 | 142466 | 3 / 77532.3 |
| poolact | tuning | all/all | cost_tight | cached | output_tokens | tokens | 82649.2 | 9/9 | 0 | 3 | 82649.2 | 3 / 29886.3 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | output_tokens | tokens | 82649.2 | 9/9 | 0 | 3 | 82649.2 | 3 / 29886.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | output_tokens | tokens | 96845.7 | 3/3 | 0 | 1 | 96845.7 | 3 / 43783.1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | output_tokens | tokens | 55766.7 | 3/3 | 0 | 1 | 55766.7 | 3 / 39331.2 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | output_tokens | tokens | 95335.3 | 3/3 | 0 | 1 | 95335.3 | 3 / 59623.9 |
| poolact | tuning | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.470592 | 9/9 | 0 | 3 | 0.470592 | 3 / 0.0554102 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | protocol_failure_rate | fraction | 0.470592 | 9/9 | 0 | 3 | 0.470592 | 3 / 0.0554102 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | protocol_failure_rate | fraction | 0.416667 | 3/3 | 0 | 1 | 0.416667 | 3 / 0.0833333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | protocol_failure_rate | fraction | 0.397129 | 3/3 | 0 | 1 | 0.397129 | 3 / 0.119484 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | protocol_failure_rate | fraction | 0.59798 | 3/3 | 0 | 1 | 0.59798 | 3 / 0.229211 |
| poolact | tuning | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | budget_utilization | fraction | 0.492657 | 9/9 | 0 | 3 | 0.492657 | 3 / 0.253608 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | budget_utilization | fraction | 0.492657 | 9/9 | 0 | 3 | 0.492657 | 3 / 0.253608 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | budget_utilization | fraction | 0.695675 | 3/3 | 0 | 1 | 0.695675 | 3 / 0.47221 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | budget_utilization | fraction | 0.644498 | 3/3 | 0 | 1 | 0.644498 | 3 / 0.151117 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | budget_utilization | fraction | 0.1378 | 3/3 | 0 | 1 | 0.1378 | 3 / 0.238676 |
| poolact | tuning | all/all | cost_tight | naive | duplicate_action_attempts | count | 2.22222 | 9/9 | 0 | 3 | 2.22222 | 3 / 2.00924 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | duplicate_action_attempts | count | 2.22222 | 9/9 | 0 | 3 | 2.22222 | 3 / 2.00924 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | duplicate_action_attempts | count | 0.666667 | 3/3 | 0 | 1 | 0.666667 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | duplicate_action_attempts | count | 6 | 3/3 | 0 | 1 | 6 | 3 / 5.56776 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | naive | feedback_attempts | count | 9 | 9/9 | 0 | 3 | 9 | 3 / 8.14453 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_attempts | count | 9 | 9/9 | 0 | 3 | 9 | 3 / 8.14453 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_attempts | count | 8.33333 | 3/3 | 0 | 1 | 8.33333 | 3 / 8.5049 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_attempts | count | 13.6667 | 3/3 | 0 | 1 | 13.6667 | 3 / 8.32666 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_attempts | count | 5 | 3/3 | 0 | 1 | 5 | 3 / 7.81025 |
| poolact | tuning | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 46493.6 | 9/9 | 0 | 3 | 46493.6 | 3 / 21986.9 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_cost_seconds | seconds | 46493.6 | 9/9 | 0 | 3 | 46493.6 | 3 / 21986.9 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_cost_seconds | seconds | 41274.3 | 3/3 | 0 | 1 | 41274.3 | 3 / 28016.1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_cost_seconds | seconds | 79679.7 | 3/3 | 0 | 1 | 79679.7 | 3 / 18682.7 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_cost_seconds | seconds | 18526.7 | 3/3 | 0 | 1 | 18526.7 | 3 / 32089.1 |
| poolact | tuning | all/all | cost_tight | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_visible | count | unknown | 1/9 | 8 | 3 | 0 | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_visible | count | unknown | 1/3 | 2 | 1 | 0 | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | input_tokens | tokens | 229168 | 9/9 | 0 | 3 | 229168 | 3 / 220874 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | input_tokens | tokens | 229168 | 9/9 | 0 | 3 | 229168 | 3 / 220874 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | input_tokens | tokens | 215628 | 3/3 | 0 | 1 | 215628 | 3 / 251241 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | input_tokens | tokens | 338965 | 3/3 | 0 | 1 | 338965 | 3 / 309320 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | input_tokens | tokens | 132913 | 3/3 | 0 | 1 | 132913 | 3 / 105246 |
| poolact | tuning | all/all | cost_tight | naive | output_tokens | tokens | 72176.2 | 9/9 | 0 | 3 | 72176.2 | 3 / 37207.1 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | output_tokens | tokens | 72176.2 | 9/9 | 0 | 3 | 72176.2 | 3 / 37207.1 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | output_tokens | tokens | 69726 | 3/3 | 0 | 1 | 69726 | 3 / 61869 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | output_tokens | tokens | 79694.3 | 3/3 | 0 | 1 | 79694.3 | 3 / 43591.1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | output_tokens | tokens | 67108.3 | 3/3 | 0 | 1 | 67108.3 | 3 / 44186.3 |
| poolact | tuning | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.461251 | 9/9 | 0 | 3 | 0.461251 | 3 / 0.189539 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | protocol_failure_rate | fraction | 0.461251 | 9/9 | 0 | 3 | 0.461251 | 3 / 0.189539 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | protocol_failure_rate | fraction | 0.404701 | 3/3 | 0 | 1 | 0.404701 | 3 / 0.176329 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | protocol_failure_rate | fraction | 0.324405 | 3/3 | 0 | 1 | 0.324405 | 3 / 0.159802 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | protocol_failure_rate | fraction | 0.654646 | 3/3 | 0 | 1 | 0.654646 | 3 / 0.304891 |
| poolact | tuning | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | budget_utilization | fraction | 0.463469 | 9/9 | 0 | 3 | 0.463469 | 3 / 0.220204 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | budget_utilization | fraction | 0.463469 | 9/9 | 0 | 3 | 0.463469 | 3 / 0.220204 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | budget_utilization | fraction | 0.559585 | 3/3 | 0 | 1 | 0.559585 | 3 / 0.145993 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | budget_utilization | fraction | 0.496797 | 3/3 | 0 | 1 | 0.496797 | 3 / 0.228619 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | budget_utilization | fraction | 0.334025 | 3/3 | 0 | 1 | 0.334025 | 3 / 0.299903 |
| poolact | tuning | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.19245 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.19245 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | duplicate_action_attempts | count | 0.666667 | 3/3 | 0 | 1 | 0.666667 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_attempts | count | 6.77778 | 9/9 | 0 | 3 | 6.77778 | 3 / 3.42107 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_attempts | count | 6.77778 | 9/9 | 0 | 3 | 6.77778 | 3 / 3.42107 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_attempts | count | 5.66667 | 3/3 | 0 | 1 | 5.66667 | 3 / 1.52753 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_attempts | count | 7 | 3/3 | 0 | 1 | 7 | 3 / 4.58258 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_attempts | count | 7.66667 | 3/3 | 0 | 1 | 7.66667 | 3 / 4.93288 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 46509.3 | 9/9 | 0 | 3 | 46509.3 | 3 / 25388.9 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_cost_seconds | seconds | 46509.3 | 9/9 | 0 | 3 | 46509.3 | 3 / 25388.9 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_cost_seconds | seconds | 33200.1 | 3/3 | 0 | 1 | 33200.1 | 3 / 8661.73 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_cost_seconds | seconds | 61419.4 | 3/3 | 0 | 1 | 61419.4 | 3 / 28264.4 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_cost_seconds | seconds | 44908.4 | 3/3 | 0 | 1 | 44908.4 | 3 / 40320.8 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | input_tokens | tokens | 238966 | 9/9 | 0 | 3 | 238966 | 3 / 130182 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | input_tokens | tokens | 238966 | 9/9 | 0 | 3 | 238966 | 3 / 130182 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | input_tokens | tokens | 247889 | 3/3 | 0 | 1 | 247889 | 3 / 225674 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | input_tokens | tokens | 216200 | 3/3 | 0 | 1 | 216200 | 3 / 164758 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | input_tokens | tokens | 252809 | 3/3 | 0 | 1 | 252809 | 3 / 50498.2 |
| poolact | tuning | all/all | cost_tight | poolact | output_tokens | tokens | 89996.3 | 9/9 | 0 | 3 | 89996.3 | 3 / 31485.4 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | output_tokens | tokens | 89996.3 | 9/9 | 0 | 3 | 89996.3 | 3 / 31485.4 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | output_tokens | tokens | 97419 | 3/3 | 0 | 1 | 97419 | 3 / 107028 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | output_tokens | tokens | 56994.3 | 3/3 | 0 | 1 | 56994.3 | 3 / 24110.6 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | output_tokens | tokens | 115576 | 3/3 | 0 | 1 | 115576 | 3 / 88984.2 |
| poolact | tuning | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.465028 | 9/9 | 0 | 3 | 0.465028 | 3 / 0.126787 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | protocol_failure_rate | fraction | 0.465028 | 9/9 | 0 | 3 | 0.465028 | 3 / 0.126787 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | protocol_failure_rate | fraction | 0.478023 | 3/3 | 0 | 1 | 0.478023 | 3 / 0.145952 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | protocol_failure_rate | fraction | 0.41645 | 3/3 | 0 | 1 | 0.41645 | 3 / 0.163664 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | protocol_failure_rate | fraction | 0.500611 | 3/3 | 0 | 1 | 0.500611 | 3 / 0.167713 |
| poolact | tuning | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |


## 资源：全部差值

资源差值只描述消耗变化；正负不能单独解释为性能改善。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.128205 | count | 不适用 | 13/13 | 0 | 0.128205 |
| expgym | evidence_audit | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.128205 | count | 不适用 | 13/13 | 0 | 0.128205 |
| expgym | evidence_audit | family/evidence_audit | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.128205 | count | 不适用 | 13/13 | 0 | 0.128205 |
| expgym | evidence_audit | family/evidence_audit | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.128205 | count | 不适用 | 13/13 | 0 | 0.128205 |
| expgym | evidence_audit | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +13.3846 | count | 不适用 | 13/13 | 0 | 13.3846 |
| expgym | evidence_audit | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +20.1282 | count | 不适用 | 13/13 | 0 | 20.1282 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_attempts | cost_free − cost_moderate | +13.3846 | count | 不适用 | 13/13 | 0 | 13.3846 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_attempts | cost_free − cost_tight | +20.1282 | count | 不适用 | 13/13 | 0 | 20.1282 |
| expgym | evidence_audit | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +4010.61 | seconds | 不适用 | 13/13 | 0 | 4010.61 |
| expgym | evidence_audit | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +6028.65 | seconds | 不适用 | 13/13 | 0 | 6028.65 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +4010.61 | seconds | 不适用 | 13/13 | 0 | 4010.61 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_cost_seconds | cost_free − cost_tight | +6028.65 | seconds | 不适用 | 13/13 | 0 | 6028.65 |
| expgym | evidence_audit | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +13.9487 | count | 不适用 | 13/13 | 0 | 13.9487 |
| expgym | evidence_audit | all/all | cost_free | feedback_visible | cost_free − cost_tight | +20.7949 | count | 不适用 | 13/13 | 0 | 20.7949 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_visible | cost_free − cost_moderate | +13.9487 | count | 不适用 | 13/13 | 0 | 13.9487 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_visible | cost_free − cost_tight | +20.7949 | count | 不适用 | 13/13 | 0 | 20.7949 |
| expgym | evidence_audit | all/all | cost_free | input_tokens | cost_free − cost_moderate | +229004 | tokens | 不适用 | 13/13 | 0 | 229004 |
| expgym | evidence_audit | all/all | cost_free | input_tokens | cost_free − cost_tight | +321479 | tokens | 不适用 | 13/13 | 0 | 321479 |
| expgym | evidence_audit | family/evidence_audit | cost_free | input_tokens | cost_free − cost_moderate | +229004 | tokens | 不适用 | 13/13 | 0 | 229004 |
| expgym | evidence_audit | family/evidence_audit | cost_free | input_tokens | cost_free − cost_tight | +321479 | tokens | 不适用 | 13/13 | 0 | 321479 |
| expgym | evidence_audit | all/all | cost_free | output_tokens | cost_free − cost_moderate | +3400.79 | tokens | 不适用 | 13/13 | 0 | 3400.79 |
| expgym | evidence_audit | all/all | cost_free | output_tokens | cost_free − cost_tight | +4928.87 | tokens | 不适用 | 13/13 | 0 | 4928.87 |
| expgym | evidence_audit | family/evidence_audit | cost_free | output_tokens | cost_free − cost_moderate | +3400.79 | tokens | 不适用 | 13/13 | 0 | 3400.79 |
| expgym | evidence_audit | family/evidence_audit | cost_free | output_tokens | cost_free − cost_tight | +4928.87 | tokens | 不适用 | 13/13 | 0 | 4928.87 |
| expgym | evidence_audit | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0134978 | fraction | +1.34978 | 13/13 | 0 | 0.0134978 |
| expgym | evidence_audit | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0698314 | fraction | -6.98314 | 13/13 | 0 | -0.0698314 |
| expgym | evidence_audit | family/evidence_audit | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0134978 | fraction | +1.34978 | 13/13 | 0 | 0.0134978 |
| expgym | evidence_audit | family/evidence_audit | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0698314 | fraction | -6.98314 | 13/13 | 0 | -0.0698314 |
| expgym | evidence_audit | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +49.483 | seconds | 不适用 | 13/13 | 0 | 49.483 |
| expgym | evidence_audit | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +66.1845 | seconds | 不适用 | 13/13 | 0 | 66.1845 |
| expgym | evidence_audit | family/evidence_audit | cost_free | wall_time_seconds | cost_free − cost_moderate | +49.483 | seconds | 不适用 | 13/13 | 0 | 49.483 |
| expgym | evidence_audit | family/evidence_audit | cost_free | wall_time_seconds | cost_free − cost_tight | +66.1845 | seconds | 不适用 | 13/13 | 0 | 66.1845 |
| expgym | evidence_audit | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0166907 | fraction | -1.66907 | 13/13 | 0 | -0.0166907 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0166907 | fraction | -1.66907 | 13/13 | 0 | -0.0166907 |
| expgym | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 13/13 | 0 | 0 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 13/13 | 0 | 0 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.74359 | count | 不适用 | 13/13 | 0 | 6.74359 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.74359 | count | 不适用 | 13/13 | 0 | 6.74359 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +2018.03 | seconds | 不适用 | 13/13 | 0 | 2018.03 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +2018.03 | seconds | 不适用 | 13/13 | 0 | 2018.03 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.84615 | count | 不适用 | 13/13 | 0 | 6.84615 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.84615 | count | 不适用 | 13/13 | 0 | 6.84615 |
| expgym | evidence_audit | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +92474.9 | tokens | 不适用 | 13/13 | 0 | 92474.9 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | cost_moderate − cost_tight | +92474.9 | tokens | 不适用 | 13/13 | 0 | 92474.9 |
| expgym | evidence_audit | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +1528.08 | tokens | 不适用 | 13/13 | 0 | 1528.08 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | cost_moderate − cost_tight | +1528.08 | tokens | 不适用 | 13/13 | 0 | 1528.08 |
| expgym | evidence_audit | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0833293 | fraction | -8.33293 | 13/13 | 0 | -0.0833293 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0833293 | fraction | -8.33293 | 13/13 | 0 | -0.0833293 |
| expgym | evidence_audit | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +16.7015 | seconds | 不适用 | 13/13 | 0 | 16.7015 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +16.7015 | seconds | 不适用 | 13/13 | 0 | 16.7015 |
| expgym | restricted_search | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.0136986 | count | 不适用 | 73/73 | 0 | -0.0136986 |
| expgym | restricted_search | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.0136986 | count | 不适用 | 73/73 | 0 | 0.0136986 |
| expgym | restricted_search | family/whatis | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.0294118 | count | 不适用 | 34/34 | 0 | 0.0294118 |
| expgym | restricted_search | family/whatis | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 34/34 | 0 | 0 |
| expgym | restricted_search | family/whois | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.0512821 | count | 不适用 | 39/39 | 0 | -0.0512821 |
| expgym | restricted_search | family/whois | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.025641 | count | 不适用 | 39/39 | 0 | 0.025641 |
| expgym | restricted_search | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +4.75342 | count | 不适用 | 73/73 | 0 | 4.75342 |
| expgym | restricted_search | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +12.9041 | count | 不适用 | 73/73 | 0 | 12.9041 |
| expgym | restricted_search | family/whatis | cost_free | feedback_attempts | cost_free − cost_moderate | +5.02941 | count | 不适用 | 34/34 | 0 | 5.02941 |
| expgym | restricted_search | family/whatis | cost_free | feedback_attempts | cost_free − cost_tight | +12.7941 | count | 不适用 | 34/34 | 0 | 12.7941 |
| expgym | restricted_search | family/whois | cost_free | feedback_attempts | cost_free − cost_moderate | +4.51282 | count | 不适用 | 39/39 | 0 | 4.51282 |
| expgym | restricted_search | family/whois | cost_free | feedback_attempts | cost_free − cost_tight | +13 | count | 不适用 | 39/39 | 0 | 13 |
| expgym | restricted_search | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +819.362 | seconds | 不适用 | 73/73 | 0 | 819.362 |
| expgym | restricted_search | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2323.51 | seconds | 不适用 | 73/73 | 0 | 2323.51 |
| expgym | restricted_search | family/whatis | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +748.241 | seconds | 不适用 | 34/34 | 0 | 748.241 |
| expgym | restricted_search | family/whatis | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2246.47 | seconds | 不适用 | 34/34 | 0 | 2246.47 |
| expgym | restricted_search | family/whois | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +881.366 | seconds | 不适用 | 39/39 | 0 | 881.366 |
| expgym | restricted_search | family/whois | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2390.67 | seconds | 不适用 | 39/39 | 0 | 2390.67 |
| expgym | restricted_search | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +5.27397 | count | 不适用 | 73/73 | 0 | 5.27397 |
| expgym | restricted_search | all/all | cost_free | feedback_visible | cost_free − cost_tight | +13.8082 | count | 不适用 | 73/73 | 0 | 13.8082 |
| expgym | restricted_search | family/whatis | cost_free | feedback_visible | cost_free − cost_moderate | +5.52941 | count | 不适用 | 34/34 | 0 | 5.52941 |
| expgym | restricted_search | family/whatis | cost_free | feedback_visible | cost_free − cost_tight | +13.6176 | count | 不适用 | 34/34 | 0 | 13.6176 |
| expgym | restricted_search | family/whois | cost_free | feedback_visible | cost_free − cost_moderate | +5.05128 | count | 不适用 | 39/39 | 0 | 5.05128 |
| expgym | restricted_search | family/whois | cost_free | feedback_visible | cost_free − cost_tight | +13.9744 | count | 不适用 | 39/39 | 0 | 13.9744 |
| expgym | restricted_search | all/all | cost_free | input_tokens | cost_free − cost_moderate | +62962.9 | tokens | 不适用 | 73/73 | 0 | 62962.9 |
| expgym | restricted_search | all/all | cost_free | input_tokens | cost_free − cost_tight | +119507 | tokens | 不适用 | 73/73 | 0 | 119507 |
| expgym | restricted_search | family/whatis | cost_free | input_tokens | cost_free − cost_moderate | +65131.9 | tokens | 不适用 | 34/34 | 0 | 65131.9 |
| expgym | restricted_search | family/whatis | cost_free | input_tokens | cost_free − cost_tight | +118457 | tokens | 不适用 | 34/34 | 0 | 118457 |
| expgym | restricted_search | family/whois | cost_free | input_tokens | cost_free − cost_moderate | +61071.9 | tokens | 不适用 | 39/39 | 0 | 61071.9 |
| expgym | restricted_search | family/whois | cost_free | input_tokens | cost_free − cost_tight | +120423 | tokens | 不适用 | 39/39 | 0 | 120423 |
| expgym | restricted_search | all/all | cost_free | output_tokens | cost_free − cost_moderate | +228.644 | tokens | 不适用 | 73/73 | 0 | 228.644 |
| expgym | restricted_search | all/all | cost_free | output_tokens | cost_free − cost_tight | +3336.66 | tokens | 不适用 | 73/73 | 0 | 3336.66 |
| expgym | restricted_search | family/whatis | cost_free | output_tokens | cost_free − cost_moderate | -1539.21 | tokens | 不适用 | 34/34 | 0 | -1539.21 |
| expgym | restricted_search | family/whatis | cost_free | output_tokens | cost_free − cost_tight | +4414.15 | tokens | 不适用 | 34/34 | 0 | 4414.15 |
| expgym | restricted_search | family/whois | cost_free | output_tokens | cost_free − cost_moderate | +1769.85 | tokens | 不适用 | 39/39 | 0 | 1769.85 |
| expgym | restricted_search | family/whois | cost_free | output_tokens | cost_free − cost_tight | +2397.31 | tokens | 不适用 | 39/39 | 0 | 2397.31 |
| expgym | restricted_search | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0132337 | fraction | -1.32337 | 73/73 | 0 | -0.0132337 |
| expgym | restricted_search | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.058074 | fraction | -5.8074 | 73/73 | 0 | -0.058074 |
| expgym | restricted_search | family/whatis | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0178815 | fraction | -1.78815 | 34/34 | 0 | -0.0178815 |
| expgym | restricted_search | family/whatis | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0784592 | fraction | -7.84592 | 34/34 | 0 | -0.0784592 |
| expgym | restricted_search | family/whois | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.00918187 | fraction | -0.918187 | 39/39 | 0 | -0.00918187 |
| expgym | restricted_search | family/whois | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0403023 | fraction | -4.03023 | 39/39 | 0 | -0.0403023 |
| expgym | restricted_search | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +6.6218 | seconds | 不适用 | 73/73 | 0 | 6.6218 |
| expgym | restricted_search | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +45.126 | seconds | 不适用 | 73/73 | 0 | 45.126 |
| expgym | restricted_search | family/whatis | cost_free | wall_time_seconds | cost_free − cost_moderate | -9.74134 | seconds | 不适用 | 34/34 | 0 | -9.74134 |
| expgym | restricted_search | family/whatis | cost_free | wall_time_seconds | cost_free − cost_tight | +57.3036 | seconds | 不适用 | 34/34 | 0 | 57.3036 |
| expgym | restricted_search | family/whois | cost_free | wall_time_seconds | cost_free − cost_moderate | +20.8871 | seconds | 不适用 | 39/39 | 0 | 20.8871 |
| expgym | restricted_search | family/whois | cost_free | wall_time_seconds | cost_free − cost_tight | +34.5096 | seconds | 不适用 | 39/39 | 0 | 34.5096 |
| expgym | restricted_search | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.326333 | fraction | -32.6333 | 73/73 | 0 | -0.326333 |
| expgym | restricted_search | family/whatis | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.314999 | fraction | -31.4999 | 34/34 | 0 | -0.314999 |
| expgym | restricted_search | family/whois | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.336214 | fraction | -33.6214 | 39/39 | 0 | -0.336214 |
| expgym | restricted_search | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.0273973 | count | 不适用 | 73/73 | 0 | 0.0273973 |
| expgym | restricted_search | family/whatis | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | -0.0294118 | count | 不适用 | 34/34 | 0 | -0.0294118 |
| expgym | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.0769231 | count | 不适用 | 39/39 | 0 | 0.0769231 |
| expgym | restricted_search | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.15068 | count | 不适用 | 73/73 | 0 | 8.15068 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +7.76471 | count | 不适用 | 34/34 | 0 | 7.76471 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.48718 | count | 不适用 | 39/39 | 0 | 8.48718 |
| expgym | restricted_search | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1504.15 | seconds | 不适用 | 73/73 | 0 | 1504.15 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1498.23 | seconds | 不适用 | 34/34 | 0 | 1498.23 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1509.3 | seconds | 不适用 | 39/39 | 0 | 1509.3 |
| expgym | restricted_search | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.53425 | count | 不适用 | 73/73 | 0 | 8.53425 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.08824 | count | 不适用 | 34/34 | 0 | 8.08824 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.92308 | count | 不适用 | 39/39 | 0 | 8.92308 |
| expgym | restricted_search | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +56544.5 | tokens | 不适用 | 73/73 | 0 | 56544.5 |
| expgym | restricted_search | family/whatis | cost_moderate | input_tokens | cost_moderate − cost_tight | +53325.1 | tokens | 不适用 | 34/34 | 0 | 53325.1 |
| expgym | restricted_search | family/whois | cost_moderate | input_tokens | cost_moderate − cost_tight | +59351.2 | tokens | 不适用 | 39/39 | 0 | 59351.2 |
| expgym | restricted_search | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +3108.01 | tokens | 不适用 | 73/73 | 0 | 3108.01 |
| expgym | restricted_search | family/whatis | cost_moderate | output_tokens | cost_moderate − cost_tight | +5953.35 | tokens | 不适用 | 34/34 | 0 | 5953.35 |
| expgym | restricted_search | family/whois | cost_moderate | output_tokens | cost_moderate − cost_tight | +627.462 | tokens | 不适用 | 39/39 | 0 | 627.462 |
| expgym | restricted_search | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0448403 | fraction | -4.48403 | 73/73 | 0 | -0.0448403 |
| expgym | restricted_search | family/whatis | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0605777 | fraction | -6.05777 | 34/34 | 0 | -0.0605777 |
| expgym | restricted_search | family/whois | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0311204 | fraction | -3.11204 | 39/39 | 0 | -0.0311204 |
| expgym | restricted_search | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +38.5042 | seconds | 不适用 | 73/73 | 0 | 38.5042 |
| expgym | restricted_search | family/whatis | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +67.0449 | seconds | 不适用 | 34/34 | 0 | 67.0449 |
| expgym | restricted_search | family/whois | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +13.6225 | seconds | 不适用 | 39/39 | 0 | 13.6225 |
| expgym | tuning | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 27/27 | 0 | 0 |
| expgym | tuning | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.037037 | count | 不适用 | 27/27 | 0 | 0.037037 |
| expgym | tuning | family/nasbench101 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/nasbench101 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/nasbench201 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.111111 | count | 不适用 | 9/9 | 0 | -0.111111 |
| expgym | tuning | family/nasbench201 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | family/paramnet | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | family/paramnet | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +6.66667 | count | 不适用 | 27/27 | 0 | 6.66667 |
| expgym | tuning | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +12.3333 | count | 不适用 | 27/27 | 0 | 12.3333 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_attempts | cost_free − cost_moderate | +8.66667 | count | 不适用 | 9/9 | 0 | 8.66667 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_attempts | cost_free − cost_tight | +12.5556 | count | 不适用 | 9/9 | 0 | 12.5556 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_attempts | cost_free − cost_moderate | +7.55556 | count | 不适用 | 9/9 | 0 | 7.55556 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_attempts | cost_free − cost_tight | +16.1111 | count | 不适用 | 9/9 | 0 | 16.1111 |
| expgym | tuning | family/paramnet | cost_free | feedback_attempts | cost_free − cost_moderate | +3.77778 | count | 不适用 | 9/9 | 0 | 3.77778 |
| expgym | tuning | family/paramnet | cost_free | feedback_attempts | cost_free − cost_tight | +8.33333 | count | 不适用 | 9/9 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_attempts | cost_free − cost_moderate | +10.6667 | count | 不适用 | 3/3 | 0 | 10.6667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_attempts | cost_free − cost_tight | +10.6667 | count | 不适用 | 3/3 | 0 | 10.6667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_attempts | cost_free − cost_moderate | +16 | count | 不适用 | 3/3 | 0 | 16 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_attempts | cost_free − cost_tight | +18.6667 | count | 不适用 | 3/3 | 0 | 18.6667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_attempts | cost_free − cost_moderate | -0.666667 | count | 不适用 | 3/3 | 0 | -0.666667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_attempts | cost_free − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_attempts | cost_free − cost_moderate | +3.33333 | count | 不适用 | 3/3 | 0 | 3.33333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_attempts | cost_free − cost_tight | +12 | count | 不适用 | 3/3 | 0 | 12 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_attempts | cost_free − cost_moderate | +7 | count | 不适用 | 3/3 | 0 | 7 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_attempts | cost_free − cost_tight | +15.6667 | count | 不适用 | 3/3 | 0 | 15.6667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_attempts | cost_free − cost_moderate | +12.3333 | count | 不适用 | 3/3 | 0 | 12.3333 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_attempts | cost_free − cost_tight | +20.6667 | count | 不适用 | 3/3 | 0 | 20.6667 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +1.66667 | count | 不适用 | 3/3 | 0 | 1.66667 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_attempts | cost_free − cost_tight | +4 | count | 不适用 | 3/3 | 0 | 4 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_attempts | cost_free − cost_tight | +9.33333 | count | 不适用 | 3/3 | 0 | 9.33333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +7.33333 | count | 不适用 | 3/3 | 0 | 7.33333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_attempts | cost_free − cost_tight | +11.6667 | count | 不适用 | 3/3 | 0 | 11.6667 |
| expgym | tuning | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +107043 | seconds | 不适用 | 27/27 | 0 | 107043 |
| expgym | tuning | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +182269 | seconds | 不适用 | 27/27 | 0 | 182269 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +68281.6 | seconds | 不适用 | 9/9 | 0 | 68281.6 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +102707 | seconds | 不适用 | 9/9 | 0 | 102707 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +250663 | seconds | 不适用 | 9/9 | 0 | 250663 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +441383 | seconds | 不适用 | 9/9 | 0 | 441383 |
| expgym | tuning | family/paramnet | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +2182.99 | seconds | 不适用 | 9/9 | 0 | 2182.99 |
| expgym | tuning | family/paramnet | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2716.27 | seconds | 不适用 | 9/9 | 0 | 2716.27 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +42236 | seconds | 不适用 | 3/3 | 0 | 42236 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_cost_seconds | cost_free − cost_tight | +64813 | seconds | 不适用 | 3/3 | 0 | 64813 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +129943 | seconds | 不适用 | 3/3 | 0 | 129943 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_cost_seconds | cost_free − cost_tight | +173876 | seconds | 不适用 | 3/3 | 0 | 173876 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +32665.5 | seconds | 不适用 | 3/3 | 0 | 32665.5 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_cost_seconds | cost_free − cost_tight | +69433.4 | seconds | 不适用 | 3/3 | 0 | 69433.4 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +44381.2 | seconds | 不适用 | 3/3 | 0 | 44381.2 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_cost_seconds | cost_free − cost_tight | +126933 | seconds | 不适用 | 3/3 | 0 | 126933 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +106776 | seconds | 不适用 | 3/3 | 0 | 106776 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +242803 | seconds | 不适用 | 3/3 | 0 | 242803 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +600832 | seconds | 不适用 | 3/3 | 0 | 600832 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +954413 | seconds | 不适用 | 3/3 | 0 | 954413 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +557.183 | seconds | 不适用 | 3/3 | 0 | 557.183 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +707.372 | seconds | 不适用 | 3/3 | 0 | 707.372 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +5075.84 | seconds | 不适用 | 3/3 | 0 | 5075.84 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +6189.82 | seconds | 不适用 | 3/3 | 0 | 6189.82 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +915.953 | seconds | 不适用 | 3/3 | 0 | 915.953 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +1251.63 | seconds | 不适用 | 3/3 | 0 | 1251.63 |
| expgym | tuning | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +7.03704 | count | 不适用 | 27/27 | 0 | 7.03704 |
| expgym | tuning | all/all | cost_free | feedback_visible | cost_free − cost_tight | +12.7778 | count | 不适用 | 27/27 | 0 | 12.7778 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_visible | cost_free − cost_moderate | +9 | count | 不适用 | 9/9 | 0 | 9 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_visible | cost_free − cost_tight | +12.8889 | count | 不适用 | 9/9 | 0 | 12.8889 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_visible | cost_free − cost_moderate | +8.33333 | count | 不适用 | 9/9 | 0 | 8.33333 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_visible | cost_free − cost_tight | +16.7778 | count | 不适用 | 9/9 | 0 | 16.7778 |
| expgym | tuning | family/paramnet | cost_free | feedback_visible | cost_free − cost_moderate | +3.77778 | count | 不适用 | 9/9 | 0 | 3.77778 |
| expgym | tuning | family/paramnet | cost_free | feedback_visible | cost_free − cost_tight | +8.66667 | count | 不适用 | 9/9 | 0 | 8.66667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_visible | cost_free − cost_moderate | +11.3333 | count | 不适用 | 3/3 | 0 | 11.3333 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_visible | cost_free − cost_tight | +11 | count | 不适用 | 3/3 | 0 | 11 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_visible | cost_free − cost_moderate | +16.3333 | count | 不适用 | 3/3 | 0 | 16.3333 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_visible | cost_free − cost_tight | +18.6667 | count | 不适用 | 3/3 | 0 | 18.6667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_visible | cost_free − cost_moderate | -0.666667 | count | 不适用 | 3/3 | 0 | -0.666667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_visible | cost_free − cost_tight | +9 | count | 不适用 | 3/3 | 0 | 9 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_visible | cost_free − cost_moderate | +4 | count | 不适用 | 3/3 | 0 | 4 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_visible | cost_free − cost_tight | +12.3333 | count | 不适用 | 3/3 | 0 | 12.3333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_visible | cost_free − cost_moderate | +8 | count | 不适用 | 3/3 | 0 | 8 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_visible | cost_free − cost_tight | +16.6667 | count | 不适用 | 3/3 | 0 | 16.6667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_visible | cost_free − cost_moderate | +13 | count | 不适用 | 3/3 | 0 | 13 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_visible | cost_free − cost_tight | +21.3333 | count | 不适用 | 3/3 | 0 | 21.3333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_visible | cost_free − cost_moderate | +1.66667 | count | 不适用 | 3/3 | 0 | 1.66667 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_visible | cost_free − cost_tight | +4.66667 | count | 不适用 | 3/3 | 0 | 4.66667 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_visible | cost_free − cost_moderate | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_visible | cost_free − cost_tight | +9.66667 | count | 不适用 | 3/3 | 0 | 9.66667 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_visible | cost_free − cost_moderate | +7.33333 | count | 不适用 | 3/3 | 0 | 7.33333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_visible | cost_free − cost_tight | +11.6667 | count | 不适用 | 3/3 | 0 | 11.6667 |
| expgym | tuning | all/all | cost_free | input_tokens | cost_free − cost_moderate | +74343.7 | tokens | 不适用 | 27/27 | 0 | 74343.7 |
| expgym | tuning | all/all | cost_free | input_tokens | cost_free − cost_tight | +123849 | tokens | 不适用 | 27/27 | 0 | 123849 |
| expgym | tuning | family/nasbench101 | cost_free | input_tokens | cost_free − cost_moderate | +136155 | tokens | 不适用 | 9/9 | 0 | 136155 |
| expgym | tuning | family/nasbench101 | cost_free | input_tokens | cost_free − cost_tight | +207846 | tokens | 不适用 | 9/9 | 0 | 207846 |
| expgym | tuning | family/nasbench201 | cost_free | input_tokens | cost_free − cost_moderate | +66315 | tokens | 不适用 | 9/9 | 0 | 66315 |
| expgym | tuning | family/nasbench201 | cost_free | input_tokens | cost_free − cost_tight | +108569 | tokens | 不适用 | 9/9 | 0 | 108569 |
| expgym | tuning | family/paramnet | cost_free | input_tokens | cost_free − cost_moderate | +20561 | tokens | 不适用 | 9/9 | 0 | 20561 |
| expgym | tuning | family/paramnet | cost_free | input_tokens | cost_free − cost_tight | +55132.1 | tokens | 不适用 | 9/9 | 0 | 55132.1 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | input_tokens | cost_free − cost_moderate | +169890 | tokens | 不适用 | 3/3 | 0 | 169890 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | input_tokens | cost_free − cost_tight | +179471 | tokens | 不适用 | 3/3 | 0 | 179471 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | input_tokens | cost_free − cost_moderate | +228194 | tokens | 不适用 | 3/3 | 0 | 228194 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | input_tokens | cost_free − cost_tight | +278923 | tokens | 不适用 | 3/3 | 0 | 278923 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | input_tokens | cost_free − cost_moderate | +10382 | tokens | 不适用 | 3/3 | 0 | 10382 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | input_tokens | cost_free − cost_tight | +165144 | tokens | 不适用 | 3/3 | 0 | 165144 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | input_tokens | cost_free − cost_moderate | +24625.3 | tokens | 不适用 | 3/3 | 0 | 24625.3 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | input_tokens | cost_free − cost_tight | +71919.3 | tokens | 不适用 | 3/3 | 0 | 71919.3 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | input_tokens | cost_free − cost_moderate | +64778.7 | tokens | 不适用 | 3/3 | 0 | 64778.7 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | input_tokens | cost_free − cost_tight | +100073 | tokens | 不适用 | 3/3 | 0 | 100073 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | input_tokens | cost_free − cost_moderate | +109541 | tokens | 不适用 | 3/3 | 0 | 109541 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | input_tokens | cost_free − cost_tight | +153714 | tokens | 不适用 | 3/3 | 0 | 153714 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | input_tokens | cost_free − cost_moderate | +5618.67 | tokens | 不适用 | 3/3 | 0 | 5618.67 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | input_tokens | cost_free − cost_tight | +17301.3 | tokens | 不适用 | 3/3 | 0 | 17301.3 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | input_tokens | cost_free − cost_moderate | +12131.7 | tokens | 不适用 | 3/3 | 0 | 12131.7 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | input_tokens | cost_free − cost_tight | +63444 | tokens | 不适用 | 3/3 | 0 | 63444 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | input_tokens | cost_free − cost_moderate | +43932.7 | tokens | 不适用 | 3/3 | 0 | 43932.7 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | input_tokens | cost_free − cost_tight | +84651 | tokens | 不适用 | 3/3 | 0 | 84651 |
| expgym | tuning | all/all | cost_free | output_tokens | cost_free − cost_moderate | +3027.81 | tokens | 不适用 | 27/27 | 0 | 3027.81 |
| expgym | tuning | all/all | cost_free | output_tokens | cost_free − cost_tight | +6710.48 | tokens | 不适用 | 27/27 | 0 | 6710.48 |
| expgym | tuning | family/nasbench101 | cost_free | output_tokens | cost_free − cost_moderate | +7002 | tokens | 不适用 | 9/9 | 0 | 7002 |
| expgym | tuning | family/nasbench101 | cost_free | output_tokens | cost_free − cost_tight | +15640.7 | tokens | 不适用 | 9/9 | 0 | 15640.7 |
| expgym | tuning | family/nasbench201 | cost_free | output_tokens | cost_free − cost_moderate | +4173.44 | tokens | 不适用 | 9/9 | 0 | 4173.44 |
| expgym | tuning | family/nasbench201 | cost_free | output_tokens | cost_free − cost_tight | +6039.78 | tokens | 不适用 | 9/9 | 0 | 6039.78 |
| expgym | tuning | family/paramnet | cost_free | output_tokens | cost_free − cost_moderate | -2092 | tokens | 不适用 | 9/9 | 0 | -2092 |
| expgym | tuning | family/paramnet | cost_free | output_tokens | cost_free − cost_tight | -1549 | tokens | 不适用 | 9/9 | 0 | -1549 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | output_tokens | cost_free − cost_moderate | +9944.67 | tokens | 不适用 | 3/3 | 0 | 9944.67 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | output_tokens | cost_free − cost_tight | +19890.3 | tokens | 不适用 | 3/3 | 0 | 19890.3 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | output_tokens | cost_free − cost_moderate | +11414.3 | tokens | 不适用 | 3/3 | 0 | 11414.3 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | output_tokens | cost_free − cost_tight | +18371.7 | tokens | 不适用 | 3/3 | 0 | 18371.7 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | output_tokens | cost_free − cost_moderate | -353 | tokens | 不适用 | 3/3 | 0 | -353 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | output_tokens | cost_free − cost_tight | +8660 | tokens | 不适用 | 3/3 | 0 | 8660 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | output_tokens | cost_free − cost_moderate | +8914.67 | tokens | 不适用 | 3/3 | 0 | 8914.67 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | output_tokens | cost_free − cost_tight | +12527.3 | tokens | 不适用 | 3/3 | 0 | 12527.3 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | output_tokens | cost_free − cost_moderate | +1898 | tokens | 不适用 | 3/3 | 0 | 1898 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | output_tokens | cost_free − cost_tight | +1290.67 | tokens | 不适用 | 3/3 | 0 | 1290.67 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | output_tokens | cost_free − cost_moderate | +1707.67 | tokens | 不适用 | 3/3 | 0 | 1707.67 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | output_tokens | cost_free − cost_tight | +4301.33 | tokens | 不适用 | 3/3 | 0 | 4301.33 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | output_tokens | cost_free − cost_moderate | -4489.67 | tokens | 不适用 | 3/3 | 0 | -4489.67 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | output_tokens | cost_free − cost_tight | -6338 | tokens | 不适用 | 3/3 | 0 | -6338 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | output_tokens | cost_free − cost_moderate | -124.333 | tokens | 不适用 | 3/3 | 0 | -124.333 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | output_tokens | cost_free − cost_tight | +3370 | tokens | 不适用 | 3/3 | 0 | 3370 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | output_tokens | cost_free − cost_moderate | -1662 | tokens | 不适用 | 3/3 | 0 | -1662 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | output_tokens | cost_free − cost_tight | -1679 | tokens | 不适用 | 3/3 | 0 | -1679 |
| expgym | tuning | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0316029 | fraction | +3.16029 | 27/27 | 0 | 0.0316029 |
| expgym | tuning | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.080162 | fraction | -8.0162 | 27/27 | 0 | -0.080162 |
| expgym | tuning | family/nasbench101 | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0255617 | fraction | +2.55617 | 9/9 | 0 | 0.0255617 |
| expgym | tuning | family/nasbench101 | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.150357 | fraction | -15.0357 | 9/9 | 0 | -0.150357 |
| expgym | tuning | family/nasbench201 | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0269895 | fraction | +2.69895 | 9/9 | 0 | 0.0269895 |
| expgym | tuning | family/nasbench201 | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0581804 | fraction | -5.81804 | 9/9 | 0 | -0.0581804 |
| expgym | tuning | family/paramnet | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0422576 | fraction | +4.22576 | 9/9 | 0 | 0.0422576 |
| expgym | tuning | family/paramnet | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0319481 | fraction | -3.19481 | 9/9 | 0 | -0.0319481 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0197095 | fraction | -1.97095 | 3/3 | 0 | -0.0197095 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.111376 | fraction | -11.1376 | 3/3 | 0 | -0.111376 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0176037 | fraction | -1.76037 | 3/3 | 0 | -0.0176037 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.273444 | fraction | -27.3444 | 3/3 | 0 | -0.273444 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.113998 | fraction | +11.3998 | 3/3 | 0 | 0.113998 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0662515 | fraction | -6.62515 | 3/3 | 0 | -0.0662515 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.105925 | fraction | +10.5925 | 3/3 | 0 | 0.105925 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.0200119 | fraction | +2.00119 | 3/3 | 0 | 0.0200119 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0106813 | fraction | +1.06813 | 3/3 | 0 | 0.0106813 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.097011 | fraction | -9.7011 | 3/3 | 0 | -0.097011 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0356375 | fraction | -3.56375 | 3/3 | 0 | -0.0356375 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0975422 | fraction | -9.75422 | 3/3 | 0 | -0.0975422 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.15406 | fraction | +15.406 | 3/3 | 0 | 0.15406 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0876068 | fraction | -8.76068 | 3/3 | 0 | -0.0876068 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.106516 | fraction | +10.6516 | 3/3 | 0 | 0.106516 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0512131 | fraction | -5.12131 | 3/3 | 0 | -0.0512131 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.133803 | fraction | -13.3803 | 3/3 | 0 | -0.133803 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.0429755 | fraction | +4.29755 | 3/3 | 0 | 0.0429755 |
| expgym | tuning | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +33.6758 | seconds | 不适用 | 27/27 | 0 | 33.6758 |
| expgym | tuning | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +79.3705 | seconds | 不适用 | 27/27 | 0 | 79.3705 |
| expgym | tuning | family/nasbench101 | cost_free | wall_time_seconds | cost_free − cost_moderate | +80.4284 | seconds | 不适用 | 9/9 | 0 | 80.4284 |
| expgym | tuning | family/nasbench101 | cost_free | wall_time_seconds | cost_free − cost_tight | +184.997 | seconds | 不适用 | 9/9 | 0 | 184.997 |
| expgym | tuning | family/nasbench201 | cost_free | wall_time_seconds | cost_free − cost_moderate | +48.4335 | seconds | 不适用 | 9/9 | 0 | 48.4335 |
| expgym | tuning | family/nasbench201 | cost_free | wall_time_seconds | cost_free − cost_tight | +71.1279 | seconds | 不适用 | 9/9 | 0 | 71.1279 |
| expgym | tuning | family/paramnet | cost_free | wall_time_seconds | cost_free − cost_moderate | -27.8346 | seconds | 不适用 | 9/9 | 0 | -27.8346 |
| expgym | tuning | family/paramnet | cost_free | wall_time_seconds | cost_free − cost_tight | -18.0135 | seconds | 不适用 | 9/9 | 0 | -18.0135 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | wall_time_seconds | cost_free − cost_moderate | +117.92 | seconds | 不适用 | 3/3 | 0 | 117.92 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | wall_time_seconds | cost_free − cost_tight | +240.701 | seconds | 不适用 | 3/3 | 0 | 240.701 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | wall_time_seconds | cost_free − cost_moderate | +131.459 | seconds | 不适用 | 3/3 | 0 | 131.459 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | wall_time_seconds | cost_free − cost_tight | +214.16 | seconds | 不适用 | 3/3 | 0 | 214.16 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | wall_time_seconds | cost_free − cost_moderate | -8.09348 | seconds | 不适用 | 3/3 | 0 | -8.09348 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | wall_time_seconds | cost_free − cost_tight | +100.131 | seconds | 不适用 | 3/3 | 0 | 100.131 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | wall_time_seconds | cost_free − cost_moderate | +104.291 | seconds | 不适用 | 3/3 | 0 | 104.291 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | wall_time_seconds | cost_free − cost_tight | +148.061 | seconds | 不适用 | 3/3 | 0 | 148.061 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | wall_time_seconds | cost_free − cost_moderate | +18.9823 | seconds | 不适用 | 3/3 | 0 | 18.9823 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | wall_time_seconds | cost_free − cost_tight | +15.3189 | seconds | 不适用 | 3/3 | 0 | 15.3189 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | wall_time_seconds | cost_free − cost_moderate | +22.0271 | seconds | 不适用 | 3/3 | 0 | 22.0271 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | wall_time_seconds | cost_free − cost_tight | +50.0042 | seconds | 不适用 | 3/3 | 0 | 50.0042 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | -57.6481 | seconds | 不适用 | 3/3 | 0 | -57.6481 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | wall_time_seconds | cost_free − cost_tight | -75.4407 | seconds | 不适用 | 3/3 | 0 | -75.4407 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | -2.77039 | seconds | 不适用 | 3/3 | 0 | -2.77039 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | wall_time_seconds | cost_free − cost_tight | +43.1278 | seconds | 不适用 | 3/3 | 0 | 43.1278 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | -23.0853 | seconds | 不适用 | 3/3 | 0 | -23.0853 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | wall_time_seconds | cost_free − cost_tight | -21.7277 | seconds | 不适用 | 3/3 | 0 | -21.7277 |
| expgym | tuning | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.133294 | fraction | -13.3294 | 27/27 | 0 | -0.133294 |
| expgym | tuning | family/nasbench101 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.162506 | fraction | -16.2506 | 9/9 | 0 | -0.162506 |
| expgym | tuning | family/nasbench201 | cost_moderate | budget_utilization | cost_moderate − cost_tight | +0.00654399 | fraction | +0.654399 | 9/9 | 0 | 0.00654399 |
| expgym | tuning | family/paramnet | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.24392 | fraction | -24.392 | 9/9 | 0 | -0.24392 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.28867 | fraction | -28.867 | 3/3 | 0 | -0.28867 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.00701594 | fraction | -0.701594 | 3/3 | 0 | -0.00701594 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.191832 | fraction | -19.1832 | 3/3 | 0 | -0.191832 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | budget_utilization | cost_moderate − cost_tight | +0.0482757 | fraction | +4.82757 | 3/3 | 0 | 0.0482757 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.000281519 | fraction | -0.0281519 | 3/3 | 0 | -0.000281519 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0283622 | fraction | -2.83622 | 3/3 | 0 | -0.0283622 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.37896 | fraction | -37.896 | 3/3 | 0 | -0.37896 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.00647197 | fraction | -0.647197 | 3/3 | 0 | -0.00647197 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.346327 | fraction | -34.6327 | 3/3 | 0 | -0.346327 |
| expgym | tuning | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.037037 | count | 不适用 | 27/27 | 0 | 0.037037 |
| expgym | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | family/nasbench201 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/paramnet | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +5.66667 | count | 不适用 | 27/27 | 0 | 5.66667 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +3.88889 | count | 不适用 | 9/9 | 0 | 3.88889 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.55556 | count | 不适用 | 9/9 | 0 | 8.55556 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +4.55556 | count | 不适用 | 9/9 | 0 | 4.55556 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +9 | count | 不适用 | 3/3 | 0 | 9 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.66667 | count | 不适用 | 3/3 | 0 | 8.66667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.66667 | count | 不适用 | 3/3 | 0 | 8.66667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +7 | count | 不适用 | 3/3 | 0 | 7 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +4.33333 | count | 不适用 | 3/3 | 0 | 4.33333 |
| expgym | tuning | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +75226.4 | seconds | 不适用 | 27/27 | 0 | 75226.4 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +34425.8 | seconds | 不适用 | 9/9 | 0 | 34425.8 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +190720 | seconds | 不适用 | 9/9 | 0 | 190720 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +533.281 | seconds | 不适用 | 9/9 | 0 | 533.281 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +22577 | seconds | 不适用 | 3/3 | 0 | 22577 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +43932.6 | seconds | 不适用 | 3/3 | 0 | 43932.6 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +36767.9 | seconds | 不适用 | 3/3 | 0 | 36767.9 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +82552.2 | seconds | 不适用 | 3/3 | 0 | 82552.2 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +136027 | seconds | 不适用 | 3/3 | 0 | 136027 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +353581 | seconds | 不适用 | 3/3 | 0 | 353581 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +150.189 | seconds | 不适用 | 3/3 | 0 | 150.189 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1113.98 | seconds | 不适用 | 3/3 | 0 | 1113.98 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +335.674 | seconds | 不适用 | 3/3 | 0 | 335.674 |
| expgym | tuning | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +5.74074 | count | 不适用 | 27/27 | 0 | 5.74074 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +3.88889 | count | 不适用 | 9/9 | 0 | 3.88889 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.44444 | count | 不适用 | 9/9 | 0 | 8.44444 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_visible | cost_moderate − cost_tight | +4.88889 | count | 不适用 | 9/9 | 0 | 4.88889 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | cost_moderate − cost_tight | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | cost_moderate − cost_tight | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | cost_moderate − cost_tight | +9.66667 | count | 不适用 | 3/3 | 0 | 9.66667 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.66667 | count | 不适用 | 3/3 | 0 | 8.66667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +3 | count | 不适用 | 3/3 | 0 | 3 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.33333 | count | 不适用 | 3/3 | 0 | 7.33333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +4.33333 | count | 不适用 | 3/3 | 0 | 4.33333 |
| expgym | tuning | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +49505.4 | tokens | 不适用 | 27/27 | 0 | 49505.4 |
| expgym | tuning | family/nasbench101 | cost_moderate | input_tokens | cost_moderate − cost_tight | +71691.2 | tokens | 不适用 | 9/9 | 0 | 71691.2 |
| expgym | tuning | family/nasbench201 | cost_moderate | input_tokens | cost_moderate − cost_tight | +42253.8 | tokens | 不适用 | 9/9 | 0 | 42253.8 |
| expgym | tuning | family/paramnet | cost_moderate | input_tokens | cost_moderate − cost_tight | +34571.1 | tokens | 不适用 | 9/9 | 0 | 34571.1 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | cost_moderate − cost_tight | +9581.67 | tokens | 不适用 | 3/3 | 0 | 9581.67 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | cost_moderate − cost_tight | +50729.7 | tokens | 不适用 | 3/3 | 0 | 50729.7 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | cost_moderate − cost_tight | +154762 | tokens | 不适用 | 3/3 | 0 | 154762 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | input_tokens | cost_moderate − cost_tight | +47294 | tokens | 不适用 | 3/3 | 0 | 47294 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | input_tokens | cost_moderate − cost_tight | +35294.3 | tokens | 不适用 | 3/3 | 0 | 35294.3 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | input_tokens | cost_moderate − cost_tight | +44173 | tokens | 不适用 | 3/3 | 0 | 44173 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +11682.7 | tokens | 不适用 | 3/3 | 0 | 11682.7 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +51312.3 | tokens | 不适用 | 3/3 | 0 | 51312.3 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +40718.3 | tokens | 不适用 | 3/3 | 0 | 40718.3 |
| expgym | tuning | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +3682.67 | tokens | 不适用 | 27/27 | 0 | 3682.67 |
| expgym | tuning | family/nasbench101 | cost_moderate | output_tokens | cost_moderate − cost_tight | +8638.67 | tokens | 不适用 | 9/9 | 0 | 8638.67 |
| expgym | tuning | family/nasbench201 | cost_moderate | output_tokens | cost_moderate − cost_tight | +1866.33 | tokens | 不适用 | 9/9 | 0 | 1866.33 |
| expgym | tuning | family/paramnet | cost_moderate | output_tokens | cost_moderate − cost_tight | +543 | tokens | 不适用 | 9/9 | 0 | 543 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | cost_moderate − cost_tight | +9945.67 | tokens | 不适用 | 3/3 | 0 | 9945.67 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | cost_moderate − cost_tight | +6957.33 | tokens | 不适用 | 3/3 | 0 | 6957.33 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | cost_moderate − cost_tight | +9013 | tokens | 不适用 | 3/3 | 0 | 9013 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | output_tokens | cost_moderate − cost_tight | +3612.67 | tokens | 不适用 | 3/3 | 0 | 3612.67 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | output_tokens | cost_moderate − cost_tight | -607.333 | tokens | 不适用 | 3/3 | 0 | -607.333 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | output_tokens | cost_moderate − cost_tight | +2593.67 | tokens | 不适用 | 3/3 | 0 | 2593.67 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | -1848.33 | tokens | 不适用 | 3/3 | 0 | -1848.33 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | +3494.33 | tokens | 不适用 | 3/3 | 0 | 3494.33 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | -17 | tokens | 不适用 | 3/3 | 0 | -17 |
| expgym | tuning | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.111765 | fraction | -11.1765 | 27/27 | 0 | -0.111765 |
| expgym | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.175919 | fraction | -17.5919 | 9/9 | 0 | -0.175919 |
| expgym | tuning | family/nasbench201 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0851699 | fraction | -8.51699 | 9/9 | 0 | -0.0851699 |
| expgym | tuning | family/paramnet | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0742058 | fraction | -7.42058 | 9/9 | 0 | -0.0742058 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0916667 | fraction | -9.16667 | 3/3 | 0 | -0.0916667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.25584 | fraction | -25.584 | 3/3 | 0 | -0.25584 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.18025 | fraction | -18.025 | 3/3 | 0 | -0.18025 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0859127 | fraction | -8.59127 | 3/3 | 0 | -0.0859127 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.107692 | fraction | -10.7692 | 3/3 | 0 | -0.107692 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0619048 | fraction | -6.19048 | 3/3 | 0 | -0.0619048 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.241667 | fraction | -24.1667 | 3/3 | 0 | -0.241667 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.157729 | fraction | -15.7729 | 3/3 | 0 | -0.157729 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.176779 | fraction | +17.6779 | 3/3 | 0 | 0.176779 |
| expgym | tuning | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +45.6947 | seconds | 不适用 | 27/27 | 0 | 45.6947 |
| expgym | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +104.569 | seconds | 不适用 | 9/9 | 0 | 104.569 |
| expgym | tuning | family/nasbench201 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +22.6944 | seconds | 不适用 | 9/9 | 0 | 22.6944 |
| expgym | tuning | family/paramnet | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +9.82106 | seconds | 不适用 | 9/9 | 0 | 9.82106 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +122.781 | seconds | 不适用 | 3/3 | 0 | 122.781 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +82.7009 | seconds | 不适用 | 3/3 | 0 | 82.7009 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +108.225 | seconds | 不适用 | 3/3 | 0 | 108.225 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +43.7695 | seconds | 不适用 | 3/3 | 0 | 43.7695 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | -3.6634 | seconds | 不适用 | 3/3 | 0 | -3.6634 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +27.977 | seconds | 不适用 | 3/3 | 0 | 27.977 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | -17.7926 | seconds | 不适用 | 3/3 | 0 | -17.7926 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +45.8982 | seconds | 不适用 | 3/3 | 0 | 45.8982 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +1.35758 | seconds | 不适用 | 3/3 | 0 | 1.35758 |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | poolact − cached | -0.379591 | fraction | -37.9591 | 13/13 | 0 | -0.379591 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | poolact − cached | -0.379591 | fraction | -37.9591 | 13/13 | 0 | -0.379591 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | -8.23077 | count | 不适用 | 13/13 | 0 | -8.23077 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | poolact − cached | -8.23077 | count | 不适用 | 13/13 | 0 | -8.23077 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | poolact − cached | -21.6923 | count | 不适用 | 13/13 | 0 | -21.6923 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | poolact − cached | -21.6923 | count | 不适用 | 13/13 | 0 | -21.6923 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -4555.09 | seconds | 不适用 | 13/13 | 0 | -4555.09 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | poolact − cached | -4555.09 | seconds | 不适用 | 13/13 | 0 | -4555.09 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | poolact − cached | -171404 | tokens | 不适用 | 13/13 | 0 | -171404 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | poolact − cached | -171404 | tokens | 不适用 | 13/13 | 0 | -171404 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | poolact − cached | +1833.31 | tokens | 不适用 | 13/13 | 0 | 1833.31 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | poolact − cached | +1833.31 | tokens | 不适用 | 13/13 | 0 | 1833.31 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | poolact − cached | +0.2124 | fraction | +21.24 | 13/13 | 0 | 0.2124 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | poolact − cached | +0.2124 | fraction | +21.24 | 13/13 | 0 | 0.2124 |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | cached − naive | +0.159949 | fraction | +15.9949 | 13/13 | 0 | 0.159949 |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | poolact − naive | -0.219642 | fraction | -21.9642 | 13/13 | 0 | -0.219642 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | cached − naive | +0.159949 | fraction | +15.9949 | 13/13 | 0 | 0.159949 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | poolact − naive | -0.219642 | fraction | -21.9642 | 13/13 | 0 | -0.219642 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | cached − naive | +5.23077 | count | 不适用 | 13/13 | 0 | 5.23077 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | -3 | count | 不适用 | 13/13 | 0 | -3 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | cached − naive | +5.23077 | count | 不适用 | 13/13 | 0 | 5.23077 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | poolact − naive | -3 | count | 不适用 | 13/13 | 0 | -3 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | cached − naive | +13.3077 | count | 不适用 | 13/13 | 0 | 13.3077 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | poolact − naive | -8.38462 | count | 不适用 | 13/13 | 0 | -8.38462 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | cached − naive | +13.3077 | count | 不适用 | 13/13 | 0 | 13.3077 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | poolact − naive | -8.38462 | count | 不适用 | 13/13 | 0 | -8.38462 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | cached − naive | +1919.38 | seconds | 不适用 | 13/13 | 0 | 1919.38 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -2635.71 | seconds | 不适用 | 13/13 | 0 | -2635.71 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | cached − naive | +1919.38 | seconds | 不适用 | 13/13 | 0 | 1919.38 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | poolact − naive | -2635.71 | seconds | 不适用 | 13/13 | 0 | -2635.71 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | cached − naive | +96756.8 | tokens | 不适用 | 13/13 | 0 | 96756.8 |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | poolact − naive | -74647.2 | tokens | 不适用 | 13/13 | 0 | -74647.2 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | cached − naive | +96756.8 | tokens | 不适用 | 13/13 | 0 | 96756.8 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | poolact − naive | -74647.2 | tokens | 不适用 | 13/13 | 0 | -74647.2 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | cached − naive | -26930.4 | tokens | 不适用 | 13/13 | 0 | -26930.4 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | poolact − naive | -25097.1 | tokens | 不适用 | 13/13 | 0 | -25097.1 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | cached − naive | -26930.4 | tokens | 不适用 | 13/13 | 0 | -26930.4 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | poolact − naive | -25097.1 | tokens | 不适用 | 13/13 | 0 | -25097.1 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | cached − naive | -0.118273 | fraction | -11.8273 | 13/13 | 0 | -0.118273 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | poolact − naive | +0.0941272 | fraction | +9.41272 | 13/13 | 0 | 0.0941272 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | cached − naive | -0.118273 | fraction | -11.8273 | 13/13 | 0 | -0.118273 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | poolact − naive | +0.0941272 | fraction | +9.41272 | 13/13 | 0 | 0.0941272 |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | poolact − cached | -0.358142 | fraction | -35.8142 | 13/13 | 0 | -0.358142 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | poolact − cached | -0.358142 | fraction | -35.8142 | 13/13 | 0 | -0.358142 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | poolact − cached | -1.46154 | count | 不适用 | 13/13 | 0 | -1.46154 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | poolact − cached | -1.46154 | count | 不适用 | 13/13 | 0 | -1.46154 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | poolact − cached | -4.76923 | count | 不适用 | 13/13 | 0 | -4.76923 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | poolact − cached | -4.76923 | count | 不适用 | 13/13 | 0 | -4.76923 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | poolact − cached | -1289.31 | seconds | 不适用 | 13/13 | 0 | -1289.31 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | poolact − cached | -1289.31 | seconds | 不适用 | 13/13 | 0 | -1289.31 |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | poolact − cached | -61270.1 | tokens | 不适用 | 13/13 | 0 | -61270.1 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | poolact − cached | -61270.1 | tokens | 不适用 | 13/13 | 0 | -61270.1 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | poolact − cached | -20899.8 | tokens | 不适用 | 13/13 | 0 | -20899.8 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | poolact − cached | -20899.8 | tokens | 不适用 | 13/13 | 0 | -20899.8 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | poolact − cached | +0.177579 | fraction | +17.7579 | 13/13 | 0 | 0.177579 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | poolact − cached | +0.177579 | fraction | +17.7579 | 13/13 | 0 | 0.177579 |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | cached − naive | -0.0404641 | fraction | -4.04641 | 13/13 | 0 | -0.0404641 |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | poolact − naive | -0.398606 | fraction | -39.8606 | 13/13 | 0 | -0.398606 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | cached − naive | -0.0404641 | fraction | -4.04641 | 13/13 | 0 | -0.0404641 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | poolact − naive | -0.398606 | fraction | -39.8606 | 13/13 | 0 | -0.398606 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | cached − naive | -0.384615 | count | 不适用 | 13/13 | 0 | -0.384615 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | poolact − naive | -1.84615 | count | 不适用 | 13/13 | 0 | -1.84615 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | cached − naive | -0.384615 | count | 不适用 | 13/13 | 0 | -0.384615 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | poolact − naive | -1.84615 | count | 不适用 | 13/13 | 0 | -1.84615 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | cached − naive | +0 | count | 不适用 | 13/13 | 0 | 0 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | poolact − naive | -4.76923 | count | 不适用 | 13/13 | 0 | -4.76923 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | cached − naive | +0 | count | 不适用 | 13/13 | 0 | 0 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | poolact − naive | -4.76923 | count | 不适用 | 13/13 | 0 | -4.76923 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | cached − naive | -145.671 | seconds | 不适用 | 13/13 | 0 | -145.671 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | poolact − naive | -1434.98 | seconds | 不适用 | 13/13 | 0 | -1434.98 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | cached − naive | -145.671 | seconds | 不适用 | 13/13 | 0 | -145.671 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | poolact − naive | -1434.98 | seconds | 不适用 | 13/13 | 0 | -1434.98 |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | cached − naive | -55191.4 | tokens | 不适用 | 13/13 | 0 | -55191.4 |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | poolact − naive | -116461 | tokens | 不适用 | 13/13 | 0 | -116461 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | cached − naive | -55191.4 | tokens | 不适用 | 13/13 | 0 | -55191.4 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | poolact − naive | -116461 | tokens | 不适用 | 13/13 | 0 | -116461 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | cached − naive | -22059.9 | tokens | 不适用 | 13/13 | 0 | -22059.9 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | poolact − naive | -42959.8 | tokens | 不适用 | 13/13 | 0 | -42959.8 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | cached − naive | -22059.9 | tokens | 不适用 | 13/13 | 0 | -22059.9 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | poolact − naive | -42959.8 | tokens | 不适用 | 13/13 | 0 | -42959.8 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | cached − naive | -0.00581149 | fraction | -0.581149 | 13/13 | 0 | -0.00581149 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | poolact − naive | +0.171768 | fraction | +17.1768 | 13/13 | 0 | 0.171768 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | cached − naive | -0.00581149 | fraction | -0.581149 | 13/13 | 0 | -0.00581149 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | poolact − naive | +0.171768 | fraction | +17.1768 | 13/13 | 0 | 0.171768 |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | poolact − cached | -0.187117 | fraction | -18.7117 | 39/39 | 0 | -0.187117 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | poolact − cached | -0.187117 | fraction | -18.7117 | 39/39 | 0 | -0.187117 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | -8.84615 | count | 不适用 | 39/39 | 0 | -8.84615 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | poolact − cached | -8.84615 | count | 不适用 | 39/39 | 0 | -8.84615 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | poolact − cached | -14.1538 | count | 不适用 | 39/39 | 0 | -14.1538 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | poolact − cached | -14.1538 | count | 不适用 | 39/39 | 0 | -14.1538 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -2245.4 | seconds | 不适用 | 39/39 | 0 | -2245.4 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | poolact − cached | -2245.4 | seconds | 不适用 | 39/39 | 0 | -2245.4 |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | poolact − cached | -42792.7 | tokens | 不适用 | 39/39 | 0 | -42792.7 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | poolact − cached | -42792.7 | tokens | 不适用 | 39/39 | 0 | -42792.7 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | poolact − cached | +962.128 | tokens | 不适用 | 39/39 | 0 | 962.128 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | poolact − cached | +962.128 | tokens | 不适用 | 39/39 | 0 | 962.128 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | poolact − cached | +0.0935741 | fraction | +9.35741 | 39/39 | 0 | 0.0935741 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | poolact − cached | +0.0935741 | fraction | +9.35741 | 39/39 | 0 | 0.0935741 |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | cached − naive | -0.0213934 | fraction | -2.13934 | 39/39 | 0 | -0.0213934 |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | poolact − naive | -0.20851 | fraction | -20.851 | 39/39 | 0 | -0.20851 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | cached − naive | -0.0213934 | fraction | -2.13934 | 39/39 | 0 | -0.0213934 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | poolact − naive | -0.20851 | fraction | -20.851 | 39/39 | 0 | -0.20851 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | cached − naive | +1.35897 | count | 不适用 | 39/39 | 0 | 1.35897 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | -7.48718 | count | 不适用 | 39/39 | 0 | -7.48718 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | cached − naive | +1.35897 | count | 不适用 | 39/39 | 0 | 1.35897 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | poolact − naive | -7.48718 | count | 不适用 | 39/39 | 0 | -7.48718 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | cached − naive | +0.153846 | count | 不适用 | 39/39 | 0 | 0.153846 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | poolact − naive | -14 | count | 不适用 | 39/39 | 0 | -14 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | cached − naive | +0.153846 | count | 不适用 | 39/39 | 0 | 0.153846 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | poolact − naive | -14 | count | 不适用 | 39/39 | 0 | -14 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | cached − naive | -256.721 | seconds | 不适用 | 39/39 | 0 | -256.721 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -2502.12 | seconds | 不适用 | 39/39 | 0 | -2502.12 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | cached − naive | -256.721 | seconds | 不适用 | 39/39 | 0 | -256.721 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | poolact − naive | -2502.12 | seconds | 不适用 | 39/39 | 0 | -2502.12 |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | cached − naive | -16832.3 | tokens | 不适用 | 39/39 | 0 | -16832.3 |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | poolact − naive | -59625.1 | tokens | 不适用 | 39/39 | 0 | -59625.1 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | cached − naive | -16832.3 | tokens | 不适用 | 39/39 | 0 | -16832.3 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | poolact − naive | -59625.1 | tokens | 不适用 | 39/39 | 0 | -59625.1 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | cached − naive | -4505.31 | tokens | 不适用 | 39/39 | 0 | -4505.31 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | poolact − naive | -3543.18 | tokens | 不适用 | 39/39 | 0 | -3543.18 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | cached − naive | -4505.31 | tokens | 不适用 | 39/39 | 0 | -4505.31 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | poolact − naive | -3543.18 | tokens | 不适用 | 39/39 | 0 | -3543.18 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | cached − naive | +0.0151137 | fraction | +1.51137 | 39/39 | 0 | 0.0151137 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | poolact − naive | +0.108688 | fraction | +10.8688 | 39/39 | 0 | 0.108688 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | cached − naive | +0.0151137 | fraction | +1.51137 | 39/39 | 0 | 0.0151137 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | poolact − naive | +0.108688 | fraction | +10.8688 | 39/39 | 0 | 0.108688 |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | poolact − cached | -0.185501 | fraction | -18.5501 | 39/39 | 0 | -0.185501 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | poolact − cached | -0.185501 | fraction | -18.5501 | 39/39 | 0 | -0.185501 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | poolact − cached | -2.58974 | count | 不适用 | 39/39 | 0 | -2.58974 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | poolact − cached | -2.58974 | count | 不适用 | 39/39 | 0 | -2.58974 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | poolact − cached | -3.71795 | count | 不适用 | 39/39 | 0 | -3.71795 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | poolact − cached | -3.71795 | count | 不适用 | 39/39 | 0 | -3.71795 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | poolact − cached | -667.805 | seconds | 不适用 | 39/39 | 0 | -667.805 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | poolact − cached | -667.805 | seconds | 不适用 | 39/39 | 0 | -667.805 |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | input_tokens | poolact − cached | +26432.3 | tokens | 不适用 | 39/39 | 0 | 26432.3 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | poolact − cached | +26432.3 | tokens | 不适用 | 39/39 | 0 | 26432.3 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | poolact − cached | +7233.87 | tokens | 不适用 | 39/39 | 0 | 7233.87 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | poolact − cached | +7233.87 | tokens | 不适用 | 39/39 | 0 | 7233.87 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | poolact − cached | +0.0937064 | fraction | +9.37064 | 39/39 | 0 | 0.0937064 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | poolact − cached | +0.0937064 | fraction | +9.37064 | 39/39 | 0 | 0.0937064 |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | cached − naive | +0.16706 | fraction | +16.706 | 39/39 | 0 | 0.16706 |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | poolact − naive | -0.0184415 | fraction | -1.84415 | 39/39 | 0 | -0.0184415 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | cached − naive | +0.16706 | fraction | +16.706 | 39/39 | 0 | 0.16706 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | poolact − naive | -0.0184415 | fraction | -1.84415 | 39/39 | 0 | -0.0184415 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | cached − naive | +1.48718 | count | 不适用 | 39/39 | 0 | 1.48718 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | poolact − naive | -1.10256 | count | 不适用 | 39/39 | 0 | -1.10256 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | cached − naive | +1.48718 | count | 不适用 | 39/39 | 0 | 1.48718 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | poolact − naive | -1.10256 | count | 不适用 | 39/39 | 0 | -1.10256 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | cached − naive | +1.89744 | count | 不适用 | 39/39 | 0 | 1.89744 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | poolact − naive | -1.82051 | count | 不适用 | 39/39 | 0 | -1.82051 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | cached − naive | +1.89744 | count | 不适用 | 39/39 | 0 | 1.89744 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | poolact − naive | -1.82051 | count | 不适用 | 39/39 | 0 | -1.82051 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | cached − naive | +601.416 | seconds | 不适用 | 39/39 | 0 | 601.416 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | poolact − naive | -66.3894 | seconds | 不适用 | 39/39 | 0 | -66.3894 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | cached − naive | +601.416 | seconds | 不适用 | 39/39 | 0 | 601.416 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | poolact − naive | -66.3894 | seconds | 不适用 | 39/39 | 0 | -66.3894 |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | input_tokens | cached − naive | -12568.7 | tokens | 不适用 | 39/39 | 0 | -12568.7 |
| poolact | restricted_search | all/all | cost_tight | input_tokens | poolact − naive | +13863.6 | tokens | 不适用 | 39/39 | 0 | 13863.6 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | cached − naive | -12568.7 | tokens | 不适用 | 39/39 | 0 | -12568.7 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | poolact − naive | +13863.6 | tokens | 不适用 | 39/39 | 0 | 13863.6 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | cached − naive | +479.769 | tokens | 不适用 | 39/39 | 0 | 479.769 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | poolact − naive | +7713.64 | tokens | 不适用 | 39/39 | 0 | 7713.64 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | cached − naive | +479.769 | tokens | 不适用 | 39/39 | 0 | 479.769 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | poolact − naive | +7713.64 | tokens | 不适用 | 39/39 | 0 | 7713.64 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | cached − naive | -0.0607438 | fraction | -6.07438 | 39/39 | 0 | -0.0607438 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | poolact − naive | +0.0329626 | fraction | +3.29626 | 39/39 | 0 | 0.0329626 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | cached − naive | -0.0607438 | fraction | -6.07438 | 39/39 | 0 | -0.0607438 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | poolact − naive | +0.0329626 | fraction | +3.29626 | 39/39 | 0 | 0.0329626 |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | tuning | all/all | cost_moderate | budget_utilization | poolact − cached | -0.216186 | fraction | -21.6186 | 9/9 | 0 | -0.216186 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | poolact − cached | -0.216186 | fraction | -21.6186 | 9/9 | 0 | -0.216186 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | poolact − cached | -0.424413 | fraction | -42.4413 | 3/3 | 0 | -0.424413 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | poolact − cached | +0.111145 | fraction | +11.1145 | 3/3 | 0 | 0.111145 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | poolact − cached | -0.33529 | fraction | -33.529 | 3/3 | 0 | -0.33529 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | -1.22222 | count | 不适用 | 9/9 | 0 | -1.22222 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | poolact − cached | -1.22222 | count | 不适用 | 9/9 | 0 | -1.22222 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | poolact − cached | -1.66667 | count | 不适用 | 3/3 | 0 | -1.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | poolact − cached | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | poolact − cached | -2.33333 | count | 不适用 | 3/3 | 0 | -2.33333 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | poolact − cached | -10.1111 | count | 不适用 | 9/9 | 0 | -10.1111 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | poolact − cached | -10.1111 | count | 不适用 | 9/9 | 0 | -10.1111 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | poolact − cached | -9.66667 | count | 不适用 | 3/3 | 0 | -9.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | poolact − cached | +4.66667 | count | 不适用 | 3/3 | 0 | 4.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | poolact − cached | -25.3333 | count | 不适用 | 3/3 | 0 | -25.3333 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -62797.8 | seconds | 不适用 | 9/9 | 0 | -62797.8 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | poolact − cached | -62797.8 | seconds | 不适用 | 9/9 | 0 | -62797.8 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | poolact − cached | -83934.5 | seconds | 不适用 | 3/3 | 0 | -83934.5 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | poolact − cached | +45803 | seconds | 不适用 | 3/3 | 0 | 45803 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | poolact − cached | -150262 | seconds | 不适用 | 3/3 | 0 | -150262 |
| poolact | tuning | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 2/9 | 7 | 0 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 2/9 | 7 | 0 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 2/3 | 1 | 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | input_tokens | poolact − cached | -65747.7 | tokens | 不适用 | 9/9 | 0 | -65747.7 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | poolact − cached | -65747.7 | tokens | 不适用 | 9/9 | 0 | -65747.7 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | poolact − cached | +103323 | tokens | 不适用 | 3/3 | 0 | 103323 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | poolact − cached | +85053 | tokens | 不适用 | 3/3 | 0 | 85053 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | poolact − cached | -385619 | tokens | 不适用 | 3/3 | 0 | -385619 |
| poolact | tuning | all/all | cost_moderate | output_tokens | poolact − cached | -22941.6 | tokens | 不适用 | 9/9 | 0 | -22941.6 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | poolact − cached | -22941.6 | tokens | 不适用 | 9/9 | 0 | -22941.6 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | poolact − cached | +7884.67 | tokens | 不适用 | 3/3 | 0 | 7884.67 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | poolact − cached | -4944.33 | tokens | 不适用 | 3/3 | 0 | -4944.33 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | poolact − cached | -71765 | tokens | 不适用 | 3/3 | 0 | -71765 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | poolact − cached | +0.133337 | fraction | +13.3337 | 9/9 | 0 | 0.133337 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | poolact − cached | +0.133337 | fraction | +13.3337 | 9/9 | 0 | 0.133337 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | poolact − cached | +0.147673 | fraction | +14.7673 | 3/3 | 0 | 0.147673 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | poolact − cached | -0.0235043 | fraction | -2.35043 | 3/3 | 0 | -0.0235043 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | poolact − cached | +0.275842 | fraction | +27.5842 | 3/3 | 0 | 0.275842 |
| poolact | tuning | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | budget_utilization | cached − naive | +0.148141 | fraction | +14.8141 | 9/9 | 0 | 0.148141 |
| poolact | tuning | all/all | cost_moderate | budget_utilization | poolact − naive | -0.068045 | fraction | -6.8045 | 9/9 | 0 | -0.068045 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | cached − naive | +0.148141 | fraction | +14.8141 | 9/9 | 0 | 0.148141 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | poolact − naive | -0.068045 | fraction | -6.8045 | 9/9 | 0 | -0.068045 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | cached − naive | +0.471803 | fraction | +47.1803 | 3/3 | 0 | 0.471803 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | poolact − naive | +0.0473897 | fraction | +4.73897 | 3/3 | 0 | 0.0473897 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | cached − naive | -0.0933723 | fraction | -9.33723 | 3/3 | 0 | -0.0933723 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | poolact − naive | +0.0177724 | fraction | +1.77724 | 3/3 | 0 | 0.0177724 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | cached − naive | +0.0659931 | fraction | +6.59931 | 3/3 | 0 | 0.0659931 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | poolact − naive | -0.269297 | fraction | -26.9297 | 3/3 | 0 | -0.269297 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | cached − naive | +1 | count | 不适用 | 9/9 | 0 | 1 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | -0.222222 | count | 不适用 | 9/9 | 0 | -0.222222 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | cached − naive | +1 | count | 不适用 | 9/9 | 0 | 1 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | poolact − naive | -0.222222 | count | 不适用 | 9/9 | 0 | -0.222222 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | cached − naive | +0.666667 | count | 不适用 | 3/3 | 0 | 0.666667 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | poolact − naive | -1 | count | 不适用 | 3/3 | 0 | -1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | cached − naive | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | cached − naive | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | poolact − naive | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | cached − naive | +5.33333 | count | 不适用 | 9/9 | 0 | 5.33333 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | poolact − naive | -4.77778 | count | 不适用 | 9/9 | 0 | -4.77778 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | cached − naive | +5.33333 | count | 不适用 | 9/9 | 0 | 5.33333 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | poolact − naive | -4.77778 | count | 不适用 | 9/9 | 0 | -4.77778 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | cached − naive | +12 | count | 不适用 | 3/3 | 0 | 12 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | poolact − naive | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | cached − naive | -6.66667 | count | 不适用 | 3/3 | 0 | -6.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | poolact − naive | -2 | count | 不适用 | 3/3 | 0 | -2 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | cached − naive | +10.6667 | count | 不适用 | 3/3 | 0 | 10.6667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | poolact − naive | -14.6667 | count | 不适用 | 3/3 | 0 | -14.6667 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | cached − naive | +28134.3 | seconds | 不适用 | 9/9 | 0 | 28134.3 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -34663.5 | seconds | 不适用 | 9/9 | 0 | -34663.5 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | cached − naive | +28134.3 | seconds | 不适用 | 9/9 | 0 | 28134.3 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | poolact − naive | -34663.5 | seconds | 不适用 | 9/9 | 0 | -34663.5 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | cached − naive | +93306.6 | seconds | 不适用 | 3/3 | 0 | 93306.6 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | poolact − naive | +9372.08 | seconds | 不适用 | 3/3 | 0 | 9372.08 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | cached − naive | -38479 | seconds | 不适用 | 3/3 | 0 | -38479 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | poolact − naive | +7324.06 | seconds | 不适用 | 3/3 | 0 | 7324.06 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | cached − naive | +29575.1 | seconds | 不适用 | 3/3 | 0 | 29575.1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | poolact − naive | -120687 | seconds | 不适用 | 3/3 | 0 | -120687 |
| poolact | tuning | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 1/9 | 8 | 0 |
| poolact | tuning | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 1/9 | 8 | 0 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 1/3 | 2 | 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | input_tokens | cached − naive | +8585.67 | tokens | 不适用 | 9/9 | 0 | 8585.67 |
| poolact | tuning | all/all | cost_moderate | input_tokens | poolact − naive | -57162 | tokens | 不适用 | 9/9 | 0 | -57162 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | cached − naive | +8585.67 | tokens | 不适用 | 9/9 | 0 | 8585.67 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | poolact − naive | -57162 | tokens | 不适用 | 9/9 | 0 | -57162 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | cached − naive | +79492 | tokens | 不适用 | 3/3 | 0 | 79492 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | poolact − naive | +182815 | tokens | 不适用 | 3/3 | 0 | 182815 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | cached − naive | -113504 | tokens | 不适用 | 3/3 | 0 | -113504 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | poolact − naive | -28451.3 | tokens | 不适用 | 3/3 | 0 | -28451.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | cached − naive | +59769.3 | tokens | 不适用 | 3/3 | 0 | 59769.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | poolact − naive | -325850 | tokens | 不适用 | 3/3 | 0 | -325850 |
| poolact | tuning | all/all | cost_moderate | output_tokens | cached − naive | +5455.78 | tokens | 不适用 | 9/9 | 0 | 5455.78 |
| poolact | tuning | all/all | cost_moderate | output_tokens | poolact − naive | -17485.8 | tokens | 不适用 | 9/9 | 0 | -17485.8 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | cached − naive | +5455.78 | tokens | 不适用 | 9/9 | 0 | 5455.78 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | poolact − naive | -17485.8 | tokens | 不适用 | 9/9 | 0 | -17485.8 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | cached − naive | +15113.7 | tokens | 不适用 | 3/3 | 0 | 15113.7 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | poolact − naive | +22998.3 | tokens | 不适用 | 3/3 | 0 | 22998.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | cached − naive | -7061 | tokens | 不适用 | 3/3 | 0 | -7061 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | poolact − naive | -12005.3 | tokens | 不适用 | 3/3 | 0 | -12005.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | cached − naive | +8314.67 | tokens | 不适用 | 3/3 | 0 | 8314.67 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | poolact − naive | -63450.3 | tokens | 不适用 | 3/3 | 0 | -63450.3 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | cached − naive | -0.0522706 | fraction | -5.22706 | 9/9 | 0 | -0.0522706 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | poolact − naive | +0.0810662 | fraction | +8.10662 | 9/9 | 0 | 0.0810662 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | cached − naive | -0.0522706 | fraction | -5.22706 | 9/9 | 0 | -0.0522706 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | poolact − naive | +0.0810662 | fraction | +8.10662 | 9/9 | 0 | 0.0810662 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | cached − naive | -0.236506 | fraction | -23.6506 | 3/3 | 0 | -0.236506 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | poolact − naive | -0.0888333 | fraction | -8.88333 | 3/3 | 0 | -0.0888333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | cached − naive | +0.251003 | fraction | +25.1003 | 3/3 | 0 | 0.251003 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | poolact − naive | +0.227498 | fraction | +22.7498 | 3/3 | 0 | 0.227498 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | cached − naive | -0.171308 | fraction | -17.1308 | 3/3 | 0 | -0.171308 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | poolact − naive | +0.104534 | fraction | +10.4534 | 3/3 | 0 | 0.104534 |
| poolact | tuning | all/all | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | budget_utilization | poolact − cached | +0.0744128 | fraction | +7.44128 | 9/9 | 0 | 0.0744128 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | poolact − cached | +0.0744128 | fraction | +7.44128 | 9/9 | 0 | 0.0744128 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | poolact − cached | +0.168012 | fraction | +16.8012 | 3/3 | 0 | 0.168012 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | poolact − cached | -0.0129032 | fraction | -1.29032 | 3/3 | 0 | -0.0129032 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | poolact − cached | +0.0681297 | fraction | +6.81297 | 3/3 | 0 | 0.0681297 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | poolact − cached | -0.555556 | count | 不适用 | 9/9 | 0 | -0.555556 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | poolact − cached | -0.555556 | count | 不适用 | 9/9 | 0 | -0.555556 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | poolact − cached | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | poolact − cached | -1.66667 | count | 不适用 | 3/3 | 0 | -1.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | poolact − cached | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | poolact − cached | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | poolact − cached | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | poolact − cached | +1 | count | 不适用 | 3/3 | 0 | 1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | poolact − cached | -2.66667 | count | 不适用 | 3/3 | 0 | -2.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | poolact − cached | +2 | count | 不适用 | 3/3 | 0 | 2 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | poolact − cached | +5844.22 | seconds | 不适用 | 9/9 | 0 | 5844.22 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | poolact − cached | +5844.22 | seconds | 不适用 | 9/9 | 0 | 5844.22 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | poolact − cached | +9968.12 | seconds | 不适用 | 3/3 | 0 | 9968.12 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | poolact − cached | -1595.24 | seconds | 不适用 | 3/3 | 0 | -1595.24 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | poolact − cached | +9159.79 | seconds | 不适用 | 3/3 | 0 | 9159.79 |
| poolact | tuning | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | input_tokens | poolact − cached | +70805.6 | tokens | 不适用 | 9/9 | 0 | 70805.6 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | poolact − cached | +70805.6 | tokens | 不适用 | 9/9 | 0 | 70805.6 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | poolact − cached | +74432 | tokens | 不适用 | 3/3 | 0 | 74432 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | poolact − cached | +27642 | tokens | 不适用 | 3/3 | 0 | 27642 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | poolact − cached | +110343 | tokens | 不适用 | 3/3 | 0 | 110343 |
| poolact | tuning | all/all | cost_tight | output_tokens | poolact − cached | +7347.11 | tokens | 不适用 | 9/9 | 0 | 7347.11 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | poolact − cached | +7347.11 | tokens | 不适用 | 9/9 | 0 | 7347.11 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | poolact − cached | +573.333 | tokens | 不适用 | 3/3 | 0 | 573.333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | poolact − cached | +1227.67 | tokens | 不适用 | 3/3 | 0 | 1227.67 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | poolact − cached | +20240.3 | tokens | 不适用 | 3/3 | 0 | 20240.3 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | poolact − cached | -0.00556384 | fraction | -0.556384 | 9/9 | 0 | -0.00556384 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | poolact − cached | -0.00556384 | fraction | -0.556384 | 9/9 | 0 | -0.00556384 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | poolact − cached | +0.0613562 | fraction | +6.13562 | 3/3 | 0 | 0.0613562 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | poolact − cached | +0.0193216 | fraction | +1.93216 | 3/3 | 0 | 0.0193216 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | poolact − cached | -0.0973693 | fraction | -9.73693 | 3/3 | 0 | -0.0973693 |
| poolact | tuning | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | budget_utilization | cached − naive | -0.103601 | fraction | -10.3601 | 9/9 | 0 | -0.103601 |
| poolact | tuning | all/all | cost_tight | budget_utilization | poolact − naive | -0.0291885 | fraction | -2.91885 | 9/9 | 0 | -0.0291885 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | cached − naive | -0.103601 | fraction | -10.3601 | 9/9 | 0 | -0.103601 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | poolact − naive | -0.0291885 | fraction | -2.91885 | 9/9 | 0 | -0.0291885 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | cached − naive | -0.304102 | fraction | -30.4102 | 3/3 | 0 | -0.304102 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | poolact − naive | -0.13609 | fraction | -13.609 | 3/3 | 0 | -0.13609 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | cached − naive | -0.134798 | fraction | -13.4798 | 3/3 | 0 | -0.134798 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | poolact − naive | -0.147701 | fraction | -14.7701 | 3/3 | 0 | -0.147701 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | cached − naive | +0.128095 | fraction | +12.8095 | 3/3 | 0 | 0.128095 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | poolact − naive | +0.196225 | fraction | +19.6225 | 3/3 | 0 | 0.196225 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | cached − naive | -1.44444 | count | 不适用 | 9/9 | 0 | -1.44444 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | poolact − naive | -2 | count | 不适用 | 9/9 | 0 | -2 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | cached − naive | -1.44444 | count | 不适用 | 9/9 | 0 | -1.44444 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | poolact − naive | -2 | count | 不适用 | 9/9 | 0 | -2 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | cached − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | cached − naive | -4.33333 | count | 不适用 | 3/3 | 0 | -4.33333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | poolact − naive | -6 | count | 不适用 | 3/3 | 0 | -6 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | cached − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | cached − naive | -2.33333 | count | 不适用 | 9/9 | 0 | -2.33333 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | poolact − naive | -2.22222 | count | 不适用 | 9/9 | 0 | -2.22222 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | cached − naive | -2.33333 | count | 不适用 | 9/9 | 0 | -2.33333 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | poolact − naive | -2.22222 | count | 不适用 | 9/9 | 0 | -2.22222 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | cached − naive | -3.66667 | count | 不适用 | 3/3 | 0 | -3.66667 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | poolact − naive | -2.66667 | count | 不适用 | 3/3 | 0 | -2.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | cached − naive | -4 | count | 不适用 | 3/3 | 0 | -4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | poolact − naive | -6.66667 | count | 不适用 | 3/3 | 0 | -6.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | cached − naive | +0.666667 | count | 不适用 | 3/3 | 0 | 0.666667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | poolact − naive | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | cached − naive | -5828.49 | seconds | 不适用 | 9/9 | 0 | -5828.49 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | poolact − naive | +15.7317 | seconds | 不适用 | 9/9 | 0 | 15.7317 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | cached − naive | -5828.49 | seconds | 不适用 | 9/9 | 0 | -5828.49 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | poolact − naive | +15.7317 | seconds | 不适用 | 9/9 | 0 | 15.7317 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | cached − naive | -18042.3 | seconds | 不适用 | 3/3 | 0 | -18042.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | poolact − naive | -8074.19 | seconds | 不适用 | 3/3 | 0 | -8074.19 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | cached − naive | -16665.1 | seconds | 不适用 | 3/3 | 0 | -16665.1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | poolact − naive | -18260.4 | seconds | 不适用 | 3/3 | 0 | -18260.4 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | cached − naive | +17222 | seconds | 不适用 | 3/3 | 0 | 17222 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | poolact − naive | +26381.7 | seconds | 不适用 | 3/3 | 0 | 26381.7 |
| poolact | tuning | all/all | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | input_tokens | cached − naive | -61008.1 | tokens | 不适用 | 9/9 | 0 | -61008.1 |
| poolact | tuning | all/all | cost_tight | input_tokens | poolact − naive | +9797.44 | tokens | 不适用 | 9/9 | 0 | 9797.44 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | cached − naive | -61008.1 | tokens | 不适用 | 9/9 | 0 | -61008.1 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | poolact − naive | +9797.44 | tokens | 不适用 | 9/9 | 0 | 9797.44 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | cached − naive | -42170.7 | tokens | 不适用 | 3/3 | 0 | -42170.7 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | poolact − naive | +32261.3 | tokens | 不适用 | 3/3 | 0 | 32261.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | cached − naive | -150407 | tokens | 不适用 | 3/3 | 0 | -150407 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | poolact − naive | -122765 | tokens | 不适用 | 3/3 | 0 | -122765 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | cached − naive | +9553.33 | tokens | 不适用 | 3/3 | 0 | 9553.33 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | poolact − naive | +119896 | tokens | 不适用 | 3/3 | 0 | 119896 |
| poolact | tuning | all/all | cost_tight | output_tokens | cached − naive | +10473 | tokens | 不适用 | 9/9 | 0 | 10473 |
| poolact | tuning | all/all | cost_tight | output_tokens | poolact − naive | +17820.1 | tokens | 不适用 | 9/9 | 0 | 17820.1 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | cached − naive | +10473 | tokens | 不适用 | 9/9 | 0 | 10473 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | poolact − naive | +17820.1 | tokens | 不适用 | 9/9 | 0 | 17820.1 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | cached − naive | +27119.7 | tokens | 不适用 | 3/3 | 0 | 27119.7 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | poolact − naive | +27693 | tokens | 不适用 | 3/3 | 0 | 27693 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | cached − naive | -23927.7 | tokens | 不适用 | 3/3 | 0 | -23927.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | poolact − naive | -22700 | tokens | 不适用 | 3/3 | 0 | -22700 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | cached − naive | +28227 | tokens | 不适用 | 3/3 | 0 | 28227 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | poolact − naive | +48467.3 | tokens | 不适用 | 3/3 | 0 | 48467.3 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | cached − naive | +0.00934101 | fraction | +0.934101 | 9/9 | 0 | 0.00934101 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | poolact − naive | +0.00377717 | fraction | +0.377717 | 9/9 | 0 | 0.00377717 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | cached − naive | +0.00934101 | fraction | +0.934101 | 9/9 | 0 | 0.00934101 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | poolact − naive | +0.00377717 | fraction | +0.377717 | 9/9 | 0 | 0.00377717 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | cached − naive | +0.0119658 | fraction | +1.19658 | 3/3 | 0 | 0.0119658 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | poolact − naive | +0.073322 | fraction | +7.3322 | 3/3 | 0 | 0.073322 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | cached − naive | +0.0727239 | fraction | +7.27239 | 3/3 | 0 | 0.0727239 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | poolact − naive | +0.0920455 | fraction | +9.20455 | 3/3 | 0 | 0.0920455 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | cached − naive | -0.0566667 | fraction | -5.66667 | 3/3 | 0 | -0.0566667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | poolact − naive | -0.154036 | fraction | -15.4036 | 3/3 | 0 | -0.154036 |
| poolact | tuning | all/all | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/3 | 3 | unknown |

