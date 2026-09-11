# 五模型任务 × 预算观察排名

排名仅使用同一端点、同一预算的原指标，先在每个端点固定 F/M/T 三档均完整的候选集，不按每档已知结果动态增减模型。原计划五模型的所有原值、分母及排除原因保留在 [RANKINGS.csv](RANKINGS.csv)。HPO 缺失模型不补零、不用已知子集均值参与完整端点排名；排除后第一仅是该固定候选集内的观察第一。并列按未舍入分数与本组最高分 anchor 的绝对差 ≤1e-12，不使用相邻分数传递链；这是浮点等分规则，不是统计等价。名次采用 competition rank（1、2、2、4）。runner-up margin 为第一与第二个候选的分数差；并列第一记 0，不用它声称显著性。

六类家族主端点的固定完整候选排名中，Free→Tight 冠军集合换位 **2/6**（计划 6 个端点）；严格五模型全三档完整的家族子集为 **1/3**。九个 HPO task 的对应计数为 **7/9**（计划 9 个），严格五模型子集为 **1/2**。分子比较 Free 与 Tight 的冠军集合，不把 Moderate 暂时并列混入；Search/HPO all 与 Audit LA 只作次级展示，不再加入这些分母。

在五模型全完整的家族中，Free；Moderate；Tight 都不存在跨家族共同第一名。这里考察部署反馈预算程度（deployment budget degree）下的相对表现：整体排序和局部冠军是否随任务、预算变化，而不是构造跨指标总榜。观察换位不意味着每个家族都会换位，也不是不同 effort、API/自部署设置已受控的纯模型因果排名。

## 家族主端点

| 端点 | 三档固定完整候选 | Free 观察第一 | Moderate 观察第一 | Tight 观察第一 | Free→Tight |
| --- | --- | --- | --- | --- | --- |
| Search whois / F1 | Kimi / GLM / Qwen / DeepSeek / GPT | GLM 0.682651 | GLM 0.642842 | GLM 0.230575 | 不变 |
| Search whatis / F1 | Kimi / GLM / Qwen / DeepSeek / GPT | GPT 0.654206 | GPT 0.453877 | DeepSeek 0.159269 | 换位 |
| Audit / EA | Kimi / GLM / Qwen / DeepSeek / GPT | Qwen 0.918552 | Qwen 0.749623 | Qwen 0.583710 | 不变 |
| ParamNet / Gap | Kimi / GLM / Qwen / GPT | GPT 97.312330 | GPT 95.271826 | GPT 85.694084 | 不变 |
| NAS101 / Gap | Kimi / GLM / Qwen / GPT | GLM 99.057476 | GPT 98.324002 | GPT 97.030843 | 换位 |
| NAS201 / Gap | Kimi / GLM / Qwen / GPT | Kimi 99.770835 | Kimi 97.076629 | Kimi 94.660569 | 不变 |

| 端点 | Free 完整排序 | Moderate 完整排序 | Tight 完整排序 |
| --- | --- | --- | --- |
| Search whois / F1 | GLM > Kimi > Qwen > GPT > DeepSeek | GLM > Qwen > GPT > Kimi > DeepSeek | GLM > Qwen > DeepSeek > GPT = Kimi |
| Search whatis / F1 | GPT > GLM > Kimi > Qwen > DeepSeek | GPT > Kimi > GLM > Qwen > DeepSeek | DeepSeek > GLM > Kimi > GPT > Qwen |
| Audit / EA | Qwen > Kimi > GPT > GLM > DeepSeek | Qwen > Kimi > GLM > GPT > DeepSeek | Qwen > GPT > Kimi > GLM > DeepSeek |
| ParamNet / Gap | GPT > Kimi > GLM > Qwen | GPT > Qwen > GLM > Kimi | GPT > Kimi > GLM > Qwen |
| NAS101 / Gap | GLM > Kimi > Qwen > GPT | GPT > Kimi > GLM > Qwen | GPT > Kimi > Qwen > GLM |
| NAS201 / Gap | Kimi > GLM > Qwen > GPT | Kimi > GLM > GPT > Qwen | Kimi > GPT > GLM > Qwen |

第一与第二候选的未标准化分差（F1/EA/LA 为 fraction，Gap 为 Gap points）：

| 端点 | Free margin | Moderate margin | Tight margin |
| --- | --- | --- | --- |
| Search whois / F1 | 0.023789 | 0.031559 | 0.004884 |
| Search whatis / F1 | 0.039291 | 0.045843 | 0.010784 |
| Audit / EA | 0.024133 | 0.061840 | 0.042232 |
| ParamNet / Gap | 0.236447 | 0.319132 | 6.271601 |
| NAS101 / Gap | 0.365462 | 0.466821 | 2.062745 |
| NAS201 / Gap | 1.133670 | 0.589777 | 2.402708 |

## 九个 HPO task

| 端点 | 三档固定完整候选 | Free 观察第一 | Moderate 观察第一 | Tight 观察第一 | Free→Tight |
| --- | --- | --- | --- | --- | --- |
| NAS101 A | Kimi / GLM / Qwen / GPT | Qwen 99.580753 | GLM 99.003299 | GPT 96.614377 | 换位 |
| NAS101 B | Kimi / GLM / Qwen / DeepSeek / GPT | GLM 97.969343 | GLM 97.467138 | Kimi 95.759638 | 换位 |
| NAS101 C | Kimi / GLM / Qwen / GPT | GLM 99.623912 | GPT 98.997748 | GPT 99.015472 | 换位 |
| NAS201 cifar10-valid | Kimi / GLM / Qwen / GPT | Kimi 100.000000 | GPT 98.855387 | GPT 97.654940 | 换位 |
| NAS201 cifar100 | Kimi / GLM / Qwen / DeepSeek / GPT | Kimi 100.000000 | Kimi 100.000000; Qwen 100.000000 | Kimi 97.479188 | 不变 |
| NAS201 imagenet16-120 | Kimi / GLM / Qwen / GPT | Kimi 99.312504 | Kimi 97.572717 | Kimi 96.295938 | 不变 |
| ParamNet adult | Kimi / GLM / Qwen / GPT | GPT 97.939423 | GLM 95.414265 | Kimi 77.355993 | 换位 |
| ParamNet higgs | Kimi / GLM / Qwen / GPT | GLM 95.829008 | GPT 97.146907 | GPT 89.704134 | 换位 |
| ParamNet letter | Kimi / GLM / Qwen / GPT | Kimi 99.221702 | Qwen 98.885684 | GPT 95.364674 | 换位 |

| 端点 | Free 完整排序 | Moderate 完整排序 | Tight 完整排序 |
| --- | --- | --- | --- |
| NAS101 A | Qwen > GLM > GPT > Kimi | GLM > GPT > Qwen > Kimi | GPT > Kimi > Qwen > GLM |
| NAS101 B | GLM > Kimi > Qwen > GPT > DeepSeek | GLM > GPT > Kimi > Qwen > DeepSeek | Kimi > GPT > Qwen > GLM > DeepSeek |
| NAS101 C | GLM > Kimi > GPT > Qwen | GPT > Kimi > Qwen > GLM | GPT > Kimi > Qwen > GLM |
| NAS201 cifar10-valid | Kimi > GPT > GLM > Qwen | GPT > GLM > Kimi > Qwen | GPT > Qwen > GLM > Kimi |
| NAS201 cifar100 | Kimi > GLM > GPT > Qwen > DeepSeek | Kimi = Qwen > GLM > GPT > DeepSeek | Kimi > GPT > DeepSeek > GLM > Qwen |
| NAS201 imagenet16-120 | Kimi > Qwen > GLM > GPT | Kimi > GLM > GPT > Qwen | Kimi > GPT > GLM > Qwen |
| ParamNet adult | GPT > Kimi > GLM > Qwen | GLM > Qwen > GPT > Kimi | Kimi > Qwen > GLM = GPT |
| ParamNet higgs | GLM > GPT > Kimi > Qwen | GPT > Qwen > GLM > Kimi | GPT > GLM > Kimi > Qwen |
| ParamNet letter | Kimi > GPT > Qwen > GLM | Qwen > GPT > GLM > Kimi | GPT > Kimi > Qwen > GLM |

第一与第二候选的未标准化分差（F1/EA/LA 为 fraction，Gap 为 Gap points）：

| 端点 | Free margin | Moderate margin | Tight margin |
| --- | --- | --- | --- |
| NAS101 A | 0.001581 | 0.124982 | 6.097286 |
| NAS101 B | 0.515308 | 0.371198 | 0.296957 |
| NAS101 C | 0.259918 | 0.090576 | 0.387905 |
| NAS201 cifar10-valid | 0.223339 | 4.974878 | 1.194864 |
| NAS201 cifar100 | 0.828137 | 0.000000 | 2.211399 |
| NAS201 imagenet16-120 | 0.911985 | 1.164535 | 12.445085 |
| ParamNet adult | 0.082429 | 3.431823 | 0.434597 |
| ParamNet higgs | 1.015808 | 3.156951 | 11.389405 |
| ParamNet letter | 0.037335 | 1.143036 | 1.132984 |

## 次级端点：不加入家族/task 换位分母

| 端点 | 三档固定完整候选 | Free 观察第一 | Moderate 观察第一 | Tight 观察第一 | Free→Tight |
| --- | --- | --- | --- | --- | --- |
| Search all / F1 | Kimi / GLM / Qwen / DeepSeek / GPT | GLM 0.651102 | GLM 0.532761 | GLM 0.192341 | 不变 |
| HPO all / Gap | Kimi / GLM / Qwen / GPT | Kimi 98.512910 | GPT 96.611095 | GPT 91.660929 | 换位 |
| Audit / LA（次指标） | Kimi / GLM / Qwen / DeepSeek / GPT | Qwen 0.947210 | Qwen 0.882353 | Qwen 0.831071 | 不变 |

| 端点 | Free 完整排序 | Moderate 完整排序 | Tight 完整排序 |
| --- | --- | --- | --- |
| Search all / F1 | GLM > GPT > Kimi > Qwen > DeepSeek | GLM > GPT > Qwen > Kimi > DeepSeek | GLM > Qwen > DeepSeek > Kimi > GPT |
| HPO all / Gap | Kimi > GPT > GLM > Qwen | GPT > GLM > Qwen > Kimi | GPT > Kimi > GLM > Qwen |
| Audit / LA（次指标） | Qwen > Kimi > GPT > GLM > DeepSeek | Qwen > GPT > Kimi > GLM > DeepSeek | Qwen > Kimi > GPT > GLM > DeepSeek |

第一与第二候选的未标准化分差（F1/EA/LA 为 fraction，Gap 为 Gap points）：

| 端点 | Free margin | Moderate margin | Tight margin |
| --- | --- | --- | --- |
| Search all / F1 | 0.010989 | 0.002161 | 0.007632 |
| HPO all / Gap | 0.539675 | 0.456535 | 1.977212 |
| Audit / LA（次指标） | 0.021116 | 0.003017 | 0.036199 |

## 所有原计划模型：原值与分母（不完整的值不进入排名）

### Search whois / F1

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 0.658862 [39/39] | 0.573004 [39/39] | 0.170136 [39/39] | 三档固定候选 |
| GLM | 0.682651 [39/39] | 0.642842 [39/39] | 0.230575 [39/39] | 三档固定候选 |
| Qwen | 0.641102 [39/39] | 0.611283 [39/39] | 0.225691 [39/39] | 三档固定候选 |
| DeepSeek | 0.498341 [39/39] | 0.497486 [39/39] | 0.177828 [39/39] | 三档固定候选 |
| GPT | 0.627828 [39/39] | 0.597486 [39/39] | 0.170136 [39/39] | 三档固定候选 |

### Search whatis / F1

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 0.609584 [34/34] | 0.408034 [34/34] | 0.143137 [34/34] | 三档固定候选 |
| GLM | 0.614914 [34/34] | 0.406491 [34/34] | 0.148485 [34/34] | 三档固定候选 |
| Qwen | 0.513103 [34/34] | 0.393451 [34/34] | 0.137701 [34/34] | 三档固定候选 |
| DeepSeek | 0.369073 [34/34] | 0.333516 [34/34] | 0.159269 [34/34] | 三档固定候选 |
| GPT | 0.654206 [34/34] | 0.453877 [34/34] | 0.138681 [34/34] | 三档固定候选 |

### Audit / EA

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 0.894419 [13/13] | 0.687783 [13/13] | 0.515837 [13/13] | 三档固定候选 |
| GLM | 0.684766 [13/13] | 0.678733 [13/13] | 0.502262 [13/13] | 三档固定候选 |
| Qwen | 0.918552 [13/13] | 0.749623 [13/13] | 0.583710 [13/13] | 三档固定候选 |
| DeepSeek | 0.639517 [13/13] | 0.586727 [13/13] | 0.475113 [13/13] | 三档固定候选 |
| GPT | 0.704374 [13/13] | 0.659125 [13/13] | 0.541478 [13/13] | 三档固定候选 |

### ParamNet / Gap

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 97.075883 [9/9] | 87.756501 [9/9] | 79.422483 [9/9] | 三档固定候选 |
| GLM | 96.038788 [9/9] | 94.240269 [9/9] | 79.401892 [9/9] | 三档固定候选 |
| Qwen | 95.282291 [9/9] | 94.952694 [9/9] | 77.865845 [9/9] | 三档固定候选 |
| DeepSeek | unknown [5/9] | unknown [8/9] | unknown [7/9] | 完整端点缺失：Free/Moderate/Tight |
| GPT | 97.312330 [9/9] | 95.271826 [9/9] | 85.694084 [9/9] | 三档固定候选 |

### NAS101 / Gap

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 98.692013 [9/9] | 97.857181 [9/9] | 94.968099 [9/9] | 三档固定候选 |
| GLM | 99.057476 [9/9] | 97.736559 [9/9] | 90.761443 [9/9] | 三档固定候选 |
| Qwen | 98.661766 [9/9] | 96.510997 [9/9] | 93.815152 [9/9] | 三档固定候选 |
| DeepSeek | unknown [7/9] | 71.877135 [9/9] | 86.864351 [9/9] | 完整端点缺失：Free |
| GPT | 98.377842 [9/9] | 98.324002 [9/9] | 97.030843 [9/9] | 三档固定候选 |

### NAS201 / Gap

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 99.770835 [9/9] | 97.076629 [9/9] | 94.660569 [9/9] | 三档固定候选 |
| GLM | 98.637164 [9/9] | 96.486852 [9/9] | 88.037331 [9/9] | 三档固定候选 |
| Qwen | 98.451560 [9/9] | 93.936417 [9/9] | 85.448973 [9/9] | 三档固定候选 |
| DeepSeek | unknown [8/9] | unknown [8/9] | 76.621201 [9/9] | 完整端点缺失：Free/Moderate |
| GPT | 98.229532 [9/9] | 96.237458 [9/9] | 92.257861 [9/9] | 三档固定候选 |

### NAS101 A

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 99.258011 [3/3] | 98.079371 [3/3] | 90.517091 [3/3] | 三档固定候选 |
| GLM | 99.579172 [3/3] | 99.003299 [3/3] | 85.756650 [3/3] | 三档固定候选 |
| Qwen | 99.580753 [3/3] | 98.190116 [3/3] | 89.675431 [3/3] | 三档固定候选 |
| DeepSeek | unknown [2/3] | 64.140107 [3/3] | 90.121573 [3/3] | 完整端点缺失：Free |
| GPT | 99.436785 [3/3] | 98.878317 [3/3] | 96.614377 [3/3] | 三档固定候选 |

### NAS101 B

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 97.454035 [3/3] | 96.585000 [3/3] | 95.759638 [3/3] | 三档固定候选 |
| GLM | 97.969343 [3/3] | 97.467138 [3/3] | 89.995192 [3/3] | 三档固定候选 |
| Qwen | 97.113406 [3/3] | 92.650329 [3/3] | 93.270448 [3/3] | 三档固定候选 |
| DeepSeek | 86.802912 [3/3] | 57.666268 [3/3] | 85.178388 [3/3] | 三档固定候选 |
| GPT | 96.362283 [3/3] | 97.095939 [3/3] | 95.462681 [3/3] | 三档固定候选 |

### NAS101 C

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 99.363994 [3/3] | 98.907173 [3/3] | 98.627567 [3/3] | 三档固定候选 |
| GLM | 99.623912 [3/3] | 96.739239 [3/3] | 96.532487 [3/3] | 三档固定候选 |
| Qwen | 99.291139 [3/3] | 98.692546 [3/3] | 98.499576 [3/3] | 三档固定候选 |
| DeepSeek | unknown [2/3] | 93.825030 [3/3] | 85.293093 [3/3] | 完整端点缺失：Free |
| GPT | 99.334460 [3/3] | 98.997748 [3/3] | 99.015472 [3/3] | 三档固定候选 |

### NAS201 cifar10-valid

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 100.000000 [3/3] | 93.657170 [3/3] | 90.206581 [3/3] | 三档固定候选 |
| GLM | 99.391401 [3/3] | 93.880509 [3/3] | 93.657170 [3/3] | 三档固定候选 |
| Qwen | 99.302065 [3/3] | 93.216075 [3/3] | 96.460076 [3/3] | 三档固定候选 |
| DeepSeek | unknown [2/3] | 86.130643 [3/3] | 82.311545 [3/3] | 完整端点缺失：Free |
| GPT | 99.776661 [3/3] | 98.855387 [3/3] | 97.654940 [3/3] | 三档固定候选 |

### NAS201 cifar100

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 100.000000 [3/3] | 100.000000 [3/3] | 97.479188 [3/3] | 三档固定候选 |
| GLM | 99.171863 [3/3] | 99.171863 [3/3] | 90.981498 [3/3] | 三档固定候选 |
| Qwen | 97.652095 [3/3] | 100.000000 [3/3] | 90.080558 [3/3] | 三档固定候选 |
| DeepSeek | 94.248544 [3/3] | 87.914661 [3/3] | 90.990598 [3/3] | 三档固定候选 |
| GPT | 98.307325 [3/3] | 94.248544 [3/3] | 95.267789 [3/3] | 三档固定候选 |

### NAS201 imagenet16-120

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 99.312504 [3/3] | 97.572717 [3/3] | 96.295938 [3/3] | 三档固定候选 |
| GLM | 97.348228 [3/3] | 96.408183 [3/3] | 79.473326 [3/3] | 三档固定候选 |
| Qwen | 98.400519 [3/3] | 88.593174 [3/3] | 69.806286 [3/3] | 三档固定候选 |
| DeepSeek | 89.841892 [3/3] | unknown [2/3] | 56.561461 [3/3] | 完整端点缺失：Moderate |
| GPT | 96.604610 [3/3] | 95.608442 [3/3] | 83.850853 [3/3] | 三档固定候选 |

### ParamNet adult

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 97.856995 [3/3] | 87.329255 [3/3] | 77.355993 [3/3] | 三档固定候选 |
| GLM | 95.601586 [3/3] | 95.414265 [3/3] | 72.013444 [3/3] | 三档固定候选 |
| Qwen | 94.590022 [3/3] | 91.982442 [3/3] | 76.921396 [3/3] | 三档固定候选 |
| DeepSeek | unknown [2/3] | 87.366726 [3/3] | unknown [2/3] | 完整端点缺失：Free/Tight |
| GPT | 97.939423 [3/3] | 90.925923 [3/3] | 72.013444 [3/3] | 三档固定候选 |

### ParamNet higgs

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 94.148953 [3/3] | 89.082285 [3/3] | 66.679766 [3/3] | 三档固定候选 |
| GLM | 95.829008 [3/3] | 92.269269 [3/3] | 78.314729 [3/3] | 三档固定候选 |
| Qwen | 93.995253 [3/3] | 93.989956 [3/3] | 65.533231 [3/3] | 三档固定候选 |
| DeepSeek | unknown [2/3] | 92.657927 [3/3] | unknown [2/3] | 完整端点缺失：Free/Tight |
| GPT | 94.813201 [3/3] | 97.146907 [3/3] | 89.704134 [3/3] | 三档固定候选 |

### ParamNet letter

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 99.221702 [3/3] | 86.857961 [3/3] | 94.231691 [3/3] | 三档固定候选 |
| GLM | 96.685771 [3/3] | 95.037272 [3/3] | 87.877503 [3/3] | 三档固定候选 |
| Qwen | 97.261597 [3/3] | 98.885684 [3/3] | 91.142909 [3/3] | 三档固定候选 |
| DeepSeek | unknown [1/3] | unknown [2/3] | 82.366233 [3/3] | 完整端点缺失：Free/Moderate |
| GPT | 99.184367 [3/3] | 97.742648 [3/3] | 95.364674 [3/3] | 三档固定候选 |

### Search all / F1

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 0.635911 [73/73] | 0.496169 [73/73] | 0.157561 [73/73] | 三档固定候选 |
| GLM | 0.651102 [73/73] | 0.532761 [73/73] | 0.192341 [73/73] | 三档固定候选 |
| Qwen | 0.581486 [73/73] | 0.509827 [73/73] | 0.184709 [73/73] | 三档固定候选 |
| DeepSeek | 0.438134 [73/73] | 0.421117 [73/73] | 0.169184 [73/73] | 三档固定候选 |
| GPT | 0.640114 [73/73] | 0.530600 [73/73] | 0.155486 [73/73] | 三档固定候选 |

### HPO all / Gap

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 98.512910 [27/27] | 94.230104 [27/27] | 89.683717 [27/27] | 三档固定候选 |
| GLM | 97.911143 [27/27] | 96.154560 [27/27] | 86.066889 [27/27] | 三档固定候选 |
| Qwen | 97.465205 [27/27] | 95.133369 [27/27] | 85.709990 [27/27] | 三档固定候选 |
| DeepSeek | unknown [20/27] | unknown [25/27] | unknown [25/27] | 完整端点缺失：Free/Moderate/Tight |
| GPT | 97.973235 [27/27] | 96.611095 [27/27] | 91.660929 [27/27] | 三档固定候选 |

### Audit / LA（次指标）

| 模型 | Free [known/expected] | Moderate [known/expected] | Tight [known/expected] | 固定候选状态 |
| --- | --- | --- | --- | --- |
| Kimi | 0.926094 [13/13] | 0.853695 [13/13] | 0.794872 [13/13] | 三档固定候选 |
| GLM | 0.692308 [13/13] | 0.760181 [13/13] | 0.736048 [13/13] | 三档固定候选 |
| Qwen | 0.947210 [13/13] | 0.882353 [13/13] | 0.831071 [13/13] | 三档固定候选 |
| DeepSeek | 0.668175 [13/13] | 0.755656 [13/13] | 0.702866 [13/13] | 三档固定候选 |
| GPT | 0.859729 [13/13] | 0.879336 [13/13] | 0.787330 [13/13] | 三档固定候选 |

数据为观察排名，不产生 p 值、显著性或跨指标统一总分。来源行和固定链接见 RANKINGS.csv；完整冠军集合转换见 RANK_TRANSITIONS.csv。
