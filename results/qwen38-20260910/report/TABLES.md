# 全部 family / task 与资源表

本附件直接展示冻结聚合表，不重新评分。unknown 与已知子集严格区分；层级 all/family/task 不相加当作额外样本。

## 质量：预定义 family / task

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | evidence_acc | fraction | 0.918552 | 13/13 | 0 | 13 | 0.918552 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | label_acc | fraction | 0.94721 | 13/13 | 0 | 13 | 0.94721 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | evidence_acc | fraction | 0.749623 | 13/13 | 0 | 13 | 0.749623 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | label_acc | fraction | 0.882353 | 13/13 | 0 | 13 | 0.882353 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | evidence_acc | fraction | 0.58371 | 13/13 | 0 | 13 | 0.58371 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | label_acc | fraction | 0.831071 | 13/13 | 0 | 13 | 0.831071 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | f1 | fraction | 0.513103 | 34/34 | 0 | 34 | 0.513103 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | f1 | fraction | 0.641102 | 39/39 | 0 | 39 | 0.641102 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | f1 | fraction | 0.393451 | 34/34 | 0 | 34 | 0.393451 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | f1 | fraction | 0.611283 | 39/39 | 0 | 39 | 0.611283 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | f1 | fraction | 0.137701 | 34/34 | 0 | 34 | 0.137701 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | f1 | fraction | 0.225691 | 39/39 | 0 | 39 | 0.225691 | 1 / unknown |
| expgym | tuning | family/nasbench101 | cost_free | single | gap | Gap points | 98.6618 | 9/9 | 0 | 3 | 98.6618 | 3 / 0.42589 |
| expgym | tuning | family/nasbench201 | cost_free | single | gap | Gap points | 98.4516 | 9/9 | 0 | 3 | 98.4516 | 3 / 0.952963 |
| expgym | tuning | family/paramnet | cost_free | single | gap | Gap points | 95.2823 | 9/9 | 0 | 3 | 95.2823 | 3 / 1.20445 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | gap | Gap points | 99.5808 | 3/3 | 0 | 1 | 99.5808 | 3 / 0.364017 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | gap | Gap points | 97.1134 | 3/3 | 0 | 1 | 97.1134 | 3 / 1.1002 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | gap | Gap points | 99.2911 | 3/3 | 0 | 1 | 99.2911 | 3 / 0.312746 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | gap | Gap points | 99.3021 | 3/3 | 0 | 1 | 99.3021 | 3 / 1.20886 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | gap | Gap points | 97.6521 | 3/3 | 0 | 1 | 97.6521 | 3 / 4.06669 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | gap | Gap points | 98.4005 | 3/3 | 0 | 1 | 98.4005 | 3 / 0.801953 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | gap | Gap points | 94.59 | 3/3 | 0 | 1 | 94.59 | 3 / 1.45964 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | gap | Gap points | 93.9953 | 3/3 | 0 | 1 | 93.9953 | 3 / 1.24093 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | gap | Gap points | 97.2616 | 3/3 | 0 | 1 | 97.2616 | 3 / 3.65974 |
| expgym | tuning | family/nasbench101 | cost_free | single | raw_perf | fraction | 0.9421 | 9/9 | 0 | 3 | 0.9421 | 3 / 0.00134343 |
| expgym | tuning | family/nasbench201 | cost_free | single | raw_perf | fraction | 0.70467 | 9/9 | 0 | 3 | 0.70467 | 3 / 0.00117517 |
| expgym | tuning | family/paramnet | cost_free | single | raw_perf | fraction | 0.839365 | 9/9 | 0 | 3 | 0.839365 | 3 / 0.00645555 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | raw_perf | fraction | 0.943131 | 3/3 | 0 | 1 | 0.943131 | 3 / 0.00256065 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | raw_perf | fraction | 0.941595 | 3/3 | 0 | 1 | 0.941595 | 3 / 0.00280375 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | raw_perf | fraction | 0.941573 | 3/3 | 0 | 1 | 0.941573 | 3 / 0.00176761 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | raw_perf | fraction | 0.915511 | 3/3 | 0 | 1 | 0.915511 | 3 / 0.00096225 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | raw_perf | fraction | 0.732167 | 3/3 | 0 | 1 | 0.732167 | 3 / 0.00496521 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | raw_perf | fraction | 0.466333 | 3/3 | 0 | 1 | 0.466333 | 3 / 0.00105848 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | raw_perf | fraction | 0.851503 | 3/3 | 0 | 1 | 0.851503 | 3 / 0.000601234 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | raw_perf | fraction | 0.715839 | 3/3 | 0 | 1 | 0.715839 | 3 / 0.00108 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | raw_perf | fraction | 0.950754 | 3/3 | 0 | 1 | 0.950754 | 3 / 0.0192116 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | gap | Gap points | 96.511 | 9/9 | 0 | 3 | 96.511 | 3 / 1.98673 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | gap | Gap points | 93.9364 | 9/9 | 0 | 3 | 93.9364 | 3 / 5.2321 |
| expgym | tuning | family/paramnet | cost_moderate | single | gap | Gap points | 94.9527 | 9/9 | 0 | 3 | 94.9527 | 3 / 0.984362 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | gap | Gap points | 98.1901 | 3/3 | 0 | 1 | 98.1901 | 3 / 1.39238 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | gap | Gap points | 92.6503 | 3/3 | 0 | 1 | 92.6503 | 3 / 7.4112 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | gap | Gap points | 98.6925 | 3/3 | 0 | 1 | 98.6925 | 3 / 0.894647 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | gap | Gap points | 93.2161 | 3/3 | 0 | 1 | 93.2161 | 3 / 9.46675 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | gap | Gap points | 100 | 3/3 | 0 | 1 | 100 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | gap | Gap points | 88.5932 | 3/3 | 0 | 1 | 88.5932 | 3 / 7.23229 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | gap | Gap points | 91.9824 | 3/3 | 0 | 1 | 91.9824 | 3 / 0.142762 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | gap | Gap points | 93.99 | 3/3 | 0 | 1 | 93.99 | 3 / 3.13574 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | gap | Gap points | 98.8857 | 3/3 | 0 | 1 | 98.8857 | 3 / 0.241026 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | raw_perf | fraction | 0.93392 | 9/9 | 0 | 3 | 0.93392 | 3 / 0.00360292 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | raw_perf | fraction | 0.699696 | 9/9 | 0 | 3 | 0.699696 | 3 / 0.00535039 |
| expgym | tuning | family/paramnet | cost_moderate | single | raw_perf | fraction | 0.841848 | 9/9 | 0 | 3 | 0.841848 | 3 / 0.000900039 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | raw_perf | fraction | 0.933349 | 3/3 | 0 | 1 | 0.933349 | 3 / 0.00979457 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | raw_perf | fraction | 0.930222 | 3/3 | 0 | 1 | 0.930222 | 3 / 0.0188868 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | raw_perf | fraction | 0.93819 | 3/3 | 0 | 1 | 0.93819 | 3 / 0.00505645 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | raw_perf | fraction | 0.910667 | 3/3 | 0 | 1 | 0.910667 | 3 / 0.00753553 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | raw_perf | fraction | 0.735033 | 3/3 | 0 | 1 | 0.735033 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | raw_perf | fraction | 0.453389 | 3/3 | 0 | 1 | 0.453389 | 3 / 0.0095457 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | raw_perf | fraction | 0.850429 | 3/3 | 0 | 1 | 0.850429 | 3 / 5.88041e-05 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | raw_perf | fraction | 0.715835 | 3/3 | 0 | 1 | 0.715835 | 3 / 0.00272908 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | raw_perf | fraction | 0.959279 | 3/3 | 0 | 1 | 0.959279 | 3 / 0.00126525 |
| expgym | tuning | family/nasbench101 | cost_tight | single | gap | Gap points | 93.8152 | 9/9 | 0 | 3 | 93.8152 | 3 / 1.86971 |
| expgym | tuning | family/nasbench201 | cost_tight | single | gap | Gap points | 85.449 | 9/9 | 0 | 3 | 85.449 | 3 / 11.4339 |
| expgym | tuning | family/paramnet | cost_tight | single | gap | Gap points | 77.8658 | 9/9 | 0 | 3 | 77.8658 | 3 / 10.3214 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | gap | Gap points | 89.6754 | 3/3 | 0 | 1 | 89.6754 | 3 / 6.78753 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | gap | Gap points | 93.2704 | 3/3 | 0 | 1 | 93.2704 | 3 / 3.21481 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | gap | Gap points | 98.4996 | 3/3 | 0 | 1 | 98.4996 | 3 / 1.45978 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | gap | Gap points | 96.4601 | 3/3 | 0 | 1 | 96.4601 | 3 / 4.97083 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | gap | Gap points | 90.0806 | 3/3 | 0 | 1 | 90.0806 | 3 / 8.59118 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | gap | Gap points | 69.8063 | 3/3 | 0 | 1 | 69.8063 | 3 / 22.9407 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | gap | Gap points | 76.9214 | 3/3 | 0 | 1 | 76.9214 | 3 / 8.50082 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | gap | Gap points | 65.5332 | 3/3 | 0 | 1 | 65.5332 | 3 / 39.3181 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | gap | Gap points | 91.1429 | 3/3 | 0 | 1 | 91.1429 | 3 / 6.14472 |
| expgym | tuning | family/nasbench101 | cost_tight | single | raw_perf | fraction | 0.914118 | 9/9 | 0 | 3 | 0.914118 | 3 / 0.0128924 |
| expgym | tuning | family/nasbench201 | cost_tight | single | raw_perf | fraction | 0.688255 | 9/9 | 0 | 3 | 0.688255 | 3 / 0.0142979 |
| expgym | tuning | family/paramnet | cost_tight | single | raw_perf | fraction | 0.817976 | 9/9 | 0 | 3 | 0.817976 | 3 / 0.0142211 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | raw_perf | fraction | 0.873453 | 3/3 | 0 | 1 | 0.873453 | 3 / 0.0477463 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | raw_perf | fraction | 0.931802 | 3/3 | 0 | 1 | 0.931802 | 3 / 0.00819265 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | raw_perf | fraction | 0.937099 | 3/3 | 0 | 1 | 0.937099 | 3 / 0.00825052 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | raw_perf | fraction | 0.913249 | 3/3 | 0 | 1 | 0.913249 | 3 / 0.00395677 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | raw_perf | fraction | 0.722922 | 3/3 | 0 | 1 | 0.722922 | 3 / 0.0104894 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | raw_perf | fraction | 0.428593 | 3/3 | 0 | 1 | 0.428593 | 3 / 0.0302788 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | raw_perf | fraction | 0.844225 | 3/3 | 0 | 1 | 0.844225 | 3 / 0.00350152 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | raw_perf | fraction | 0.691069 | 3/3 | 0 | 1 | 0.691069 | 3 / 0.0342191 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | raw_perf | fraction | 0.918634 | 3/3 | 0 | 1 | 0.918634 | 3 / 0.0322563 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | evidence_acc_mi | fraction | 0.71267 | 13/13 | 0 | 13 | 0.71267 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | evidence_acc_mv | fraction | 0.746606 | 13/13 | 0 | 13 | 0.746606 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | label_acc_mi | fraction | 0.891403 | 13/13 | 0 | 13 | 0.891403 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | label_acc_mv | fraction | 0.891403 | 13/13 | 0 | 13 | 0.891403 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | evidence_acc_mi | fraction | 0.676471 | 13/13 | 0 | 13 | 0.676471 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | evidence_acc_mv | fraction | 0.687783 | 13/13 | 0 | 13 | 0.687783 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | label_acc_mi | fraction | 0.890271 | 13/13 | 0 | 13 | 0.890271 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | label_acc_mv | fraction | 0.900452 | 13/13 | 0 | 13 | 0.900452 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | evidence_acc_mi | fraction | 0.924208 | 13/13 | 0 | 13 | 0.924208 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | evidence_acc_mv | fraction | 0.936652 | 13/13 | 0 | 13 | 0.936652 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | label_acc_mi | fraction | 0.95362 | 13/13 | 0 | 13 | 0.95362 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | label_acc_mv | fraction | 0.959276 | 13/13 | 0 | 13 | 0.959276 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | evidence_acc_mi | fraction | 0.590498 | 13/13 | 0 | 13 | 0.590498 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | evidence_acc_mv | fraction | 0.60181 | 13/13 | 0 | 13 | 0.60181 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | label_acc_mi | fraction | 0.837104 | 13/13 | 0 | 13 | 0.837104 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | label_acc_mv | fraction | 0.837104 | 13/13 | 0 | 13 | 0.837104 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | evidence_acc_mi | fraction | 0.552036 | 13/13 | 0 | 13 | 0.552036 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | evidence_acc_mv | fraction | 0.561086 | 13/13 | 0 | 13 | 0.561086 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | label_acc_mi | fraction | 0.816742 | 13/13 | 0 | 13 | 0.816742 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | label_acc_mv | fraction | 0.832579 | 13/13 | 0 | 13 | 0.832579 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | evidence_acc_mi | fraction | 0.632353 | 13/13 | 0 | 13 | 0.632353 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | evidence_acc_mv | fraction | 0.638009 | 13/13 | 0 | 13 | 0.638009 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | label_acc_mi | fraction | 0.854072 | 13/13 | 0 | 13 | 0.854072 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | label_acc_mv | fraction | 0.855204 | 13/13 | 0 | 13 | 0.855204 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | f1_mi | fraction | 0.590689 | 39/39 | 0 | 39 | 0.590689 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | f1_mv | fraction | 0.611731 | 39/39 | 0 | 39 | 0.611731 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | f1_mi | fraction | 0.588896 | 39/39 | 0 | 39 | 0.588896 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | f1_mv | fraction | 0.612138 | 39/39 | 0 | 39 | 0.612138 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | f1_mi | fraction | 0.623277 | 39/39 | 0 | 39 | 0.623277 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | f1_mv | fraction | 0.634849 | 39/39 | 0 | 39 | 0.634849 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | f1_mi | fraction | 0.223102 | 39/39 | 0 | 39 | 0.223102 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | f1_mv | fraction | 0.233139 | 39/39 | 0 | 39 | 0.233139 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | f1_mi | fraction | 0.18552 | 39/39 | 0 | 39 | 0.18552 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | f1_mv | fraction | 0.182956 | 39/39 | 0 | 39 | 0.182956 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | f1_mi | fraction | 0.2269 | 39/39 | 0 | 39 | 0.2269 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | f1_mv | fraction | 0.206888 | 39/39 | 0 | 39 | 0.206888 | 1 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_bon | Gap points | 99.0035 | 9/9 | 0 | 3 | 99.0035 | 3 / 0.59512 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_bon | Gap points | 99.3561 | 3/3 | 0 | 1 | 99.3561 | 3 / 0.124884 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_bon | Gap points | 98.0916 | 3/3 | 0 | 1 | 98.0916 | 3 / 1.69431 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_bon | Gap points | 99.5629 | 3/3 | 0 | 1 | 99.5629 | 3 / 0.0328887 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | gap_mi | Gap points | 97.7233 | 9/9 | 0 | 3 | 97.7233 | 3 / 0.787076 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | gap_mi | Gap points | 98.3392 | 3/3 | 0 | 1 | 98.3392 | 3 / 0.222193 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | gap_mi | Gap points | 96.1811 | 3/3 | 0 | 1 | 96.1811 | 3 / 2.7171 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | gap_mi | Gap points | 98.6497 | 3/3 | 0 | 1 | 98.6497 | 3 / 0.205769 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_bon | fraction | 0.942916 | 9/9 | 0 | 3 | 0.942916 | 3 / 0.00166549 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_bon | fraction | 0.941551 | 3/3 | 0 | 1 | 0.941551 | 3 / 0.000878487 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_bon | fraction | 0.944088 | 3/3 | 0 | 1 | 0.944088 | 3 / 0.0043178 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_bon | fraction | 0.943109 | 3/3 | 0 | 1 | 0.943109 | 3 / 0.000185883 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | raw_perf_mi | fraction | 0.937188 | 9/9 | 0 | 3 | 0.937188 | 3 / 0.00156556 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | raw_perf_mi | fraction | 0.934398 | 3/3 | 0 | 1 | 0.934398 | 3 / 0.001563 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | raw_perf_mi | fraction | 0.939219 | 3/3 | 0 | 1 | 0.939219 | 3 / 0.00692429 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | raw_perf_mi | fraction | 0.937948 | 3/3 | 0 | 1 | 0.937948 | 3 / 0.00116299 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_bon | Gap points | 98.7009 | 9/9 | 0 | 3 | 98.7009 | 3 / 0.268677 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_bon | Gap points | 99.2675 | 3/3 | 0 | 1 | 99.2675 | 3 / 0.518301 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_bon | Gap points | 97.227 | 3/3 | 0 | 1 | 97.227 | 3 / 0.777756 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_bon | Gap points | 99.6082 | 3/3 | 0 | 1 | 99.6082 | 3 / 0.384208 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | gap_mi | Gap points | 96.923 | 9/9 | 0 | 3 | 96.923 | 3 / 0.717014 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | gap_mi | Gap points | 97.3967 | 3/3 | 0 | 1 | 97.3967 | 3 / 1.5394 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | gap_mi | Gap points | 94.5816 | 3/3 | 0 | 1 | 94.5816 | 3 / 0.822795 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | gap_mi | Gap points | 98.7905 | 3/3 | 0 | 1 | 98.7905 | 3 / 0.363373 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_bon | fraction | 0.942059 | 9/9 | 0 | 3 | 0.942059 | 3 / 0.000950685 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_bon | fraction | 0.940928 | 3/3 | 0 | 1 | 0.940928 | 3 / 0.00364594 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_bon | fraction | 0.941885 | 3/3 | 0 | 1 | 0.941885 | 3 / 0.00198204 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_bon | fraction | 0.943365 | 3/3 | 0 | 1 | 0.943365 | 3 / 0.0021715 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | raw_perf_mi | fraction | 0.933885 | 9/9 | 0 | 3 | 0.933885 | 3 / 0.00442297 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | raw_perf_mi | fraction | 0.927768 | 3/3 | 0 | 1 | 0.927768 | 3 / 0.0108288 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | raw_perf_mi | fraction | 0.935143 | 3/3 | 0 | 1 | 0.935143 | 3 / 0.00209682 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | raw_perf_mi | fraction | 0.938744 | 3/3 | 0 | 1 | 0.938744 | 3 / 0.00205374 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_bon | Gap points | 99.1479 | 9/9 | 0 | 3 | 99.1479 | 3 / 0.267095 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_bon | Gap points | 99.4336 | 3/3 | 0 | 1 | 99.4336 | 3 / 0.370275 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_bon | Gap points | 98.1047 | 3/3 | 0 | 1 | 98.1047 | 3 / 0.511838 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_bon | Gap points | 99.9055 | 3/3 | 0 | 1 | 99.9055 | 3 / 0.341953 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | gap_mi | Gap points | 98.8695 | 9/9 | 0 | 3 | 98.8695 | 3 / 0.264573 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | gap_mi | Gap points | 99.2825 | 3/3 | 0 | 1 | 99.2825 | 3 / 0.328324 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | gap_mi | Gap points | 97.573 | 3/3 | 0 | 1 | 97.573 | 3 / 0.543601 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | gap_mi | Gap points | 99.7529 | 3/3 | 0 | 1 | 99.7529 | 3 / 0.309797 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_bon | fraction | 0.943754 | 9/9 | 0 | 3 | 0.943754 | 3 / 0.00106122 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_bon | fraction | 0.942096 | 3/3 | 0 | 1 | 0.942096 | 3 / 0.00260467 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_bon | fraction | 0.944122 | 3/3 | 0 | 1 | 0.944122 | 3 / 0.00130437 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_bon | fraction | 0.945045 | 3/3 | 0 | 1 | 0.945045 | 3 / 0.00193268 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | raw_perf_mi | fraction | 0.942661 | 9/9 | 0 | 3 | 0.942661 | 3 / 0.00103685 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | raw_perf_mi | fraction | 0.941033 | 3/3 | 0 | 1 | 0.941033 | 3 / 0.00230956 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | raw_perf_mi | fraction | 0.942767 | 3/3 | 0 | 1 | 0.942767 | 3 / 0.00138532 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | raw_perf_mi | fraction | 0.944183 | 3/3 | 0 | 1 | 0.944183 | 3 / 0.00175094 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_bon | Gap points | 98.1504 | 9/9 | 0 | 3 | 98.1504 | 3 / 0.316521 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_bon | Gap points | 97.7535 | 3/3 | 0 | 1 | 97.7535 | 3 / 1.40464 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_bon | Gap points | 97.5326 | 3/3 | 0 | 1 | 97.5326 | 3 / 0.314516 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_bon | Gap points | 99.1651 | 3/3 | 0 | 1 | 99.1651 | 3 / 0.305253 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | gap_mi | Gap points | 90.7576 | 9/9 | 0 | 3 | 90.7576 | 3 / 4.33446 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | gap_mi | Gap points | 86.1534 | 3/3 | 0 | 1 | 86.1534 | 3 / 11.3399 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | gap_mi | Gap points | 88.9362 | 3/3 | 0 | 1 | 88.9362 | 3 / 2.72392 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | gap_mi | Gap points | 97.1833 | 3/3 | 0 | 1 | 97.1833 | 3 / 1.05872 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_bon | fraction | 0.937934 | 9/9 | 0 | 3 | 0.937934 | 3 / 0.00258256 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_bon | fraction | 0.930277 | 3/3 | 0 | 1 | 0.930277 | 3 / 0.0098808 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_bon | fraction | 0.942664 | 3/3 | 0 | 1 | 0.942664 | 3 / 0.000801517 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_bon | fraction | 0.940861 | 3/3 | 0 | 1 | 0.940861 | 3 / 0.00172526 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | raw_perf_mi | fraction | 0.899698 | 9/9 | 0 | 3 | 0.899698 | 3 / 0.0275565 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | raw_perf_mi | fraction | 0.848677 | 3/3 | 0 | 1 | 0.848677 | 3 / 0.0797695 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | raw_perf_mi | fraction | 0.920757 | 3/3 | 0 | 1 | 0.920757 | 3 / 0.00694166 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | raw_perf_mi | fraction | 0.92966 | 3/3 | 0 | 1 | 0.92966 | 3 / 0.00598378 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_bon | Gap points | 98.5243 | 9/9 | 0 | 3 | 98.5243 | 3 / 0.495823 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_bon | Gap points | 99.2169 | 3/3 | 0 | 1 | 99.2169 | 3 / 0.511468 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_bon | Gap points | 96.9999 | 3/3 | 0 | 1 | 96.9999 | 3 / 0.659229 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_bon | Gap points | 99.3561 | 3/3 | 0 | 1 | 99.3561 | 3 / 0.596361 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | gap_mi | Gap points | 90.6211 | 9/9 | 0 | 3 | 90.6211 | 3 / 3.79446 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | gap_mi | Gap points | 85.5658 | 3/3 | 0 | 1 | 85.5658 | 3 / 11.6551 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | gap_mi | Gap points | 89.0945 | 3/3 | 0 | 1 | 89.0945 | 3 / 1.50264 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | gap_mi | Gap points | 97.203 | 3/3 | 0 | 1 | 97.203 | 3 / 1.88909 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_bon | fraction | 0.941273 | 9/9 | 0 | 3 | 0.941273 | 3 / 0.00229571 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_bon | fraction | 0.940572 | 3/3 | 0 | 1 | 0.940572 | 3 / 0.00359788 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_bon | fraction | 0.941306 | 3/3 | 0 | 1 | 0.941306 | 3 / 0.00167999 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_bon | fraction | 0.94194 | 3/3 | 0 | 1 | 0.94194 | 3 / 0.00337057 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | raw_perf_mi | fraction | 0.891752 | 9/9 | 0 | 3 | 0.891752 | 3 / 0.0391485 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | raw_perf_mi | fraction | 0.824324 | 3/3 | 0 | 1 | 0.824324 | 3 / 0.116938 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | raw_perf_mi | fraction | 0.92116 | 3/3 | 0 | 1 | 0.92116 | 3 / 0.00382935 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | raw_perf_mi | fraction | 0.929771 | 3/3 | 0 | 1 | 0.929771 | 3 / 0.0106769 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_bon | Gap points | 98.2911 | 9/9 | 0 | 3 | 98.2911 | 3 / 0.166013 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_bon | Gap points | 98.2819 | 3/3 | 0 | 1 | 98.2819 | 3 / 0.596738 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_bon | Gap points | 97.6331 | 3/3 | 0 | 1 | 97.6331 | 3 / 0.322064 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_bon | Gap points | 98.9584 | 3/3 | 0 | 1 | 98.9584 | 3 / 0.375154 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | gap_mi | Gap points | 96.2707 | 9/9 | 0 | 3 | 96.2707 | 3 / 0.86707 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | gap_mi | Gap points | 96.6694 | 3/3 | 0 | 1 | 96.6694 | 3 / 1.79282 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | gap_mi | Gap points | 93.7115 | 3/3 | 0 | 1 | 93.7115 | 3 / 3.36251 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | gap_mi | Gap points | 98.4312 | 3/3 | 0 | 1 | 98.4312 | 3 / 0.771057 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_bon | fraction | 0.938869 | 9/9 | 0 | 3 | 0.938869 | 3 / 0.001521 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_bon | fraction | 0.933994 | 3/3 | 0 | 1 | 0.933994 | 3 / 0.00419771 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_bon | fraction | 0.94292 | 3/3 | 0 | 1 | 0.94292 | 3 / 0.000820752 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_bon | fraction | 0.939692 | 3/3 | 0 | 1 | 0.939692 | 3 / 0.00212033 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | raw_perf_mi | fraction | 0.930763 | 9/9 | 0 | 3 | 0.930763 | 3 / 0.00170524 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | raw_perf_mi | fraction | 0.922651 | 3/3 | 0 | 1 | 0.922651 | 3 / 0.0126114 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | raw_perf_mi | fraction | 0.932926 | 3/3 | 0 | 1 | 0.932926 | 3 / 0.00856906 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | raw_perf_mi | fraction | 0.936713 | 3/3 | 0 | 1 | 0.936713 | 3 / 0.00435793 |


## 质量：全部对应差值

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | family/evidence_audit | cost_free | evidence_acc | cost_free − cost_moderate | +0.168929 | fraction | +16.8929 | 13/13 | 0 | 0.168929 |
| expgym | evidence_audit | family/evidence_audit | cost_free | evidence_acc | cost_free − cost_tight | +0.334842 | fraction | +33.4842 | 13/13 | 0 | 0.334842 |
| expgym | evidence_audit | family/evidence_audit | cost_free | label_acc | cost_free − cost_moderate | +0.0648567 | fraction | +6.48567 | 13/13 | 0 | 0.0648567 |
| expgym | evidence_audit | family/evidence_audit | cost_free | label_acc | cost_free − cost_tight | +0.116139 | fraction | +11.6139 | 13/13 | 0 | 0.116139 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc | cost_moderate − cost_tight | +0.165913 | fraction | +16.5913 | 13/13 | 0 | 0.165913 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | label_acc | cost_moderate − cost_tight | +0.0512821 | fraction | +5.12821 | 13/13 | 0 | 0.0512821 |
| expgym | restricted_search | family/whatis | cost_free | f1 | cost_free − cost_moderate | +0.119652 | fraction | +11.9652 | 34/34 | 0 | 0.119652 |
| expgym | restricted_search | family/whatis | cost_free | f1 | cost_free − cost_tight | +0.375403 | fraction | +37.5403 | 34/34 | 0 | 0.375403 |
| expgym | restricted_search | family/whois | cost_free | f1 | cost_free − cost_moderate | +0.0298183 | fraction | +2.98183 | 39/39 | 0 | 0.0298183 |
| expgym | restricted_search | family/whois | cost_free | f1 | cost_free − cost_tight | +0.415411 | fraction | +41.5411 | 39/39 | 0 | 0.415411 |
| expgym | restricted_search | family/whatis | cost_moderate | f1 | cost_moderate − cost_tight | +0.25575 | fraction | +25.575 | 34/34 | 0 | 0.25575 |
| expgym | restricted_search | family/whois | cost_moderate | f1 | cost_moderate − cost_tight | +0.385592 | fraction | +38.5592 | 39/39 | 0 | 0.385592 |
| expgym | tuning | family/nasbench101 | cost_free | gap | cost_free − cost_moderate | +2.15077 | Gap points | 不适用 | 9/9 | 0 | 2.15077 |
| expgym | tuning | family/nasbench101 | cost_free | gap | cost_free − cost_tight | +4.84661 | Gap points | 不适用 | 9/9 | 0 | 4.84661 |
| expgym | tuning | family/nasbench201 | cost_free | gap | cost_free − cost_moderate | +4.51514 | Gap points | 不适用 | 9/9 | 0 | 4.51514 |
| expgym | tuning | family/nasbench201 | cost_free | gap | cost_free − cost_tight | +13.0026 | Gap points | 不适用 | 9/9 | 0 | 13.0026 |
| expgym | tuning | family/paramnet | cost_free | gap | cost_free − cost_moderate | +0.329597 | Gap points | 不适用 | 9/9 | 0 | 0.329597 |
| expgym | tuning | family/paramnet | cost_free | gap | cost_free − cost_tight | +17.4164 | Gap points | 不适用 | 9/9 | 0 | 17.4164 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | gap | cost_free − cost_moderate | +1.39064 | Gap points | 不适用 | 3/3 | 0 | 1.39064 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | gap | cost_free − cost_tight | +9.90532 | Gap points | 不适用 | 3/3 | 0 | 9.90532 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | gap | cost_free − cost_moderate | +4.46308 | Gap points | 不适用 | 3/3 | 0 | 4.46308 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | gap | cost_free − cost_tight | +3.84296 | Gap points | 不适用 | 3/3 | 0 | 3.84296 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | gap | cost_free − cost_moderate | +0.598593 | Gap points | 不适用 | 3/3 | 0 | 0.598593 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | gap | cost_free − cost_tight | +0.791563 | Gap points | 不适用 | 3/3 | 0 | 0.791563 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | gap | cost_free − cost_moderate | +6.08599 | Gap points | 不适用 | 3/3 | 0 | 6.08599 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | gap | cost_free − cost_tight | +2.84199 | Gap points | 不适用 | 3/3 | 0 | 2.84199 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | gap | cost_free − cost_moderate | -2.3479 | Gap points | 不适用 | 3/3 | 0 | -2.3479 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | gap | cost_free − cost_tight | +7.57154 | Gap points | 不适用 | 3/3 | 0 | 7.57154 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | gap | cost_free − cost_moderate | +9.80734 | Gap points | 不适用 | 3/3 | 0 | 9.80734 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | gap | cost_free − cost_tight | +28.5942 | Gap points | 不适用 | 3/3 | 0 | 28.5942 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | gap | cost_free − cost_moderate | +2.60758 | Gap points | 不适用 | 3/3 | 0 | 2.60758 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | gap | cost_free − cost_tight | +17.6686 | Gap points | 不适用 | 3/3 | 0 | 17.6686 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | gap | cost_free − cost_moderate | +0.0052971 | Gap points | 不适用 | 3/3 | 0 | 0.0052971 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | gap | cost_free − cost_tight | +28.462 | Gap points | 不适用 | 3/3 | 0 | 28.462 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | gap | cost_free − cost_moderate | -1.62409 | Gap points | 不适用 | 3/3 | 0 | -1.62409 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | gap | cost_free − cost_tight | +6.11869 | Gap points | 不适用 | 3/3 | 0 | 6.11869 |
| expgym | tuning | family/nasbench101 | cost_free | raw_perf | cost_free − cost_moderate | +0.00817975 | fraction | +0.817975 | 9/9 | 0 | 0.00817975 |
| expgym | tuning | family/nasbench101 | cost_free | raw_perf | cost_free − cost_tight | +0.0279818 | fraction | +2.79818 | 9/9 | 0 | 0.0279818 |
| expgym | tuning | family/nasbench201 | cost_free | raw_perf | cost_free − cost_moderate | +0.00497407 | fraction | +0.497407 | 9/9 | 0 | 0.00497407 |
| expgym | tuning | family/nasbench201 | cost_free | raw_perf | cost_free − cost_tight | +0.0164158 | fraction | +1.64158 | 9/9 | 0 | 0.0164158 |
| expgym | tuning | family/paramnet | cost_free | raw_perf | cost_free − cost_moderate | -0.00248229 | fraction | -0.248229 | 9/9 | 0 | -0.00248229 |
| expgym | tuning | family/paramnet | cost_free | raw_perf | cost_free − cost_tight | +0.0213895 | fraction | +2.13895 | 9/9 | 0 | 0.0213895 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | raw_perf | cost_free − cost_moderate | +0.00978231 | fraction | +0.978231 | 3/3 | 0 | 0.00978231 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | raw_perf | cost_free − cost_tight | +0.0696781 | fraction | +6.96781 | 3/3 | 0 | 0.0696781 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | raw_perf | cost_free − cost_moderate | +0.0113738 | fraction | +1.13738 | 3/3 | 0 | 0.0113738 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | raw_perf | cost_free − cost_tight | +0.00979343 | fraction | +0.979343 | 3/3 | 0 | 0.00979343 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | raw_perf | cost_free − cost_moderate | +0.00338319 | fraction | +0.338319 | 3/3 | 0 | 0.00338319 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | raw_perf | cost_free − cost_tight | +0.00447383 | fraction | +0.447383 | 3/3 | 0 | 0.00447383 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | raw_perf | cost_free − cost_moderate | +0.00484444 | fraction | +0.484444 | 3/3 | 0 | 0.00484444 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | raw_perf | cost_free − cost_tight | +0.00226222 | fraction | +0.226222 | 3/3 | 0 | 0.00226222 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | raw_perf | cost_free − cost_moderate | -0.00286667 | fraction | -0.286667 | 3/3 | 0 | -0.00286667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | raw_perf | cost_free − cost_tight | +0.00924444 | fraction | +0.924444 | 3/3 | 0 | 0.00924444 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | raw_perf | cost_free − cost_moderate | +0.0129444 | fraction | +1.29444 | 3/3 | 0 | 0.0129444 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | raw_perf | cost_free − cost_tight | +0.0377407 | fraction | +3.77407 | 3/3 | 0 | 0.0377407 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | raw_perf | cost_free − cost_moderate | +0.00107407 | fraction | +0.107407 | 3/3 | 0 | 0.00107407 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | raw_perf | cost_free − cost_tight | +0.00727778 | fraction | +0.727778 | 3/3 | 0 | 0.00727778 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | raw_perf | cost_free − cost_moderate | +4.61014e-06 | fraction | +0.000461014 | 3/3 | 0 | 4.61014e-06 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | raw_perf | cost_free − cost_tight | +0.0247709 | fraction | +2.47709 | 3/3 | 0 | 0.0247709 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | raw_perf | cost_free − cost_moderate | -0.00852555 | fraction | -0.852555 | 3/3 | 0 | -0.00852555 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | raw_perf | cost_free − cost_tight | +0.0321197 | fraction | +3.21197 | 3/3 | 0 | 0.0321197 |
| expgym | tuning | family/nasbench101 | cost_moderate | gap | cost_moderate − cost_tight | +2.69585 | Gap points | 不适用 | 9/9 | 0 | 2.69585 |
| expgym | tuning | family/nasbench201 | cost_moderate | gap | cost_moderate − cost_tight | +8.48744 | Gap points | 不适用 | 9/9 | 0 | 8.48744 |
| expgym | tuning | family/paramnet | cost_moderate | gap | cost_moderate − cost_tight | +17.0868 | Gap points | 不适用 | 9/9 | 0 | 17.0868 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | gap | cost_moderate − cost_tight | +8.51469 | Gap points | 不适用 | 3/3 | 0 | 8.51469 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | gap | cost_moderate − cost_tight | -0.620119 | Gap points | 不适用 | 3/3 | 0 | -0.620119 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | gap | cost_moderate − cost_tight | +0.19297 | Gap points | 不适用 | 3/3 | 0 | 0.19297 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | gap | cost_moderate − cost_tight | -3.244 | Gap points | 不适用 | 3/3 | 0 | -3.244 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | gap | cost_moderate − cost_tight | +9.91944 | Gap points | 不适用 | 3/3 | 0 | 9.91944 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | gap | cost_moderate − cost_tight | +18.7869 | Gap points | 不适用 | 3/3 | 0 | 18.7869 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | gap | cost_moderate − cost_tight | +15.061 | Gap points | 不适用 | 3/3 | 0 | 15.061 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | gap | cost_moderate − cost_tight | +28.4567 | Gap points | 不适用 | 3/3 | 0 | 28.4567 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | gap | cost_moderate − cost_tight | +7.74277 | Gap points | 不适用 | 3/3 | 0 | 7.74277 |
| expgym | tuning | family/nasbench101 | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0198021 | fraction | +1.98021 | 9/9 | 0 | 0.0198021 |
| expgym | tuning | family/nasbench201 | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0114417 | fraction | +1.14417 | 9/9 | 0 | 0.0114417 |
| expgym | tuning | family/paramnet | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0238718 | fraction | +2.38718 | 9/9 | 0 | 0.0238718 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0598958 | fraction | +5.98958 | 3/3 | 0 | 0.0598958 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.00158032 | fraction | -0.158032 | 3/3 | 0 | -0.00158032 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.00109065 | fraction | +0.109065 | 3/3 | 0 | 0.00109065 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | raw_perf | cost_moderate − cost_tight | -0.00258222 | fraction | -0.258222 | 3/3 | 0 | -0.00258222 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0121111 | fraction | +1.21111 | 3/3 | 0 | 0.0121111 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0247963 | fraction | +2.47963 | 3/3 | 0 | 0.0247963 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.00620371 | fraction | +0.620371 | 3/3 | 0 | 0.00620371 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0247663 | fraction | +2.47663 | 3/3 | 0 | 0.0247663 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | raw_perf | cost_moderate − cost_tight | +0.0406453 | fraction | +4.06453 | 3/3 | 0 | 0.0406453 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | poolact − cached | +0.211538 | fraction | +21.1538 | 13/13 | 0 | 0.211538 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | poolact − cached | +0.190045 | fraction | +19.0045 | 13/13 | 0 | 0.190045 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | poolact − cached | +0.0622172 | fraction | +6.22172 | 13/13 | 0 | 0.0622172 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | poolact − cached | +0.0678733 | fraction | +6.78733 | 13/13 | 0 | 0.0678733 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | cached − naive | +0.0361991 | fraction | +3.61991 | 13/13 | 0 | 0.0361991 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mi | poolact − naive | +0.247738 | fraction | +24.7738 | 13/13 | 0 | 0.247738 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | cached − naive | +0.0588235 | fraction | +5.88235 | 13/13 | 0 | 0.0588235 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | evidence_acc_mv | poolact − naive | +0.248869 | fraction | +24.8869 | 13/13 | 0 | 0.248869 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | cached − naive | +0.00113122 | fraction | +0.113122 | 13/13 | 0 | 0.00113122 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mi | poolact − naive | +0.0633484 | fraction | +6.33484 | 13/13 | 0 | 0.0633484 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | cached − naive | -0.00904977 | fraction | -0.904977 | 13/13 | 0 | -0.00904977 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | label_acc_mv | poolact − naive | +0.0588235 | fraction | +5.88235 | 13/13 | 0 | 0.0588235 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | poolact − cached | +0.0418552 | fraction | +4.18552 | 13/13 | 0 | 0.0418552 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | poolact − cached | +0.0361991 | fraction | +3.61991 | 13/13 | 0 | 0.0361991 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | poolact − cached | +0.0169683 | fraction | +1.69683 | 13/13 | 0 | 0.0169683 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | poolact − cached | +0.0180995 | fraction | +1.80995 | 13/13 | 0 | 0.0180995 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | cached − naive | +0.0384615 | fraction | +3.84615 | 13/13 | 0 | 0.0384615 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mi | poolact − naive | +0.0803167 | fraction | +8.03167 | 13/13 | 0 | 0.0803167 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | cached − naive | +0.040724 | fraction | +4.0724 | 13/13 | 0 | 0.040724 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | evidence_acc_mv | poolact − naive | +0.0769231 | fraction | +7.69231 | 13/13 | 0 | 0.0769231 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | cached − naive | +0.020362 | fraction | +2.0362 | 13/13 | 0 | 0.020362 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mi | poolact − naive | +0.0373303 | fraction | +3.73303 | 13/13 | 0 | 0.0373303 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | cached − naive | +0.00452489 | fraction | +0.452489 | 13/13 | 0 | 0.00452489 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | label_acc_mv | poolact − naive | +0.0226244 | fraction | +2.26244 | 13/13 | 0 | 0.0226244 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | poolact − cached | +0.0325878 | fraction | +3.25878 | 39/39 | 0 | 0.0325878 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | poolact − cached | +0.0231176 | fraction | +2.31176 | 39/39 | 0 | 0.0231176 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | cached − naive | +0.0017932 | fraction | +0.17932 | 39/39 | 0 | 0.0017932 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mi | poolact − naive | +0.034381 | fraction | +3.4381 | 39/39 | 0 | 0.034381 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | cached − naive | -0.000407 | fraction | -0.0407 | 39/39 | 0 | -0.000407 |
| poolact | restricted_search | family/whois | cost_moderate | f1_mv | poolact − naive | +0.0227106 | fraction | +2.27106 | 39/39 | 0 | 0.0227106 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | poolact − cached | +0.00379751 | fraction | +0.379751 | 39/39 | 0 | 0.00379751 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | poolact − cached | -0.0262515 | fraction | -2.62515 | 39/39 | 0 | -0.0262515 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | cached − naive | +0.0375819 | fraction | +3.75819 | 39/39 | 0 | 0.0375819 |
| poolact | restricted_search | family/whois | cost_tight | f1_mi | poolact − naive | +0.0413794 | fraction | +4.13794 | 39/39 | 0 | 0.0413794 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | cached − naive | +0.0501832 | fraction | +5.01832 | 39/39 | 0 | 0.0501832 |
| poolact | restricted_search | family/whois | cost_tight | f1_mv | poolact − naive | +0.0239316 | fraction | +2.39316 | 39/39 | 0 | 0.0239316 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | poolact − cached | +0.144411 | Gap points | 不适用 | 9/9 | 0 | 0.144411 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | poolact − cached | +0.0775193 | Gap points | 不适用 | 3/3 | 0 | 0.0775193 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | poolact − cached | +0.0130978 | Gap points | 不适用 | 3/3 | 0 | 0.0130978 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | poolact − cached | +0.342615 | Gap points | 不适用 | 3/3 | 0 | 0.342615 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | poolact − cached | +1.14615 | Gap points | 不适用 | 9/9 | 0 | 1.14615 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | poolact − cached | +0.943307 | Gap points | 不适用 | 3/3 | 0 | 0.943307 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | poolact − cached | +1.39198 | Gap points | 不适用 | 3/3 | 0 | 1.39198 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | poolact − cached | +1.10316 | Gap points | 不适用 | 3/3 | 0 | 1.10316 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | poolact − cached | +0.000838368 | fraction | +0.0838368 | 9/9 | 0 | 0.000838368 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | poolact − cached | +0.000545303 | fraction | +0.0545303 | 3/3 | 0 | 0.000545303 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | poolact − cached | +3.33786e-05 | fraction | +0.00333786 | 3/3 | 0 | 3.33786e-05 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | poolact − cached | +0.00193642 | fraction | +0.193642 | 3/3 | 0 | 0.00193642 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | poolact − cached | +0.00547264 | fraction | +0.547264 | 9/9 | 0 | 0.00547264 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | poolact − cached | +0.00663561 | fraction | +0.663561 | 3/3 | 0 | 0.00663561 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | poolact − cached | +0.00354734 | fraction | +0.354734 | 3/3 | 0 | 0.00354734 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | poolact − cached | +0.00623497 | fraction | +0.623497 | 3/3 | 0 | 0.00623497 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | cached − naive | +0.302657 | Gap points | 不适用 | 9/9 | 0 | 0.302657 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_bon | poolact − naive | +0.447068 | Gap points | 不适用 | 9/9 | 0 | 0.447068 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | cached − naive | +0.0885967 | Gap points | 不适用 | 3/3 | 0 | 0.0885967 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_bon | poolact − naive | +0.166116 | Gap points | 不适用 | 3/3 | 0 | 0.166116 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | cached − naive | +0.864664 | Gap points | 不适用 | 3/3 | 0 | 0.864664 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_bon | poolact − naive | +0.877761 | Gap points | 不适用 | 3/3 | 0 | 0.877761 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | cached − naive | -0.0452879 | Gap points | 不适用 | 3/3 | 0 | -0.0452879 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_bon | poolact − naive | +0.297327 | Gap points | 不适用 | 3/3 | 0 | 0.297327 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | cached − naive | +0.800382 | Gap points | 不适用 | 9/9 | 0 | 0.800382 |
| poolact | tuning | family/nasbench101 | cost_moderate | gap_mi | poolact − naive | +1.94653 | Gap points | 不适用 | 9/9 | 0 | 1.94653 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | cached − naive | +0.942517 | Gap points | 不适用 | 3/3 | 0 | 0.942517 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | gap_mi | poolact − naive | +1.88582 | Gap points | 不适用 | 3/3 | 0 | 1.88582 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | cached − naive | +1.59942 | Gap points | 不适用 | 3/3 | 0 | 1.59942 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | gap_mi | poolact − naive | +2.9914 | Gap points | 不适用 | 3/3 | 0 | 2.9914 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | cached − naive | -0.140787 | Gap points | 不适用 | 3/3 | 0 | -0.140787 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | gap_mi | poolact − naive | +0.962377 | Gap points | 不适用 | 3/3 | 0 | 0.962377 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | cached − naive | +0.000856927 | fraction | +0.0856927 | 9/9 | 0 | 0.000856927 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_bon | poolact − naive | +0.0016953 | fraction | +0.16953 | 9/9 | 0 | 0.0016953 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | cached − naive | +0.000623226 | fraction | +0.0623226 | 3/3 | 0 | 0.000623226 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_bon | poolact − naive | +0.00116853 | fraction | +0.116853 | 3/3 | 0 | 0.00116853 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | cached − naive | +0.00220352 | fraction | +0.220352 | 3/3 | 0 | 0.00220352 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_bon | poolact − naive | +0.0022369 | fraction | +0.22369 | 3/3 | 0 | 0.0022369 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | cached − naive | -0.000255962 | fraction | -0.0255962 | 3/3 | 0 | -0.000255962 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_bon | poolact − naive | +0.00168046 | fraction | +0.168046 | 3/3 | 0 | 0.00168046 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | cached − naive | +0.00330344 | fraction | +0.330344 | 9/9 | 0 | 0.00330344 |
| poolact | tuning | family/nasbench101 | cost_moderate | raw_perf_mi | poolact − naive | +0.00877608 | fraction | +0.877608 | 9/9 | 0 | 0.00877608 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | cached − naive | +0.00663005 | fraction | +0.663005 | 3/3 | 0 | 0.00663005 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | raw_perf_mi | poolact − naive | +0.0132657 | fraction | +1.32657 | 3/3 | 0 | 0.0132657 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | cached − naive | +0.00407597 | fraction | +0.407597 | 3/3 | 0 | 0.00407597 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | raw_perf_mi | poolact − naive | +0.00762331 | fraction | +0.762331 | 3/3 | 0 | 0.00762331 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | cached − naive | -0.000795715 | fraction | -0.0795715 | 3/3 | 0 | -0.000795715 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | raw_perf_mi | poolact − naive | +0.00543925 | fraction | +0.543925 | 3/3 | 0 | 0.00543925 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | poolact − cached | +0.140699 | Gap points | 不适用 | 9/9 | 0 | 0.140699 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | poolact − cached | +0.52841 | Gap points | 不适用 | 3/3 | 0 | 0.52841 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | poolact − cached | +0.10044 | Gap points | 不适用 | 3/3 | 0 | 0.10044 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | poolact − cached | -0.206754 | Gap points | 不适用 | 3/3 | 0 | -0.206754 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | poolact − cached | +5.51307 | Gap points | 不适用 | 9/9 | 0 | 5.51307 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | poolact − cached | +10.516 | Gap points | 不适用 | 3/3 | 0 | 10.516 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | poolact − cached | +4.77532 | Gap points | 不适用 | 3/3 | 0 | 4.77532 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | poolact − cached | +1.24789 | Gap points | 不适用 | 3/3 | 0 | 1.24789 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | poolact − cached | +0.000934824 | fraction | +0.0934824 | 9/9 | 0 | 0.000934824 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | poolact − cached | +0.00371706 | fraction | +0.371706 | 3/3 | 0 | 0.00371706 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | poolact − cached | +0.000255962 | fraction | +0.0255962 | 3/3 | 0 | 0.000255962 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | poolact − cached | -0.00116855 | fraction | -0.116855 | 3/3 | 0 | -0.00116855 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | poolact − cached | +0.0310654 | fraction | +3.10654 | 9/9 | 0 | 0.0310654 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | poolact − cached | +0.0739739 | fraction | +7.39739 | 3/3 | 0 | 0.0739739 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | poolact − cached | +0.0121695 | fraction | +1.21695 | 3/3 | 0 | 0.0121695 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | poolact − cached | +0.00705295 | fraction | +0.705295 | 3/3 | 0 | 0.00705295 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | cached − naive | -0.373878 | Gap points | 不适用 | 9/9 | 0 | -0.373878 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_bon | poolact − naive | -0.233179 | Gap points | 不适用 | 9/9 | 0 | -0.233179 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | cached − naive | -1.46341 | Gap points | 不适用 | 3/3 | 0 | -1.46341 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_bon | poolact − naive | -0.935003 | Gap points | 不适用 | 3/3 | 0 | -0.935003 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | cached − naive | +0.532777 | Gap points | 不适用 | 3/3 | 0 | 0.532777 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_bon | poolact − naive | +0.633217 | Gap points | 不适用 | 3/3 | 0 | 0.633217 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | cached − naive | -0.190998 | Gap points | 不适用 | 3/3 | 0 | -0.190998 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_bon | poolact − naive | -0.397751 | Gap points | 不适用 | 3/3 | 0 | -0.397751 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | cached − naive | +0.136512 | Gap points | 不适用 | 9/9 | 0 | 0.136512 |
| poolact | tuning | family/nasbench101 | cost_tight | gap_mi | poolact − naive | +5.64958 | Gap points | 不适用 | 9/9 | 0 | 5.64958 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | cached − naive | +0.587533 | Gap points | 不适用 | 3/3 | 0 | 0.587533 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | gap_mi | poolact − naive | +11.1035 | Gap points | 不适用 | 3/3 | 0 | 11.1035 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | cached − naive | -0.158306 | Gap points | 不适用 | 3/3 | 0 | -0.158306 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | gap_mi | poolact − naive | +4.61701 | Gap points | 不适用 | 3/3 | 0 | 4.61701 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | cached − naive | -0.0196902 | Gap points | 不适用 | 3/3 | 0 | -0.0196902 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | gap_mi | poolact − naive | +1.2282 | Gap points | 不适用 | 3/3 | 0 | 1.2282 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | cached − naive | -0.00333867 | fraction | -0.333867 | 9/9 | 0 | -0.00333867 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_bon | poolact − naive | -0.00240385 | fraction | -0.240385 | 9/9 | 0 | -0.00240385 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | cached − naive | -0.0102943 | fraction | -1.02943 | 3/3 | 0 | -0.0102943 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_bon | poolact − naive | -0.0065772 | fraction | -0.65772 | 3/3 | 0 | -0.0065772 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | cached − naive | +0.00135773 | fraction | +0.135773 | 3/3 | 0 | 0.00135773 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_bon | poolact − naive | +0.0016137 | fraction | +0.16137 | 3/3 | 0 | 0.0016137 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | cached − naive | -0.0010795 | fraction | -0.10795 | 3/3 | 0 | -0.0010795 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_bon | poolact − naive | -0.00224805 | fraction | -0.224805 | 3/3 | 0 | -0.00224805 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | cached − naive | +0.00794605 | fraction | +0.794605 | 9/9 | 0 | 0.00794605 |
| poolact | tuning | family/nasbench101 | cost_tight | raw_perf_mi | poolact − naive | +0.0390115 | fraction | +3.90115 | 9/9 | 0 | 0.0390115 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | cached − naive | +0.0243529 | fraction | +2.43529 | 3/3 | 0 | 0.0243529 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | raw_perf_mi | poolact − naive | +0.0983268 | fraction | +9.83268 | 3/3 | 0 | 0.0983268 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | cached − naive | -0.000403427 | fraction | -0.0403427 | 3/3 | 0 | -0.000403427 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | raw_perf_mi | poolact − naive | +0.011766 | fraction | +1.1766 | 3/3 | 0 | 0.011766 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | cached − naive | -0.000111287 | fraction | -0.0111287 | 3/3 | 0 | -0.000111287 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | raw_perf_mi | poolact − naive | +0.00694166 | fraction | +0.694166 | 3/3 | 0 | 0.00694166 |


## 资源：全部层次

| 系统 | 场景 | 层/切片 | 档位 | 策略 | 指标 | 单位 | 完整均值 | known/expected | missing | item 数 | 已知子集均值 | R / SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | single | duplicate_action_attempts | count | 0.025641 | 13/13 | 0 | 13 | 0.025641 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | duplicate_action_attempts | count | 0.025641 | 13/13 | 0 | 13 | 0.025641 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_attempts | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_attempts | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_cost_seconds | seconds | 8356.56 | 13/13 | 0 | 13 | 8356.56 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_cost_seconds | seconds | 8356.56 | 13/13 | 0 | 13 | 8356.56 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | feedback_visible | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | feedback_visible | count | 27.8205 | 13/13 | 0 | 13 | 27.8205 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | input_tokens | tokens | 307147 | 13/13 | 0 | 13 | 307147 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | input_tokens | tokens | 307147 | 13/13 | 0 | 13 | 307147 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | output_tokens | tokens | 13626.3 | 13/13 | 0 | 13 | 13626.3 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | output_tokens | tokens | 13626.3 | 13/13 | 0 | 13 | 13626.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | protocol_failure_rate | fraction | 0.01859 | 13/13 | 0 | 13 | 0.01859 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | protocol_failure_rate | fraction | 0.01859 | 13/13 | 0 | 13 | 0.01859 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_free | single | wall_time_seconds | seconds | 562.461 | 13/13 | 0 | 13 | 562.461 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_free | single | wall_time_seconds | seconds | 562.461 | 13/13 | 0 | 13 | 562.461 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | budget_utilization | fraction | 0.980844 | 13/13 | 0 | 13 | 0.980844 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | budget_utilization | fraction | 0.980844 | 13/13 | 0 | 13 | 0.980844 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_attempts | count | 9.76923 | 13/13 | 0 | 13 | 9.76923 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_attempts | count | 9.76923 | 13/13 | 0 | 13 | 9.76923 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2942.53 | 13/13 | 0 | 13 | 2942.53 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_cost_seconds | seconds | 2942.53 | 13/13 | 0 | 13 | 2942.53 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | feedback_visible | count | 9.35897 | 13/13 | 0 | 13 | 9.35897 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | feedback_visible | count | 9.35897 | 13/13 | 0 | 13 | 9.35897 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | input_tokens | tokens | 95237.2 | 13/13 | 0 | 13 | 95237.2 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | input_tokens | tokens | 95237.2 | 13/13 | 0 | 13 | 95237.2 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | output_tokens | tokens | 12671.3 | 13/13 | 0 | 13 | 12671.3 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | output_tokens | tokens | 12671.3 | 13/13 | 0 | 13 | 12671.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0042735 | 13/13 | 0 | 13 | 0.0042735 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | protocol_failure_rate | fraction | 0.0042735 | 13/13 | 0 | 13 | 0.0042735 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_moderate | single | wall_time_seconds | seconds | 464.679 | 13/13 | 0 | 13 | 464.679 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | single | wall_time_seconds | seconds | 464.679 | 13/13 | 0 | 13 | 464.679 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | budget_utilization | fraction | 1.01773 | 13/13 | 0 | 13 | 1.01773 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | budget_utilization | fraction | 1.01773 | 13/13 | 0 | 13 | 1.01773 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | duplicate_action_attempts | count | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_attempts | count | 3.05128 | 13/13 | 0 | 13 | 3.05128 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_attempts | count | 3.05128 | 13/13 | 0 | 13 | 3.05128 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_cost_seconds | seconds | 915.954 | 13/13 | 0 | 13 | 915.954 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_cost_seconds | seconds | 915.954 | 13/13 | 0 | 13 | 915.954 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | feedback_visible | count | 2.4359 | 13/13 | 0 | 13 | 2.4359 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | feedback_visible | count | 2.4359 | 13/13 | 0 | 13 | 2.4359 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | input_tokens | tokens | 29621.7 | 13/13 | 0 | 13 | 29621.7 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | input_tokens | tokens | 29621.7 | 13/13 | 0 | 13 | 29621.7 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | output_tokens | tokens | 10947.3 | 13/13 | 0 | 13 | 10947.3 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | output_tokens | tokens | 10947.3 | 13/13 | 0 | 13 | 10947.3 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.00854701 | 13/13 | 0 | 13 | 0.00854701 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | protocol_failure_rate | fraction | 0.00854701 | 13/13 | 0 | 13 | 0.00854701 | 1 / unknown |
| expgym | evidence_audit | all/all | cost_tight | single | wall_time_seconds | seconds | 410.386 | 13/13 | 0 | 13 | 410.386 | 1 / unknown |
| expgym | evidence_audit | family/evidence_audit | cost_tight | single | wall_time_seconds | seconds | 410.386 | 13/13 | 0 | 13 | 410.386 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | duplicate_action_attempts | count | 0.0410959 | 73/73 | 0 | 73 | 0.0410959 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | duplicate_action_attempts | count | 0.0588235 | 34/34 | 0 | 34 | 0.0588235 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | duplicate_action_attempts | count | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_attempts | count | 14.6438 | 73/73 | 0 | 73 | 14.6438 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_attempts | count | 15.1765 | 34/34 | 0 | 34 | 15.1765 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_attempts | count | 14.1795 | 39/39 | 0 | 39 | 14.1795 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_cost_seconds | seconds | 3497.12 | 73/73 | 0 | 73 | 3497.12 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_cost_seconds | seconds | 3768.88 | 34/34 | 0 | 34 | 3768.88 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_cost_seconds | seconds | 3260.19 | 39/39 | 0 | 39 | 3260.19 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | feedback_visible | count | 14.6438 | 73/73 | 0 | 73 | 14.6438 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | feedback_visible | count | 15.1765 | 34/34 | 0 | 34 | 15.1765 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | feedback_visible | count | 14.1795 | 39/39 | 0 | 39 | 14.1795 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | input_tokens | tokens | 83932.8 | 73/73 | 0 | 73 | 83932.8 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | input_tokens | tokens | 90625.9 | 34/34 | 0 | 34 | 90625.9 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | input_tokens | tokens | 78097.8 | 39/39 | 0 | 39 | 78097.8 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | output_tokens | tokens | 6003.32 | 73/73 | 0 | 73 | 6003.32 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | output_tokens | tokens | 5953.74 | 34/34 | 0 | 34 | 5953.74 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | output_tokens | tokens | 6046.54 | 39/39 | 0 | 39 | 6046.54 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0336668 | 73/73 | 0 | 73 | 0.0336668 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | protocol_failure_rate | fraction | 0.0354229 | 34/34 | 0 | 34 | 0.0354229 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | protocol_failure_rate | fraction | 0.0321358 | 39/39 | 0 | 39 | 0.0321358 | 1 / unknown |
| expgym | restricted_search | all/all | cost_free | single | wall_time_seconds | seconds | 258.116 | 73/73 | 0 | 73 | 258.116 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_free | single | wall_time_seconds | seconds | 254.609 | 34/34 | 0 | 34 | 254.609 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_free | single | wall_time_seconds | seconds | 261.173 | 39/39 | 0 | 39 | 261.173 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | budget_utilization | fraction | 0.825366 | 73/73 | 0 | 73 | 0.825366 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | budget_utilization | fraction | 0.845349 | 34/34 | 0 | 34 | 0.845349 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | budget_utilization | fraction | 0.807944 | 39/39 | 0 | 39 | 0.807944 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.0547945 | 73/73 | 0 | 73 | 0.0547945 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | duplicate_action_attempts | count | 0.0882353 | 34/34 | 0 | 34 | 0.0882353 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | duplicate_action_attempts | count | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_attempts | count | 10.7671 | 73/73 | 0 | 73 | 10.7671 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_attempts | count | 10.4706 | 34/34 | 0 | 34 | 10.4706 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_attempts | count | 11.0256 | 39/39 | 0 | 39 | 11.0256 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 2476.1 | 73/73 | 0 | 73 | 2476.1 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_cost_seconds | seconds | 2536.05 | 34/34 | 0 | 34 | 2536.05 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_cost_seconds | seconds | 2423.83 | 39/39 | 0 | 39 | 2423.83 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | feedback_visible | count | 10.4658 | 73/73 | 0 | 73 | 10.4658 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | feedback_visible | count | 10.0882 | 34/34 | 0 | 34 | 10.0882 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | feedback_visible | count | 10.7949 | 39/39 | 0 | 39 | 10.7949 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | input_tokens | tokens | 53450.2 | 73/73 | 0 | 73 | 53450.2 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | input_tokens | tokens | 51986 | 34/34 | 0 | 34 | 51986 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | input_tokens | tokens | 54726.6 | 39/39 | 0 | 39 | 54726.6 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | output_tokens | tokens | 5958.51 | 73/73 | 0 | 73 | 5958.51 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | output_tokens | tokens | 5809.88 | 34/34 | 0 | 34 | 5809.88 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | output_tokens | tokens | 6088.08 | 39/39 | 0 | 39 | 6088.08 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.0455848 | 73/73 | 0 | 73 | 0.0455848 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | protocol_failure_rate | fraction | 0.0415138 | 34/34 | 0 | 34 | 0.0415138 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | protocol_failure_rate | fraction | 0.0491339 | 39/39 | 0 | 39 | 0.0491339 | 1 / unknown |
| expgym | restricted_search | all/all | cost_moderate | single | wall_time_seconds | seconds | 246.692 | 73/73 | 0 | 73 | 246.692 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_moderate | single | wall_time_seconds | seconds | 237.486 | 34/34 | 0 | 34 | 237.486 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_moderate | single | wall_time_seconds | seconds | 254.717 | 39/39 | 0 | 39 | 254.717 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | budget_utilization | fraction | 1.09615 | 73/73 | 0 | 73 | 1.09615 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | budget_utilization | fraction | 1.09715 | 34/34 | 0 | 34 | 1.09715 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | budget_utilization | fraction | 1.09528 | 39/39 | 0 | 39 | 1.09528 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | duplicate_action_attempts | count | 0.0136986 | 73/73 | 0 | 73 | 0.0136986 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | duplicate_action_attempts | count | 0 | 34/34 | 0 | 34 | 0 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | duplicate_action_attempts | count | 0.025641 | 39/39 | 0 | 39 | 0.025641 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_attempts | count | 4.0137 | 73/73 | 0 | 73 | 4.0137 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_attempts | count | 3.76471 | 34/34 | 0 | 34 | 3.76471 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_attempts | count | 4.23077 | 39/39 | 0 | 39 | 4.23077 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_cost_seconds | seconds | 986.534 | 73/73 | 0 | 73 | 986.534 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_cost_seconds | seconds | 987.436 | 34/34 | 0 | 34 | 987.436 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_cost_seconds | seconds | 985.748 | 39/39 | 0 | 39 | 985.748 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | feedback_visible | count | 3.35616 | 73/73 | 0 | 73 | 3.35616 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | feedback_visible | count | 3.08824 | 34/34 | 0 | 34 | 3.08824 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | feedback_visible | count | 3.58974 | 39/39 | 0 | 39 | 3.58974 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | input_tokens | tokens | 9639.47 | 73/73 | 0 | 73 | 9639.47 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | input_tokens | tokens | 11103.4 | 34/34 | 0 | 34 | 11103.4 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | input_tokens | tokens | 8363.23 | 39/39 | 0 | 39 | 8363.23 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | output_tokens | tokens | 2305.89 | 73/73 | 0 | 73 | 2305.89 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | output_tokens | tokens | 3408.62 | 34/34 | 0 | 34 | 3408.62 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | output_tokens | tokens | 1344.54 | 39/39 | 0 | 39 | 1344.54 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.0550554 | 73/73 | 0 | 73 | 0.0550554 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | protocol_failure_rate | fraction | 0.0633053 | 34/34 | 0 | 34 | 0.0633053 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | protocol_failure_rate | fraction | 0.0478632 | 39/39 | 0 | 39 | 0.0478632 | 1 / unknown |
| expgym | restricted_search | all/all | cost_tight | single | wall_time_seconds | seconds | 86.6643 | 73/73 | 0 | 73 | 86.6643 | 1 / unknown |
| expgym | restricted_search | family/whatis | cost_tight | single | wall_time_seconds | seconds | 120.722 | 34/34 | 0 | 34 | 120.722 | 1 / unknown |
| expgym | restricted_search | family/whois | cost_tight | single | wall_time_seconds | seconds | 56.9734 | 39/39 | 0 | 39 | 56.9734 | 1 / unknown |
| expgym | tuning | all/all | cost_free | single | duplicate_action_attempts | count | 0.185185 | 27/27 | 0 | 9 | 0.185185 | 3 / 0.1283 |
| expgym | tuning | family/nasbench101 | cost_free | single | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.19245 |
| expgym | tuning | family/nasbench201 | cost_free | single | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| expgym | tuning | family/paramnet | cost_free | single | duplicate_action_attempts | count | 0.111111 | 9/9 | 0 | 3 | 0.111111 | 3 / 0.19245 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_free | single | feedback_attempts | count | 29.0741 | 27/27 | 0 | 9 | 29.0741 | 3 / 0.739814 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_attempts | count | 29.6667 | 9/9 | 0 | 3 | 29.6667 | 3 / 0 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_attempts | count | 29.5556 | 9/9 | 0 | 3 | 29.5556 | 3 / 0.509175 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_attempts | count | 28 | 9/9 | 0 | 3 | 28 | 3 / 2.64575 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_attempts | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_attempts | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_attempts | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_attempts | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_attempts | count | 29 | 3/3 | 0 | 1 | 29 | 3 / 1.73205 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_attempts | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_attempts | count | 24 | 3/3 | 0 | 1 | 24 | 3 / 7.93725 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_attempts | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_attempts | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | all/all | cost_free | single | feedback_cost_seconds | seconds | 312526 | 27/27 | 0 | 9 | 312526 | 3 / 4786.27 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_cost_seconds | seconds | 207745 | 9/9 | 0 | 3 | 207745 | 3 / 18101.5 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_cost_seconds | seconds | 724245 | 9/9 | 0 | 3 | 724245 | 3 / 4637.73 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_cost_seconds | seconds | 5588.45 | 9/9 | 0 | 3 | 5588.45 | 3 / 1845.06 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_cost_seconds | seconds | 232024 | 3/3 | 0 | 1 | 232024 | 3 / 9625.25 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_cost_seconds | seconds | 216573 | 3/3 | 0 | 1 | 216573 | 3 / 46716.8 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_cost_seconds | seconds | 174639 | 3/3 | 0 | 1 | 174639 | 3 / 1271.21 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_cost_seconds | seconds | 313032 | 3/3 | 0 | 1 | 313032 | 3 / 14792.7 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_cost_seconds | seconds | 479488 | 3/3 | 0 | 1 | 479488 | 3 / 8554.4 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_cost_seconds | seconds | 1.38021e+06 | 3/3 | 0 | 1 | 1.38021e+06 | 3 / 3624.87 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_cost_seconds | seconds | 7847.6 | 3/3 | 0 | 1 | 7847.6 | 3 / 7036.51 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_cost_seconds | seconds | 6750.44 | 3/3 | 0 | 1 | 6750.44 | 3 / 2477.05 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_cost_seconds | seconds | 2167.31 | 3/3 | 0 | 1 | 2167.31 | 3 / 1354.71 |
| expgym | tuning | all/all | cost_free | single | feedback_visible | count | 29.0741 | 27/27 | 0 | 9 | 29.0741 | 3 / 0.739814 |
| expgym | tuning | family/nasbench101 | cost_free | single | feedback_visible | count | 29.6667 | 9/9 | 0 | 3 | 29.6667 | 3 / 0 |
| expgym | tuning | family/nasbench201 | cost_free | single | feedback_visible | count | 29.5556 | 9/9 | 0 | 3 | 29.5556 | 3 / 0.509175 |
| expgym | tuning | family/paramnet | cost_free | single | feedback_visible | count | 28 | 9/9 | 0 | 3 | 28 | 3 / 2.64575 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | feedback_visible | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | feedback_visible | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | feedback_visible | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | feedback_visible | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | feedback_visible | count | 29 | 3/3 | 0 | 1 | 29 | 3 / 1.73205 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | feedback_visible | count | 29.6667 | 3/3 | 0 | 1 | 29.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | feedback_visible | count | 24 | 3/3 | 0 | 1 | 24 | 3 / 7.93725 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | feedback_visible | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | feedback_visible | count | 30 | 3/3 | 0 | 1 | 30 | 3 / 0 |
| expgym | tuning | all/all | cost_free | single | input_tokens | tokens | 267768 | 27/27 | 0 | 9 | 267768 | 3 / 10232.3 |
| expgym | tuning | family/nasbench101 | cost_free | single | input_tokens | tokens | 506931 | 9/9 | 0 | 3 | 506931 | 3 / 40027.1 |
| expgym | tuning | family/nasbench201 | cost_free | single | input_tokens | tokens | 163517 | 9/9 | 0 | 3 | 163517 | 3 / 3108.3 |
| expgym | tuning | family/paramnet | cost_free | single | input_tokens | tokens | 132857 | 9/9 | 0 | 3 | 132857 | 3 / 15366.1 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | input_tokens | tokens | 509378 | 3/3 | 0 | 1 | 509378 | 3 / 33813.4 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | input_tokens | tokens | 427859 | 3/3 | 0 | 1 | 427859 | 3 / 96842.4 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | input_tokens | tokens | 583555 | 3/3 | 0 | 1 | 583555 | 3 / 118003 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | input_tokens | tokens | 177520 | 3/3 | 0 | 1 | 177520 | 3 / 38984.4 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | input_tokens | tokens | 143432 | 3/3 | 0 | 1 | 143432 | 3 / 30996.3 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | input_tokens | tokens | 169600 | 3/3 | 0 | 1 | 169600 | 3 / 12345.6 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | input_tokens | tokens | 118599 | 3/3 | 0 | 1 | 118599 | 3 / 44916.2 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | input_tokens | tokens | 139769 | 3/3 | 0 | 1 | 139769 | 3 / 3394.26 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | input_tokens | tokens | 140202 | 3/3 | 0 | 1 | 140202 | 3 / 2345.01 |
| expgym | tuning | all/all | cost_free | single | output_tokens | tokens | 13746.3 | 27/27 | 0 | 9 | 13746.3 | 3 / 2582.25 |
| expgym | tuning | family/nasbench101 | cost_free | single | output_tokens | tokens | 23854 | 9/9 | 0 | 3 | 23854 | 3 / 2675.67 |
| expgym | tuning | family/nasbench201 | cost_free | single | output_tokens | tokens | 7465.89 | 9/9 | 0 | 3 | 7465.89 | 3 / 845.037 |
| expgym | tuning | family/paramnet | cost_free | single | output_tokens | tokens | 9919 | 9/9 | 0 | 3 | 9919 | 3 / 5737.52 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | output_tokens | tokens | 25171.3 | 3/3 | 0 | 1 | 25171.3 | 3 / 2327.36 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | output_tokens | tokens | 18368.7 | 3/3 | 0 | 1 | 18368.7 | 3 / 5377.91 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | output_tokens | tokens | 28022 | 3/3 | 0 | 1 | 28022 | 3 / 6296.93 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | output_tokens | tokens | 8311 | 3/3 | 0 | 1 | 8311 | 3 / 2013.51 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | output_tokens | tokens | 6653.67 | 3/3 | 0 | 1 | 6653.67 | 3 / 1267.01 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | output_tokens | tokens | 7433 | 3/3 | 0 | 1 | 7433 | 3 / 998.548 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | output_tokens | tokens | 17407.3 | 3/3 | 0 | 1 | 17407.3 | 3 / 17003.4 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | output_tokens | tokens | 6066 | 3/3 | 0 | 1 | 6066 | 3 / 168.893 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | output_tokens | tokens | 6283.67 | 3/3 | 0 | 1 | 6283.67 | 3 / 315.773 |
| expgym | tuning | all/all | cost_free | single | protocol_failure_rate | fraction | 0.0088942 | 27/27 | 0 | 9 | 0.0088942 | 3 / 0.00635119 |
| expgym | tuning | family/nasbench101 | cost_free | single | protocol_failure_rate | fraction | 0.0107527 | 9/9 | 0 | 3 | 0.0107527 | 3 / 0 |
| expgym | tuning | family/nasbench201 | cost_free | single | protocol_failure_rate | fraction | 0.00358423 | 9/9 | 0 | 3 | 0.00358423 | 3 / 0.00620807 |
| expgym | tuning | family/paramnet | cost_free | single | protocol_failure_rate | fraction | 0.0123457 | 9/9 | 0 | 3 | 0.0123457 | 3 / 0.0213833 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | protocol_failure_rate | fraction | 0.0107527 | 3/3 | 0 | 1 | 0.0107527 | 3 / 0.0186242 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | protocol_failure_rate | fraction | 0.0107527 | 3/3 | 0 | 1 | 0.0107527 | 3 / 0.0186242 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | protocol_failure_rate | fraction | 0.0107527 | 3/3 | 0 | 1 | 0.0107527 | 3 / 0.0186242 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | protocol_failure_rate | fraction | 0.0107527 | 3/3 | 0 | 1 | 0.0107527 | 3 / 0.0186242 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | protocol_failure_rate | fraction | 0.037037 | 3/3 | 0 | 1 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_free | single | wall_time_seconds | seconds | 503.443 | 27/27 | 0 | 9 | 503.443 | 3 / 93.3476 |
| expgym | tuning | family/nasbench101 | cost_free | single | wall_time_seconds | seconds | 909.556 | 9/9 | 0 | 3 | 909.556 | 3 / 131.371 |
| expgym | tuning | family/nasbench201 | cost_free | single | wall_time_seconds | seconds | 297.579 | 9/9 | 0 | 3 | 297.579 | 3 / 38.703 |
| expgym | tuning | family/paramnet | cost_free | single | wall_time_seconds | seconds | 303.193 | 9/9 | 0 | 3 | 303.193 | 3 / 185.127 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | single | wall_time_seconds | seconds | 956.496 | 3/3 | 0 | 1 | 956.496 | 3 / 123.451 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | single | wall_time_seconds | seconds | 713.655 | 3/3 | 0 | 1 | 713.655 | 3 / 207.079 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | single | wall_time_seconds | seconds | 1058.52 | 3/3 | 0 | 1 | 1058.52 | 3 / 268.446 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | single | wall_time_seconds | seconds | 329.568 | 3/3 | 0 | 1 | 329.568 | 3 / 83.1519 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | single | wall_time_seconds | seconds | 265.726 | 3/3 | 0 | 1 | 265.726 | 3 / 54.0434 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | single | wall_time_seconds | seconds | 297.445 | 3/3 | 0 | 1 | 297.445 | 3 / 35.7119 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | single | wall_time_seconds | seconds | 539.275 | 3/3 | 0 | 1 | 539.275 | 3 / 543.878 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | single | wall_time_seconds | seconds | 181.836 | 3/3 | 0 | 1 | 181.836 | 3 / 7.31379 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | single | wall_time_seconds | seconds | 188.467 | 3/3 | 0 | 1 | 188.467 | 3 / 12.6554 |
| expgym | tuning | all/all | cost_moderate | single | budget_utilization | fraction | 0.929251 | 27/27 | 0 | 9 | 0.929251 | 3 / 0.0167424 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | budget_utilization | fraction | 0.902589 | 9/9 | 0 | 3 | 0.902589 | 3 / 0.0772529 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | budget_utilization | fraction | 0.943374 | 9/9 | 0 | 3 | 0.943374 | 3 / 0.0351666 |
| expgym | tuning | family/paramnet | cost_moderate | single | budget_utilization | fraction | 0.941789 | 9/9 | 0 | 3 | 0.941789 | 3 / 0.0267192 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | budget_utilization | fraction | 0.822908 | 3/3 | 0 | 1 | 0.822908 | 3 / 0.246674 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | budget_utilization | fraction | 0.92604 | 3/3 | 0 | 1 | 0.92604 | 3 / 0.0455801 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | budget_utilization | fraction | 0.958817 | 3/3 | 0 | 1 | 0.958817 | 3 / 0.0395409 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | budget_utilization | fraction | 0.956606 | 3/3 | 0 | 1 | 0.956606 | 3 / 0.0808421 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | budget_utilization | fraction | 0.892607 | 3/3 | 0 | 1 | 0.892607 | 3 / 0.0717405 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | budget_utilization | fraction | 0.98091 | 3/3 | 0 | 1 | 0.98091 | 3 / 0.0142025 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | budget_utilization | fraction | 0.92023 | 3/3 | 0 | 1 | 0.92023 | 3 / 0.0547409 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | budget_utilization | fraction | 0.955848 | 3/3 | 0 | 1 | 0.955848 | 3 / 0.0177344 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | budget_utilization | fraction | 0.949289 | 3/3 | 0 | 1 | 0.949289 | 3 / 0.0156908 |
| expgym | tuning | all/all | cost_moderate | single | duplicate_action_attempts | count | 0.037037 | 27/27 | 0 | 9 | 0.037037 | 3 / 0.06415 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | duplicate_action_attempts | count | 0.111111 | 9/9 | 0 | 3 | 0.111111 | 3 / 0.19245 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/paramnet | cost_moderate | single | duplicate_action_attempts | count | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_moderate | single | feedback_attempts | count | 9.66667 | 27/27 | 0 | 9 | 9.66667 | 3 / 0.509175 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_attempts | count | 8.77778 | 9/9 | 0 | 3 | 8.77778 | 3 / 1.34715 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_attempts | count | 10.6667 | 9/9 | 0 | 3 | 10.6667 | 3 / 0.881917 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_attempts | count | 9.55556 | 9/9 | 0 | 3 | 9.55556 | 3 / 2.14303 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_attempts | count | 5 | 3/3 | 0 | 1 | 5 | 3 / 3 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_attempts | count | 8 | 3/3 | 0 | 1 | 8 | 3 / 3.4641 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_attempts | count | 13.3333 | 3/3 | 0 | 1 | 13.3333 | 3 / 4.6188 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_attempts | count | 11 | 3/3 | 0 | 1 | 11 | 3 / 1 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_attempts | count | 10.3333 | 3/3 | 0 | 1 | 10.3333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_attempts | count | 10.6667 | 3/3 | 0 | 1 | 10.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_attempts | count | 3 | 3/3 | 0 | 1 | 3 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_attempts | count | 15 | 3/3 | 0 | 1 | 15 | 3 / 7 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_attempts | count | 10.6667 | 3/3 | 0 | 1 | 10.6667 | 3 / 2.08167 |
| expgym | tuning | all/all | cost_moderate | single | feedback_cost_seconds | seconds | 112730 | 27/27 | 0 | 9 | 112730 | 3 / 1640.56 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_cost_seconds | seconds | 81172.1 | 9/9 | 0 | 3 | 81172.1 | 3 / 3932.63 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_cost_seconds | seconds | 255872 | 9/9 | 0 | 3 | 255872 | 3 / 3711.88 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_cost_seconds | seconds | 1145.2 | 9/9 | 0 | 3 | 1145.2 | 3 / 21.7829 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_cost_seconds | seconds | 40685.8 | 3/3 | 0 | 1 | 40685.8 | 3 / 12196 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_cost_seconds | seconds | 95405.9 | 3/3 | 0 | 1 | 95405.9 | 3 / 4695.92 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_cost_seconds | seconds | 107425 | 3/3 | 0 | 1 | 107425 | 3 / 4430.11 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_cost_seconds | seconds | 108193 | 3/3 | 0 | 1 | 108193 | 3 / 9143.28 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_cost_seconds | seconds | 166376 | 3/3 | 0 | 1 | 166376 | 3 / 13372 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_cost_seconds | seconds | 493047 | 3/3 | 0 | 1 | 493047 | 3 / 7138.77 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_cost_seconds | seconds | 262.624 | 3/3 | 0 | 1 | 262.624 | 3 / 15.6224 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_cost_seconds | seconds | 2240.1 | 3/3 | 0 | 1 | 2240.1 | 3 / 41.5619 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_cost_seconds | seconds | 932.871 | 3/3 | 0 | 1 | 932.871 | 3 / 15.4194 |
| expgym | tuning | all/all | cost_moderate | single | feedback_visible | count | 9.59259 | 27/27 | 0 | 9 | 9.59259 | 3 / 0.525091 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | feedback_visible | count | 8.66667 | 9/9 | 0 | 3 | 8.66667 | 3 / 1.33333 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | feedback_visible | count | 10.5556 | 9/9 | 0 | 3 | 10.5556 | 3 / 0.693889 |
| expgym | tuning | family/paramnet | cost_moderate | single | feedback_visible | count | 9.55556 | 9/9 | 0 | 3 | 9.55556 | 3 / 2.14303 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | feedback_visible | count | 5 | 3/3 | 0 | 1 | 5 | 3 / 3 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | feedback_visible | count | 8 | 3/3 | 0 | 1 | 8 | 3 / 3.4641 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | feedback_visible | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 4.3589 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | feedback_visible | count | 10.6667 | 3/3 | 0 | 1 | 10.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | feedback_visible | count | 10.3333 | 3/3 | 0 | 1 | 10.3333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | feedback_visible | count | 10.6667 | 3/3 | 0 | 1 | 10.6667 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | feedback_visible | count | 3 | 3/3 | 0 | 1 | 3 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | feedback_visible | count | 15 | 3/3 | 0 | 1 | 15 | 3 / 7 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | feedback_visible | count | 10.6667 | 3/3 | 0 | 1 | 10.6667 | 3 / 2.08167 |
| expgym | tuning | all/all | cost_moderate | single | input_tokens | tokens | 64952.8 | 27/27 | 0 | 9 | 64952.8 | 3 / 7593.76 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | input_tokens | tokens | 118858 | 9/9 | 0 | 3 | 118858 | 3 / 27067.2 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | input_tokens | tokens | 44585 | 9/9 | 0 | 3 | 44585 | 3 / 5054.44 |
| expgym | tuning | family/paramnet | cost_moderate | single | input_tokens | tokens | 31415.1 | 9/9 | 0 | 3 | 31415.1 | 3 / 12452.3 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | input_tokens | tokens | 63442 | 3/3 | 0 | 1 | 63442 | 3 / 47774.9 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | input_tokens | tokens | 81153 | 3/3 | 0 | 1 | 81153 | 3 / 41960.2 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | input_tokens | tokens | 211980 | 3/3 | 0 | 1 | 211980 | 3 / 91915.1 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | input_tokens | tokens | 38466.3 | 3/3 | 0 | 1 | 38466.3 | 3 / 7227.3 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | input_tokens | tokens | 46864.3 | 3/3 | 0 | 1 | 46864.3 | 3 / 13114.1 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | input_tokens | tokens | 48424.3 | 3/3 | 0 | 1 | 48424.3 | 3 / 9788.83 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | input_tokens | tokens | 6561.33 | 3/3 | 0 | 1 | 6561.33 | 3 / 597.046 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | input_tokens | tokens | 56433.3 | 3/3 | 0 | 1 | 56433.3 | 3 / 36963.6 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | input_tokens | tokens | 31250.7 | 3/3 | 0 | 1 | 31250.7 | 3 / 9128.49 |
| expgym | tuning | all/all | cost_moderate | single | output_tokens | tokens | 7655.89 | 27/27 | 0 | 9 | 7655.89 | 3 / 1092.65 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | output_tokens | tokens | 14297.9 | 9/9 | 0 | 3 | 14297.9 | 3 / 2487.62 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | output_tokens | tokens | 5289.33 | 9/9 | 0 | 3 | 5289.33 | 3 / 766.384 |
| expgym | tuning | family/paramnet | cost_moderate | single | output_tokens | tokens | 3380.44 | 9/9 | 0 | 3 | 3380.44 | 3 / 520.895 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | output_tokens | tokens | 11655.3 | 3/3 | 0 | 1 | 11655.3 | 3 / 4129.87 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | output_tokens | tokens | 10771.3 | 3/3 | 0 | 1 | 10771.3 | 3 / 2299.64 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | output_tokens | tokens | 20467 | 3/3 | 0 | 1 | 20467 | 3 / 5096.45 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | output_tokens | tokens | 3955.67 | 3/3 | 0 | 1 | 3955.67 | 3 / 726.281 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | output_tokens | tokens | 6287.33 | 3/3 | 0 | 1 | 6287.33 | 3 / 3257.51 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | output_tokens | tokens | 5625 | 3/3 | 0 | 1 | 5625 | 3 / 881.939 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | output_tokens | tokens | 2165.67 | 3/3 | 0 | 1 | 2165.67 | 3 / 704.188 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | output_tokens | tokens | 4613.33 | 3/3 | 0 | 1 | 4613.33 | 3 / 1270.56 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | output_tokens | tokens | 3362.33 | 3/3 | 0 | 1 | 3362.33 | 3 / 848.151 |
| expgym | tuning | all/all | cost_moderate | single | protocol_failure_rate | fraction | 0.023952 | 27/27 | 0 | 9 | 0.023952 | 3 / 0.00408001 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | protocol_failure_rate | fraction | 0.0547619 | 9/9 | 0 | 3 | 0.0547619 | 3 / 0.0257539 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | protocol_failure_rate | fraction | 0.017094 | 9/9 | 0 | 3 | 0.017094 | 3 / 0.0148039 |
| expgym | tuning | family/paramnet | cost_moderate | single | protocol_failure_rate | fraction | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | protocol_failure_rate | fraction | 0.164286 | 3/3 | 0 | 1 | 0.164286 | 3 / 0.0772618 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | protocol_failure_rate | fraction | 0.025641 | 3/3 | 0 | 1 | 0.025641 | 3 / 0.0444116 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | protocol_failure_rate | fraction | 0.025641 | 3/3 | 0 | 1 | 0.025641 | 3 / 0.0444116 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | all/all | cost_moderate | single | wall_time_seconds | seconds | 286.81 | 27/27 | 0 | 9 | 286.81 | 3 / 41.9926 |
| expgym | tuning | family/nasbench101 | cost_moderate | single | wall_time_seconds | seconds | 548.849 | 9/9 | 0 | 3 | 548.849 | 3 / 99.2052 |
| expgym | tuning | family/nasbench201 | cost_moderate | single | wall_time_seconds | seconds | 208.345 | 9/9 | 0 | 3 | 208.345 | 3 / 29.6128 |
| expgym | tuning | family/paramnet | cost_moderate | single | wall_time_seconds | seconds | 103.235 | 9/9 | 0 | 3 | 103.235 | 3 / 14.8124 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | single | wall_time_seconds | seconds | 445.441 | 3/3 | 0 | 1 | 445.441 | 3 / 149.572 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | single | wall_time_seconds | seconds | 423.834 | 3/3 | 0 | 1 | 423.834 | 3 / 84.4138 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | single | wall_time_seconds | seconds | 777.274 | 3/3 | 0 | 1 | 777.274 | 3 / 209.564 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | single | wall_time_seconds | seconds | 160.71 | 3/3 | 0 | 1 | 160.71 | 3 / 24.4981 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | single | wall_time_seconds | seconds | 247.052 | 3/3 | 0 | 1 | 247.052 | 3 / 126.005 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | single | wall_time_seconds | seconds | 217.272 | 3/3 | 0 | 1 | 217.272 | 3 / 36.5702 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | single | wall_time_seconds | seconds | 64.1304 | 3/3 | 0 | 1 | 64.1304 | 3 / 20.1395 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | single | wall_time_seconds | seconds | 140.667 | 3/3 | 0 | 1 | 140.667 | 3 / 36.3365 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | single | wall_time_seconds | seconds | 104.909 | 3/3 | 0 | 1 | 104.909 | 3 / 24.3199 |
| expgym | tuning | all/all | cost_tight | single | budget_utilization | fraction | 1.10872 | 27/27 | 0 | 9 | 1.10872 | 3 / 0.0439762 |
| expgym | tuning | family/nasbench101 | cost_tight | single | budget_utilization | fraction | 1.16385 | 9/9 | 0 | 3 | 1.16385 | 3 / 0.0783946 |
| expgym | tuning | family/nasbench201 | cost_tight | single | budget_utilization | fraction | 1.05574 | 9/9 | 0 | 3 | 1.05574 | 3 / 0.0943435 |
| expgym | tuning | family/paramnet | cost_tight | single | budget_utilization | fraction | 1.10656 | 9/9 | 0 | 3 | 1.10656 | 3 / 0.158316 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | budget_utilization | fraction | 1.36539 | 3/3 | 0 | 1 | 1.36539 | 3 / 0.0361766 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | budget_utilization | fraction | 1.17549 | 3/3 | 0 | 1 | 1.17549 | 3 / 0.172992 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | budget_utilization | fraction | 0.950661 | 3/3 | 0 | 1 | 0.950661 | 3 / 0.102067 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | budget_utilization | fraction | 1.02576 | 3/3 | 0 | 1 | 1.02576 | 3 / 0.100897 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | budget_utilization | fraction | 1.05996 | 3/3 | 0 | 1 | 1.05996 | 3 / 0.103509 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | budget_utilization | fraction | 1.08149 | 3/3 | 0 | 1 | 1.08149 | 3 / 0.0916116 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | budget_utilization | fraction | 1.25637 | 3/3 | 0 | 1 | 1.25637 | 3 / 0.338057 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | budget_utilization | fraction | 1.08863 | 3/3 | 0 | 1 | 1.08863 | 3 / 0.189811 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | budget_utilization | fraction | 0.974681 | 3/3 | 0 | 1 | 0.974681 | 3 / 0.154531 |
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
| expgym | tuning | all/all | cost_tight | single | feedback_attempts | count | 3.81481 | 27/27 | 0 | 9 | 3.81481 | 3 / 0.669746 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_attempts | count | 3.77778 | 9/9 | 0 | 3 | 3.77778 | 3 / 0.693889 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_attempts | count | 3.77778 | 9/9 | 0 | 3 | 3.77778 | 3 / 0.19245 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_attempts | count | 3.88889 | 9/9 | 0 | 3 | 3.88889 | 3 / 1.34715 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_attempts | count | 2.33333 | 3/3 | 0 | 1 | 2.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_attempts | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_attempts | count | 5 | 3/3 | 0 | 1 | 5 | 3 / 2 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_attempts | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_attempts | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_attempts | count | 4 | 3/3 | 0 | 1 | 4 | 3 / 1 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_attempts | count | 2 | 3/3 | 0 | 1 | 2 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_attempts | count | 3 | 3/3 | 0 | 1 | 3 | 3 / 1 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_attempts | count | 6.66667 | 3/3 | 0 | 1 | 6.66667 | 3 / 3.78594 |
| expgym | tuning | all/all | cost_tight | single | feedback_cost_seconds | seconds | 38539.2 | 27/27 | 0 | 9 | 38539.2 | 3 / 3325.8 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_cost_seconds | seconds | 29512.3 | 9/9 | 0 | 3 | 29512.3 | 3 / 2664.91 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_cost_seconds | seconds | 85718.5 | 9/9 | 0 | 3 | 85718.5 | 3 / 7376.74 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_cost_seconds | seconds | 386.766 | 9/9 | 0 | 3 | 386.766 | 3 / 57.326 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_cost_seconds | seconds | 20252 | 3/3 | 0 | 1 | 20252 | 3 / 536.587 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_cost_seconds | seconds | 36331.8 | 3/3 | 0 | 1 | 36331.8 | 3 / 5346.78 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_cost_seconds | seconds | 31953.2 | 3/3 | 0 | 1 | 31953.2 | 3 / 3430.64 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_cost_seconds | seconds | 34804.2 | 3/3 | 0 | 1 | 34804.2 | 3 / 3423.44 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_cost_seconds | seconds | 59271.3 | 3/3 | 0 | 1 | 59271.3 | 3 / 5788.02 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_cost_seconds | seconds | 163080 | 3/3 | 0 | 1 | 163080 | 3 / 13814.4 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_cost_seconds | seconds | 107.566 | 3/3 | 0 | 1 | 107.566 | 3 / 28.9433 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_cost_seconds | seconds | 765.386 | 3/3 | 0 | 1 | 765.386 | 3 / 133.451 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_cost_seconds | seconds | 287.347 | 3/3 | 0 | 1 | 287.347 | 3 / 45.5576 |
| expgym | tuning | all/all | cost_tight | single | feedback_visible | count | 3.22222 | 27/27 | 0 | 9 | 3.22222 | 3 / 0.7698 |
| expgym | tuning | family/nasbench101 | cost_tight | single | feedback_visible | count | 3.11111 | 9/9 | 0 | 3 | 3.11111 | 3 / 0.96225 |
| expgym | tuning | family/nasbench201 | cost_tight | single | feedback_visible | count | 3.22222 | 9/9 | 0 | 3 | 3.22222 | 3 / 0.693889 |
| expgym | tuning | family/paramnet | cost_tight | single | feedback_visible | count | 3.33333 | 9/9 | 0 | 3 | 3.33333 | 3 / 1 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | feedback_visible | count | 1.33333 | 3/3 | 0 | 1 | 1.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | feedback_visible | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | feedback_visible | count | 4.66667 | 3/3 | 0 | 1 | 4.66667 | 3 / 2.51661 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | feedback_visible | count | 3 | 3/3 | 0 | 1 | 3 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | feedback_visible | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | feedback_visible | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | feedback_visible | count | 1.33333 | 3/3 | 0 | 1 | 1.33333 | 3 / 0.57735 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | feedback_visible | count | 2.33333 | 3/3 | 0 | 1 | 2.33333 | 3 / 1.52753 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | feedback_visible | count | 6.33333 | 3/3 | 0 | 1 | 6.33333 | 3 / 3.21455 |
| expgym | tuning | all/all | cost_tight | single | input_tokens | tokens | 23737.1 | 27/27 | 0 | 9 | 23737.1 | 3 / 4180.96 |
| expgym | tuning | family/nasbench101 | cost_tight | single | input_tokens | tokens | 48063.1 | 9/9 | 0 | 3 | 48063.1 | 3 / 7138.71 |
| expgym | tuning | family/nasbench201 | cost_tight | single | input_tokens | tokens | 12939.1 | 9/9 | 0 | 3 | 12939.1 | 3 / 3928.09 |
| expgym | tuning | family/paramnet | cost_tight | single | input_tokens | tokens | 10209.1 | 9/9 | 0 | 3 | 10209.1 | 3 / 4145.93 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | input_tokens | tokens | 26524.7 | 3/3 | 0 | 1 | 26524.7 | 3 / 25905.6 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | input_tokens | tokens | 42931 | 3/3 | 0 | 1 | 42931 | 3 / 21210.9 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | input_tokens | tokens | 74733.7 | 3/3 | 0 | 1 | 74733.7 | 3 / 27827.1 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | input_tokens | tokens | 10749.7 | 3/3 | 0 | 1 | 10749.7 | 3 / 1598.08 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | input_tokens | tokens | 11110 | 3/3 | 0 | 1 | 11110 | 3 / 1763.23 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | input_tokens | tokens | 16957.7 | 3/3 | 0 | 1 | 16957.7 | 3 / 9162.58 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | input_tokens | tokens | 4769 | 3/3 | 0 | 1 | 4769 | 3 / 1602.72 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | input_tokens | tokens | 6457.67 | 3/3 | 0 | 1 | 6457.67 | 3 / 4600.8 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | input_tokens | tokens | 19400.7 | 3/3 | 0 | 1 | 19400.7 | 3 / 13327.5 |
| expgym | tuning | all/all | cost_tight | single | output_tokens | tokens | 6487.81 | 27/27 | 0 | 9 | 6487.81 | 3 / 695.72 |
| expgym | tuning | family/nasbench101 | cost_tight | single | output_tokens | tokens | 12504.8 | 9/9 | 0 | 3 | 12504.8 | 3 / 2520.34 |
| expgym | tuning | family/nasbench201 | cost_tight | single | output_tokens | tokens | 4639.11 | 9/9 | 0 | 3 | 4639.11 | 3 / 2505.57 |
| expgym | tuning | family/paramnet | cost_tight | single | output_tokens | tokens | 2319.56 | 9/9 | 0 | 3 | 2319.56 | 3 / 401.05 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | output_tokens | tokens | 8333.67 | 3/3 | 0 | 1 | 8333.67 | 3 / 6206.24 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | output_tokens | tokens | 11525.7 | 3/3 | 0 | 1 | 11525.7 | 3 / 9135.82 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | output_tokens | tokens | 17655 | 3/3 | 0 | 1 | 17655 | 3 / 730.787 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | output_tokens | tokens | 3381.67 | 3/3 | 0 | 1 | 3381.67 | 3 / 1432.08 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | output_tokens | tokens | 2300.33 | 3/3 | 0 | 1 | 2300.33 | 3 / 291.833 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | output_tokens | tokens | 8235.33 | 3/3 | 0 | 1 | 8235.33 | 3 / 6720.77 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | output_tokens | tokens | 2736.33 | 3/3 | 0 | 1 | 2736.33 | 3 / 1770.35 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | output_tokens | tokens | 1723.33 | 3/3 | 0 | 1 | 1723.33 | 3 / 1694.17 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | output_tokens | tokens | 2499 | 3/3 | 0 | 1 | 2499 | 3 / 763.126 |
| expgym | tuning | all/all | cost_tight | single | protocol_failure_rate | fraction | 0.0188713 | 27/27 | 0 | 9 | 0.0188713 | 3 / 0.0190501 |
| expgym | tuning | family/nasbench101 | cost_tight | single | protocol_failure_rate | fraction | 0.0380952 | 9/9 | 0 | 3 | 0.0380952 | 3 / 0.0659829 |
| expgym | tuning | family/nasbench201 | cost_tight | single | protocol_failure_rate | fraction | 0 | 9/9 | 0 | 3 | 0 | 3 / 0 |
| expgym | tuning | family/paramnet | cost_tight | single | protocol_failure_rate | fraction | 0.0185185 | 9/9 | 0 | 3 | 0.0185185 | 3 / 0.032075 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | protocol_failure_rate | fraction | 0.0666667 | 3/3 | 0 | 1 | 0.0666667 | 3 / 0.11547 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | protocol_failure_rate | fraction | 0.047619 | 3/3 | 0 | 1 | 0.047619 | 3 / 0.0824786 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | protocol_failure_rate | fraction | 0.0555556 | 3/3 | 0 | 1 | 0.0555556 | 3 / 0.096225 |
| expgym | tuning | all/all | cost_tight | single | wall_time_seconds | seconds | 227.094 | 27/27 | 0 | 9 | 227.094 | 3 / 38.7972 |
| expgym | tuning | family/nasbench101 | cost_tight | single | wall_time_seconds | seconds | 440.19 | 9/9 | 0 | 3 | 440.19 | 3 / 36.7573 |
| expgym | tuning | family/nasbench201 | cost_tight | single | wall_time_seconds | seconds | 171.719 | 9/9 | 0 | 3 | 171.719 | 3 / 105.053 |
| expgym | tuning | family/paramnet | cost_tight | single | wall_time_seconds | seconds | 69.3723 | 9/9 | 0 | 3 | 69.3723 | 3 / 8.59963 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_tight | single | wall_time_seconds | seconds | 317.048 | 3/3 | 0 | 1 | 317.048 | 3 / 237.964 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_tight | single | wall_time_seconds | seconds | 370.223 | 3/3 | 0 | 1 | 370.223 | 3 / 232.01 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_tight | single | wall_time_seconds | seconds | 633.298 | 3/3 | 0 | 1 | 633.298 | 3 / 104.994 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_tight | single | wall_time_seconds | seconds | 128.428 | 3/3 | 0 | 1 | 128.428 | 3 / 52.4739 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_tight | single | wall_time_seconds | seconds | 78.0559 | 3/3 | 0 | 1 | 78.0559 | 3 / 13.7669 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_tight | single | wall_time_seconds | seconds | 308.673 | 3/3 | 0 | 1 | 308.673 | 3 / 272.654 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_tight | single | wall_time_seconds | seconds | 81.1279 | 3/3 | 0 | 1 | 81.1279 | 3 / 49.3646 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_tight | single | wall_time_seconds | seconds | 52.9929 | 3/3 | 0 | 1 | 52.9929 | 3 / 50.4478 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_tight | single | wall_time_seconds | seconds | 73.9961 | 3/3 | 0 | 1 | 73.9961 | 3 / 19.9047 |
| poolact | evidence_audit | all/all | cost_moderate | cached | budget_utilization | fraction | 0.992037 | 13/13 | 0 | 13 | 0.992037 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | budget_utilization | fraction | 0.992037 | 13/13 | 0 | 13 | 0.992037 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | duplicate_action_attempts | count | 22.8462 | 13/13 | 0 | 13 | 22.8462 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | duplicate_action_attempts | count | 22.8462 | 13/13 | 0 | 13 | 22.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_attempts | count | 44.3846 | 13/13 | 0 | 13 | 44.3846 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_attempts | count | 44.3846 | 13/13 | 0 | 13 | 44.3846 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 11904.4 | 13/13 | 0 | 13 | 11904.4 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_cost_seconds | seconds | 11904.4 | 13/13 | 0 | 13 | 11904.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | input_tokens | tokens | 432018 | 13/13 | 0 | 13 | 432018 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | input_tokens | tokens | 432018 | 13/13 | 0 | 13 | 432018 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | output_tokens | tokens | 45707.3 | 13/13 | 0 | 13 | 45707.3 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | output_tokens | tokens | 45707.3 | 13/13 | 0 | 13 | 45707.3 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.00458645 | 13/13 | 0 | 13 | 0.00458645 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | protocol_failure_rate | fraction | 0.00458645 | 13/13 | 0 | 13 | 0.00458645 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | budget_utilization | fraction | 0.991054 | 13/13 | 0 | 13 | 0.991054 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | budget_utilization | fraction | 0.991054 | 13/13 | 0 | 13 | 0.991054 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | duplicate_action_attempts | count | 19.2308 | 13/13 | 0 | 13 | 19.2308 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | duplicate_action_attempts | count | 19.2308 | 13/13 | 0 | 13 | 19.2308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_attempts | count | 39.4615 | 13/13 | 0 | 13 | 39.4615 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_attempts | count | 39.4615 | 13/13 | 0 | 13 | 39.4615 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 11892.6 | 13/13 | 0 | 13 | 11892.6 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_cost_seconds | seconds | 11892.6 | 13/13 | 0 | 13 | 11892.6 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | input_tokens | tokens | 367328 | 13/13 | 0 | 13 | 367328 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | input_tokens | tokens | 367328 | 13/13 | 0 | 13 | 367328 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | output_tokens | tokens | 44462.9 | 13/13 | 0 | 13 | 44462.9 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | output_tokens | tokens | 44462.9 | 13/13 | 0 | 13 | 44462.9 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.00858935 | 13/13 | 0 | 13 | 0.00858935 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | protocol_failure_rate | fraction | 0.00858935 | 13/13 | 0 | 13 | 0.00858935 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.946671 | 13/13 | 0 | 13 | 0.946671 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | budget_utilization | fraction | 0.946671 | 13/13 | 0 | 13 | 0.946671 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 8.92308 | 13/13 | 0 | 13 | 8.92308 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | duplicate_action_attempts | count | 8.92308 | 13/13 | 0 | 13 | 8.92308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_attempts | count | 37.7692 | 13/13 | 0 | 13 | 37.7692 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_attempts | count | 37.7692 | 13/13 | 0 | 13 | 37.7692 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 11360.1 | 13/13 | 0 | 13 | 11360.1 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_cost_seconds | seconds | 11360.1 | 13/13 | 0 | 13 | 11360.1 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | input_tokens | tokens | 607185 | 13/13 | 0 | 13 | 607185 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | input_tokens | tokens | 607185 | 13/13 | 0 | 13 | 607185 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | output_tokens | tokens | 60782.2 | 13/13 | 0 | 13 | 60782.2 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | output_tokens | tokens | 60782.2 | 13/13 | 0 | 13 | 60782.2 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0127373 | 13/13 | 0 | 13 | 0.0127373 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0127373 | 13/13 | 0 | 13 | 0.0127373 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | budget_utilization | fraction | 0.980283 | 13/13 | 0 | 13 | 0.980283 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | budget_utilization | fraction | 0.980283 | 13/13 | 0 | 13 | 0.980283 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | duplicate_action_attempts | count | 5.92308 | 13/13 | 0 | 13 | 5.92308 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | duplicate_action_attempts | count | 5.92308 | 13/13 | 0 | 13 | 5.92308 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 3529.02 | 13/13 | 0 | 13 | 3529.02 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_cost_seconds | seconds | 3529.02 | 13/13 | 0 | 13 | 3529.02 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | input_tokens | tokens | 115659 | 13/13 | 0 | 13 | 115659 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | input_tokens | tokens | 115659 | 13/13 | 0 | 13 | 115659 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | output_tokens | tokens | 47583 | 13/13 | 0 | 13 | 47583 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | output_tokens | tokens | 47583 | 13/13 | 0 | 13 | 47583 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.00857347 | 13/13 | 0 | 13 | 0.00857347 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | protocol_failure_rate | fraction | 0.00857347 | 13/13 | 0 | 13 | 0.00857347 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | budget_utilization | fraction | 0.992365 | 13/13 | 0 | 13 | 0.992365 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | budget_utilization | fraction | 0.992365 | 13/13 | 0 | 13 | 0.992365 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | duplicate_action_attempts | count | 6.30769 | 13/13 | 0 | 13 | 6.30769 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | duplicate_action_attempts | count | 6.30769 | 13/13 | 0 | 13 | 6.30769 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_attempts | count | 11.8462 | 13/13 | 0 | 13 | 11.8462 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 3572.51 | 13/13 | 0 | 13 | 3572.51 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_cost_seconds | seconds | 3572.51 | 13/13 | 0 | 13 | 3572.51 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | input_tokens | tokens | 109687 | 13/13 | 0 | 13 | 109687 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | input_tokens | tokens | 109687 | 13/13 | 0 | 13 | 109687 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | output_tokens | tokens | 43988.4 | 13/13 | 0 | 13 | 43988.4 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | output_tokens | tokens | 43988.4 | 13/13 | 0 | 13 | 43988.4 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | protocol_failure_rate | fraction | 0 | 13/13 | 0 | 13 | 0 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | budget_utilization | fraction | 1.00332 | 13/13 | 0 | 13 | 1.00332 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | budget_utilization | fraction | 1.00332 | 13/13 | 0 | 13 | 1.00332 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | duplicate_action_attempts | count | 3.23077 | 13/13 | 0 | 13 | 3.23077 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | duplicate_action_attempts | count | 3.23077 | 13/13 | 0 | 13 | 3.23077 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_attempts | count | 12 | 13/13 | 0 | 13 | 12 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_attempts | count | 12 | 13/13 | 0 | 13 | 12 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 3611.96 | 13/13 | 0 | 13 | 3611.96 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_cost_seconds | seconds | 3611.96 | 13/13 | 0 | 13 | 3611.96 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | feedback_visible | count | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | input_tokens | tokens | 121894 | 13/13 | 0 | 13 | 121894 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | input_tokens | tokens | 121894 | 13/13 | 0 | 13 | 121894 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | output_tokens | tokens | 45493.9 | 13/13 | 0 | 13 | 45493.9 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | output_tokens | tokens | 45493.9 | 13/13 | 0 | 13 | 45493.9 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.00885628 | 13/13 | 0 | 13 | 0.00885628 | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | protocol_failure_rate | fraction | 0.00885628 | 13/13 | 0 | 13 | 0.00885628 | 1 / unknown |
| poolact | evidence_audit | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/13 | 13 | 13 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | budget_utilization | fraction | 0.758836 | 39/39 | 0 | 39 | 0.758836 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | budget_utilization | fraction | 0.758836 | 39/39 | 0 | 39 | 0.758836 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | duplicate_action_attempts | count | 25.7179 | 39/39 | 0 | 39 | 25.7179 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | duplicate_action_attempts | count | 25.7179 | 39/39 | 0 | 39 | 25.7179 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_attempts | count | 47.4615 | 39/39 | 0 | 39 | 47.4615 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_attempts | count | 47.4615 | 39/39 | 0 | 39 | 47.4615 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 9106.03 | 39/39 | 0 | 39 | 9106.03 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_cost_seconds | seconds | 9106.03 | 39/39 | 0 | 39 | 9106.03 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | input_tokens | tokens | 250738 | 39/39 | 0 | 39 | 250738 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | input_tokens | tokens | 250738 | 39/39 | 0 | 39 | 250738 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | output_tokens | tokens | 23713.9 | 39/39 | 0 | 39 | 23713.9 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | output_tokens | tokens | 23713.9 | 39/39 | 0 | 39 | 23713.9 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.0437267 | 39/39 | 0 | 39 | 0.0437267 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | protocol_failure_rate | fraction | 0.0437267 | 39/39 | 0 | 39 | 0.0437267 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | budget_utilization | fraction | 0.819506 | 39/39 | 0 | 39 | 0.819506 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | budget_utilization | fraction | 0.819506 | 39/39 | 0 | 39 | 0.819506 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | duplicate_action_attempts | count | 24.5128 | 39/39 | 0 | 39 | 24.5128 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | duplicate_action_attempts | count | 24.5128 | 39/39 | 0 | 39 | 24.5128 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_attempts | count | 45.1795 | 39/39 | 0 | 39 | 45.1795 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_attempts | count | 45.1795 | 39/39 | 0 | 39 | 45.1795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 9834.08 | 39/39 | 0 | 39 | 9834.08 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_cost_seconds | seconds | 9834.08 | 39/39 | 0 | 39 | 9834.08 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | input_tokens | tokens | 230992 | 39/39 | 0 | 39 | 230992 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | input_tokens | tokens | 230992 | 39/39 | 0 | 39 | 230992 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | output_tokens | tokens | 25173.2 | 39/39 | 0 | 39 | 25173.2 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | output_tokens | tokens | 25173.2 | 39/39 | 0 | 39 | 25173.2 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.0487763 | 39/39 | 0 | 39 | 0.0487763 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | protocol_failure_rate | fraction | 0.0487763 | 39/39 | 0 | 39 | 0.0487763 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.655585 | 39/39 | 0 | 39 | 0.655585 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | budget_utilization | fraction | 0.655585 | 39/39 | 0 | 39 | 0.655585 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 21.2308 | 39/39 | 0 | 39 | 21.2308 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | duplicate_action_attempts | count | 21.2308 | 39/39 | 0 | 39 | 21.2308 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_attempts | count | 44.4872 | 39/39 | 0 | 39 | 44.4872 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_attempts | count | 44.4872 | 39/39 | 0 | 39 | 44.4872 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 7867.02 | 39/39 | 0 | 39 | 7867.02 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_cost_seconds | seconds | 7867.02 | 39/39 | 0 | 39 | 7867.02 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | input_tokens | tokens | 548091 | 39/39 | 0 | 39 | 548091 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | input_tokens | tokens | 548091 | 39/39 | 0 | 39 | 548091 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | output_tokens | tokens | 35190.8 | 39/39 | 0 | 39 | 35190.8 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | output_tokens | tokens | 35190.8 | 39/39 | 0 | 39 | 35190.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.00973334 | 39/39 | 0 | 39 | 0.00973334 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | protocol_failure_rate | fraction | 0.00973334 | 39/39 | 0 | 39 | 0.00973334 | 1 / unknown |
| poolact | restricted_search | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | budget_utilization | fraction | 1.08491 | 39/39 | 0 | 39 | 1.08491 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | budget_utilization | fraction | 1.08491 | 39/39 | 0 | 39 | 1.08491 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | duplicate_action_attempts | count | 9.46154 | 39/39 | 0 | 39 | 9.46154 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | duplicate_action_attempts | count | 9.46154 | 39/39 | 0 | 39 | 9.46154 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_attempts | count | 16.4103 | 39/39 | 0 | 39 | 16.4103 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_attempts | count | 16.4103 | 39/39 | 0 | 39 | 16.4103 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 3905.68 | 39/39 | 0 | 39 | 3905.68 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_cost_seconds | seconds | 3905.68 | 39/39 | 0 | 39 | 3905.68 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | input_tokens | tokens | 35458.3 | 39/39 | 0 | 39 | 35458.3 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | input_tokens | tokens | 35458.3 | 39/39 | 0 | 39 | 35458.3 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | output_tokens | tokens | 6880.9 | 39/39 | 0 | 39 | 6880.9 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | output_tokens | tokens | 6880.9 | 39/39 | 0 | 39 | 6880.9 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.0671366 | 39/39 | 0 | 39 | 0.0671366 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | protocol_failure_rate | fraction | 0.0671366 | 39/39 | 0 | 39 | 0.0671366 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | budget_utilization | fraction | 1.1019 | 39/39 | 0 | 39 | 1.1019 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | budget_utilization | fraction | 1.1019 | 39/39 | 0 | 39 | 1.1019 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | duplicate_action_attempts | count | 9.74359 | 39/39 | 0 | 39 | 9.74359 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | duplicate_action_attempts | count | 9.74359 | 39/39 | 0 | 39 | 9.74359 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_attempts | count | 16.5128 | 39/39 | 0 | 39 | 16.5128 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_attempts | count | 16.5128 | 39/39 | 0 | 39 | 16.5128 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 3966.82 | 39/39 | 0 | 39 | 3966.82 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_cost_seconds | seconds | 3966.82 | 39/39 | 0 | 39 | 3966.82 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | input_tokens | tokens | 34095.2 | 39/39 | 0 | 39 | 34095.2 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | input_tokens | tokens | 34095.2 | 39/39 | 0 | 39 | 34095.2 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | output_tokens | tokens | 7174.33 | 39/39 | 0 | 39 | 7174.33 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | output_tokens | tokens | 7174.33 | 39/39 | 0 | 39 | 7174.33 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.0525472 | 39/39 | 0 | 39 | 0.0525472 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | protocol_failure_rate | fraction | 0.0525472 | 39/39 | 0 | 39 | 0.0525472 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | budget_utilization | fraction | 1.0877 | 39/39 | 0 | 39 | 1.0877 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | budget_utilization | fraction | 1.0877 | 39/39 | 0 | 39 | 1.0877 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | duplicate_action_attempts | count | 4.71795 | 39/39 | 0 | 39 | 4.71795 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | duplicate_action_attempts | count | 4.71795 | 39/39 | 0 | 39 | 4.71795 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_attempts | count | 16.5385 | 39/39 | 0 | 39 | 16.5385 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_attempts | count | 16.5385 | 39/39 | 0 | 39 | 16.5385 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 3915.71 | 39/39 | 0 | 39 | 3915.71 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_cost_seconds | seconds | 3915.71 | 39/39 | 0 | 39 | 3915.71 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | feedback_visible | count | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | input_tokens | tokens | 60483.8 | 39/39 | 0 | 39 | 60483.8 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | input_tokens | tokens | 60483.8 | 39/39 | 0 | 39 | 60483.8 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | output_tokens | tokens | 14122.6 | 39/39 | 0 | 39 | 14122.6 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | output_tokens | tokens | 14122.6 | 39/39 | 0 | 39 | 14122.6 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.0162939 | 39/39 | 0 | 39 | 0.0162939 | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | protocol_failure_rate | fraction | 0.0162939 | 39/39 | 0 | 39 | 0.0162939 | 1 / unknown |
| poolact | restricted_search | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | restricted_search | family/whois | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/39 | 39 | 39 | unknown | 1 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | budget_utilization | fraction | 0.979511 | 9/9 | 0 | 3 | 0.979511 | 3 / 0.0242982 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | budget_utilization | fraction | 0.979511 | 9/9 | 0 | 3 | 0.979511 | 3 / 0.0242982 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | budget_utilization | fraction | 0.986855 | 3/3 | 0 | 1 | 0.986855 | 3 / 0.0680669 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | budget_utilization | fraction | 0.973162 | 3/3 | 0 | 1 | 0.973162 | 3 / 0.0169633 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | budget_utilization | fraction | 0.978514 | 3/3 | 0 | 1 | 0.978514 | 3 / 0.0207612 |
| poolact | tuning | all/all | cost_moderate | cached | duplicate_action_attempts | count | 0.333333 | 9/9 | 0 | 3 | 0.333333 | 3 / 0 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | duplicate_action_attempts | count | 0.333333 | 9/9 | 0 | 3 | 0.333333 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | duplicate_action_attempts | count | 1 | 3/3 | 0 | 1 | 1 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_attempts | count | 46.6667 | 9/9 | 0 | 3 | 46.6667 | 3 / 3.1798 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_attempts | count | 46.6667 | 9/9 | 0 | 3 | 46.6667 | 3 / 3.1798 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_attempts | count | 30.3333 | 3/3 | 0 | 1 | 30.3333 | 3 / 11.6762 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_attempts | count | 46.6667 | 3/3 | 0 | 1 | 46.6667 | 3 / 4.16333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_attempts | count | 63 | 3/3 | 0 | 1 | 63 | 3 / 5 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_cost_seconds | seconds | 344912 | 9/9 | 0 | 3 | 344912 | 3 / 5388.06 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_cost_seconds | seconds | 344912 | 9/9 | 0 | 3 | 344912 | 3 / 5388.06 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_cost_seconds | seconds | 195166 | 3/3 | 0 | 1 | 195166 | 3 / 13461.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_cost_seconds | seconds | 401043 | 3/3 | 0 | 1 | 401043 | 3 / 6990.6 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_cost_seconds | seconds | 438526 | 3/3 | 0 | 1 | 438526 | 3 / 9304.24 |
| poolact | tuning | all/all | cost_moderate | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | cached | input_tokens | tokens | 669798 | 9/9 | 0 | 3 | 669798 | 3 / 32659.4 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | input_tokens | tokens | 669798 | 9/9 | 0 | 3 | 669798 | 3 / 32659.4 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | input_tokens | tokens | 342022 | 3/3 | 0 | 1 | 342022 | 3 / 204040 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | input_tokens | tokens | 591813 | 3/3 | 0 | 1 | 591813 | 3 / 45336.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | input_tokens | tokens | 1.07556e+06 | 3/3 | 0 | 1 | 1.07556e+06 | 3 / 161472 |
| poolact | tuning | all/all | cost_moderate | cached | output_tokens | tokens | 61250.9 | 9/9 | 0 | 3 | 61250.9 | 3 / 5192.04 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | output_tokens | tokens | 61250.9 | 9/9 | 0 | 3 | 61250.9 | 3 / 5192.04 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | output_tokens | tokens | 43659.7 | 3/3 | 0 | 1 | 43659.7 | 3 / 8421.88 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | output_tokens | tokens | 54668.7 | 3/3 | 0 | 1 | 54668.7 | 3 / 7473.19 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | output_tokens | tokens | 85424.3 | 3/3 | 0 | 1 | 85424.3 | 3 / 11698.7 |
| poolact | tuning | all/all | cost_moderate | cached | protocol_failure_rate | fraction | 0.0273574 | 9/9 | 0 | 3 | 0.0273574 | 3 / 0.0089794 |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | protocol_failure_rate | fraction | 0.0273574 | 9/9 | 0 | 3 | 0.0273574 | 3 / 0.0089794 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | protocol_failure_rate | fraction | 0.0495781 | 3/3 | 0 | 1 | 0.0495781 | 3 / 0.0254537 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | protocol_failure_rate | fraction | 0.0181941 | 3/3 | 0 | 1 | 0.0181941 | 3 / 0.0178667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | protocol_failure_rate | fraction | 0.0143 | 3/3 | 0 | 1 | 0.0143 | 3 / 0.013582 |
| poolact | tuning | all/all | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | budget_utilization | fraction | 0.950695 | 9/9 | 0 | 3 | 0.950695 | 3 / 0.0141404 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | budget_utilization | fraction | 0.950695 | 9/9 | 0 | 3 | 0.950695 | 3 / 0.0141404 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | budget_utilization | fraction | 0.937051 | 3/3 | 0 | 1 | 0.937051 | 3 / 0.0580653 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | budget_utilization | fraction | 0.953541 | 3/3 | 0 | 1 | 0.953541 | 3 / 0.0626824 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | budget_utilization | fraction | 0.961494 | 3/3 | 0 | 1 | 0.961494 | 3 / 0.0145895 |
| poolact | tuning | all/all | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.333333 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 9/9 | 0 | 3 | 0.666667 | 3 / 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | duplicate_action_attempts | count | 1 | 3/3 | 0 | 1 | 1 | 3 / 1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | duplicate_action_attempts | count | 0.666667 | 3/3 | 0 | 1 | 0.666667 | 3 / 1.1547 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_attempts | count | 46.8889 | 9/9 | 0 | 3 | 46.8889 | 3 / 5.67972 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_attempts | count | 46.8889 | 9/9 | 0 | 3 | 46.8889 | 3 / 5.67972 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_attempts | count | 20.3333 | 3/3 | 0 | 1 | 20.3333 | 3 / 3.78594 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_attempts | count | 51.6667 | 3/3 | 0 | 1 | 51.6667 | 3 / 6.50641 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_attempts | count | 68.6667 | 3/3 | 0 | 1 | 68.6667 | 3 / 8.0829 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_cost_seconds | seconds | 336391 | 9/9 | 0 | 3 | 336391 | 3 / 4830.55 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_cost_seconds | seconds | 336391 | 9/9 | 0 | 3 | 336391 | 3 / 4830.55 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_cost_seconds | seconds | 185317 | 3/3 | 0 | 1 | 185317 | 3 / 11483.4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_cost_seconds | seconds | 392957 | 3/3 | 0 | 1 | 392957 | 3 / 25831.6 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_cost_seconds | seconds | 430898 | 3/3 | 0 | 1 | 430898 | 3 / 6538.36 |
| poolact | tuning | all/all | cost_moderate | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | naive | input_tokens | tokens | 635250 | 9/9 | 0 | 3 | 635250 | 3 / 104855 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | input_tokens | tokens | 635250 | 9/9 | 0 | 3 | 635250 | 3 / 104855 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | input_tokens | tokens | 197118 | 3/3 | 0 | 1 | 197118 | 3 / 91494.4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | input_tokens | tokens | 685985 | 3/3 | 0 | 1 | 685985 | 3 / 83491.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | input_tokens | tokens | 1.02265e+06 | 3/3 | 0 | 1 | 1.02265e+06 | 3 / 147767 |
| poolact | tuning | all/all | cost_moderate | naive | output_tokens | tokens | 57983.1 | 9/9 | 0 | 3 | 57983.1 | 3 / 5929.93 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | output_tokens | tokens | 57983.1 | 9/9 | 0 | 3 | 57983.1 | 3 / 5929.93 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | output_tokens | tokens | 34636.7 | 3/3 | 0 | 1 | 34636.7 | 3 / 10784 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | output_tokens | tokens | 60875 | 3/3 | 0 | 1 | 60875 | 3 / 2464.85 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | output_tokens | tokens | 78437.7 | 3/3 | 0 | 1 | 78437.7 | 3 / 7132.69 |
| poolact | tuning | all/all | cost_moderate | naive | protocol_failure_rate | fraction | 0.0195836 | 9/9 | 0 | 3 | 0.0195836 | 3 / 0.0119131 |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | protocol_failure_rate | fraction | 0.0195836 | 9/9 | 0 | 3 | 0.0195836 | 3 / 0.0119131 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | protocol_failure_rate | fraction | 0.045679 | 3/3 | 0 | 1 | 0.045679 | 3 / 0.050557 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | protocol_failure_rate | fraction | 0.0130719 | 3/3 | 0 | 1 | 0.0130719 | 3 / 0.0226412 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | budget_utilization | fraction | 0.81604 | 9/9 | 0 | 3 | 0.81604 | 3 / 0.0336904 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | budget_utilization | fraction | 0.81604 | 9/9 | 0 | 3 | 0.81604 | 3 / 0.0336904 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | budget_utilization | fraction | 0.85574 | 3/3 | 0 | 1 | 0.85574 | 3 / 0.0665167 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | budget_utilization | fraction | 0.883737 | 3/3 | 0 | 1 | 0.883737 | 3 / 0.0870204 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | budget_utilization | fraction | 0.708643 | 3/3 | 0 | 1 | 0.708643 | 3 / 0.191743 |
| poolact | tuning | all/all | cost_moderate | poolact | duplicate_action_attempts | count | 1.88889 | 9/9 | 0 | 3 | 1.88889 | 3 / 0.3849 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | duplicate_action_attempts | count | 1.88889 | 9/9 | 0 | 3 | 1.88889 | 3 / 0.3849 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | duplicate_action_attempts | count | 1.33333 | 3/3 | 0 | 1 | 1.33333 | 3 / 2.3094 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | duplicate_action_attempts | count | 3.33333 | 3/3 | 0 | 1 | 3.33333 | 3 / 1.52753 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | duplicate_action_attempts | count | 1 | 3/3 | 0 | 1 | 1 | 3 / 1.73205 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_attempts | count | 39.6667 | 9/9 | 0 | 3 | 39.6667 | 3 / 4.91031 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_attempts | count | 39.6667 | 9/9 | 0 | 3 | 39.6667 | 3 / 4.91031 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_attempts | count | 23 | 3/3 | 0 | 1 | 23 | 3 / 9.64365 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_attempts | count | 44.3333 | 3/3 | 0 | 1 | 44.3333 | 3 / 5.50757 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_attempts | count | 51.6667 | 3/3 | 0 | 1 | 51.6667 | 3 / 11.3725 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_cost_seconds | seconds | 283669 | 9/9 | 0 | 3 | 283669 | 3 / 15602.3 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_cost_seconds | seconds | 283669 | 9/9 | 0 | 3 | 283669 | 3 / 15602.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_cost_seconds | seconds | 169236 | 3/3 | 0 | 1 | 169236 | 3 / 13154.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_cost_seconds | seconds | 364190 | 3/3 | 0 | 1 | 364190 | 3 / 35861.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_cost_seconds | seconds | 317581 | 3/3 | 0 | 1 | 317581 | 3 / 85930.5 |
| poolact | tuning | all/all | cost_moderate | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_moderate | poolact | input_tokens | tokens | 2.08789e+06 | 9/9 | 0 | 3 | 2.08789e+06 | 3 / 570805 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | input_tokens | tokens | 2.08789e+06 | 9/9 | 0 | 3 | 2.08789e+06 | 3 / 570805 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | input_tokens | tokens | 613850 | 3/3 | 0 | 1 | 613850 | 3 / 482165 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | input_tokens | tokens | 1.8563e+06 | 3/3 | 0 | 1 | 1.8563e+06 | 3 / 737568 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | input_tokens | tokens | 3.79353e+06 | 3/3 | 0 | 1 | 3.79353e+06 | 3 / 1.1474e+06 |
| poolact | tuning | all/all | cost_moderate | poolact | output_tokens | tokens | 120290 | 9/9 | 0 | 3 | 120290 | 3 / 15752.3 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | output_tokens | tokens | 120290 | 9/9 | 0 | 3 | 120290 | 3 / 15752.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | output_tokens | tokens | 79800 | 3/3 | 0 | 1 | 79800 | 3 / 39188.1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | output_tokens | tokens | 102003 | 3/3 | 0 | 1 | 102003 | 3 / 32545.5 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | output_tokens | tokens | 179067 | 3/3 | 0 | 1 | 179067 | 3 / 26771.6 |
| poolact | tuning | all/all | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0147306 | 9/9 | 0 | 3 | 0.0147306 | 3 / 0.00912009 |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0147306 | 9/9 | 0 | 3 | 0.0147306 | 3 / 0.00912009 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0305556 | 3/3 | 0 | 1 | 0.0305556 | 3 / 0.0267879 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | protocol_failure_rate | fraction | 0.0136364 | 3/3 | 0 | 1 | 0.0136364 | 3 / 0.0120261 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | budget_utilization | fraction | 1.11116 | 9/9 | 0 | 3 | 1.11116 | 3 / 0.040331 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | budget_utilization | fraction | 1.11116 | 9/9 | 0 | 3 | 1.11116 | 3 / 0.040331 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | budget_utilization | fraction | 1.30837 | 3/3 | 0 | 1 | 1.30837 | 3 / 0.175666 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | budget_utilization | fraction | 1.053 | 3/3 | 0 | 1 | 1.053 | 3 / 0.105832 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | budget_utilization | fraction | 0.972107 | 3/3 | 0 | 1 | 0.972107 | 3 / 0.0342461 |
| poolact | tuning | all/all | cost_tight | cached | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | cached | feedback_attempts | count | 13.3333 | 9/9 | 0 | 3 | 13.3333 | 3 / 0.333333 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_attempts | count | 13.3333 | 9/9 | 0 | 3 | 13.3333 | 3 / 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_attempts | count | 7.66667 | 3/3 | 0 | 1 | 7.66667 | 3 / 1.1547 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_attempts | count | 14.3333 | 3/3 | 0 | 1 | 14.3333 | 3 / 4.04145 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_attempts | count | 18 | 3/3 | 0 | 1 | 18 | 3 / 3.60555 |
| poolact | tuning | all/all | cost_tight | cached | feedback_cost_seconds | seconds | 112835 | 9/9 | 0 | 3 | 112835 | 3 / 1857.69 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_cost_seconds | seconds | 112835 | 9/9 | 0 | 3 | 112835 | 3 / 1857.69 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_cost_seconds | seconds | 77625.4 | 3/3 | 0 | 1 | 77625.4 | 3 / 10422.2 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_cost_seconds | seconds | 130184 | 3/3 | 0 | 1 | 130184 | 3 / 13084 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_cost_seconds | seconds | 130696 | 3/3 | 0 | 1 | 130696 | 3 / 4604.27 |
| poolact | tuning | all/all | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | cached | input_tokens | tokens | 141519 | 9/9 | 0 | 3 | 141519 | 3 / 13866.4 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | input_tokens | tokens | 141519 | 9/9 | 0 | 3 | 141519 | 3 / 13866.4 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | input_tokens | tokens | 82594.7 | 3/3 | 0 | 1 | 82594.7 | 3 / 14155.9 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | input_tokens | tokens | 147984 | 3/3 | 0 | 1 | 147984 | 3 / 51196.3 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | input_tokens | tokens | 193979 | 3/3 | 0 | 1 | 193979 | 3 / 73583.2 |
| poolact | tuning | all/all | cost_tight | cached | output_tokens | tokens | 37746 | 9/9 | 0 | 3 | 37746 | 3 / 8818.97 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | output_tokens | tokens | 37746 | 9/9 | 0 | 3 | 37746 | 3 / 8818.97 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | output_tokens | tokens | 27941.7 | 3/3 | 0 | 1 | 27941.7 | 3 / 7562.46 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | output_tokens | tokens | 36539.3 | 3/3 | 0 | 1 | 36539.3 | 3 / 7595.15 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | output_tokens | tokens | 48757 | 3/3 | 0 | 1 | 48757 | 3 / 15724.8 |
| poolact | tuning | all/all | cost_tight | cached | protocol_failure_rate | fraction | 0.0575375 | 9/9 | 0 | 3 | 0.0575375 | 3 / 0.0304565 |
| poolact | tuning | family/nasbench101 | cost_tight | cached | protocol_failure_rate | fraction | 0.0575375 | 9/9 | 0 | 3 | 0.0575375 | 3 / 0.0304565 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | protocol_failure_rate | fraction | 0.126374 | 3/3 | 0 | 1 | 0.126374 | 3 / 0.0475838 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | protocol_failure_rate | fraction | 0.0462388 | 3/3 | 0 | 1 | 0.0462388 | 3 / 0.047679 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | cached | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | budget_utilization | fraction | 1.09346 | 9/9 | 0 | 3 | 1.09346 | 3 / 0.106143 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | budget_utilization | fraction | 1.09346 | 9/9 | 0 | 3 | 1.09346 | 3 / 0.106143 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | budget_utilization | fraction | 1.20015 | 3/3 | 0 | 1 | 1.20015 | 3 / 0.273991 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | budget_utilization | fraction | 1.0836 | 3/3 | 0 | 1 | 1.0836 | 3 / 0.10581 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | budget_utilization | fraction | 0.99664 | 3/3 | 0 | 1 | 0.99664 | 3 / 0.0561195 |
| poolact | tuning | all/all | cost_tight | naive | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | all/all | cost_tight | naive | feedback_attempts | count | 12.1111 | 9/9 | 0 | 3 | 12.1111 | 3 / 1.64429 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_attempts | count | 12.1111 | 9/9 | 0 | 3 | 12.1111 | 3 / 1.64429 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_attempts | count | 7 | 3/3 | 0 | 1 | 7 | 3 / 1.73205 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_attempts | count | 14 | 3/3 | 0 | 1 | 14 | 3 / 1.73205 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_attempts | count | 15.3333 | 3/3 | 0 | 1 | 15.3333 | 3 / 3.05505 |
| poolact | tuning | all/all | cost_tight | naive | feedback_cost_seconds | seconds | 113055 | 9/9 | 0 | 3 | 113055 | 3 / 7134.14 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_cost_seconds | seconds | 113055 | 9/9 | 0 | 3 | 113055 | 3 / 7134.14 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_cost_seconds | seconds | 71204.8 | 3/3 | 0 | 1 | 71204.8 | 3 / 16255.8 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_cost_seconds | seconds | 133966 | 3/3 | 0 | 1 | 133966 | 3 / 13081.4 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_cost_seconds | seconds | 133995 | 3/3 | 0 | 1 | 133995 | 3 / 7545.06 |
| poolact | tuning | all/all | cost_tight | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | naive | input_tokens | tokens | 129448 | 9/9 | 0 | 3 | 129448 | 3 / 11351.1 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | input_tokens | tokens | 129448 | 9/9 | 0 | 3 | 129448 | 3 / 11351.1 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | input_tokens | tokens | 66733.3 | 3/3 | 0 | 1 | 66733.3 | 3 / 23649.9 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | input_tokens | tokens | 151648 | 3/3 | 0 | 1 | 151648 | 3 / 11482 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | input_tokens | tokens | 169962 | 3/3 | 0 | 1 | 169962 | 3 / 19116.8 |
| poolact | tuning | all/all | cost_tight | naive | output_tokens | tokens | 32709.7 | 9/9 | 0 | 3 | 32709.7 | 3 / 5087.63 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | output_tokens | tokens | 32709.7 | 9/9 | 0 | 3 | 32709.7 | 3 / 5087.63 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | output_tokens | tokens | 22758.3 | 3/3 | 0 | 1 | 22758.3 | 3 / 8054.83 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | output_tokens | tokens | 29763 | 3/3 | 0 | 1 | 29763 | 3 / 4379.56 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | output_tokens | tokens | 45607.7 | 3/3 | 0 | 1 | 45607.7 | 3 / 5083.44 |
| poolact | tuning | all/all | cost_tight | naive | protocol_failure_rate | fraction | 0.0958787 | 9/9 | 0 | 3 | 0.0958787 | 3 / 0.0253025 |
| poolact | tuning | family/nasbench101 | cost_tight | naive | protocol_failure_rate | fraction | 0.0958787 | 9/9 | 0 | 3 | 0.0958787 | 3 / 0.0253025 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | protocol_failure_rate | fraction | 0.109668 | 3/3 | 0 | 1 | 0.109668 | 3 / 0.050314 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | protocol_failure_rate | fraction | 0.143867 | 3/3 | 0 | 1 | 0.143867 | 3 / 0.0527825 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | protocol_failure_rate | fraction | 0.0341006 | 3/3 | 0 | 1 | 0.0341006 | 3 / 0.0305124 |
| poolact | tuning | all/all | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | naive | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | budget_utilization | fraction | 1.02778 | 9/9 | 0 | 3 | 1.02778 | 3 / 0.0341902 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | budget_utilization | fraction | 1.02778 | 9/9 | 0 | 3 | 1.02778 | 3 / 0.0341902 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | budget_utilization | fraction | 1.20355 | 3/3 | 0 | 1 | 1.20355 | 3 / 0.136917 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | budget_utilization | fraction | 0.989111 | 3/3 | 0 | 1 | 0.989111 | 3 / 0.0541499 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | budget_utilization | fraction | 0.890681 | 3/3 | 0 | 1 | 0.890681 | 3 / 0.13157 |
| poolact | tuning | all/all | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | duplicate_action_attempts | count | 0.222222 | 9/9 | 0 | 3 | 0.222222 | 3 / 0.3849 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | duplicate_action_attempts | count | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | duplicate_action_attempts | count | 0.333333 | 3/3 | 0 | 1 | 0.333333 | 3 / 0.57735 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_attempts | count | 14.4444 | 9/9 | 0 | 3 | 14.4444 | 3 / 1.34715 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_attempts | count | 14.4444 | 9/9 | 0 | 3 | 14.4444 | 3 / 1.34715 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_attempts | count | 9.33333 | 3/3 | 0 | 1 | 9.33333 | 3 / 1.52753 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_attempts | count | 13 | 3/3 | 0 | 1 | 13 | 3 / 3.60555 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_attempts | count | 21 | 3/3 | 0 | 1 | 21 | 3 / 6.08276 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_cost_seconds | seconds | 104480 | 9/9 | 0 | 3 | 104480 | 3 / 4712.86 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_cost_seconds | seconds | 104480 | 9/9 | 0 | 3 | 104480 | 3 / 4712.86 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_cost_seconds | seconds | 71406.6 | 3/3 | 0 | 1 | 71406.6 | 3 / 8123.29 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_cost_seconds | seconds | 122284 | 3/3 | 0 | 1 | 122284 | 3 / 6694.59 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_cost_seconds | seconds | 119749 | 3/3 | 0 | 1 | 119749 | 3 / 17689.1 |
| poolact | tuning | all/all | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | feedback_visible | count | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | feedback_visible | count | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | all/all | cost_tight | poolact | input_tokens | tokens | 293543 | 9/9 | 0 | 3 | 293543 | 3 / 73250.2 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | input_tokens | tokens | 293543 | 9/9 | 0 | 3 | 293543 | 3 / 73250.2 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | input_tokens | tokens | 126894 | 3/3 | 0 | 1 | 126894 | 3 / 23241.4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | input_tokens | tokens | 189027 | 3/3 | 0 | 1 | 189027 | 3 / 84843 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | input_tokens | tokens | 564708 | 3/3 | 0 | 1 | 564708 | 3 / 282273 |
| poolact | tuning | all/all | cost_tight | poolact | output_tokens | tokens | 54818.2 | 9/9 | 0 | 3 | 54818.2 | 3 / 2782.29 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | output_tokens | tokens | 54818.2 | 9/9 | 0 | 3 | 54818.2 | 3 / 2782.29 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | output_tokens | tokens | 38968 | 3/3 | 0 | 1 | 38968 | 3 / 3608.29 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | output_tokens | tokens | 41561 | 3/3 | 0 | 1 | 41561 | 3 / 18857.1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | output_tokens | tokens | 83925.7 | 3/3 | 0 | 1 | 83925.7 | 3 / 23190.9 |
| poolact | tuning | all/all | cost_tight | poolact | protocol_failure_rate | fraction | 0.028719 | 9/9 | 0 | 3 | 0.028719 | 3 / 0.0146298 |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | protocol_failure_rate | fraction | 0.028719 | 9/9 | 0 | 3 | 0.028719 | 3 / 0.0146298 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | protocol_failure_rate | fraction | 0.0464744 | 3/3 | 0 | 1 | 0.0464744 | 3 / 0.0408889 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | protocol_failure_rate | fraction | 0.0396825 | 3/3 | 0 | 1 | 0.0396825 | 3 / 0.0363696 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | protocol_failure_rate | fraction | 0 | 3/3 | 0 | 1 | 0 | 3 / 0 |
| poolact | tuning | all/all | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | family/nasbench101 | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/9 | 9 | 3 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | poolact | wall_time_seconds | seconds | unknown | 0/3 | 3 | 1 | unknown | 3 / unknown |


## 资源：全部差值

资源差值只描述消耗变化；正负不能单独解释为性能改善。

| 系统 | 场景 | 层/切片 | 档位 | 指标 | 差值方向 | 完整差值 | 单位 | 百分点差 | 配对 known/expected | missing | 仅已知配对子集 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| expgym | evidence_audit | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.025641 | count | 不适用 | 13/13 | 0 | 0.025641 |
| expgym | evidence_audit | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.025641 | count | 不适用 | 13/13 | 0 | 0.025641 |
| expgym | evidence_audit | family/evidence_audit | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.025641 | count | 不适用 | 13/13 | 0 | 0.025641 |
| expgym | evidence_audit | family/evidence_audit | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.025641 | count | 不适用 | 13/13 | 0 | 0.025641 |
| expgym | evidence_audit | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +18.0513 | count | 不适用 | 13/13 | 0 | 18.0513 |
| expgym | evidence_audit | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +24.7692 | count | 不适用 | 13/13 | 0 | 24.7692 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_attempts | cost_free − cost_moderate | +18.0513 | count | 不适用 | 13/13 | 0 | 18.0513 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_attempts | cost_free − cost_tight | +24.7692 | count | 不适用 | 13/13 | 0 | 24.7692 |
| expgym | evidence_audit | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +5414.03 | seconds | 不适用 | 13/13 | 0 | 5414.03 |
| expgym | evidence_audit | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +7440.6 | seconds | 不适用 | 13/13 | 0 | 7440.6 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +5414.03 | seconds | 不适用 | 13/13 | 0 | 5414.03 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_cost_seconds | cost_free − cost_tight | +7440.6 | seconds | 不适用 | 13/13 | 0 | 7440.6 |
| expgym | evidence_audit | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +18.4615 | count | 不适用 | 13/13 | 0 | 18.4615 |
| expgym | evidence_audit | all/all | cost_free | feedback_visible | cost_free − cost_tight | +25.3846 | count | 不适用 | 13/13 | 0 | 25.3846 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_visible | cost_free − cost_moderate | +18.4615 | count | 不适用 | 13/13 | 0 | 18.4615 |
| expgym | evidence_audit | family/evidence_audit | cost_free | feedback_visible | cost_free − cost_tight | +25.3846 | count | 不适用 | 13/13 | 0 | 25.3846 |
| expgym | evidence_audit | all/all | cost_free | input_tokens | cost_free − cost_moderate | +211910 | tokens | 不适用 | 13/13 | 0 | 211910 |
| expgym | evidence_audit | all/all | cost_free | input_tokens | cost_free − cost_tight | +277526 | tokens | 不适用 | 13/13 | 0 | 277526 |
| expgym | evidence_audit | family/evidence_audit | cost_free | input_tokens | cost_free − cost_moderate | +211910 | tokens | 不适用 | 13/13 | 0 | 211910 |
| expgym | evidence_audit | family/evidence_audit | cost_free | input_tokens | cost_free − cost_tight | +277526 | tokens | 不适用 | 13/13 | 0 | 277526 |
| expgym | evidence_audit | all/all | cost_free | output_tokens | cost_free − cost_moderate | +955.051 | tokens | 不适用 | 13/13 | 0 | 955.051 |
| expgym | evidence_audit | all/all | cost_free | output_tokens | cost_free − cost_tight | +2679.05 | tokens | 不适用 | 13/13 | 0 | 2679.05 |
| expgym | evidence_audit | family/evidence_audit | cost_free | output_tokens | cost_free − cost_moderate | +955.051 | tokens | 不适用 | 13/13 | 0 | 955.051 |
| expgym | evidence_audit | family/evidence_audit | cost_free | output_tokens | cost_free − cost_tight | +2679.05 | tokens | 不适用 | 13/13 | 0 | 2679.05 |
| expgym | evidence_audit | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0143165 | fraction | +1.43165 | 13/13 | 0 | 0.0143165 |
| expgym | evidence_audit | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.010043 | fraction | +1.0043 | 13/13 | 0 | 0.010043 |
| expgym | evidence_audit | family/evidence_audit | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0143165 | fraction | +1.43165 | 13/13 | 0 | 0.0143165 |
| expgym | evidence_audit | family/evidence_audit | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.010043 | fraction | +1.0043 | 13/13 | 0 | 0.010043 |
| expgym | evidence_audit | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +97.7818 | seconds | 不适用 | 13/13 | 0 | 97.7818 |
| expgym | evidence_audit | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +152.075 | seconds | 不适用 | 13/13 | 0 | 152.075 |
| expgym | evidence_audit | family/evidence_audit | cost_free | wall_time_seconds | cost_free − cost_moderate | +97.7818 | seconds | 不适用 | 13/13 | 0 | 97.7818 |
| expgym | evidence_audit | family/evidence_audit | cost_free | wall_time_seconds | cost_free − cost_tight | +152.075 | seconds | 不适用 | 13/13 | 0 | 152.075 |
| expgym | evidence_audit | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0368828 | fraction | -3.68828 | 13/13 | 0 | -0.0368828 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0368828 | fraction | -3.68828 | 13/13 | 0 | -0.0368828 |
| expgym | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 13/13 | 0 | 0 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 13/13 | 0 | 0 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.71795 | count | 不适用 | 13/13 | 0 | 6.71795 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.71795 | count | 不适用 | 13/13 | 0 | 6.71795 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +2026.58 | seconds | 不适用 | 13/13 | 0 | 2026.58 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +2026.58 | seconds | 不适用 | 13/13 | 0 | 2026.58 |
| expgym | evidence_audit | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.92308 | count | 不适用 | 13/13 | 0 | 6.92308 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.92308 | count | 不适用 | 13/13 | 0 | 6.92308 |
| expgym | evidence_audit | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +65615.5 | tokens | 不适用 | 13/13 | 0 | 65615.5 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | cost_moderate − cost_tight | +65615.5 | tokens | 不适用 | 13/13 | 0 | 65615.5 |
| expgym | evidence_audit | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +1724 | tokens | 不适用 | 13/13 | 0 | 1724 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | cost_moderate − cost_tight | +1724 | tokens | 不适用 | 13/13 | 0 | 1724 |
| expgym | evidence_audit | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0042735 | fraction | -0.42735 | 13/13 | 0 | -0.0042735 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0042735 | fraction | -0.42735 | 13/13 | 0 | -0.0042735 |
| expgym | evidence_audit | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +54.2927 | seconds | 不适用 | 13/13 | 0 | 54.2927 |
| expgym | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +54.2927 | seconds | 不适用 | 13/13 | 0 | 54.2927 |
| expgym | restricted_search | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.0136986 | count | 不适用 | 73/73 | 0 | -0.0136986 |
| expgym | restricted_search | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.0273973 | count | 不适用 | 73/73 | 0 | 0.0273973 |
| expgym | restricted_search | family/whatis | cost_free | duplicate_action_attempts | cost_free − cost_moderate | -0.0294118 | count | 不适用 | 34/34 | 0 | -0.0294118 |
| expgym | restricted_search | family/whatis | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.0588235 | count | 不适用 | 34/34 | 0 | 0.0588235 |
| expgym | restricted_search | family/whois | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 39/39 | 0 | 0 |
| expgym | restricted_search | family/whois | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 39/39 | 0 | 0 |
| expgym | restricted_search | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +3.87671 | count | 不适用 | 73/73 | 0 | 3.87671 |
| expgym | restricted_search | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +10.6301 | count | 不适用 | 73/73 | 0 | 10.6301 |
| expgym | restricted_search | family/whatis | cost_free | feedback_attempts | cost_free − cost_moderate | +4.70588 | count | 不适用 | 34/34 | 0 | 4.70588 |
| expgym | restricted_search | family/whatis | cost_free | feedback_attempts | cost_free − cost_tight | +11.4118 | count | 不适用 | 34/34 | 0 | 11.4118 |
| expgym | restricted_search | family/whois | cost_free | feedback_attempts | cost_free − cost_moderate | +3.15385 | count | 不适用 | 39/39 | 0 | 3.15385 |
| expgym | restricted_search | family/whois | cost_free | feedback_attempts | cost_free − cost_tight | +9.94872 | count | 不适用 | 39/39 | 0 | 9.94872 |
| expgym | restricted_search | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +1021.02 | seconds | 不适用 | 73/73 | 0 | 1021.02 |
| expgym | restricted_search | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2510.58 | seconds | 不适用 | 73/73 | 0 | 2510.58 |
| expgym | restricted_search | family/whatis | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +1232.84 | seconds | 不适用 | 34/34 | 0 | 1232.84 |
| expgym | restricted_search | family/whatis | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2781.45 | seconds | 不适用 | 34/34 | 0 | 2781.45 |
| expgym | restricted_search | family/whois | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +836.363 | seconds | 不适用 | 39/39 | 0 | 836.363 |
| expgym | restricted_search | family/whois | cost_free | feedback_cost_seconds | cost_free − cost_tight | +2274.45 | seconds | 不适用 | 39/39 | 0 | 2274.45 |
| expgym | restricted_search | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +4.17808 | count | 不适用 | 73/73 | 0 | 4.17808 |
| expgym | restricted_search | all/all | cost_free | feedback_visible | cost_free − cost_tight | +11.2877 | count | 不适用 | 73/73 | 0 | 11.2877 |
| expgym | restricted_search | family/whatis | cost_free | feedback_visible | cost_free − cost_moderate | +5.08824 | count | 不适用 | 34/34 | 0 | 5.08824 |
| expgym | restricted_search | family/whatis | cost_free | feedback_visible | cost_free − cost_tight | +12.0882 | count | 不适用 | 34/34 | 0 | 12.0882 |
| expgym | restricted_search | family/whois | cost_free | feedback_visible | cost_free − cost_moderate | +3.38462 | count | 不适用 | 39/39 | 0 | 3.38462 |
| expgym | restricted_search | family/whois | cost_free | feedback_visible | cost_free − cost_tight | +10.5897 | count | 不适用 | 39/39 | 0 | 10.5897 |
| expgym | restricted_search | all/all | cost_free | input_tokens | cost_free − cost_moderate | +30482.6 | tokens | 不适用 | 73/73 | 0 | 30482.6 |
| expgym | restricted_search | all/all | cost_free | input_tokens | cost_free − cost_tight | +74293.3 | tokens | 不适用 | 73/73 | 0 | 74293.3 |
| expgym | restricted_search | family/whatis | cost_free | input_tokens | cost_free − cost_moderate | +38639.9 | tokens | 不适用 | 34/34 | 0 | 38639.9 |
| expgym | restricted_search | family/whatis | cost_free | input_tokens | cost_free − cost_tight | +79522.5 | tokens | 不适用 | 34/34 | 0 | 79522.5 |
| expgym | restricted_search | family/whois | cost_free | input_tokens | cost_free − cost_moderate | +23371.2 | tokens | 不适用 | 39/39 | 0 | 23371.2 |
| expgym | restricted_search | family/whois | cost_free | input_tokens | cost_free − cost_tight | +69734.5 | tokens | 不适用 | 39/39 | 0 | 69734.5 |
| expgym | restricted_search | all/all | cost_free | output_tokens | cost_free − cost_moderate | +44.8082 | tokens | 不适用 | 73/73 | 0 | 44.8082 |
| expgym | restricted_search | all/all | cost_free | output_tokens | cost_free − cost_tight | +3697.42 | tokens | 不适用 | 73/73 | 0 | 3697.42 |
| expgym | restricted_search | family/whatis | cost_free | output_tokens | cost_free − cost_moderate | +143.853 | tokens | 不适用 | 34/34 | 0 | 143.853 |
| expgym | restricted_search | family/whatis | cost_free | output_tokens | cost_free − cost_tight | +2545.12 | tokens | 不适用 | 34/34 | 0 | 2545.12 |
| expgym | restricted_search | family/whois | cost_free | output_tokens | cost_free − cost_moderate | -41.5385 | tokens | 不适用 | 39/39 | 0 | -41.5385 |
| expgym | restricted_search | family/whois | cost_free | output_tokens | cost_free − cost_tight | +4702 | tokens | 不适用 | 39/39 | 0 | 4702 |
| expgym | restricted_search | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.011918 | fraction | -1.1918 | 73/73 | 0 | -0.011918 |
| expgym | restricted_search | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0213886 | fraction | -2.13886 | 73/73 | 0 | -0.0213886 |
| expgym | restricted_search | family/whatis | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.00609091 | fraction | -0.609091 | 34/34 | 0 | -0.00609091 |
| expgym | restricted_search | family/whatis | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0278824 | fraction | -2.78824 | 34/34 | 0 | -0.0278824 |
| expgym | restricted_search | family/whois | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0169981 | fraction | -1.69981 | 39/39 | 0 | -0.0169981 |
| expgym | restricted_search | family/whois | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0157274 | fraction | -1.57274 | 39/39 | 0 | -0.0157274 |
| expgym | restricted_search | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +11.4238 | seconds | 不适用 | 73/73 | 0 | 11.4238 |
| expgym | restricted_search | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +171.451 | seconds | 不适用 | 73/73 | 0 | 171.451 |
| expgym | restricted_search | family/whatis | cost_free | wall_time_seconds | cost_free − cost_moderate | +17.1224 | seconds | 不适用 | 34/34 | 0 | 17.1224 |
| expgym | restricted_search | family/whatis | cost_free | wall_time_seconds | cost_free − cost_tight | +133.887 | seconds | 不适用 | 34/34 | 0 | 133.887 |
| expgym | restricted_search | family/whois | cost_free | wall_time_seconds | cost_free − cost_moderate | +6.45582 | seconds | 不适用 | 39/39 | 0 | 6.45582 |
| expgym | restricted_search | family/whois | cost_free | wall_time_seconds | cost_free − cost_tight | +204.2 | seconds | 不适用 | 39/39 | 0 | 204.2 |
| expgym | restricted_search | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.270784 | fraction | -27.0784 | 73/73 | 0 | -0.270784 |
| expgym | restricted_search | family/whatis | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.251802 | fraction | -25.1802 | 34/34 | 0 | -0.251802 |
| expgym | restricted_search | family/whois | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.287332 | fraction | -28.7332 | 39/39 | 0 | -0.287332 |
| expgym | restricted_search | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.0410959 | count | 不适用 | 73/73 | 0 | 0.0410959 |
| expgym | restricted_search | family/whatis | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.0882353 | count | 不适用 | 34/34 | 0 | 0.0882353 |
| expgym | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 39/39 | 0 | 0 |
| expgym | restricted_search | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.75342 | count | 不适用 | 73/73 | 0 | 6.75342 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.70588 | count | 不适用 | 34/34 | 0 | 6.70588 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.79487 | count | 不适用 | 39/39 | 0 | 6.79487 |
| expgym | restricted_search | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1489.56 | seconds | 不适用 | 73/73 | 0 | 1489.56 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1548.61 | seconds | 不适用 | 34/34 | 0 | 1548.61 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1438.08 | seconds | 不适用 | 39/39 | 0 | 1438.08 |
| expgym | restricted_search | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.10959 | count | 不适用 | 73/73 | 0 | 7.10959 |
| expgym | restricted_search | family/whatis | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7 | count | 不适用 | 34/34 | 0 | 7 |
| expgym | restricted_search | family/whois | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.20513 | count | 不适用 | 39/39 | 0 | 7.20513 |
| expgym | restricted_search | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +43810.7 | tokens | 不适用 | 73/73 | 0 | 43810.7 |
| expgym | restricted_search | family/whatis | cost_moderate | input_tokens | cost_moderate − cost_tight | +40882.6 | tokens | 不适用 | 34/34 | 0 | 40882.6 |
| expgym | restricted_search | family/whois | cost_moderate | input_tokens | cost_moderate − cost_tight | +46363.4 | tokens | 不适用 | 39/39 | 0 | 46363.4 |
| expgym | restricted_search | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +3652.62 | tokens | 不适用 | 73/73 | 0 | 3652.62 |
| expgym | restricted_search | family/whatis | cost_moderate | output_tokens | cost_moderate − cost_tight | +2401.26 | tokens | 不适用 | 34/34 | 0 | 2401.26 |
| expgym | restricted_search | family/whois | cost_moderate | output_tokens | cost_moderate − cost_tight | +4743.54 | tokens | 不适用 | 39/39 | 0 | 4743.54 |
| expgym | restricted_search | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.00947062 | fraction | -0.947062 | 73/73 | 0 | -0.00947062 |
| expgym | restricted_search | family/whatis | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0217915 | fraction | -2.17915 | 34/34 | 0 | -0.0217915 |
| expgym | restricted_search | family/whois | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.00127068 | fraction | +0.127068 | 39/39 | 0 | 0.00127068 |
| expgym | restricted_search | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +160.027 | seconds | 不适用 | 73/73 | 0 | 160.027 |
| expgym | restricted_search | family/whatis | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +116.765 | seconds | 不适用 | 34/34 | 0 | 116.765 |
| expgym | restricted_search | family/whois | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +197.744 | seconds | 不适用 | 39/39 | 0 | 197.744 |
| expgym | tuning | all/all | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.148148 | count | 不适用 | 27/27 | 0 | 0.148148 |
| expgym | tuning | all/all | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.185185 | count | 不适用 | 27/27 | 0 | 0.185185 |
| expgym | tuning | family/nasbench101 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/nasbench101 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.222222 | count | 不适用 | 9/9 | 0 | 0.222222 |
| expgym | tuning | family/nasbench201 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.222222 | count | 不适用 | 9/9 | 0 | 0.222222 |
| expgym | tuning | family/nasbench201 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.222222 | count | 不适用 | 9/9 | 0 | 0.222222 |
| expgym | tuning | family/paramnet | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/paramnet | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | duplicate_action_attempts | cost_free − cost_moderate | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | duplicate_action_attempts | cost_free − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | all/all | cost_free | feedback_attempts | cost_free − cost_moderate | +19.4074 | count | 不适用 | 27/27 | 0 | 19.4074 |
| expgym | tuning | all/all | cost_free | feedback_attempts | cost_free − cost_tight | +25.2593 | count | 不适用 | 27/27 | 0 | 25.2593 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_attempts | cost_free − cost_moderate | +20.8889 | count | 不适用 | 9/9 | 0 | 20.8889 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_attempts | cost_free − cost_tight | +25.8889 | count | 不适用 | 9/9 | 0 | 25.8889 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_attempts | cost_free − cost_moderate | +18.8889 | count | 不适用 | 9/9 | 0 | 18.8889 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_attempts | cost_free − cost_tight | +25.7778 | count | 不适用 | 9/9 | 0 | 25.7778 |
| expgym | tuning | family/paramnet | cost_free | feedback_attempts | cost_free − cost_moderate | +18.4444 | count | 不适用 | 9/9 | 0 | 18.4444 |
| expgym | tuning | family/paramnet | cost_free | feedback_attempts | cost_free − cost_tight | +24.1111 | count | 不适用 | 9/9 | 0 | 24.1111 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_attempts | cost_free − cost_moderate | +24.6667 | count | 不适用 | 3/3 | 0 | 24.6667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_attempts | cost_free − cost_tight | +27.3333 | count | 不适用 | 3/3 | 0 | 27.3333 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_attempts | cost_free − cost_moderate | +21.6667 | count | 不适用 | 3/3 | 0 | 21.6667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_attempts | cost_free − cost_tight | +25.6667 | count | 不适用 | 3/3 | 0 | 25.6667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_attempts | cost_free − cost_moderate | +16.3333 | count | 不适用 | 3/3 | 0 | 16.3333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_attempts | cost_free − cost_tight | +24.6667 | count | 不适用 | 3/3 | 0 | 24.6667 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_attempts | cost_free − cost_moderate | +19 | count | 不适用 | 3/3 | 0 | 19 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_attempts | cost_free − cost_tight | +26.6667 | count | 不适用 | 3/3 | 0 | 26.6667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_attempts | cost_free − cost_moderate | +18.6667 | count | 不适用 | 3/3 | 0 | 18.6667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_attempts | cost_free − cost_tight | +25 | count | 不适用 | 3/3 | 0 | 25 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_attempts | cost_free − cost_moderate | +19 | count | 不适用 | 3/3 | 0 | 19 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_attempts | cost_free − cost_tight | +25.6667 | count | 不适用 | 3/3 | 0 | 25.6667 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +21 | count | 不适用 | 3/3 | 0 | 21 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_attempts | cost_free − cost_tight | +22 | count | 不适用 | 3/3 | 0 | 22 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +15 | count | 不适用 | 3/3 | 0 | 15 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_attempts | cost_free − cost_tight | +27 | count | 不适用 | 3/3 | 0 | 27 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_attempts | cost_free − cost_moderate | +19.3333 | count | 不适用 | 3/3 | 0 | 19.3333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_attempts | cost_free − cost_tight | +23.3333 | count | 不适用 | 3/3 | 0 | 23.3333 |
| expgym | tuning | all/all | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +199796 | seconds | 不适用 | 27/27 | 0 | 199796 |
| expgym | tuning | all/all | cost_free | feedback_cost_seconds | cost_free − cost_tight | +273987 | seconds | 不适用 | 27/27 | 0 | 273987 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +126573 | seconds | 不适用 | 9/9 | 0 | 126573 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +178233 | seconds | 不适用 | 9/9 | 0 | 178233 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +468373 | seconds | 不适用 | 9/9 | 0 | 468373 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +638526 | seconds | 不适用 | 9/9 | 0 | 638526 |
| expgym | tuning | family/paramnet | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +4443.26 | seconds | 不适用 | 9/9 | 0 | 4443.26 |
| expgym | tuning | family/paramnet | cost_free | feedback_cost_seconds | cost_free − cost_tight | +5201.69 | seconds | 不适用 | 9/9 | 0 | 5201.69 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +191338 | seconds | 不适用 | 3/3 | 0 | 191338 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_cost_seconds | cost_free − cost_tight | +211772 | seconds | 不适用 | 3/3 | 0 | 211772 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +121167 | seconds | 不适用 | 3/3 | 0 | 121167 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_cost_seconds | cost_free − cost_tight | +180241 | seconds | 不适用 | 3/3 | 0 | 180241 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +67214.2 | seconds | 不适用 | 3/3 | 0 | 67214.2 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_cost_seconds | cost_free − cost_tight | +142686 | seconds | 不适用 | 3/3 | 0 | 142686 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +204840 | seconds | 不适用 | 3/3 | 0 | 204840 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_cost_seconds | cost_free − cost_tight | +278228 | seconds | 不适用 | 3/3 | 0 | 278228 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +313111 | seconds | 不适用 | 3/3 | 0 | 313111 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +420217 | seconds | 不适用 | 3/3 | 0 | 420217 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +887167 | seconds | 不适用 | 3/3 | 0 | 887167 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_cost_seconds | cost_free − cost_tight | +1.21713e+06 | seconds | 不适用 | 3/3 | 0 | 1.21713e+06 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +7584.98 | seconds | 不适用 | 3/3 | 0 | 7584.98 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +7740.04 | seconds | 不适用 | 3/3 | 0 | 7740.04 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +4510.34 | seconds | 不适用 | 3/3 | 0 | 4510.34 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +5985.06 | seconds | 不适用 | 3/3 | 0 | 5985.06 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_cost_seconds | cost_free − cost_moderate | +1234.44 | seconds | 不适用 | 3/3 | 0 | 1234.44 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_cost_seconds | cost_free − cost_tight | +1879.97 | seconds | 不适用 | 3/3 | 0 | 1879.97 |
| expgym | tuning | all/all | cost_free | feedback_visible | cost_free − cost_moderate | +19.4815 | count | 不适用 | 27/27 | 0 | 19.4815 |
| expgym | tuning | all/all | cost_free | feedback_visible | cost_free − cost_tight | +25.8519 | count | 不适用 | 27/27 | 0 | 25.8519 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_visible | cost_free − cost_moderate | +21 | count | 不适用 | 9/9 | 0 | 21 |
| expgym | tuning | family/nasbench101 | cost_free | feedback_visible | cost_free − cost_tight | +26.5556 | count | 不适用 | 9/9 | 0 | 26.5556 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_visible | cost_free − cost_moderate | +19 | count | 不适用 | 9/9 | 0 | 19 |
| expgym | tuning | family/nasbench201 | cost_free | feedback_visible | cost_free − cost_tight | +26.3333 | count | 不适用 | 9/9 | 0 | 26.3333 |
| expgym | tuning | family/paramnet | cost_free | feedback_visible | cost_free − cost_moderate | +18.4444 | count | 不适用 | 9/9 | 0 | 18.4444 |
| expgym | tuning | family/paramnet | cost_free | feedback_visible | cost_free − cost_tight | +24.6667 | count | 不适用 | 9/9 | 0 | 24.6667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_visible | cost_free − cost_moderate | +24.6667 | count | 不适用 | 3/3 | 0 | 24.6667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | feedback_visible | cost_free − cost_tight | +28.3333 | count | 不适用 | 3/3 | 0 | 28.3333 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_visible | cost_free − cost_moderate | +21.6667 | count | 不适用 | 3/3 | 0 | 21.6667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | feedback_visible | cost_free − cost_tight | +26.3333 | count | 不适用 | 3/3 | 0 | 26.3333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_visible | cost_free − cost_moderate | +16.6667 | count | 不适用 | 3/3 | 0 | 16.6667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | feedback_visible | cost_free − cost_tight | +25 | count | 不适用 | 3/3 | 0 | 25 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_visible | cost_free − cost_moderate | +19.3333 | count | 不适用 | 3/3 | 0 | 19.3333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | feedback_visible | cost_free − cost_tight | +27 | count | 不适用 | 3/3 | 0 | 27 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_visible | cost_free − cost_moderate | +18.6667 | count | 不适用 | 3/3 | 0 | 18.6667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | feedback_visible | cost_free − cost_tight | +25.6667 | count | 不适用 | 3/3 | 0 | 25.6667 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_visible | cost_free − cost_moderate | +19 | count | 不适用 | 3/3 | 0 | 19 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | feedback_visible | cost_free − cost_tight | +26.3333 | count | 不适用 | 3/3 | 0 | 26.3333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_visible | cost_free − cost_moderate | +21 | count | 不适用 | 3/3 | 0 | 21 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | feedback_visible | cost_free − cost_tight | +22.6667 | count | 不适用 | 3/3 | 0 | 22.6667 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_visible | cost_free − cost_moderate | +15 | count | 不适用 | 3/3 | 0 | 15 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | feedback_visible | cost_free − cost_tight | +27.6667 | count | 不适用 | 3/3 | 0 | 27.6667 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_visible | cost_free − cost_moderate | +19.3333 | count | 不适用 | 3/3 | 0 | 19.3333 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | feedback_visible | cost_free − cost_tight | +23.6667 | count | 不适用 | 3/3 | 0 | 23.6667 |
| expgym | tuning | all/all | cost_free | input_tokens | cost_free − cost_moderate | +202815 | tokens | 不适用 | 27/27 | 0 | 202815 |
| expgym | tuning | all/all | cost_free | input_tokens | cost_free − cost_tight | +244031 | tokens | 不适用 | 27/27 | 0 | 244031 |
| expgym | tuning | family/nasbench101 | cost_free | input_tokens | cost_free − cost_moderate | +388072 | tokens | 不适用 | 9/9 | 0 | 388072 |
| expgym | tuning | family/nasbench101 | cost_free | input_tokens | cost_free − cost_tight | +458867 | tokens | 不适用 | 9/9 | 0 | 458867 |
| expgym | tuning | family/nasbench201 | cost_free | input_tokens | cost_free − cost_moderate | +118932 | tokens | 不适用 | 9/9 | 0 | 118932 |
| expgym | tuning | family/nasbench201 | cost_free | input_tokens | cost_free − cost_tight | +150578 | tokens | 不适用 | 9/9 | 0 | 150578 |
| expgym | tuning | family/paramnet | cost_free | input_tokens | cost_free − cost_moderate | +101442 | tokens | 不适用 | 9/9 | 0 | 101442 |
| expgym | tuning | family/paramnet | cost_free | input_tokens | cost_free − cost_tight | +122648 | tokens | 不适用 | 9/9 | 0 | 122648 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | input_tokens | cost_free − cost_moderate | +445936 | tokens | 不适用 | 3/3 | 0 | 445936 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | input_tokens | cost_free − cost_tight | +482853 | tokens | 不适用 | 3/3 | 0 | 482853 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | input_tokens | cost_free − cost_moderate | +346706 | tokens | 不适用 | 3/3 | 0 | 346706 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | input_tokens | cost_free − cost_tight | +384928 | tokens | 不适用 | 3/3 | 0 | 384928 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | input_tokens | cost_free − cost_moderate | +371575 | tokens | 不适用 | 3/3 | 0 | 371575 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | input_tokens | cost_free − cost_tight | +508821 | tokens | 不适用 | 3/3 | 0 | 508821 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | input_tokens | cost_free − cost_moderate | +139053 | tokens | 不适用 | 3/3 | 0 | 139053 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | input_tokens | cost_free − cost_tight | +166770 | tokens | 不适用 | 3/3 | 0 | 166770 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | input_tokens | cost_free − cost_moderate | +96567.7 | tokens | 不适用 | 3/3 | 0 | 96567.7 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | input_tokens | cost_free − cost_tight | +132322 | tokens | 不适用 | 3/3 | 0 | 132322 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | input_tokens | cost_free − cost_moderate | +121176 | tokens | 不适用 | 3/3 | 0 | 121176 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | input_tokens | cost_free − cost_tight | +152643 | tokens | 不适用 | 3/3 | 0 | 152643 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | input_tokens | cost_free − cost_moderate | +112038 | tokens | 不适用 | 3/3 | 0 | 112038 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | input_tokens | cost_free − cost_tight | +113830 | tokens | 不适用 | 3/3 | 0 | 113830 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | input_tokens | cost_free − cost_moderate | +83336 | tokens | 不适用 | 3/3 | 0 | 83336 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | input_tokens | cost_free − cost_tight | +133312 | tokens | 不适用 | 3/3 | 0 | 133312 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | input_tokens | cost_free − cost_moderate | +108951 | tokens | 不适用 | 3/3 | 0 | 108951 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | input_tokens | cost_free − cost_tight | +120801 | tokens | 不适用 | 3/3 | 0 | 120801 |
| expgym | tuning | all/all | cost_free | output_tokens | cost_free − cost_moderate | +6090.41 | tokens | 不适用 | 27/27 | 0 | 6090.41 |
| expgym | tuning | all/all | cost_free | output_tokens | cost_free − cost_tight | +7258.48 | tokens | 不适用 | 27/27 | 0 | 7258.48 |
| expgym | tuning | family/nasbench101 | cost_free | output_tokens | cost_free − cost_moderate | +9556.11 | tokens | 不适用 | 9/9 | 0 | 9556.11 |
| expgym | tuning | family/nasbench101 | cost_free | output_tokens | cost_free − cost_tight | +11349.2 | tokens | 不适用 | 9/9 | 0 | 11349.2 |
| expgym | tuning | family/nasbench201 | cost_free | output_tokens | cost_free − cost_moderate | +2176.56 | tokens | 不适用 | 9/9 | 0 | 2176.56 |
| expgym | tuning | family/nasbench201 | cost_free | output_tokens | cost_free − cost_tight | +2826.78 | tokens | 不适用 | 9/9 | 0 | 2826.78 |
| expgym | tuning | family/paramnet | cost_free | output_tokens | cost_free − cost_moderate | +6538.56 | tokens | 不适用 | 9/9 | 0 | 6538.56 |
| expgym | tuning | family/paramnet | cost_free | output_tokens | cost_free − cost_tight | +7599.44 | tokens | 不适用 | 9/9 | 0 | 7599.44 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | output_tokens | cost_free − cost_moderate | +13516 | tokens | 不适用 | 3/3 | 0 | 13516 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | output_tokens | cost_free − cost_tight | +16837.7 | tokens | 不适用 | 3/3 | 0 | 16837.7 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | output_tokens | cost_free − cost_moderate | +7597.33 | tokens | 不适用 | 3/3 | 0 | 7597.33 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | output_tokens | cost_free − cost_tight | +6843 | tokens | 不适用 | 3/3 | 0 | 6843 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | output_tokens | cost_free − cost_moderate | +7555 | tokens | 不适用 | 3/3 | 0 | 7555 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | output_tokens | cost_free − cost_tight | +10367 | tokens | 不适用 | 3/3 | 0 | 10367 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | output_tokens | cost_free − cost_moderate | +4355.33 | tokens | 不适用 | 3/3 | 0 | 4355.33 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | output_tokens | cost_free − cost_tight | +4929.33 | tokens | 不适用 | 3/3 | 0 | 4929.33 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | output_tokens | cost_free − cost_moderate | +366.333 | tokens | 不适用 | 3/3 | 0 | 366.333 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | output_tokens | cost_free − cost_tight | +4353.33 | tokens | 不适用 | 3/3 | 0 | 4353.33 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | output_tokens | cost_free − cost_moderate | +1808 | tokens | 不适用 | 3/3 | 0 | 1808 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | output_tokens | cost_free − cost_tight | -802.333 | tokens | 不适用 | 3/3 | 0 | -802.333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | output_tokens | cost_free − cost_moderate | +15241.7 | tokens | 不适用 | 3/3 | 0 | 15241.7 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | output_tokens | cost_free − cost_tight | +14671 | tokens | 不适用 | 3/3 | 0 | 14671 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | output_tokens | cost_free − cost_moderate | +1452.67 | tokens | 不适用 | 3/3 | 0 | 1452.67 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | output_tokens | cost_free − cost_tight | +4342.67 | tokens | 不适用 | 3/3 | 0 | 4342.67 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | output_tokens | cost_free − cost_moderate | +2921.33 | tokens | 不适用 | 3/3 | 0 | 2921.33 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | output_tokens | cost_free − cost_tight | +3784.67 | tokens | 不适用 | 3/3 | 0 | 3784.67 |
| expgym | tuning | all/all | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0150578 | fraction | -1.50578 | 27/27 | 0 | -0.0150578 |
| expgym | tuning | all/all | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.00997705 | fraction | -0.997705 | 27/27 | 0 | -0.00997705 |
| expgym | tuning | family/nasbench101 | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0440092 | fraction | -4.40092 | 9/9 | 0 | -0.0440092 |
| expgym | tuning | family/nasbench101 | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0273425 | fraction | -2.73425 | 9/9 | 0 | -0.0273425 |
| expgym | tuning | family/nasbench201 | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0135098 | fraction | -1.35098 | 9/9 | 0 | -0.0135098 |
| expgym | tuning | family/nasbench201 | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.00358423 | fraction | +0.358423 | 9/9 | 0 | 0.00358423 |
| expgym | tuning | family/paramnet | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0123457 | fraction | +1.23457 | 9/9 | 0 | 0.0123457 |
| expgym | tuning | family/paramnet | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.00617284 | fraction | -0.617284 | 9/9 | 0 | -0.00617284 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.153533 | fraction | -15.3533 | 3/3 | 0 | -0.153533 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.055914 | fraction | -5.5914 | 3/3 | 0 | -0.055914 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0107527 | fraction | +1.07527 | 3/3 | 0 | 0.0107527 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.0107527 | fraction | +1.07527 | 3/3 | 0 | 0.0107527 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.0107527 | fraction | +1.07527 | 3/3 | 0 | 0.0107527 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0368664 | fraction | -3.68664 | 3/3 | 0 | -0.0368664 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.025641 | fraction | -2.5641 | 3/3 | 0 | -0.025641 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | protocol_failure_rate | cost_free − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | protocol_failure_rate | cost_free − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | protocol_failure_rate | cost_free − cost_moderate | -0.0148883 | fraction | -1.48883 | 3/3 | 0 | -0.0148883 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.0107527 | fraction | +1.07527 | 3/3 | 0 | 0.0107527 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0.037037 | fraction | +3.7037 | 3/3 | 0 | 0.037037 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | +0.037037 | fraction | +3.7037 | 3/3 | 0 | 0.037037 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | protocol_failure_rate | cost_free − cost_moderate | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | protocol_failure_rate | cost_free − cost_tight | -0.0555556 | fraction | -5.55556 | 3/3 | 0 | -0.0555556 |
| expgym | tuning | all/all | cost_free | wall_time_seconds | cost_free − cost_moderate | +216.633 | seconds | 不适用 | 27/27 | 0 | 216.633 |
| expgym | tuning | all/all | cost_free | wall_time_seconds | cost_free − cost_tight | +276.349 | seconds | 不适用 | 27/27 | 0 | 276.349 |
| expgym | tuning | family/nasbench101 | cost_free | wall_time_seconds | cost_free − cost_moderate | +360.706 | seconds | 不适用 | 9/9 | 0 | 360.706 |
| expgym | tuning | family/nasbench101 | cost_free | wall_time_seconds | cost_free − cost_tight | +469.366 | seconds | 不适用 | 9/9 | 0 | 469.366 |
| expgym | tuning | family/nasbench201 | cost_free | wall_time_seconds | cost_free − cost_moderate | +89.2347 | seconds | 不适用 | 9/9 | 0 | 89.2347 |
| expgym | tuning | family/nasbench201 | cost_free | wall_time_seconds | cost_free − cost_tight | +125.86 | seconds | 不适用 | 9/9 | 0 | 125.86 |
| expgym | tuning | family/paramnet | cost_free | wall_time_seconds | cost_free − cost_moderate | +199.958 | seconds | 不适用 | 9/9 | 0 | 199.958 |
| expgym | tuning | family/paramnet | cost_free | wall_time_seconds | cost_free − cost_tight | +233.821 | seconds | 不适用 | 9/9 | 0 | 233.821 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | wall_time_seconds | cost_free − cost_moderate | +511.056 | seconds | 不适用 | 3/3 | 0 | 511.056 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_free | wall_time_seconds | cost_free − cost_tight | +639.449 | seconds | 不适用 | 3/3 | 0 | 639.449 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | wall_time_seconds | cost_free − cost_moderate | +289.822 | seconds | 不适用 | 3/3 | 0 | 289.822 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_free | wall_time_seconds | cost_free − cost_tight | +343.432 | seconds | 不适用 | 3/3 | 0 | 343.432 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | wall_time_seconds | cost_free − cost_moderate | +281.242 | seconds | 不适用 | 3/3 | 0 | 281.242 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_free | wall_time_seconds | cost_free − cost_tight | +425.218 | seconds | 不适用 | 3/3 | 0 | 425.218 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | wall_time_seconds | cost_free − cost_moderate | +168.857 | seconds | 不适用 | 3/3 | 0 | 168.857 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_free | wall_time_seconds | cost_free − cost_tight | +201.139 | seconds | 不适用 | 3/3 | 0 | 201.139 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | wall_time_seconds | cost_free − cost_moderate | +18.6741 | seconds | 不适用 | 3/3 | 0 | 18.6741 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_free | wall_time_seconds | cost_free − cost_tight | +187.67 | seconds | 不适用 | 3/3 | 0 | 187.67 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | wall_time_seconds | cost_free − cost_moderate | +80.1727 | seconds | 不适用 | 3/3 | 0 | 80.1727 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_free | wall_time_seconds | cost_free − cost_tight | -11.2283 | seconds | 不适用 | 3/3 | 0 | -11.2283 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | +475.145 | seconds | 不适用 | 3/3 | 0 | 475.145 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_free | wall_time_seconds | cost_free − cost_tight | +458.147 | seconds | 不适用 | 3/3 | 0 | 458.147 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | +41.1693 | seconds | 不适用 | 3/3 | 0 | 41.1693 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_free | wall_time_seconds | cost_free − cost_tight | +128.843 | seconds | 不适用 | 3/3 | 0 | 128.843 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | wall_time_seconds | cost_free − cost_moderate | +83.5586 | seconds | 不适用 | 3/3 | 0 | 83.5586 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_free | wall_time_seconds | cost_free − cost_tight | +114.471 | seconds | 不适用 | 3/3 | 0 | 114.471 |
| expgym | tuning | all/all | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.179464 | fraction | -17.9464 | 27/27 | 0 | -0.179464 |
| expgym | tuning | family/nasbench101 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.261258 | fraction | -26.1258 | 9/9 | 0 | -0.261258 |
| expgym | tuning | family/nasbench201 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.112362 | fraction | -11.2362 | 9/9 | 0 | -0.112362 |
| expgym | tuning | family/paramnet | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.164773 | fraction | -16.4773 | 9/9 | 0 | -0.164773 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.542477 | fraction | -54.2477 | 3/3 | 0 | -0.542477 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.249454 | fraction | -24.9454 | 3/3 | 0 | -0.249454 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | cost_moderate − cost_tight | +0.00815614 | fraction | +0.815614 | 3/3 | 0 | 0.00815614 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0691535 | fraction | -6.91535 | 3/3 | 0 | -0.0691535 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.167358 | fraction | -16.7358 | 3/3 | 0 | -0.167358 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.100575 | fraction | -10.0575 | 3/3 | 0 | -0.100575 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.336142 | fraction | -33.6142 | 3/3 | 0 | -0.336142 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.132784 | fraction | -13.2784 | 3/3 | 0 | -0.132784 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | budget_utilization | cost_moderate − cost_tight | -0.0253924 | fraction | -2.53924 | 3/3 | 0 | -0.0253924 |
| expgym | tuning | all/all | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.037037 | count | 不适用 | 27/27 | 0 | 0.037037 |
| expgym | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.111111 | count | 不适用 | 9/9 | 0 | 0.111111 |
| expgym | tuning | family/nasbench201 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | family/paramnet | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 9/9 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | duplicate_action_attempts | cost_moderate − cost_tight | +0 | count | 不适用 | 3/3 | 0 | 0 |
| expgym | tuning | all/all | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +5.85185 | count | 不适用 | 27/27 | 0 | 5.85185 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +5 | count | 不适用 | 9/9 | 0 | 5 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.88889 | count | 不适用 | 9/9 | 0 | 6.88889 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +5.66667 | count | 不适用 | 9/9 | 0 | 5.66667 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +4 | count | 不适用 | 3/3 | 0 | 4 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +7.66667 | count | 不适用 | 3/3 | 0 | 7.66667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.33333 | count | 不适用 | 3/3 | 0 | 6.33333 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +6.66667 | count | 不适用 | 3/3 | 0 | 6.66667 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +1 | count | 不适用 | 3/3 | 0 | 1 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +12 | count | 不适用 | 3/3 | 0 | 12 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_attempts | cost_moderate − cost_tight | +4 | count | 不适用 | 3/3 | 0 | 4 |
| expgym | tuning | all/all | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +74190.6 | seconds | 不适用 | 27/27 | 0 | 74190.6 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +51659.7 | seconds | 不适用 | 9/9 | 0 | 51659.7 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +170154 | seconds | 不适用 | 9/9 | 0 | 170154 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +758.431 | seconds | 不适用 | 9/9 | 0 | 758.431 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +20433.8 | seconds | 不适用 | 3/3 | 0 | 20433.8 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +59074.1 | seconds | 不适用 | 3/3 | 0 | 59074.1 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +75471.3 | seconds | 不适用 | 3/3 | 0 | 75471.3 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +73388.5 | seconds | 不适用 | 3/3 | 0 | 73388.5 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +107105 | seconds | 不适用 | 3/3 | 0 | 107105 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +329967 | seconds | 不适用 | 3/3 | 0 | 329967 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +155.057 | seconds | 不适用 | 3/3 | 0 | 155.057 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +1474.71 | seconds | 不适用 | 3/3 | 0 | 1474.71 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_cost_seconds | cost_moderate − cost_tight | +645.523 | seconds | 不适用 | 3/3 | 0 | 645.523 |
| expgym | tuning | all/all | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.37037 | count | 不适用 | 27/27 | 0 | 6.37037 |
| expgym | tuning | family/nasbench101 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +5.55556 | count | 不适用 | 9/9 | 0 | 5.55556 |
| expgym | tuning | family/nasbench201 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.33333 | count | 不适用 | 9/9 | 0 | 7.33333 |
| expgym | tuning | family/paramnet | cost_moderate | feedback_visible | cost_moderate − cost_tight | +6.22222 | count | 不适用 | 9/9 | 0 | 6.22222 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | cost_moderate − cost_tight | +3.66667 | count | 不适用 | 3/3 | 0 | 3.66667 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | cost_moderate − cost_tight | +4.66667 | count | 不适用 | 3/3 | 0 | 4.66667 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | cost_moderate − cost_tight | +8.33333 | count | 不适用 | 3/3 | 0 | 8.33333 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.66667 | count | 不适用 | 3/3 | 0 | 7.66667 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7 | count | 不适用 | 3/3 | 0 | 7 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | feedback_visible | cost_moderate − cost_tight | +7.33333 | count | 不适用 | 3/3 | 0 | 7.33333 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +1.66667 | count | 不适用 | 3/3 | 0 | 1.66667 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +12.6667 | count | 不适用 | 3/3 | 0 | 12.6667 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | feedback_visible | cost_moderate − cost_tight | +4.33333 | count | 不适用 | 3/3 | 0 | 4.33333 |
| expgym | tuning | all/all | cost_moderate | input_tokens | cost_moderate − cost_tight | +41215.7 | tokens | 不适用 | 27/27 | 0 | 41215.7 |
| expgym | tuning | family/nasbench101 | cost_moderate | input_tokens | cost_moderate − cost_tight | +70795.1 | tokens | 不适用 | 9/9 | 0 | 70795.1 |
| expgym | tuning | family/nasbench201 | cost_moderate | input_tokens | cost_moderate − cost_tight | +31645.9 | tokens | 不适用 | 9/9 | 0 | 31645.9 |
| expgym | tuning | family/paramnet | cost_moderate | input_tokens | cost_moderate − cost_tight | +21206 | tokens | 不适用 | 9/9 | 0 | 21206 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | cost_moderate − cost_tight | +36917.3 | tokens | 不适用 | 3/3 | 0 | 36917.3 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | cost_moderate − cost_tight | +38222 | tokens | 不适用 | 3/3 | 0 | 38222 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | cost_moderate − cost_tight | +137246 | tokens | 不适用 | 3/3 | 0 | 137246 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | input_tokens | cost_moderate − cost_tight | +27716.7 | tokens | 不适用 | 3/3 | 0 | 27716.7 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | input_tokens | cost_moderate − cost_tight | +35754.3 | tokens | 不适用 | 3/3 | 0 | 35754.3 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | input_tokens | cost_moderate − cost_tight | +31466.7 | tokens | 不适用 | 3/3 | 0 | 31466.7 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +1792.33 | tokens | 不适用 | 3/3 | 0 | 1792.33 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +49975.7 | tokens | 不适用 | 3/3 | 0 | 49975.7 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | input_tokens | cost_moderate − cost_tight | +11850 | tokens | 不适用 | 3/3 | 0 | 11850 |
| expgym | tuning | all/all | cost_moderate | output_tokens | cost_moderate − cost_tight | +1168.07 | tokens | 不适用 | 27/27 | 0 | 1168.07 |
| expgym | tuning | family/nasbench101 | cost_moderate | output_tokens | cost_moderate − cost_tight | +1793.11 | tokens | 不适用 | 9/9 | 0 | 1793.11 |
| expgym | tuning | family/nasbench201 | cost_moderate | output_tokens | cost_moderate − cost_tight | +650.222 | tokens | 不适用 | 9/9 | 0 | 650.222 |
| expgym | tuning | family/paramnet | cost_moderate | output_tokens | cost_moderate − cost_tight | +1060.89 | tokens | 不适用 | 9/9 | 0 | 1060.89 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | cost_moderate − cost_tight | +3321.67 | tokens | 不适用 | 3/3 | 0 | 3321.67 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | cost_moderate − cost_tight | -754.333 | tokens | 不适用 | 3/3 | 0 | -754.333 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | cost_moderate − cost_tight | +2812 | tokens | 不适用 | 3/3 | 0 | 2812 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | output_tokens | cost_moderate − cost_tight | +574 | tokens | 不适用 | 3/3 | 0 | 574 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | output_tokens | cost_moderate − cost_tight | +3987 | tokens | 不适用 | 3/3 | 0 | 3987 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | output_tokens | cost_moderate − cost_tight | -2610.33 | tokens | 不适用 | 3/3 | 0 | -2610.33 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | -570.667 | tokens | 不适用 | 3/3 | 0 | -570.667 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | +2890 | tokens | 不适用 | 3/3 | 0 | 2890 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | output_tokens | cost_moderate − cost_tight | +863.333 | tokens | 不适用 | 3/3 | 0 | 863.333 |
| expgym | tuning | all/all | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.00508072 | fraction | +0.508072 | 27/27 | 0 | 0.00508072 |
| expgym | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.0166667 | fraction | +1.66667 | 9/9 | 0 | 0.0166667 |
| expgym | tuning | family/nasbench201 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.017094 | fraction | +1.7094 | 9/9 | 0 | 0.017094 |
| expgym | tuning | family/paramnet | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0185185 | fraction | -1.85185 | 9/9 | 0 | -0.0185185 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.097619 | fraction | +9.7619 | 3/3 | 0 | 0.097619 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.047619 | fraction | -4.7619 | 3/3 | 0 | -0.047619 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.025641 | fraction | +2.5641 | 3/3 | 0 | 0.025641 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0.025641 | fraction | +2.5641 | 3/3 | 0 | 0.025641 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | +0 | fraction | +0 | 3/3 | 0 | 0 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | protocol_failure_rate | cost_moderate − cost_tight | -0.0555556 | fraction | -5.55556 | 3/3 | 0 | -0.0555556 |
| expgym | tuning | all/all | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +59.7161 | seconds | 不适用 | 27/27 | 0 | 59.7161 |
| expgym | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +108.66 | seconds | 不适用 | 9/9 | 0 | 108.66 |
| expgym | tuning | family/nasbench201 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +36.6257 | seconds | 不适用 | 9/9 | 0 | 36.6257 |
| expgym | tuning | family/paramnet | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +33.8629 | seconds | 不适用 | 9/9 | 0 | 33.8629 |
| expgym | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +128.393 | seconds | 不适用 | 3/3 | 0 | 128.393 |
| expgym | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +53.6106 | seconds | 不适用 | 3/3 | 0 | 53.6106 |
| expgym | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +143.976 | seconds | 不适用 | 3/3 | 0 | 143.976 |
| expgym | tuning | task/hpobench:nasbench201:cifar10-valid | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +32.2821 | seconds | 不适用 | 3/3 | 0 | 32.2821 |
| expgym | tuning | task/hpobench:nasbench201:cifar100 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +168.996 | seconds | 不适用 | 3/3 | 0 | 168.996 |
| expgym | tuning | task/hpobench:nasbench201:imagenet16-120 | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | -91.401 | seconds | 不适用 | 3/3 | 0 | -91.401 |
| expgym | tuning | task/hpobench:paramnet:adult:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | -16.9976 | seconds | 不适用 | 3/3 | 0 | -16.9976 |
| expgym | tuning | task/hpobench:paramnet:higgs:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +87.6738 | seconds | 不适用 | 3/3 | 0 | 87.6738 |
| expgym | tuning | task/hpobench:paramnet:letter:steps | cost_moderate | wall_time_seconds | cost_moderate − cost_tight | +30.9125 | seconds | 不适用 | 3/3 | 0 | 30.9125 |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | poolact − cached | -0.0453656 | fraction | -4.53656 | 13/13 | 0 | -0.0453656 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | poolact − cached | -0.0453656 | fraction | -4.53656 | 13/13 | 0 | -0.0453656 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | -13.9231 | count | 不适用 | 13/13 | 0 | -13.9231 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | poolact − cached | -13.9231 | count | 不适用 | 13/13 | 0 | -13.9231 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | poolact − cached | -6.61538 | count | 不适用 | 13/13 | 0 | -6.61538 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | poolact − cached | -6.61538 | count | 不适用 | 13/13 | 0 | -6.61538 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -544.387 | seconds | 不适用 | 13/13 | 0 | -544.387 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | poolact − cached | -544.387 | seconds | 不适用 | 13/13 | 0 | -544.387 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | poolact − cached | +175167 | tokens | 不适用 | 13/13 | 0 | 175167 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | poolact − cached | +175167 | tokens | 不适用 | 13/13 | 0 | 175167 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | poolact − cached | +15074.8 | tokens | 不适用 | 13/13 | 0 | 15074.8 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | poolact − cached | +15074.8 | tokens | 不适用 | 13/13 | 0 | 15074.8 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | poolact − cached | +0.00815081 | fraction | +0.815081 | 13/13 | 0 | 0.00815081 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | poolact − cached | +0.00815081 | fraction | +0.815081 | 13/13 | 0 | 0.00815081 |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | cached − naive | +0.000982985 | fraction | +0.0982985 | 13/13 | 0 | 0.000982985 |
| poolact | evidence_audit | all/all | cost_moderate | budget_utilization | poolact − naive | -0.0443826 | fraction | -4.43826 | 13/13 | 0 | -0.0443826 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | cached − naive | +0.000982985 | fraction | +0.0982985 | 13/13 | 0 | 0.000982985 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | budget_utilization | poolact − naive | -0.0443826 | fraction | -4.43826 | 13/13 | 0 | -0.0443826 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | cached − naive | +3.61538 | count | 不适用 | 13/13 | 0 | 3.61538 |
| poolact | evidence_audit | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | -10.3077 | count | 不适用 | 13/13 | 0 | -10.3077 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | cached − naive | +3.61538 | count | 不适用 | 13/13 | 0 | 3.61538 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | duplicate_action_attempts | poolact − naive | -10.3077 | count | 不适用 | 13/13 | 0 | -10.3077 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | cached − naive | +4.92308 | count | 不适用 | 13/13 | 0 | 4.92308 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_attempts | poolact − naive | -1.69231 | count | 不适用 | 13/13 | 0 | -1.69231 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | cached − naive | +4.92308 | count | 不适用 | 13/13 | 0 | 4.92308 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_attempts | poolact − naive | -1.69231 | count | 不适用 | 13/13 | 0 | -1.69231 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | cached − naive | +11.7958 | seconds | 不适用 | 13/13 | 0 | 11.7958 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -532.591 | seconds | 不适用 | 13/13 | 0 | -532.591 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | cached − naive | +11.7958 | seconds | 不适用 | 13/13 | 0 | 11.7958 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_cost_seconds | poolact − naive | -532.591 | seconds | 不适用 | 13/13 | 0 | -532.591 |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | cached − naive | +64689.5 | tokens | 不适用 | 13/13 | 0 | 64689.5 |
| poolact | evidence_audit | all/all | cost_moderate | input_tokens | poolact − naive | +239857 | tokens | 不适用 | 13/13 | 0 | 239857 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | cached − naive | +64689.5 | tokens | 不适用 | 13/13 | 0 | 64689.5 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | input_tokens | poolact − naive | +239857 | tokens | 不适用 | 13/13 | 0 | 239857 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | cached − naive | +1244.38 | tokens | 不适用 | 13/13 | 0 | 1244.38 |
| poolact | evidence_audit | all/all | cost_moderate | output_tokens | poolact − naive | +16319.2 | tokens | 不适用 | 13/13 | 0 | 16319.2 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | cached − naive | +1244.38 | tokens | 不适用 | 13/13 | 0 | 1244.38 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | output_tokens | poolact − naive | +16319.2 | tokens | 不适用 | 13/13 | 0 | 16319.2 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | cached − naive | -0.0040029 | fraction | -0.40029 | 13/13 | 0 | -0.0040029 |
| poolact | evidence_audit | all/all | cost_moderate | protocol_failure_rate | poolact − naive | +0.00414791 | fraction | +0.414791 | 13/13 | 0 | 0.00414791 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | cached − naive | -0.0040029 | fraction | -0.40029 | 13/13 | 0 | -0.0040029 |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | protocol_failure_rate | poolact − naive | +0.00414791 | fraction | +0.414791 | 13/13 | 0 | 0.00414791 |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | poolact − cached | +0.02304 | fraction | +2.304 | 13/13 | 0 | 0.02304 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | poolact − cached | +0.02304 | fraction | +2.304 | 13/13 | 0 | 0.02304 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | poolact − cached | -2.69231 | count | 不适用 | 13/13 | 0 | -2.69231 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | poolact − cached | -2.69231 | count | 不适用 | 13/13 | 0 | -2.69231 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | poolact − cached | +0.153846 | count | 不适用 | 13/13 | 0 | 0.153846 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | poolact − cached | +0.153846 | count | 不适用 | 13/13 | 0 | 0.153846 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | poolact − cached | +82.9442 | seconds | 不适用 | 13/13 | 0 | 82.9442 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | poolact − cached | +82.9442 | seconds | 不适用 | 13/13 | 0 | 82.9442 |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | poolact − cached | +6235.15 | tokens | 不适用 | 13/13 | 0 | 6235.15 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | poolact − cached | +6235.15 | tokens | 不适用 | 13/13 | 0 | 6235.15 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | poolact − cached | -2089.08 | tokens | 不适用 | 13/13 | 0 | -2089.08 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | poolact − cached | -2089.08 | tokens | 不适用 | 13/13 | 0 | -2089.08 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | poolact − cached | +0.000282805 | fraction | +0.0282805 | 13/13 | 0 | 0.000282805 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | poolact − cached | +0.000282805 | fraction | +0.0282805 | 13/13 | 0 | 0.000282805 |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | cached − naive | -0.0120823 | fraction | -1.20823 | 13/13 | 0 | -0.0120823 |
| poolact | evidence_audit | all/all | cost_tight | budget_utilization | poolact − naive | +0.0109578 | fraction | +1.09578 | 13/13 | 0 | 0.0109578 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | cached − naive | -0.0120823 | fraction | -1.20823 | 13/13 | 0 | -0.0120823 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | budget_utilization | poolact − naive | +0.0109578 | fraction | +1.09578 | 13/13 | 0 | 0.0109578 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | cached − naive | -0.384615 | count | 不适用 | 13/13 | 0 | -0.384615 |
| poolact | evidence_audit | all/all | cost_tight | duplicate_action_attempts | poolact − naive | -3.07692 | count | 不适用 | 13/13 | 0 | -3.07692 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | cached − naive | -0.384615 | count | 不适用 | 13/13 | 0 | -0.384615 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | duplicate_action_attempts | poolact − naive | -3.07692 | count | 不适用 | 13/13 | 0 | -3.07692 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | cached − naive | +0 | count | 不适用 | 13/13 | 0 | 0 |
| poolact | evidence_audit | all/all | cost_tight | feedback_attempts | poolact − naive | +0.153846 | count | 不适用 | 13/13 | 0 | 0.153846 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | cached − naive | +0 | count | 不适用 | 13/13 | 0 | 0 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_attempts | poolact − naive | +0.153846 | count | 不适用 | 13/13 | 0 | 0.153846 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | cached − naive | -43.4962 | seconds | 不适用 | 13/13 | 0 | -43.4962 |
| poolact | evidence_audit | all/all | cost_tight | feedback_cost_seconds | poolact − naive | +39.4479 | seconds | 不适用 | 13/13 | 0 | 39.4479 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | cached − naive | -43.4962 | seconds | 不适用 | 13/13 | 0 | -43.4962 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_cost_seconds | poolact − naive | +39.4479 | seconds | 不适用 | 13/13 | 0 | 39.4479 |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | cached − naive | +5971.85 | tokens | 不适用 | 13/13 | 0 | 5971.85 |
| poolact | evidence_audit | all/all | cost_tight | input_tokens | poolact − naive | +12207 | tokens | 不适用 | 13/13 | 0 | 12207 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | cached − naive | +5971.85 | tokens | 不适用 | 13/13 | 0 | 5971.85 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | input_tokens | poolact − naive | +12207 | tokens | 不适用 | 13/13 | 0 | 12207 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | cached − naive | +3594.62 | tokens | 不适用 | 13/13 | 0 | 3594.62 |
| poolact | evidence_audit | all/all | cost_tight | output_tokens | poolact − naive | +1505.54 | tokens | 不适用 | 13/13 | 0 | 1505.54 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | cached − naive | +3594.62 | tokens | 不适用 | 13/13 | 0 | 3594.62 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | output_tokens | poolact − naive | +1505.54 | tokens | 不适用 | 13/13 | 0 | 1505.54 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | cached − naive | +0.00857347 | fraction | +0.857347 | 13/13 | 0 | 0.00857347 |
| poolact | evidence_audit | all/all | cost_tight | protocol_failure_rate | poolact − naive | +0.00885628 | fraction | +0.885628 | 13/13 | 0 | 0.00885628 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | cached − naive | +0.00857347 | fraction | +0.857347 | 13/13 | 0 | 0.00857347 |
| poolact | evidence_audit | family/evidence_audit | cost_tight | protocol_failure_rate | poolact − naive | +0.00885628 | fraction | +0.885628 | 13/13 | 0 | 0.00885628 |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | all/all | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | evidence_audit | family/evidence_audit | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/13 | 13 | unknown |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | poolact − cached | -0.103251 | fraction | -10.3251 | 39/39 | 0 | -0.103251 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | poolact − cached | -0.103251 | fraction | -10.3251 | 39/39 | 0 | -0.103251 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | -4.48718 | count | 不适用 | 39/39 | 0 | -4.48718 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | poolact − cached | -4.48718 | count | 不适用 | 39/39 | 0 | -4.48718 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | poolact − cached | -2.97436 | count | 不适用 | 39/39 | 0 | -2.97436 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | poolact − cached | -2.97436 | count | 不适用 | 39/39 | 0 | -2.97436 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -1239.01 | seconds | 不适用 | 39/39 | 0 | -1239.01 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | poolact − cached | -1239.01 | seconds | 不适用 | 39/39 | 0 | -1239.01 |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | poolact − cached | +297353 | tokens | 不适用 | 39/39 | 0 | 297353 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | poolact − cached | +297353 | tokens | 不适用 | 39/39 | 0 | 297353 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | poolact − cached | +11476.9 | tokens | 不适用 | 39/39 | 0 | 11476.9 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | poolact − cached | +11476.9 | tokens | 不适用 | 39/39 | 0 | 11476.9 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | poolact − cached | -0.0339934 | fraction | -3.39934 | 39/39 | 0 | -0.0339934 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | poolact − cached | -0.0339934 | fraction | -3.39934 | 39/39 | 0 | -0.0339934 |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | cached − naive | -0.0606709 | fraction | -6.06709 | 39/39 | 0 | -0.0606709 |
| poolact | restricted_search | all/all | cost_moderate | budget_utilization | poolact − naive | -0.163922 | fraction | -16.3922 | 39/39 | 0 | -0.163922 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | cached − naive | -0.0606709 | fraction | -6.06709 | 39/39 | 0 | -0.0606709 |
| poolact | restricted_search | family/whois | cost_moderate | budget_utilization | poolact − naive | -0.163922 | fraction | -16.3922 | 39/39 | 0 | -0.163922 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | cached − naive | +1.20513 | count | 不适用 | 39/39 | 0 | 1.20513 |
| poolact | restricted_search | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | -3.28205 | count | 不适用 | 39/39 | 0 | -3.28205 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | cached − naive | +1.20513 | count | 不适用 | 39/39 | 0 | 1.20513 |
| poolact | restricted_search | family/whois | cost_moderate | duplicate_action_attempts | poolact − naive | -3.28205 | count | 不适用 | 39/39 | 0 | -3.28205 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | cached − naive | +2.28205 | count | 不适用 | 39/39 | 0 | 2.28205 |
| poolact | restricted_search | all/all | cost_moderate | feedback_attempts | poolact − naive | -0.692308 | count | 不适用 | 39/39 | 0 | -0.692308 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | cached − naive | +2.28205 | count | 不适用 | 39/39 | 0 | 2.28205 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_attempts | poolact − naive | -0.692308 | count | 不适用 | 39/39 | 0 | -0.692308 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | cached − naive | -728.051 | seconds | 不适用 | 39/39 | 0 | -728.051 |
| poolact | restricted_search | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -1967.06 | seconds | 不适用 | 39/39 | 0 | -1967.06 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | cached − naive | -728.051 | seconds | 不适用 | 39/39 | 0 | -728.051 |
| poolact | restricted_search | family/whois | cost_moderate | feedback_cost_seconds | poolact − naive | -1967.06 | seconds | 不适用 | 39/39 | 0 | -1967.06 |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | cached − naive | +19746.3 | tokens | 不适用 | 39/39 | 0 | 19746.3 |
| poolact | restricted_search | all/all | cost_moderate | input_tokens | poolact − naive | +317100 | tokens | 不适用 | 39/39 | 0 | 317100 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | cached − naive | +19746.3 | tokens | 不适用 | 39/39 | 0 | 19746.3 |
| poolact | restricted_search | family/whois | cost_moderate | input_tokens | poolact − naive | +317100 | tokens | 不适用 | 39/39 | 0 | 317100 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | cached − naive | -1459.28 | tokens | 不适用 | 39/39 | 0 | -1459.28 |
| poolact | restricted_search | all/all | cost_moderate | output_tokens | poolact − naive | +10017.6 | tokens | 不适用 | 39/39 | 0 | 10017.6 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | cached − naive | -1459.28 | tokens | 不适用 | 39/39 | 0 | -1459.28 |
| poolact | restricted_search | family/whois | cost_moderate | output_tokens | poolact − naive | +10017.6 | tokens | 不适用 | 39/39 | 0 | 10017.6 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | cached − naive | -0.00504959 | fraction | -0.504959 | 39/39 | 0 | -0.00504959 |
| poolact | restricted_search | all/all | cost_moderate | protocol_failure_rate | poolact − naive | -0.039043 | fraction | -3.9043 | 39/39 | 0 | -0.039043 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | cached − naive | -0.00504959 | fraction | -0.504959 | 39/39 | 0 | -0.00504959 |
| poolact | restricted_search | family/whois | cost_moderate | protocol_failure_rate | poolact − naive | -0.039043 | fraction | -3.9043 | 39/39 | 0 | -0.039043 |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_moderate | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | poolact − cached | +0.00278719 | fraction | +0.278719 | 39/39 | 0 | 0.00278719 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | poolact − cached | +0.00278719 | fraction | +0.278719 | 39/39 | 0 | 0.00278719 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | poolact − cached | -4.74359 | count | 不适用 | 39/39 | 0 | -4.74359 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | poolact − cached | -4.74359 | count | 不适用 | 39/39 | 0 | -4.74359 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | poolact − cached | +0.128205 | count | 不适用 | 39/39 | 0 | 0.128205 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | poolact − cached | +0.128205 | count | 不适用 | 39/39 | 0 | 0.128205 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | poolact − cached | +10.0339 | seconds | 不适用 | 39/39 | 0 | 10.0339 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | poolact − cached | +10.0339 | seconds | 不适用 | 39/39 | 0 | 10.0339 |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | input_tokens | poolact − cached | +25025.6 | tokens | 不适用 | 39/39 | 0 | 25025.6 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | poolact − cached | +25025.6 | tokens | 不适用 | 39/39 | 0 | 25025.6 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | poolact − cached | +7241.74 | tokens | 不适用 | 39/39 | 0 | 7241.74 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | poolact − cached | +7241.74 | tokens | 不适用 | 39/39 | 0 | 7241.74 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | poolact − cached | -0.0508427 | fraction | -5.08427 | 39/39 | 0 | -0.0508427 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | poolact − cached | -0.0508427 | fraction | -5.08427 | 39/39 | 0 | -0.0508427 |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | cached − naive | -0.0169841 | fraction | -1.69841 | 39/39 | 0 | -0.0169841 |
| poolact | restricted_search | all/all | cost_tight | budget_utilization | poolact − naive | -0.0141969 | fraction | -1.41969 | 39/39 | 0 | -0.0141969 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | cached − naive | -0.0169841 | fraction | -1.69841 | 39/39 | 0 | -0.0169841 |
| poolact | restricted_search | family/whois | cost_tight | budget_utilization | poolact − naive | -0.0141969 | fraction | -1.41969 | 39/39 | 0 | -0.0141969 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | cached − naive | -0.282051 | count | 不适用 | 39/39 | 0 | -0.282051 |
| poolact | restricted_search | all/all | cost_tight | duplicate_action_attempts | poolact − naive | -5.02564 | count | 不适用 | 39/39 | 0 | -5.02564 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | cached − naive | -0.282051 | count | 不适用 | 39/39 | 0 | -0.282051 |
| poolact | restricted_search | family/whois | cost_tight | duplicate_action_attempts | poolact − naive | -5.02564 | count | 不适用 | 39/39 | 0 | -5.02564 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | cached − naive | -0.102564 | count | 不适用 | 39/39 | 0 | -0.102564 |
| poolact | restricted_search | all/all | cost_tight | feedback_attempts | poolact − naive | +0.025641 | count | 不适用 | 39/39 | 0 | 0.025641 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | cached − naive | -0.102564 | count | 不适用 | 39/39 | 0 | -0.102564 |
| poolact | restricted_search | family/whois | cost_tight | feedback_attempts | poolact − naive | +0.025641 | count | 不适用 | 39/39 | 0 | 0.025641 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | cached − naive | -61.1427 | seconds | 不适用 | 39/39 | 0 | -61.1427 |
| poolact | restricted_search | all/all | cost_tight | feedback_cost_seconds | poolact − naive | -51.1089 | seconds | 不适用 | 39/39 | 0 | -51.1089 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | cached − naive | -61.1427 | seconds | 不适用 | 39/39 | 0 | -61.1427 |
| poolact | restricted_search | family/whois | cost_tight | feedback_cost_seconds | poolact − naive | -51.1089 | seconds | 不适用 | 39/39 | 0 | -51.1089 |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | cached − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | input_tokens | cached − naive | +1363.1 | tokens | 不适用 | 39/39 | 0 | 1363.1 |
| poolact | restricted_search | all/all | cost_tight | input_tokens | poolact − naive | +26388.7 | tokens | 不适用 | 39/39 | 0 | 26388.7 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | cached − naive | +1363.1 | tokens | 不适用 | 39/39 | 0 | 1363.1 |
| poolact | restricted_search | family/whois | cost_tight | input_tokens | poolact − naive | +26388.7 | tokens | 不适用 | 39/39 | 0 | 26388.7 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | cached − naive | -293.436 | tokens | 不适用 | 39/39 | 0 | -293.436 |
| poolact | restricted_search | all/all | cost_tight | output_tokens | poolact − naive | +6948.31 | tokens | 不适用 | 39/39 | 0 | 6948.31 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | cached − naive | -293.436 | tokens | 不适用 | 39/39 | 0 | -293.436 |
| poolact | restricted_search | family/whois | cost_tight | output_tokens | poolact − naive | +6948.31 | tokens | 不适用 | 39/39 | 0 | 6948.31 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | cached − naive | +0.0145893 | fraction | +1.45893 | 39/39 | 0 | 0.0145893 |
| poolact | restricted_search | all/all | cost_tight | protocol_failure_rate | poolact − naive | -0.0362533 | fraction | -3.62533 | 39/39 | 0 | -0.0362533 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | cached − naive | +0.0145893 | fraction | +1.45893 | 39/39 | 0 | 0.0145893 |
| poolact | restricted_search | family/whois | cost_tight | protocol_failure_rate | poolact − naive | -0.0362533 | fraction | -3.62533 | 39/39 | 0 | -0.0362533 |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | all/all | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | cached − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | restricted_search | family/whois | cost_tight | wall_time_seconds | poolact − naive | unknown | seconds | 不适用 | 0/39 | 39 | unknown |
| poolact | tuning | all/all | cost_moderate | budget_utilization | poolact − cached | -0.163471 | fraction | -16.3471 | 9/9 | 0 | -0.163471 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | poolact − cached | -0.163471 | fraction | -16.3471 | 9/9 | 0 | -0.163471 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | poolact − cached | -0.131115 | fraction | -13.1115 | 3/3 | 0 | -0.131115 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | poolact − cached | -0.0894255 | fraction | -8.94255 | 3/3 | 0 | -0.0894255 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | poolact − cached | -0.269872 | fraction | -26.9872 | 3/3 | 0 | -0.269872 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | poolact − cached | +1.55556 | count | 不适用 | 9/9 | 0 | 1.55556 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | poolact − cached | +1.55556 | count | 不适用 | 9/9 | 0 | 1.55556 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | poolact − cached | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | poolact − cached | +3.33333 | count | 不适用 | 3/3 | 0 | 3.33333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | poolact − cached | +1 | count | 不适用 | 3/3 | 0 | 1 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | poolact − cached | -7 | count | 不适用 | 9/9 | 0 | -7 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | poolact − cached | -7 | count | 不适用 | 9/9 | 0 | -7 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | poolact − cached | -7.33333 | count | 不适用 | 3/3 | 0 | -7.33333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | poolact − cached | -2.33333 | count | 不适用 | 3/3 | 0 | -2.33333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | poolact − cached | -11.3333 | count | 不适用 | 3/3 | 0 | -11.3333 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | poolact − cached | -61242.2 | seconds | 不适用 | 9/9 | 0 | -61242.2 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | poolact − cached | -61242.2 | seconds | 不适用 | 9/9 | 0 | -61242.2 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | poolact − cached | -25930 | seconds | 不适用 | 3/3 | 0 | -25930 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | poolact − cached | -36852.5 | seconds | 不适用 | 3/3 | 0 | -36852.5 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | poolact − cached | -120944 | seconds | 不适用 | 3/3 | 0 | -120944 |
| poolact | tuning | all/all | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | input_tokens | poolact − cached | +1.41809e+06 | tokens | 不适用 | 9/9 | 0 | 1.41809e+06 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | poolact − cached | +1.41809e+06 | tokens | 不适用 | 9/9 | 0 | 1.41809e+06 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | poolact − cached | +271828 | tokens | 不适用 | 3/3 | 0 | 271828 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | poolact − cached | +1.26449e+06 | tokens | 不适用 | 3/3 | 0 | 1.26449e+06 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | poolact − cached | +2.71797e+06 | tokens | 不适用 | 3/3 | 0 | 2.71797e+06 |
| poolact | tuning | all/all | cost_moderate | output_tokens | poolact − cached | +59039 | tokens | 不适用 | 9/9 | 0 | 59039 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | poolact − cached | +59039 | tokens | 不适用 | 9/9 | 0 | 59039 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | poolact − cached | +36140.3 | tokens | 不适用 | 3/3 | 0 | 36140.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | poolact − cached | +47334 | tokens | 不适用 | 3/3 | 0 | 47334 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | poolact − cached | +93642.7 | tokens | 不适用 | 3/3 | 0 | 93642.7 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | poolact − cached | -0.0126268 | fraction | -1.26268 | 9/9 | 0 | -0.0126268 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | poolact − cached | -0.0126268 | fraction | -1.26268 | 9/9 | 0 | -0.0126268 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | poolact − cached | -0.0190226 | fraction | -1.90226 | 3/3 | 0 | -0.0190226 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | poolact − cached | -0.00455771 | fraction | -0.455771 | 3/3 | 0 | -0.00455771 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | poolact − cached | -0.0143 | fraction | -1.43 | 3/3 | 0 | -0.0143 |
| poolact | tuning | all/all | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | budget_utilization | cached − naive | +0.0288152 | fraction | +2.88152 | 9/9 | 0 | 0.0288152 |
| poolact | tuning | all/all | cost_moderate | budget_utilization | poolact − naive | -0.134655 | fraction | -13.4655 | 9/9 | 0 | -0.134655 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | cached − naive | +0.0288152 | fraction | +2.88152 | 9/9 | 0 | 0.0288152 |
| poolact | tuning | family/nasbench101 | cost_moderate | budget_utilization | poolact − naive | -0.134655 | fraction | -13.4655 | 9/9 | 0 | -0.134655 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | cached − naive | +0.0498045 | fraction | +4.98045 | 3/3 | 0 | 0.0498045 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | budget_utilization | poolact − naive | -0.0813102 | fraction | -8.13102 | 3/3 | 0 | -0.0813102 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | cached − naive | +0.0196212 | fraction | +1.96212 | 3/3 | 0 | 0.0196212 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | budget_utilization | poolact − naive | -0.0698042 | fraction | -6.98042 | 3/3 | 0 | -0.0698042 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | cached − naive | +0.0170199 | fraction | +1.70199 | 3/3 | 0 | 0.0170199 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | budget_utilization | poolact − naive | -0.252852 | fraction | -25.2852 | 3/3 | 0 | -0.252852 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | cached − naive | -0.333333 | count | 不适用 | 9/9 | 0 | -0.333333 |
| poolact | tuning | all/all | cost_moderate | duplicate_action_attempts | poolact − naive | +1.22222 | count | 不适用 | 9/9 | 0 | 1.22222 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | cached − naive | -0.333333 | count | 不适用 | 9/9 | 0 | -0.333333 |
| poolact | tuning | family/nasbench101 | cost_moderate | duplicate_action_attempts | poolact − naive | +1.22222 | count | 不适用 | 9/9 | 0 | 1.22222 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | cached − naive | +0.666667 | count | 不适用 | 3/3 | 0 | 0.666667 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | duplicate_action_attempts | poolact − naive | +1 | count | 不适用 | 3/3 | 0 | 1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | cached − naive | -1 | count | 不适用 | 3/3 | 0 | -1 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | duplicate_action_attempts | poolact − naive | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | cached − naive | -0.666667 | count | 不适用 | 3/3 | 0 | -0.666667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | duplicate_action_attempts | poolact − naive | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | cached − naive | -0.222222 | count | 不适用 | 9/9 | 0 | -0.222222 |
| poolact | tuning | all/all | cost_moderate | feedback_attempts | poolact − naive | -7.22222 | count | 不适用 | 9/9 | 0 | -7.22222 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | cached − naive | -0.222222 | count | 不适用 | 9/9 | 0 | -0.222222 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_attempts | poolact − naive | -7.22222 | count | 不适用 | 9/9 | 0 | -7.22222 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | cached − naive | +10 | count | 不适用 | 3/3 | 0 | 10 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_attempts | poolact − naive | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | cached − naive | -5 | count | 不适用 | 3/3 | 0 | -5 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_attempts | poolact − naive | -7.33333 | count | 不适用 | 3/3 | 0 | -7.33333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | cached − naive | -5.66667 | count | 不适用 | 3/3 | 0 | -5.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_attempts | poolact − naive | -17 | count | 不适用 | 3/3 | 0 | -17 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | cached − naive | +8521.05 | seconds | 不适用 | 9/9 | 0 | 8521.05 |
| poolact | tuning | all/all | cost_moderate | feedback_cost_seconds | poolact − naive | -52721.2 | seconds | 不适用 | 9/9 | 0 | -52721.2 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | cached − naive | +8521.05 | seconds | 不适用 | 9/9 | 0 | 8521.05 |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_cost_seconds | poolact − naive | -52721.2 | seconds | 不适用 | 9/9 | 0 | -52721.2 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | cached − naive | +9849.64 | seconds | 不适用 | 3/3 | 0 | 9849.64 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_cost_seconds | poolact − naive | -16080.4 | seconds | 不适用 | 3/3 | 0 | -16080.4 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | cached − naive | +8085.96 | seconds | 不适用 | 3/3 | 0 | 8085.96 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_cost_seconds | poolact − naive | -28766.5 | seconds | 不适用 | 3/3 | 0 | -28766.5 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | cached − naive | +7627.55 | seconds | 不适用 | 3/3 | 0 | 7627.55 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_cost_seconds | poolact − naive | -113317 | seconds | 不适用 | 3/3 | 0 | -113317 |
| poolact | tuning | all/all | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | all/all | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | cached − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | feedback_visible | poolact − naive | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_moderate | input_tokens | cached − naive | +34547.6 | tokens | 不适用 | 9/9 | 0 | 34547.6 |
| poolact | tuning | all/all | cost_moderate | input_tokens | poolact − naive | +1.45264e+06 | tokens | 不适用 | 9/9 | 0 | 1.45264e+06 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | cached − naive | +34547.6 | tokens | 不适用 | 9/9 | 0 | 34547.6 |
| poolact | tuning | family/nasbench101 | cost_moderate | input_tokens | poolact − naive | +1.45264e+06 | tokens | 不适用 | 9/9 | 0 | 1.45264e+06 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | cached − naive | +144904 | tokens | 不适用 | 3/3 | 0 | 144904 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | input_tokens | poolact − naive | +416732 | tokens | 不适用 | 3/3 | 0 | 416732 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | cached − naive | -94171.7 | tokens | 不适用 | 3/3 | 0 | -94171.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | input_tokens | poolact − naive | +1.17032e+06 | tokens | 不适用 | 3/3 | 0 | 1.17032e+06 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | cached − naive | +52910.7 | tokens | 不适用 | 3/3 | 0 | 52910.7 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | input_tokens | poolact − naive | +2.77088e+06 | tokens | 不适用 | 3/3 | 0 | 2.77088e+06 |
| poolact | tuning | all/all | cost_moderate | output_tokens | cached − naive | +3267.78 | tokens | 不适用 | 9/9 | 0 | 3267.78 |
| poolact | tuning | all/all | cost_moderate | output_tokens | poolact − naive | +62306.8 | tokens | 不适用 | 9/9 | 0 | 62306.8 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | cached − naive | +3267.78 | tokens | 不适用 | 9/9 | 0 | 3267.78 |
| poolact | tuning | family/nasbench101 | cost_moderate | output_tokens | poolact − naive | +62306.8 | tokens | 不适用 | 9/9 | 0 | 62306.8 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | cached − naive | +9023 | tokens | 不适用 | 3/3 | 0 | 9023 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | output_tokens | poolact − naive | +45163.3 | tokens | 不适用 | 3/3 | 0 | 45163.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | cached − naive | -6206.33 | tokens | 不适用 | 3/3 | 0 | -6206.33 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | output_tokens | poolact − naive | +41127.7 | tokens | 不适用 | 3/3 | 0 | 41127.7 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | cached − naive | +6986.67 | tokens | 不适用 | 3/3 | 0 | 6986.67 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | output_tokens | poolact − naive | +100629 | tokens | 不适用 | 3/3 | 0 | 100629 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | cached − naive | +0.00777377 | fraction | +0.777377 | 9/9 | 0 | 0.00777377 |
| poolact | tuning | all/all | cost_moderate | protocol_failure_rate | poolact − naive | -0.004853 | fraction | -0.4853 | 9/9 | 0 | -0.004853 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | cached − naive | +0.00777377 | fraction | +0.777377 | 9/9 | 0 | 0.00777377 |
| poolact | tuning | family/nasbench101 | cost_moderate | protocol_failure_rate | poolact − naive | -0.004853 | fraction | -0.4853 | 9/9 | 0 | -0.004853 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | cached − naive | +0.00389912 | fraction | +0.389912 | 3/3 | 0 | 0.00389912 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_moderate | protocol_failure_rate | poolact − naive | -0.0151235 | fraction | -1.51235 | 3/3 | 0 | -0.0151235 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | cached − naive | +0.00512217 | fraction | +0.512217 | 3/3 | 0 | 0.00512217 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_moderate | protocol_failure_rate | poolact − naive | +0.000564468 | fraction | +0.0564468 | 3/3 | 0 | 0.000564468 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | cached − naive | +0.0143 | fraction | +1.43 | 3/3 | 0 | 0.0143 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_moderate | protocol_failure_rate | poolact − naive | +0 | fraction | +0 | 3/3 | 0 | 0 |
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
| poolact | tuning | all/all | cost_tight | budget_utilization | poolact − cached | -0.0833786 | fraction | -8.33786 | 9/9 | 0 | -0.0833786 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | poolact − cached | -0.0833786 | fraction | -8.33786 | 9/9 | 0 | -0.0833786 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | poolact − cached | -0.104817 | fraction | -10.4817 | 3/3 | 0 | -0.104817 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | poolact − cached | -0.063893 | fraction | -6.3893 | 3/3 | 0 | -0.063893 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | poolact − cached | -0.0814254 | fraction | -8.14254 | 3/3 | 0 | -0.0814254 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | poolact − cached | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | poolact − cached | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | poolact − cached | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | poolact − cached | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | poolact − cached | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | poolact − cached | +1.11111 | count | 不适用 | 9/9 | 0 | 1.11111 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | poolact − cached | +1.11111 | count | 不适用 | 9/9 | 0 | 1.11111 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | poolact − cached | +1.66667 | count | 不适用 | 3/3 | 0 | 1.66667 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | poolact − cached | -1.33333 | count | 不适用 | 3/3 | 0 | -1.33333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | poolact − cached | +3 | count | 不适用 | 3/3 | 0 | 3 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | poolact − cached | -8355.09 | seconds | 不适用 | 9/9 | 0 | -8355.09 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | poolact − cached | -8355.09 | seconds | 不适用 | 9/9 | 0 | -8355.09 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | poolact − cached | -6218.8 | seconds | 不适用 | 3/3 | 0 | -6218.8 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | poolact − cached | -7899.14 | seconds | 不适用 | 3/3 | 0 | -7899.14 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | poolact − cached | -10947.3 | seconds | 不适用 | 3/3 | 0 | -10947.3 |
| poolact | tuning | all/all | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_visible | poolact − cached | unknown | count | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | input_tokens | poolact − cached | +152024 | tokens | 不适用 | 9/9 | 0 | 152024 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | poolact − cached | +152024 | tokens | 不适用 | 9/9 | 0 | 152024 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | poolact − cached | +44299.3 | tokens | 不适用 | 3/3 | 0 | 44299.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | poolact − cached | +41043 | tokens | 不适用 | 3/3 | 0 | 41043 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | poolact − cached | +370729 | tokens | 不适用 | 3/3 | 0 | 370729 |
| poolact | tuning | all/all | cost_tight | output_tokens | poolact − cached | +17072.2 | tokens | 不适用 | 9/9 | 0 | 17072.2 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | poolact − cached | +17072.2 | tokens | 不适用 | 9/9 | 0 | 17072.2 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | poolact − cached | +11026.3 | tokens | 不适用 | 3/3 | 0 | 11026.3 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | poolact − cached | +5021.67 | tokens | 不适用 | 3/3 | 0 | 5021.67 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | poolact − cached | +35168.7 | tokens | 不适用 | 3/3 | 0 | 35168.7 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | poolact − cached | -0.0288185 | fraction | -2.88185 | 9/9 | 0 | -0.0288185 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | poolact − cached | -0.0288185 | fraction | -2.88185 | 9/9 | 0 | -0.0288185 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | poolact − cached | -0.0798993 | fraction | -7.98993 | 3/3 | 0 | -0.0798993 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | poolact − cached | -0.00655625 | fraction | -0.655625 | 3/3 | 0 | -0.00655625 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | poolact − cached | +0 | fraction | +0 | 3/3 | 0 | 0 |
| poolact | tuning | all/all | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | family/nasbench101 | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/9 | 9 | unknown |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | wall_time_seconds | poolact − cached | unknown | seconds | 不适用 | 0/3 | 3 | unknown |
| poolact | tuning | all/all | cost_tight | budget_utilization | cached − naive | +0.0176965 | fraction | +1.76965 | 9/9 | 0 | 0.0176965 |
| poolact | tuning | all/all | cost_tight | budget_utilization | poolact − naive | -0.0656821 | fraction | -6.56821 | 9/9 | 0 | -0.0656821 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | cached − naive | +0.0176965 | fraction | +1.76965 | 9/9 | 0 | 0.0176965 |
| poolact | tuning | family/nasbench101 | cost_tight | budget_utilization | poolact − naive | -0.0656821 | fraction | -6.56821 | 9/9 | 0 | -0.0656821 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | cached − naive | +0.108219 | fraction | +10.8219 | 3/3 | 0 | 0.108219 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | budget_utilization | poolact − naive | +0.00340161 | fraction | +0.340161 | 3/3 | 0 | 0.00340161 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | cached − naive | -0.0305963 | fraction | -3.05963 | 3/3 | 0 | -0.0305963 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | budget_utilization | poolact − naive | -0.0944893 | fraction | -9.44893 | 3/3 | 0 | -0.0944893 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | cached − naive | -0.0245333 | fraction | -2.45333 | 3/3 | 0 | -0.0245333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | budget_utilization | poolact − naive | -0.105959 | fraction | -10.5959 | 3/3 | 0 | -0.105959 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | cached − naive | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | all/all | cost_tight | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | cached − naive | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | family/nasbench101 | cost_tight | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 9/9 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | cached − naive | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | duplicate_action_attempts | poolact − naive | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | cached − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | duplicate_action_attempts | poolact − naive | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | cached − naive | -0.333333 | count | 不适用 | 3/3 | 0 | -0.333333 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | duplicate_action_attempts | poolact − naive | +0 | count | 不适用 | 3/3 | 0 | 0 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | cached − naive | +1.22222 | count | 不适用 | 9/9 | 0 | 1.22222 |
| poolact | tuning | all/all | cost_tight | feedback_attempts | poolact − naive | +2.33333 | count | 不适用 | 9/9 | 0 | 2.33333 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | cached − naive | +1.22222 | count | 不适用 | 9/9 | 0 | 1.22222 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_attempts | poolact − naive | +2.33333 | count | 不适用 | 9/9 | 0 | 2.33333 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | cached − naive | +0.666667 | count | 不适用 | 3/3 | 0 | 0.666667 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_attempts | poolact − naive | +2.33333 | count | 不适用 | 3/3 | 0 | 2.33333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | cached − naive | +0.333333 | count | 不适用 | 3/3 | 0 | 0.333333 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_attempts | poolact − naive | -1 | count | 不适用 | 3/3 | 0 | -1 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | cached − naive | +2.66667 | count | 不适用 | 3/3 | 0 | 2.66667 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_attempts | poolact − naive | +5.66667 | count | 不适用 | 3/3 | 0 | 5.66667 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | cached − naive | -220.147 | seconds | 不适用 | 9/9 | 0 | -220.147 |
| poolact | tuning | all/all | cost_tight | feedback_cost_seconds | poolact − naive | -8575.24 | seconds | 不适用 | 9/9 | 0 | -8575.24 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | cached − naive | -220.147 | seconds | 不适用 | 9/9 | 0 | -220.147 |
| poolact | tuning | family/nasbench101 | cost_tight | feedback_cost_seconds | poolact − naive | -8575.24 | seconds | 不适用 | 9/9 | 0 | -8575.24 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | cached − naive | +6420.62 | seconds | 不适用 | 3/3 | 0 | 6420.62 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | feedback_cost_seconds | poolact − naive | +201.817 | seconds | 不适用 | 3/3 | 0 | 201.817 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | cached − naive | -3782.65 | seconds | 不适用 | 3/3 | 0 | -3782.65 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | feedback_cost_seconds | poolact − naive | -11681.8 | seconds | 不适用 | 3/3 | 0 | -11681.8 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | cached − naive | -3298.41 | seconds | 不适用 | 3/3 | 0 | -3298.41 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | feedback_cost_seconds | poolact − naive | -14245.8 | seconds | 不适用 | 3/3 | 0 | -14245.8 |
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
| poolact | tuning | all/all | cost_tight | input_tokens | cached − naive | +12071.3 | tokens | 不适用 | 9/9 | 0 | 12071.3 |
| poolact | tuning | all/all | cost_tight | input_tokens | poolact − naive | +164095 | tokens | 不适用 | 9/9 | 0 | 164095 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | cached − naive | +12071.3 | tokens | 不适用 | 9/9 | 0 | 12071.3 |
| poolact | tuning | family/nasbench101 | cost_tight | input_tokens | poolact − naive | +164095 | tokens | 不适用 | 9/9 | 0 | 164095 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | cached − naive | +15861.3 | tokens | 不适用 | 3/3 | 0 | 15861.3 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | input_tokens | poolact − naive | +60160.7 | tokens | 不适用 | 3/3 | 0 | 60160.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | cached − naive | -3664 | tokens | 不适用 | 3/3 | 0 | -3664 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | input_tokens | poolact − naive | +37379 | tokens | 不适用 | 3/3 | 0 | 37379 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | cached − naive | +24016.7 | tokens | 不适用 | 3/3 | 0 | 24016.7 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | input_tokens | poolact − naive | +394746 | tokens | 不适用 | 3/3 | 0 | 394746 |
| poolact | tuning | all/all | cost_tight | output_tokens | cached − naive | +5036.33 | tokens | 不适用 | 9/9 | 0 | 5036.33 |
| poolact | tuning | all/all | cost_tight | output_tokens | poolact − naive | +22108.6 | tokens | 不适用 | 9/9 | 0 | 22108.6 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | cached − naive | +5036.33 | tokens | 不适用 | 9/9 | 0 | 5036.33 |
| poolact | tuning | family/nasbench101 | cost_tight | output_tokens | poolact − naive | +22108.6 | tokens | 不适用 | 9/9 | 0 | 22108.6 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | cached − naive | +5183.33 | tokens | 不适用 | 3/3 | 0 | 5183.33 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | output_tokens | poolact − naive | +16209.7 | tokens | 不适用 | 3/3 | 0 | 16209.7 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | cached − naive | +6776.33 | tokens | 不适用 | 3/3 | 0 | 6776.33 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | output_tokens | poolact − naive | +11798 | tokens | 不适用 | 3/3 | 0 | 11798 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | cached − naive | +3149.33 | tokens | 不适用 | 3/3 | 0 | 3149.33 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | output_tokens | poolact − naive | +38318 | tokens | 不适用 | 3/3 | 0 | 38318 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | cached − naive | -0.0383412 | fraction | -3.83412 | 9/9 | 0 | -0.0383412 |
| poolact | tuning | all/all | cost_tight | protocol_failure_rate | poolact − naive | -0.0671597 | fraction | -6.71597 | 9/9 | 0 | -0.0671597 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | cached − naive | -0.0383412 | fraction | -3.83412 | 9/9 | 0 | -0.0383412 |
| poolact | tuning | family/nasbench101 | cost_tight | protocol_failure_rate | poolact − naive | -0.0671597 | fraction | -6.71597 | 9/9 | 0 | -0.0671597 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | cached − naive | +0.0167055 | fraction | +1.67055 | 3/3 | 0 | 0.0167055 |
| poolact | tuning | task/hpobench:nasbench101:A | cost_tight | protocol_failure_rate | poolact − naive | -0.0631938 | fraction | -6.31938 | 3/3 | 0 | -0.0631938 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | cached − naive | -0.0976285 | fraction | -9.76285 | 3/3 | 0 | -0.0976285 |
| poolact | tuning | task/hpobench:nasbench101:B | cost_tight | protocol_failure_rate | poolact − naive | -0.104185 | fraction | -10.4185 | 3/3 | 0 | -0.104185 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | cached − naive | -0.0341006 | fraction | -3.41006 | 3/3 | 0 | -0.0341006 |
| poolact | tuning | task/hpobench:nasbench101:C | cost_tight | protocol_failure_rate | poolact − naive | -0.0341006 | fraction | -3.41006 | 3/3 | 0 | -0.0341006 |
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

