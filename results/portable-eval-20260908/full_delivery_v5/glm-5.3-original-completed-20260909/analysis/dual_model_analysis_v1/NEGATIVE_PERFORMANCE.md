# 全部负性能比较（已冻结原效应的投影）

不改变主次身份、指标、分母或负号。单位为原指标单位；Gap/raw、all/family 切片相关或重复，不能当独立实验计数。完整精度见 NUMERICAL_EXTRACT.json；其 input_refs 固定两个原 effects.csv。正值、零值、资源指标与全部 unknown 未删，仍在原导出目录。

## kimi-k3：23 项

| comparison 后缀 | 场景 / 切片 | strategy | 预算 | metric | baseline | target | effect | R3 SD |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| secondary_62708b9f42dce525c574 | poolact/restricted_search/whois | cached | cost_moderate | f1_mv | 0.645919 | 0.642034 | -0.003885 | null（R1） |
| secondary_90eb9dc7dea09d3cf560 | poolact/restricted_search/whois | cached | cost_tight | f1_mi | 0.201002 | 0.192511 | -0.008492 | null（R1） |
| secondary_070e6cd93773ca31d5c4 | poolact/restricted_search/whois | cached | cost_tight | f1_mv | 0.212871 | 0.187230 | -0.025641 | null（R1） |
| secondary_0fbfe2655a342c798365 | poolact/evidence_audit/all | cached | cost_moderate | evidence_acc_mi | 0.702489 | 0.670814 | -0.031674 | null（R1） |
| secondary_0921089d34875c2bfe87 | poolact/evidence_audit/all | cached | cost_moderate | label_acc_mi | 0.894796 | 0.840498 | -0.054299 | null（R1） |
| secondary_ad173cf33a801bacc5d6 | poolact/evidence_audit/all | cached | cost_tight | evidence_acc_mi | 0.545249 | 0.542986 | -0.002262 | null（R1） |
| secondary_73c51957a3a01dd8d972 | poolact/evidence_audit/all | cached | cost_tight | evidence_acc_mv | 0.552036 | 0.547511 | -0.004525 | null（R1） |
| secondary_589f2de3cf2bca29e68b | poolact/evidence_audit/all | cached | cost_tight | label_acc_mi | 0.822398 | 0.811086 | -0.011312 | null（R1） |
| secondary_01c208d425cd05f0bdb9 | poolact/evidence_audit/all | cached | cost_tight | label_acc_mv | 0.841629 | 0.837104 | -0.004525 | null（R1） |
| secondary_e29b670610737e4f0fb2 | poolact/tuning/all | cached | cost_tight | gap_mi | 94.258262 | 94.111464 | -0.146798 | 1.410002 |
| secondary_1d9adbb9931c80dd4794 | poolact/tuning/all | cached | cost_tight | raw_perf_mi | 0.919430 | 0.916669 | -0.002762 | 0.008548 |
| secondary_c3909ad9681f5a1899ea | poolact/tuning/family=nasbench101 | cached | cost_tight | gap_mi | 94.258262 | 94.111464 | -0.146798 | 1.410002 |
| secondary_7ec49274ecfab04a28de | poolact/tuning/family=nasbench101 | cached | cost_tight | raw_perf_mi | 0.919430 | 0.916669 | -0.002762 | 0.008548 |
| secondary_7bc315d18136af1262b9 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | gap_bon | 99.319713 | 99.134610 | -0.185104 | 0.208673 |
| secondary_92fb5eac67fa39710b4d | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | gap_mi | 98.287414 | 97.813188 | -0.474226 | 1.382527 |
| secondary_680762e72d87507ba5d7 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | raw_perf_bon | 0.941295 | 0.939993 | -0.001302 | 0.001468 |
| secondary_aaca681a0ca403db6321 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | raw_perf_mi | 0.934033 | 0.930697 | -0.003336 | 0.009725 |
| secondary_c8b0ea946bd48c79ae86 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_tight | gap_mi | 93.427698 | 91.237326 | -2.190372 | 1.748757 |
| secondary_83a9e1e6ea29ffa5db90 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_tight | raw_perf_mi | 0.899848 | 0.884440 | -0.015408 | 0.012301 |
| secondary_0e00f043d03e4d35f5a8 | poolact/tuning/task=hpobench:nasbench101:A | poolact | cost_tight | gap_bon | 98.807122 | 98.691632 | -0.115490 | 0.593511 |
| secondary_1bf3ce81826e410a7b3f | poolact/tuning/task=hpobench:nasbench101:A | poolact | cost_tight | raw_perf_bon | 0.937689 | 0.936877 | -0.000812 | 0.004175 |
| secondary_c05b2aa81f8d54ba2fc9 | poolact/tuning/task=hpobench:nasbench101:B | cached | cost_moderate | gap_bon | 97.755357 | 97.676749 | -0.078608 | 0.340629 |
| secondary_20da10863367d24970dd | poolact/tuning/task=hpobench:nasbench101:B | cached | cost_moderate | raw_perf_bon | 0.943231 | 0.943031 | -0.000200 | 0.000868 |

## glm-5.3：8 项

| comparison 后缀 | 场景 / 切片 | strategy | 预算 | metric | baseline | target | effect | R3 SD |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| secondary_353bdb04637b583922d4 | expgym/evidence_audit/all | single | Free−Tight | label_acc | 0.692308 | 0.736048 | -0.043741 | null（R1） |
| secondary_1ee8df68035f7c9b9c67 | poolact/evidence_audit/all | cached | cost_moderate | label_acc_mi | 0.757919 | 0.753394 | -0.004525 | null（R1） |
| secondary_765356f432b6b882efdd | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | gap_bon | 99.215297 | 99.049178 | -0.166119 | 0.265153 |
| secondary_06087b241df7e8d05696 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_moderate | raw_perf_bon | 0.940560 | 0.939392 | -0.001169 | 0.001865 |
| secondary_c4a202464c48befb7c3a | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_tight | gap_mi | 88.907337 | 87.932388 | -0.974949 | 4.852116 |
| secondary_5a9e2dab92074ab08de6 | poolact/tuning/task=hpobench:nasbench101:A | cached | cost_tight | raw_perf_mi | 0.868050 | 0.861192 | -0.006858 | 0.034132 |
| secondary_4fa5df34a4731d4d89ec | poolact/tuning/task=hpobench:nasbench101:B | cached | cost_moderate | gap_bon | 98.248830 | 98.174594 | -0.074237 | 1.161220 |
| secondary_106e9b16fe20f40f9c9f | poolact/tuning/task=hpobench:nasbench101:B | cached | cost_moderate | raw_perf_bon | 0.944489 | 0.944300 | -0.000189 | 0.002959 |

