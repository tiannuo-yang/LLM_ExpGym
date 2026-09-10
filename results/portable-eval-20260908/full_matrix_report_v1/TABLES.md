# 全设置绝对指标表（自动生成）

输入固定为提交 `6119f9d136c9ed1f06a7bedd7371be0deb9b5d59` 的两模型最终导出。只聚合冻结 CSV，不调用模型、投票器或 scorer。

先在每 item 内等权平均 outer repeats，再跨 item 等权。Exp Audit 已在原导出内将三个固定 orders 文档内等权平均；N4 pool 是一个单元。

分数保留原单位：F1/EA/LA/raw 为 0–1，Gap 为 points（本库定义越高越好，可超过 100）。表显示六位小数；全部原精度均值、完整分母、unknown 和 seedblock 描述 SD 见 [aggregate_metrics.csv](aggregate_metrics.csv)，三个 HPO seed blocks 的所有 task/setting 见 [by_outerseed.csv](by_outerseed.csv)。R1 SD 是 null，不是零；没有 CI/p 或总体推广。

## ExpGym：Search / Audit

| 场景 | 切片 | 预算 | 指标 | items / R1 | Kimi-K3 | GLM-5.3 |
| --- | --- | --- | --- | --- | --- | --- |
| restricted_search | all | Free | f1 | 73 | 0.635911 | 0.651102 |
| restricted_search | all | Moderate | f1 | 73 | 0.496169 | 0.532761 |
| restricted_search | all | Tight | f1 | 73 | 0.157561 | 0.192341 |
| restricted_search | whois | Free | f1 | 39 | 0.658862 | 0.682651 |
| restricted_search | whois | Moderate | f1 | 39 | 0.573004 | 0.642842 |
| restricted_search | whois | Tight | f1 | 39 | 0.170136 | 0.230575 |
| restricted_search | whatis | Free | f1 | 34 | 0.609584 | 0.614914 |
| restricted_search | whatis | Moderate | f1 | 34 | 0.408034 | 0.406491 |
| restricted_search | whatis | Tight | f1 | 34 | 0.143137 | 0.148485 |
| evidence_audit | all | Free | evidence_acc | 13 | 0.894419 | 0.684766 |
| evidence_audit | all | Free | label_acc | 13 | 0.926094 | 0.692308 |
| evidence_audit | all | Moderate | evidence_acc | 13 | 0.687783 | 0.678733 |
| evidence_audit | all | Moderate | label_acc | 13 | 0.853695 | 0.760181 |
| evidence_audit | all | Tight | evidence_acc | 13 | 0.515837 | 0.502262 |
| evidence_audit | all | Tight | label_acc | 13 | 0.794872 | 0.736048 |

## ExpGym：HPO 全体、家族及逐任务（R3）

| 切片 | 预算 | items（每项 R=3） | K3 Gap | K3 raw | GLM Gap | GLM raw |
| --- | --- | --- | --- | --- | --- | --- |
| all | Free | 9 | 98.512910 | 0.830424 | 97.911143 | 0.829110 |
| all | Moderate | 9 | 94.230104 | 0.819970 | 96.154560 | 0.824766 |
| all | Tight | 9 | 89.683717 | 0.814494 | 86.066889 | 0.801956 |
| family=nasbench101 | Free | 3 | 98.692013 | 0.941770 | 99.057476 | 0.943450 |
| family=nasbench101 | Moderate | 3 | 97.857181 | 0.937407 | 97.736559 | 0.936239 |
| family=nasbench101 | Tight | 3 | 94.968099 | 0.918447 | 90.761443 | 0.898441 |
| family=nasbench201 | Free | 3 | 99.770835 | 0.706212 | 98.637164 | 0.704850 |
| family=nasbench201 | Moderate | 3 | 97.076629 | 0.703764 | 96.486852 | 0.702974 |
| family=nasbench201 | Tight | 3 | 94.660569 | 0.701261 | 88.037331 | 0.692131 |
| family=paramnet | Free | 3 | 97.075883 | 0.843288 | 96.038788 | 0.839029 |
| family=paramnet | Moderate | 3 | 87.756501 | 0.818739 | 94.240269 | 0.835086 |
| family=paramnet | Tight | 3 | 79.422483 | 0.823773 | 79.401892 | 0.815296 |
| task=hpobench:nasbench101:A | Free | 1 | 99.258011 | 0.940861 | 99.579172 | 0.943120 |
| task=hpobench:nasbench101:A | Moderate | 1 | 98.079371 | 0.932570 | 99.003299 | 0.939069 |
| task=hpobench:nasbench101:A | Tight | 1 | 90.517091 | 0.879374 | 85.756650 | 0.845887 |
| task=hpobench:nasbench101:B | Free | 1 | 97.454035 | 0.942463 | 97.969343 | 0.943777 |
| task=hpobench:nasbench101:B | Moderate | 1 | 96.585000 | 0.940249 | 97.467138 | 0.942497 |
| task=hpobench:nasbench101:B | Tight | 1 | 95.759638 | 0.938145 | 89.995192 | 0.923455 |
| task=hpobench:nasbench101:C | Free | 1 | 99.363994 | 0.941985 | 99.623912 | 0.943454 |
| task=hpobench:nasbench101:C | Moderate | 1 | 98.907173 | 0.939403 | 96.739239 | 0.927150 |
| task=hpobench:nasbench101:C | Tight | 1 | 98.627567 | 0.937823 | 96.532487 | 0.925982 |
| task=hpobench:nasbench201:cifar10-valid | Free | 1 | 100.000000 | 0.916067 | 99.391401 | 0.915582 |
| task=hpobench:nasbench201:cifar10-valid | Moderate | 1 | 93.657170 | 0.911018 | 93.880509 | 0.911196 |
| task=hpobench:nasbench201:cifar10-valid | Tight | 1 | 90.206581 | 0.908271 | 93.657170 | 0.911018 |
| task=hpobench:nasbench201:cifar100 | Free | 1 | 100.000000 | 0.735033 | 99.171863 | 0.734022 |
| task=hpobench:nasbench201:cifar100 | Moderate | 1 | 100.000000 | 0.735033 | 99.171863 | 0.734022 |
| task=hpobench:nasbench201:cifar100 | Tight | 1 | 97.479188 | 0.731956 | 90.981498 | 0.724022 |
| task=hpobench:nasbench201:imagenet16-120 | Free | 1 | 99.312504 | 0.467537 | 97.348228 | 0.464944 |
| task=hpobench:nasbench201:imagenet16-120 | Moderate | 1 | 97.572717 | 0.465241 | 96.408183 | 0.463704 |
| task=hpobench:nasbench201:imagenet16-120 | Tight | 1 | 96.295938 | 0.463556 | 79.473326 | 0.441352 |
| task=hpobench:paramnet:adult:steps | Free | 1 | 97.856995 | 0.852849 | 95.601586 | 0.851920 |
| task=hpobench:paramnet:adult:steps | Moderate | 1 | 87.329255 | 0.848512 | 95.414265 | 0.851843 |
| task=hpobench:paramnet:adult:steps | Tight | 1 | 77.355993 | 0.844404 | 72.013444 | 0.842204 |
| task=hpobench:paramnet:higgs:steps | Free | 1 | 94.148953 | 0.715973 | 95.829008 | 0.717435 |
| task=hpobench:paramnet:higgs:steps | Moderate | 1 | 89.082285 | 0.711564 | 92.269269 | 0.714337 |
| task=hpobench:paramnet:higgs:steps | Tight | 1 | 66.679766 | 0.692066 | 78.314729 | 0.702193 |
| task=hpobench:paramnet:letter:steps | Free | 1 | 99.221702 | 0.961043 | 96.685771 | 0.947731 |
| task=hpobench:paramnet:letter:steps | Moderate | 1 | 86.857961 | 0.896141 | 95.037272 | 0.939077 |
| task=hpobench:paramnet:letter:steps | Tight | 1 | 94.231691 | 0.934848 | 87.877503 | 0.901493 |

## PoolAct：Search whois / Audit（N4，R1）

Search 仅39 whois，故 all=whois；无 Pool whatis 设置。Audit 为原 default order；MI 为四 agent 指标均值，MV 为冻结投票输出指标。

| 模型 | 预算 | 策略 | F1 MI | F1 MV | EA MI | EA MV | LA MI | LA MV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | Moderate | naive | 0.623870 | 0.645919 | 0.702489 | 0.737557 | 0.894796 | 0.923077 |
| kimi-k3 | Moderate | cached | 0.632024 | 0.642034 | 0.670814 | 0.764706 | 0.840498 | 0.936652 |
| kimi-k3 | Moderate | poolact | 0.640914 | 0.667409 | 0.908371 | 0.936652 | 0.928733 | 0.972851 |
| kimi-k3 | Tight | naive | 0.201002 | 0.212871 | 0.545249 | 0.552036 | 0.822398 | 0.841629 |
| kimi-k3 | Tight | cached | 0.192511 | 0.187230 | 0.542986 | 0.547511 | 0.811086 | 0.837104 |
| kimi-k3 | Tight | poolact | 0.272395 | 0.304324 | 0.602941 | 0.628959 | 0.846154 | 0.873303 |
| glm-5.3 | Moderate | naive | 0.599406 | 0.620278 | 0.654977 | 0.809955 | 0.757919 | 0.927602 |
| glm-5.3 | Moderate | cached | 0.620111 | 0.656725 | 0.668552 | 0.846154 | 0.753394 | 0.936652 |
| glm-5.3 | Moderate | poolact | 0.659089 | 0.657419 | 0.802036 | 0.977376 | 0.808824 | 0.981900 |
| glm-5.3 | Tight | naive | 0.203255 | 0.208597 | 0.549774 | 0.588235 | 0.792986 | 0.868778 |
| glm-5.3 | Tight | cached | 0.203255 | 0.208597 | 0.585973 | 0.601810 | 0.869910 | 0.891403 |
| glm-5.3 | Tight | poolact | 0.247425 | 0.300050 | 0.607466 | 0.692308 | 0.798643 | 0.904977 |

## PoolAct：NAS101 A/B/C（N4，R3）

all 即 NAS101 三任务等权；不含 ParamNet/NAS201。BoN 与 MI 均原样保留，不能只看最高值。

| 模型 | 切片 | 预算 | 策略 | Gap MI | Gap BoN | raw MI | raw BoN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | all | Moderate | naive | 98.038866 | 98.986955 | 0.938288 | 0.943153 |
| kimi-k3 | all | Moderate | cached | 97.961140 | 98.839323 | 0.937575 | 0.942315 |
| kimi-k3 | all | Moderate | poolact | 98.556328 | 98.871046 | 0.941256 | 0.942805 |
| kimi-k3 | all | Tight | naive | 94.258262 | 97.993150 | 0.919430 | 0.938976 |
| kimi-k3 | all | Tight | cached | 94.111464 | 98.366255 | 0.916669 | 0.940167 |
| kimi-k3 | all | Tight | poolact | 96.051676 | 98.365115 | 0.929105 | 0.939919 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | naive | 98.287414 | 99.319713 | 0.934033 | 0.941295 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | cached | 97.813188 | 99.134610 | 0.930697 | 0.939993 |
| kimi-k3 | task=hpobench:nasbench101:A | Moderate | poolact | 99.263154 | 99.621889 | 0.940897 | 0.943421 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | naive | 93.427698 | 98.807122 | 0.899848 | 0.937689 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | cached | 91.237326 | 98.864077 | 0.884440 | 0.938090 |
| kimi-k3 | task=hpobench:nasbench101:A | Tight | poolact | 95.504557 | 98.691632 | 0.914458 | 0.936877 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | naive | 96.818635 | 97.755357 | 0.940844 | 0.943231 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | cached | 96.872130 | 97.676749 | 0.940981 | 0.943031 |
| kimi-k3 | task=hpobench:nasbench101:B | Moderate | poolact | 97.211667 | 97.593781 | 0.941846 | 0.942820 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | naive | 92.227822 | 96.135197 | 0.929145 | 0.939103 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | cached | 93.119782 | 97.047906 | 0.931418 | 0.941429 |
| kimi-k3 | task=hpobench:nasbench101:B | Tight | poolact | 93.599063 | 97.205119 | 0.932639 | 0.941829 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | naive | 99.010548 | 99.885793 | 0.939987 | 0.944934 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | cached | 99.198101 | 99.706609 | 0.941047 | 0.943921 |
| kimi-k3 | task=hpobench:nasbench101:C | Moderate | poolact | 99.194164 | 99.397468 | 0.941025 | 0.942174 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | naive | 97.119267 | 99.037133 | 0.929298 | 0.940138 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | cached | 97.977285 | 99.186781 | 0.934147 | 0.940983 |
| kimi-k3 | task=hpobench:nasbench101:C | Tight | poolact | 99.051407 | 99.198595 | 0.940218 | 0.941050 |
| glm-5.3 | all | Moderate | naive | 97.873330 | 99.007686 | 0.937173 | 0.942712 |
| glm-5.3 | all | Moderate | cached | 98.061333 | 99.115941 | 0.938197 | 0.943324 |
| glm-5.3 | all | Moderate | poolact | 98.965828 | 99.380739 | 0.942421 | 0.944478 |
| glm-5.3 | all | Tight | naive | 83.960328 | 93.809666 | 0.880532 | 0.920903 |
| glm-5.3 | all | Tight | cached | 86.182578 | 94.548781 | 0.888600 | 0.923040 |
| glm-5.3 | all | Tight | poolact | 96.176599 | 98.463026 | 0.928628 | 0.941020 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | naive | 97.771660 | 99.215297 | 0.930405 | 0.940560 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | cached | 97.880822 | 99.049178 | 0.931173 | 0.939392 |
| glm-5.3 | task=hpobench:nasbench101:A | Moderate | poolact | 98.993806 | 99.520635 | 0.939002 | 0.942708 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | naive | 88.907337 | 94.397901 | 0.868050 | 0.906673 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | cached | 87.932388 | 94.459601 | 0.861192 | 0.907107 |
| glm-5.3 | task=hpobench:nasbench101:A | Tight | poolact | 95.258942 | 99.224789 | 0.912730 | 0.940627 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | naive | 96.762956 | 98.248830 | 0.940702 | 0.944489 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | cached | 96.848113 | 98.174594 | 0.940919 | 0.944300 |
| glm-5.3 | task=hpobench:nasbench101:B | Moderate | poolact | 98.202974 | 98.716097 | 0.944372 | 0.945680 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | naive | 71.553333 | 88.785528 | 0.876458 | 0.920373 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | cached | 75.460710 | 90.785619 | 0.886415 | 0.925470 |
| glm-5.3 | task=hpobench:nasbench101:B | Tight | poolact | 94.632951 | 96.912531 | 0.935274 | 0.941084 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | naive | 99.085373 | 99.558932 | 0.940410 | 0.943087 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | cached | 99.455064 | 100.124052 | 0.942500 | 0.946281 |
| glm-5.3 | task=hpobench:nasbench101:C | Moderate | poolact | 99.700703 | 99.905485 | 0.943888 | 0.945045 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | naive | 91.420315 | 98.245569 | 0.897088 | 0.935664 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | cached | 95.154636 | 98.401123 | 0.918194 | 0.936543 |
| glm-5.3 | task=hpobench:nasbench101:C | Tight | poolact | 98.637904 | 99.251758 | 0.937881 | 0.941351 |

## R3 seed blocks

直接展示上述全体任务的三个等权 seedblock 均值：Exp HPO 为九任务，Pool NAS 为三任务。outer0/1/2 对应请求 base seed 标签2200/2204/2208；不是已验证的独立随机重复。SD 是这三个均值的样本描述 SD，不是标准误、置信区间或显著性。完整逐 task 数据仍见 by_outerseed.csv。

| 模型 | 系统 | 预算 | 策略 | 指标 | outer0 | outer1 | outer2 | 描述 SD |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | expgym | Free | single | gap | 98.323337 | 98.022659 | 99.192735 | 0.607637 |
| kimi-k3 | expgym | Moderate | single | gap | 91.888380 | 96.720920 | 94.081011 | 2.419717 |
| kimi-k3 | expgym | Tight | single | gap | 94.484532 | 84.994278 | 89.572341 | 4.746108 |
| kimi-k3 | poolact | Moderate | naive | gap_mi | 98.159365 | 97.682031 | 98.275201 | 0.314409 |
| kimi-k3 | poolact | Moderate | naive | gap_bon | 98.929687 | 99.008280 | 99.022896 | 0.050130 |
| kimi-k3 | poolact | Moderate | cached | gap_mi | 98.189185 | 97.876493 | 97.817742 | 0.199665 |
| kimi-k3 | poolact | Moderate | cached | gap_bon | 98.999939 | 98.619248 | 98.898781 | 0.197187 |
| kimi-k3 | poolact | Moderate | poolact | gap_mi | 98.742041 | 98.409035 | 98.517909 | 0.169795 |
| kimi-k3 | poolact | Moderate | poolact | gap_bon | 99.203580 | 98.778343 | 98.631216 | 0.297230 |
| kimi-k3 | poolact | Tight | naive | gap_mi | 95.204981 | 95.935980 | 91.633827 | 2.302029 |
| kimi-k3 | poolact | Tight | naive | gap_bon | 98.382865 | 97.934448 | 97.662139 | 0.363931 |
| kimi-k3 | poolact | Tight | cached | gap_mi | 94.012988 | 95.230677 | 93.090729 | 1.073367 |
| kimi-k3 | poolact | Tight | cached | gap_bon | 98.556372 | 98.499508 | 98.042884 | 0.281487 |
| kimi-k3 | poolact | Tight | poolact | gap_mi | 96.017289 | 96.675142 | 95.462595 | 0.607004 |
| kimi-k3 | poolact | Tight | poolact | gap_bon | 98.509911 | 98.153972 | 98.431462 | 0.187015 |
| glm-5.3 | expgym | Free | single | gap | 97.433902 | 97.962348 | 98.337178 | 0.453810 |
| glm-5.3 | expgym | Moderate | single | gap | 94.984465 | 98.060230 | 95.418984 | 1.664598 |
| glm-5.3 | expgym | Tight | single | gap | 86.858680 | 88.946705 | 82.395281 | 3.346713 |
| glm-5.3 | poolact | Moderate | naive | gap_mi | 98.284886 | 97.116195 | 98.218909 | 0.656527 |
| glm-5.3 | poolact | Moderate | naive | gap_bon | 98.659706 | 99.337451 | 99.025902 | 0.339239 |
| glm-5.3 | poolact | Moderate | cached | gap_mi | 98.313975 | 98.089126 | 97.780897 | 0.267624 |
| glm-5.3 | poolact | Moderate | cached | gap_bon | 99.041402 | 99.010835 | 99.295587 | 0.156326 |
| glm-5.3 | poolact | Moderate | poolact | gap_mi | 98.943264 | 98.786747 | 99.167472 | 0.191363 |
| glm-5.3 | poolact | Moderate | poolact | gap_bon | 99.303895 | 99.400526 | 99.437796 | 0.069109 |
| glm-5.3 | poolact | Tight | naive | gap_mi | 87.086990 | 81.378917 | 83.415077 | 2.892836 |
| glm-5.3 | poolact | Tight | naive | gap_bon | 93.425246 | 91.065575 | 96.938176 | 2.955113 |
| glm-5.3 | poolact | Tight | cached | gap_mi | 87.586956 | 86.326175 | 84.634604 | 1.481405 |
| glm-5.3 | poolact | Tight | cached | gap_bon | 97.310553 | 98.131415 | 88.204374 | 5.509725 |
| glm-5.3 | poolact | Tight | poolact | gap_mi | 96.015442 | 95.255042 | 97.259313 | 1.011807 |
| glm-5.3 | poolact | Tight | poolact | gap_bon | 98.309475 | 98.353883 | 98.725721 | 0.228581 |

## 场景级资源均值

以下均取同一分析单元的冻结遥测，再按 item/repeat 等权；不是整项 study 总账。Input/Output 为 token；reasoning 已包含于 Output，不能再相加。反馈秒是模拟工具反馈成本，不是 GPU 秒。Exp Audit 列为每文档三个 orders 的均值，不是三 orders 合计。

Pool input/output tokens、feedback成本/次数为四 agents 合计；Pool wall 是整个 pool 子进程实际 source_capture.elapsed_seconds，不是 agent wall 的 sum/max。Exp wall 为单 agent 实测（Audit再平均三个orders）。不能相加推导整个并行 study 实际耗时或 GPU-hour；总账另见主报告。每个 Pool 的 feedback_visible 原导出缺失，在 CSV 保留 unknown，未补零；本表展示可用的反馈尝试数。

Free 的反馈预算为无限且不展示成本，不意味着实际反馈成本为零。budget_utilization 保留在 CSV，有限预算下 Pool 为四 agents 总反馈成本/(4×单 agent 预算)；允许最后一次工具越界带来大于1的值。

| 模型 | 系统 | 场景 | 预算 | 策略 | Input tokens | Output tokens | 反馈秒 | 冻结 wall 秒 | 反馈尝试数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kimi-k3 | expgym | restricted_search | Free | single | 99545.136986 | 9387.739726 | 3631.827073 | 664.067277 | 14.054795 |
| kimi-k3 | expgym | restricted_search | Moderate | single | 43586.767123 | 7193.082192 | 2525.175439 | 523.515513 | 9.958904 |
| kimi-k3 | expgym | restricted_search | Tight | single | 6940.410959 | 2861.712329 | 1012.913496 | 203.157551 | 3.753425 |
| kimi-k3 | expgym | evidence_audit | Free | single | 366956.589744 | 16024.974359 | 8327.956221 | 1086.338041 | 27.717949 |
| kimi-k3 | expgym | evidence_audit | Moderate | single | 104462.025641 | 14751.871795 | 2844.170369 | 1017.687354 | 9.435897 |
| kimi-k3 | expgym | evidence_audit | Tight | single | 22878.307692 | 8032.512821 | 850.588274 | 571.388226 | 2.820513 |
| kimi-k3 | expgym | tuning | Free | single | 230295.592593 | 14047.407407 | 252387.797068 | 825.945845 | 23.666667 |
| kimi-k3 | expgym | tuning | Moderate | single | 57097.444444 | 8961.444444 | 96667.251220 | 493.495243 | 8.111111 |
| kimi-k3 | expgym | tuning | Tight | single | 21049.037037 | 6563.111111 | 36051.521950 | 382.524720 | 3.814815 |
| kimi-k3 | poolact | restricted_search | Moderate | naive | 171855.666667 | 24429.564103 | 9643.410741 | 670.684804 | 39.384615 |
| kimi-k3 | poolact | restricted_search | Moderate | cached | 193728.256410 | 25506.128205 | 8963.780838 | 636.872697 | 41.051282 |
| kimi-k3 | poolact | restricted_search | Moderate | poolact | 469631.333333 | 39232.923077 | 7673.324528 | 2785.353798 | 40.666667 |
| kimi-k3 | poolact | restricted_search | Tight | naive | 30428.615385 | 12059.948718 | 4109.480041 | 384.863589 | 15.461538 |
| kimi-k3 | poolact | restricted_search | Tight | cached | 35100.794872 | 13563.769231 | 4007.590673 | 468.324156 | 16.256410 |
| kimi-k3 | poolact | restricted_search | Tight | poolact | 73846.153846 | 17289.384615 | 3886.969286 | 1169.436990 | 17.461538 |
| kimi-k3 | poolact | evidence_audit | Moderate | naive | 435431.692308 | 59997.076923 | 11537.166336 | 1771.345564 | 38.307692 |
| kimi-k3 | poolact | evidence_audit | Moderate | cached | 506641.076923 | 59882.538462 | 10966.121039 | 1551.636591 | 43.846154 |
| kimi-k3 | poolact | evidence_audit | Moderate | poolact | 670641.692308 | 76833.461538 | 11228.417970 | 5380.948324 | 37.615385 |
| kimi-k3 | poolact | evidence_audit | Tight | naive | 94498.384615 | 36806.846154 | 3153.365251 | 1039.522642 | 10.461538 |
| kimi-k3 | poolact | evidence_audit | Tight | cached | 104495.000000 | 40671.076923 | 3219.343615 | 1207.165748 | 10.769231 |
| kimi-k3 | poolact | evidence_audit | Tight | poolact | 123983.153846 | 47385.307692 | 3507.503484 | 3396.817980 | 11.615385 |
| kimi-k3 | poolact | tuning | Moderate | naive | 519038.333333 | 67688.333333 | 322161.705777 | 1608.792329 | 39.222222 |
| kimi-k3 | poolact | tuning | Moderate | cached | 512309.777778 | 63995.888889 | 309297.951823 | 1398.424206 | 38.444444 |
| kimi-k3 | poolact | tuning | Moderate | poolact | 1118384.333333 | 88541.222222 | 268570.794532 | 5582.461858 | 32.888889 |
| kimi-k3 | poolact | tuning | Tight | naive | 113636.888889 | 34181.000000 | 109658.326131 | 800.030740 | 12.666667 |
| kimi-k3 | poolact | tuning | Tight | cached | 113071.888889 | 35135.888889 | 114140.534058 | 867.783888 | 12.666667 |
| kimi-k3 | poolact | tuning | Tight | poolact | 169065.666667 | 33587.333333 | 105743.352919 | 1758.332952 | 12.222222 |
| glm-5.3 | expgym | restricted_search | Free | single | 169909.917808 | 19600.808219 | 4126.073236 | 494.852681 | 16.863014 |
| glm-5.3 | expgym | restricted_search | Moderate | single | 67510.958904 | 19054.767123 | 2558.468748 | 481.319470 | 10.287671 |
| glm-5.3 | expgym | restricted_search | Tight | single | 14507.273973 | 9697.479452 | 1056.824892 | 244.842457 | 4.054795 |
| glm-5.3 | expgym | evidence_audit | Free | single | 899925.666667 | 49681.974359 | 7895.183171 | 1256.699367 | 26.307692 |
| glm-5.3 | expgym | evidence_audit | Moderate | single | 468084.230769 | 84948.794872 | 2935.049756 | 2134.877804 | 9.794872 |
| glm-5.3 | expgym | evidence_audit | Tight | single | 110772.923077 | 49455.769231 | 907.450009 | 1261.353119 | 3.025641 |
| glm-5.3 | expgym | tuning | Free | single | 274232.037037 | 14701.185185 | 346971.654252 | 374.648285 | 29.407407 |
| glm-5.3 | expgym | tuning | Moderate | single | 184063.444444 | 27606.629630 | 113814.763947 | 620.089671 | 10.629630 |
| glm-5.3 | expgym | tuning | Tight | single | 37732.703704 | 16316.370370 | 37035.891735 | 403.254350 | 3.666667 |
| glm-5.3 | poolact | restricted_search | Moderate | naive | 302391.282051 | 82204.641026 | 10017.152159 | 889.069421 | 41.025641 |
| glm-5.3 | poolact | restricted_search | Moderate | cached | 355575.743590 | 83759.102564 | 9200.367612 | 840.881999 | 44.512821 |
| glm-5.3 | poolact | restricted_search | Moderate | poolact | 1062983.717949 | 135370.948718 | 8433.958196 | 3376.654692 | 47.153846 |
| glm-5.3 | poolact | restricted_search | Tight | naive | 45893.282051 | 43355.051282 | 4168.844006 | 531.803013 | 16.230769 |
| glm-5.3 | poolact | restricted_search | Tight | cached | 69631.128205 | 46091.564103 | 4144.983991 | 566.510133 | 17.615385 |
| glm-5.3 | poolact | restricted_search | Tight | poolact | 240859.076923 | 88946.358974 | 4024.406994 | 2257.047684 | 20.410256 |
| glm-5.3 | poolact | evidence_audit | Moderate | naive | 1798701.769231 | 322716.615385 | 11668.482933 | 2641.934361 | 38.846154 |
| glm-5.3 | poolact | evidence_audit | Moderate | cached | 2465750.923077 | 352803.461538 | 10778.941689 | 2982.409317 | 47.076923 |
| glm-5.3 | poolact | evidence_audit | Moderate | poolact | 1828379.923077 | 287668.000000 | 11390.704547 | 7175.411588 | 38.384615 |
| glm-5.3 | poolact | evidence_audit | Tight | naive | 456518.538462 | 207078.538462 | 3584.775565 | 1825.328098 | 11.923077 |
| glm-5.3 | poolact | evidence_audit | Tight | cached | 490287.307692 | 211146.230769 | 3570.146708 | 1663.473940 | 12.384615 |
| glm-5.3 | poolact | evidence_audit | Tight | poolact | 422295.153846 | 231944.307692 | 3559.264010 | 5667.666078 | 11.846154 |
| glm-5.3 | poolact | tuning | Moderate | naive | 988802.111111 | 197910.666667 | 338082.847551 | 1745.712838 | 38.666667 |
| glm-5.3 | poolact | tuning | Moderate | cached | 1071169.666667 | 215092.777778 | 327973.409776 | 1772.964828 | 39.444444 |
| glm-5.3 | poolact | tuning | Moderate | poolact | 3115054.777778 | 322813.888889 | 318969.753086 | 7034.944031 | 43.666667 |
| glm-5.3 | poolact | tuning | Tight | naive | 369815.333333 | 133198.555556 | 113389.873281 | 1299.392815 | 13.888889 |
| glm-5.3 | poolact | tuning | Tight | cached | 244441.444444 | 87543.111111 | 117391.549025 | 965.025405 | 13.666667 |
| glm-5.3 | poolact | tuning | Tight | poolact | 457954.555556 | 130600.000000 | 107524.511929 | 2708.759140 | 15.555556 |

## 复算

```bash
python3.11 results/portable-eval-20260908/full_matrix_report_v1/aggregate_settings.py --output-dir /absolute/new-output-directory
```

脚本仅读取两份 final export 的 EXPORT_INDEX/manifest/metrics/effects 共8文件，核固定哈希；输出5个文件，已有文件拒绝覆盖。`--check` 只读比较当前5文件与重算字节。原 effects 的全部 baseline/target 与新绝对均值逐一核对：质量指标绝对容差 1e-12；资源指标相对/绝对容差均1e-12，以容纳大数两层浮点平均的末位舍入。null 也按原样匹配；该核对不是新独立评分或统计假设检验。
