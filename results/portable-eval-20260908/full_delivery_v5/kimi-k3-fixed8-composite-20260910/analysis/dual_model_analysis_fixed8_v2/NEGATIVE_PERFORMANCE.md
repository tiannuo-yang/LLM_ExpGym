# 全部负性能比较（固定 8 项恢复后的双模型）

这是对两份最终冻结 effects.csv 中预定义性能 metric 的机械筛选：effect < 0。K3 来源 actual_k3_fixed8_composite_export_v2_py311_final，GLM 来源 actual_formal_export_glm_completed_v2。保留全部 49 行：K3 41、GLM 8；原报告 K3 23 + GLM 8 均逐字段不变，新增 18 行来自原本 incomplete 的 K3 组。Gap/raw 及 all/family 是同底层量的重复切片，不能当作 49 个独立反例或胜率分母。

性能 metric 集合：`f1`, `f1_mi`, `f1_mv`, `evidence_acc`, `evidence_acc_mi`, `evidence_acc_mv`, `label_acc`, `label_acc_mi`, `label_acc_mv`, `gap`, `gap_mi`, `gap_bon`, `raw_perf`, `raw_perf_mi`, `raw_perf_bon`。资源/协议负值不在本表，仍完整保留在原 effects.csv。Exp 为效用方向 Free−Tight，负值表示 Tight 反而更高；Pool 为 candidate−naive，负值表示同 N4 / 同反馈预算下 candidate 较低。所有 CI/p 为 null。SD 为三个预声明 seed blocks 的描述性样本 SD，不是稳定性或显著性证明。

表保留原 CSV 浮点字符串；完整 outer 三值、分母和 comparison IDs 见 [NEGATIVE_PERFORMANCE.csv](NEGATIVE_PERFORMANCE.csv) 与 [NUMERICAL_EXTRACT.json](NUMERICAL_EXTRACT.json)。

## kimi-k3

| comparison | system / slice | regime / strategy | metric | baseline | target | effect | outer SD |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| kimi-k3__secondary_62708b9f42dce525c574 | poolact / whois | cost_moderate / cached | f1_mv | 0.6459192223898106 | 0.6420342185048067 | -0.003885003885003886 | null (R1) |
| kimi-k3__secondary_90eb9dc7dea09d3cf560 | poolact / whois | cost_tight / cached | f1_mi | 0.2010021024726907 | 0.19251059398118223 | -0.00849150849150849 | null (R1) |
| kimi-k3__secondary_070e6cd93773ca31d5c4 | poolact / whois | cost_tight / cached | f1_mv | 0.21287078934137757 | 0.18722976370035194 | -0.02564102564102564 | null (R1) |
| kimi-k3__secondary_0fbfe2655a342c798365 | poolact / all | cost_moderate / cached | evidence_acc_mi | 0.7024886877828054 | 0.670814479638009 | -0.031674208144796386 | null (R1) |
| kimi-k3__secondary_0921089d34875c2bfe87 | poolact / all | cost_moderate / cached | label_acc_mi | 0.8947963800904978 | 0.8404977375565611 | -0.054298642533936674 | null (R1) |
| kimi-k3__secondary_ad173cf33a801bacc5d6 | poolact / all | cost_tight / cached | evidence_acc_mi | 0.5452488687782806 | 0.5429864253393665 | -0.002262443438914032 | null (R1) |
| kimi-k3__secondary_73c51957a3a01dd8d972 | poolact / all | cost_tight / cached | evidence_acc_mv | 0.5520361990950227 | 0.5475113122171946 | -0.004524886877828049 | null (R1) |
| kimi-k3__secondary_589f2de3cf2bca29e68b | poolact / all | cost_tight / cached | label_acc_mi | 0.8223981900452488 | 0.8110859728506787 | -0.011312217194570139 | null (R1) |
| kimi-k3__secondary_01c208d425cd05f0bdb9 | poolact / all | cost_tight / cached | label_acc_mv | 0.8416289592760181 | 0.8371040723981901 | -0.004524886877828047 | null (R1) |
| kimi-k3__secondary_dc67550f1a28d930cdd0 | poolact / all | cost_moderate / cached | gap_bon | 98.98695455112885 | 98.83932273799364 | -0.14763181313520116 | 0.23054277757032 |
| kimi-k3__secondary_5892d984da717adfa0b3 | poolact / all | cost_moderate / cached | gap_mi | 98.03886592767417 | 97.9611398348133 | -0.07772609286087907 | 0.3390056200941265 |
| kimi-k3__secondary_f4010a108d06cfeccb32 | poolact / all | cost_moderate / cached | raw_perf_bon | 0.9431534873114692 | 0.9423151038311146 | -0.0008383834803545999 | 0.001386180943170425 |
| kimi-k3__secondary_57bcfe33d472ce60ec29 | poolact / all | cost_moderate / cached | raw_perf_mi | 0.9382882990218975 | 0.937575117305473 | -0.0007131817164244517 | 0.002935510089161734 |
| kimi-k3__secondary_3f58e3ba6a3707f40015 | poolact / all | cost_moderate / poolact | gap_bon | 98.98695455112885 | 98.871046094003 | -0.1159084571258404 | 0.3471291056129085 |
| kimi-k3__secondary_c3500912a6e431c48d82 | poolact / all | cost_moderate / poolact | raw_perf_bon | 0.9431534873114692 | 0.942804789101636 | -0.0003486982098332117 | 0.0017320628479594855 |
| kimi-k3__secondary_e29b670610737e4f0fb2 | poolact / all | cost_tight / cached | gap_mi | 94.25826234358385 | 94.11146437303562 | -0.14679797054823182 | 1.4100024995747078 |
| kimi-k3__secondary_1d9adbb9931c80dd4794 | poolact / all | cost_tight / cached | raw_perf_mi | 0.9194303464006495 | 0.9166685199296033 | -0.0027618264710461324 | 0.00854832263579508 |
| kimi-k3__secondary_90e3f34c735ca7ac96d5 | poolact / family=nasbench101 | cost_moderate / cached | gap_bon | 98.98695455112885 | 98.83932273799364 | -0.14763181313520116 | 0.23054277757032 |
| kimi-k3__secondary_a1c03e66acd6cf089f2c | poolact / family=nasbench101 | cost_moderate / cached | gap_mi | 98.03886592767417 | 97.9611398348133 | -0.07772609286087907 | 0.3390056200941265 |
| kimi-k3__secondary_73bb6783f635d485561a | poolact / family=nasbench101 | cost_moderate / cached | raw_perf_bon | 0.9431534873114692 | 0.9423151038311146 | -0.0008383834803545999 | 0.001386180943170425 |
| kimi-k3__secondary_2ec2f2caa9fe737012fe | poolact / family=nasbench101 | cost_moderate / cached | raw_perf_mi | 0.9382882990218975 | 0.937575117305473 | -0.0007131817164244517 | 0.002935510089161734 |
| kimi-k3__secondary_d7833409f7542a245886 | poolact / family=nasbench101 | cost_moderate / poolact | gap_bon | 98.98695455112885 | 98.871046094003 | -0.1159084571258404 | 0.3471291056129085 |
| kimi-k3__secondary_cf08c7d4b453fd128064 | poolact / family=nasbench101 | cost_moderate / poolact | raw_perf_bon | 0.9431534873114692 | 0.942804789101636 | -0.0003486982098332117 | 0.0017320628479594855 |
| kimi-k3__secondary_c3909ad9681f5a1899ea | poolact / family=nasbench101 | cost_tight / cached | gap_mi | 94.25826234358385 | 94.11146437303562 | -0.14679797054823182 | 1.4100024995747078 |
| kimi-k3__secondary_7ec49274ecfab04a28de | poolact / family=nasbench101 | cost_tight / cached | raw_perf_mi | 0.9194303464006495 | 0.9166685199296033 | -0.0027618264710461324 | 0.00854832263579508 |
| kimi-k3__secondary_7bc315d18136af1262b9 | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | gap_bon | 99.31971338543822 | 99.13460964341456 | -0.18510374202364707 | 0.20867254173511796 |
| kimi-k3__secondary_92fb5eac67fa39710b4d | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | gap_mi | 98.28741426632331 | 97.81318843066789 | -0.47422583565542215 | 1.382527401184944 |
| kimi-k3__secondary_680762e72d87507ba5d7 | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | raw_perf_bon | 0.9412949681282043 | 0.9399928715493944 | -0.0013020965788099377 | 0.0014678893020443565 |
| kimi-k3__secondary_aaca681a0ca403db6321 | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | raw_perf_mi | 0.9340333475006951 | 0.930697446068128 | -0.00333590143256716 | 0.009725271782803734 |
| kimi-k3__secondary_c8b0ea946bd48c79ae86 | poolact / task=hpobench:nasbench101:A | cost_tight / cached | gap_mi | 93.4276982130541 | 91.23732621405718 | -2.1903719989969233 | 1.748756550082471 |
| kimi-k3__secondary_83a9e1e6ea29ffa5db90 | poolact / task=hpobench:nasbench101:A | cost_tight / cached | raw_perf_mi | 0.8998480869664086 | 0.8844401008552975 | -0.015407986111111124 | 0.012301479679125127 |
| kimi-k3__secondary_0e00f043d03e4d35f5a8 | poolact / task=hpobench:nasbench101:A | cost_tight / poolact | gap_bon | 98.80712166648453 | 98.69163165615801 | -0.11549001032652484 | 0.5935112620269246 |
| kimi-k3__secondary_1bf3ce81826e410a7b3f | poolact / task=hpobench:nasbench101:A | cost_tight / poolact | raw_perf_bon | 0.9376891851425171 | 0.9368767804569669 | -0.0008124046855502905 | 0.004175004650482497 |
| kimi-k3__secondary_c05b2aa81f8d54ba2fc9 | poolact / task=hpobench:nasbench101:B | cost_moderate / cached | gap_bon | 97.75535713525542 | 97.67674946832543 | -0.0786076669300068 | 0.34062859223362896 |
| kimi-k3__secondary_20da10863367d24970dd | poolact / task=hpobench:nasbench101:B | cost_moderate / cached | raw_perf_bon | 0.9432313905821906 | 0.9430310659938388 | -0.00020032458835176717 | 0.0008680614141722468 |
| kimi-k3__secondary_fab2e14a6ccd48e60ae4 | poolact / task=hpobench:nasbench101:B | cost_moderate / poolact | gap_bon | 97.75535713525542 | 97.5937810613429 | -0.16157607391253256 | 0.3669090426713214 |
| kimi-k3__secondary_05c0148a17e0f3bfae22 | poolact / task=hpobench:nasbench101:B | cost_moderate / poolact | raw_perf_bon | 0.9432313905821906 | 0.9428196284506056 | -0.00041176213158500286 | 0.0009350347848527189 |
| kimi-k3__secondary_d1ee56761e1aa894b400 | poolact / task=hpobench:nasbench101:C | cost_moderate / cached | gap_bon | 99.8857931326929 | 99.70660910224095 | -0.17918403045194964 | 0.5447548362160523 |
| kimi-k3__secondary_b0d2e3904f0db9eaaf8b | poolact / task=hpobench:nasbench101:C | cost_moderate / cached | raw_perf_bon | 0.9449341032240126 | 0.9439213739501106 | -0.0010127292739020948 | 0.0030788969772821296 |
| kimi-k3__secondary_b32ed26ebc37c10bc397 | poolact / task=hpobench:nasbench101:C | cost_moderate / poolact | gap_bon | 99.8857931326929 | 99.39746840195308 | -0.4883247307398288 | 0.5677473613037444 |
| kimi-k3__secondary_04f3e2bc1aedb51fccad | poolact / task=hpobench:nasbench101:C | cost_moderate / poolact | raw_perf_bon | 0.9449341032240126 | 0.9421741432613797 | -0.002759959962632933 | 0.0032088483082043633 |

## glm-5.3

| comparison | system / slice | regime / strategy | metric | baseline | target | effect | outer SD |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| glm-5.3__secondary_353bdb04637b583922d4 | expgym / all | Free→Tight / single | label_acc | 0.6923076923076923 | 0.7360482654600301 | -0.04374057315233785 | null (R1) |
| glm-5.3__secondary_1ee8df68035f7c9b9c67 | poolact / all | cost_moderate / cached | label_acc_mi | 0.7579185520361991 | 0.753393665158371 | -0.004524886877828064 | null (R1) |
| glm-5.3__secondary_765356f432b6b882efdd | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | gap_bon | 99.21529702453788 | 99.049178160994 | -0.16611886354387195 | 0.2651525438315017 |
| glm-5.3__secondary_06087b241df7e8d05696 | poolact / task=hpobench:nasbench101:A | cost_moderate / cached | raw_perf_bon | 0.9405604600906372 | 0.9393919110298157 | -0.0011685490608214961 | 0.0018651930880017448 |
| glm-5.3__secondary_c4a202464c48befb7c3a | poolact / task=hpobench:nasbench101:A | cost_tight / cached | gap_mi | 88.90733650955693 | 87.93238768148167 | -0.9749488280752464 | 4.852116380256538 |
| glm-5.3__secondary_5a9e2dab92074ab08de6 | poolact / task=hpobench:nasbench101:A | cost_tight / cached | raw_perf_mi | 0.8680499858326381 | 0.8611917909648683 | -0.006858194867769914 | 0.03413180127883497 |
| glm-5.3__secondary_4fa5df34a4731d4d89ec | poolact / task=hpobench:nasbench101:B | cost_moderate / cached | gap_bon | 98.24883022604952 | 98.17459369426155 | -0.07423653178797451 | 1.161220125046389 |
| glm-5.3__secondary_106e9b16fe20f40f9c9f | poolact / task=hpobench:nasbench101:B | cost_moderate / cached | raw_perf_bon | 0.9444889624913534 | 0.9442997773488363 | -0.00018918514251708984 | 0.0029592653314953693 |
