# Gap0：未交付结果的数值比较补充

[主问题精简版](README.zh.md) · [完整历史详细报告](../README.zh.md) · [原始dump与完整索引](../ARCHIVE_INDEX.md)

## 指标与来源

这是本次用户请求下新增的回顾性交付效用，不重评分、不改写原严格端点。仅已执行、正常返回且缺最终配置的agent效用取0；已评分agent的原Gap不变，保留冻结legacy final-selection规则，Gap允许超过100。异常、未开始或缺失执行记录不会自动计零。

对池p：MI0 = Σ已交付成员Gap / 4；BoN0 = max({已交付成员Gap}∪{0})。先在每个item内平均原3个重复，再对item等权。三成员有结果的池保留这三人的贡献，不把全池作零；四人均缺配置的正常结束池才MI0=BoN0=0。后者不是把无法计算的原真实Gap补成零。

本研究的调优重复/N固定且均衡，因此MI0也能写成有效成员比例×已评分成员平均Gap；此恒等式仅描述本研究权重，不推广给不均衡任务，更不适用于BoN0。条件均值只看已评分成员，含选择偏差，不能作为完整端点或用它选择候选模型。

来源与投影字段：[GAP0_INPUTS.json](GAP0_INPUTS.json)。五份已有评分/终态CSV经显式字段投影后冻结于inputs，保存源SHA、源数据行号和投影SHA；不含回答正文。DeepSeek/GPT各135个调优执行单元、297名agent均校验身份和终态。另三个模型的原严格端点完整，按同一规则其Gap0等于原Gap；不重新访问其raw。

GPT缺失1名成员，终止原因为本地上下文上限。DeepSeek缺失92名，均为正常返回的missing configuration；原终态导出无更细loop终止原因，不推断其全部由context或输出长度引起。

## 全设置数值

原严格列中：ExpGym分母为单agent重复，Pool分母为四人全有效池；“成员有效”分母是agent，两者不同。条件成员Gap列始终为已评分agent平均，即使当前行展示BoN也不是条件BoN。原未知端点保持unknown，Gap0只在独立新列中展示。

| 模型 | 系统 | 范围 | 预算 | 策略 | 新指标 | 原严格指标 | Gap0 | 成员有效 | 全有效池 | 条件成员Gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Kimi | ExpGym | all | free | single | gap0 | 98.51 | 98.51 | 27/27 | — | 98.51 |
| Kimi | ExpGym | all | moderate | single | gap0 | 94.23 | 94.23 | 27/27 | — | 94.23 |
| Kimi | ExpGym | all | tight | single | gap0 | 89.68 | 89.68 | 27/27 | — | 89.68 |
| Kimi | ExpGym | nasbench101 | free | single | gap0 | 98.69 | 98.69 | 9/9 | — | 98.69 |
| Kimi | ExpGym | nasbench101 | moderate | single | gap0 | 97.86 | 97.86 | 9/9 | — | 97.86 |
| Kimi | ExpGym | nasbench101 | tight | single | gap0 | 94.97 | 94.97 | 9/9 | — | 94.97 |
| Kimi | ExpGym | nasbench201 | free | single | gap0 | 99.77 | 99.77 | 9/9 | — | 99.77 |
| Kimi | ExpGym | nasbench201 | moderate | single | gap0 | 97.08 | 97.08 | 9/9 | — | 97.08 |
| Kimi | ExpGym | nasbench201 | tight | single | gap0 | 94.66 | 94.66 | 9/9 | — | 94.66 |
| Kimi | ExpGym | paramnet | free | single | gap0 | 97.08 | 97.08 | 9/9 | — | 97.08 |
| Kimi | ExpGym | paramnet | moderate | single | gap0 | 87.76 | 87.76 | 9/9 | — | 87.76 |
| Kimi | ExpGym | paramnet | tight | single | gap0 | 79.42 | 79.42 | 9/9 | — | 79.42 |
| Kimi | Pool | all | moderate | cached | gap0_bon | 98.84 | 98.84 | 36/36 | 9/9 | 97.96 |
| Kimi | Pool | all | moderate | cached | gap0_mi | 97.96 | 97.96 | 36/36 | 9/9 | 97.96 |
| Kimi | Pool | all | moderate | naive | gap0_bon | 98.99 | 98.99 | 36/36 | 9/9 | 98.04 |
| Kimi | Pool | all | moderate | naive | gap0_mi | 98.04 | 98.04 | 36/36 | 9/9 | 98.04 |
| Kimi | Pool | all | moderate | poolact | gap0_bon | 98.87 | 98.87 | 36/36 | 9/9 | 98.56 |
| Kimi | Pool | all | moderate | poolact | gap0_mi | 98.56 | 98.56 | 36/36 | 9/9 | 98.56 |
| Kimi | Pool | all | tight | cached | gap0_bon | 98.37 | 98.37 | 36/36 | 9/9 | 94.11 |
| Kimi | Pool | all | tight | cached | gap0_mi | 94.11 | 94.11 | 36/36 | 9/9 | 94.11 |
| Kimi | Pool | all | tight | naive | gap0_bon | 97.99 | 97.99 | 36/36 | 9/9 | 94.26 |
| Kimi | Pool | all | tight | naive | gap0_mi | 94.26 | 94.26 | 36/36 | 9/9 | 94.26 |
| Kimi | Pool | all | tight | poolact | gap0_bon | 98.37 | 98.37 | 36/36 | 9/9 | 96.05 |
| Kimi | Pool | all | tight | poolact | gap0_mi | 96.05 | 96.05 | 36/36 | 9/9 | 96.05 |
| GLM | ExpGym | all | free | single | gap0 | 97.91 | 97.91 | 27/27 | — | 97.91 |
| GLM | ExpGym | all | moderate | single | gap0 | 96.15 | 96.15 | 27/27 | — | 96.15 |
| GLM | ExpGym | all | tight | single | gap0 | 86.07 | 86.07 | 27/27 | — | 86.07 |
| GLM | ExpGym | nasbench101 | free | single | gap0 | 99.06 | 99.06 | 9/9 | — | 99.06 |
| GLM | ExpGym | nasbench101 | moderate | single | gap0 | 97.74 | 97.74 | 9/9 | — | 97.74 |
| GLM | ExpGym | nasbench101 | tight | single | gap0 | 90.76 | 90.76 | 9/9 | — | 90.76 |
| GLM | ExpGym | nasbench201 | free | single | gap0 | 98.64 | 98.64 | 9/9 | — | 98.64 |
| GLM | ExpGym | nasbench201 | moderate | single | gap0 | 96.49 | 96.49 | 9/9 | — | 96.49 |
| GLM | ExpGym | nasbench201 | tight | single | gap0 | 88.04 | 88.04 | 9/9 | — | 88.04 |
| GLM | ExpGym | paramnet | free | single | gap0 | 96.04 | 96.04 | 9/9 | — | 96.04 |
| GLM | ExpGym | paramnet | moderate | single | gap0 | 94.24 | 94.24 | 9/9 | — | 94.24 |
| GLM | ExpGym | paramnet | tight | single | gap0 | 79.40 | 79.40 | 9/9 | — | 79.40 |
| GLM | Pool | all | moderate | cached | gap0_bon | 99.12 | 99.12 | 36/36 | 9/9 | 98.06 |
| GLM | Pool | all | moderate | cached | gap0_mi | 98.06 | 98.06 | 36/36 | 9/9 | 98.06 |
| GLM | Pool | all | moderate | naive | gap0_bon | 99.01 | 99.01 | 36/36 | 9/9 | 97.87 |
| GLM | Pool | all | moderate | naive | gap0_mi | 97.87 | 97.87 | 36/36 | 9/9 | 97.87 |
| GLM | Pool | all | moderate | poolact | gap0_bon | 99.38 | 99.38 | 36/36 | 9/9 | 98.97 |
| GLM | Pool | all | moderate | poolact | gap0_mi | 98.97 | 98.97 | 36/36 | 9/9 | 98.97 |
| GLM | Pool | all | tight | cached | gap0_bon | 94.55 | 94.55 | 36/36 | 9/9 | 86.18 |
| GLM | Pool | all | tight | cached | gap0_mi | 86.18 | 86.18 | 36/36 | 9/9 | 86.18 |
| GLM | Pool | all | tight | naive | gap0_bon | 93.81 | 93.81 | 36/36 | 9/9 | 83.96 |
| GLM | Pool | all | tight | naive | gap0_mi | 83.96 | 83.96 | 36/36 | 9/9 | 83.96 |
| GLM | Pool | all | tight | poolact | gap0_bon | 98.46 | 98.46 | 36/36 | 9/9 | 96.18 |
| GLM | Pool | all | tight | poolact | gap0_mi | 96.18 | 96.18 | 36/36 | 9/9 | 96.18 |
| Qwen | ExpGym | all | free | single | gap0 | 97.47 | 97.47 | 27/27 | — | 97.47 |
| Qwen | ExpGym | all | moderate | single | gap0 | 95.13 | 95.13 | 27/27 | — | 95.13 |
| Qwen | ExpGym | all | tight | single | gap0 | 85.71 | 85.71 | 27/27 | — | 85.71 |
| Qwen | ExpGym | nasbench101 | free | single | gap0 | 98.66 | 98.66 | 9/9 | — | 98.66 |
| Qwen | ExpGym | nasbench101 | moderate | single | gap0 | 96.51 | 96.51 | 9/9 | — | 96.51 |
| Qwen | ExpGym | nasbench101 | tight | single | gap0 | 93.82 | 93.82 | 9/9 | — | 93.82 |
| Qwen | ExpGym | nasbench201 | free | single | gap0 | 98.45 | 98.45 | 9/9 | — | 98.45 |
| Qwen | ExpGym | nasbench201 | moderate | single | gap0 | 93.94 | 93.94 | 9/9 | — | 93.94 |
| Qwen | ExpGym | nasbench201 | tight | single | gap0 | 85.45 | 85.45 | 9/9 | — | 85.45 |
| Qwen | ExpGym | paramnet | free | single | gap0 | 95.28 | 95.28 | 9/9 | — | 95.28 |
| Qwen | ExpGym | paramnet | moderate | single | gap0 | 94.95 | 94.95 | 9/9 | — | 94.95 |
| Qwen | ExpGym | paramnet | tight | single | gap0 | 77.87 | 77.87 | 9/9 | — | 77.87 |
| Qwen | Pool | all | moderate | cached | gap0_bon | 99.00 | 99.00 | 36/36 | 9/9 | 97.72 |
| Qwen | Pool | all | moderate | cached | gap0_mi | 97.72 | 97.72 | 36/36 | 9/9 | 97.72 |
| Qwen | Pool | all | moderate | naive | gap0_bon | 98.70 | 98.70 | 36/36 | 9/9 | 96.92 |
| Qwen | Pool | all | moderate | naive | gap0_mi | 96.92 | 96.92 | 36/36 | 9/9 | 96.92 |
| Qwen | Pool | all | moderate | poolact | gap0_bon | 99.15 | 99.15 | 36/36 | 9/9 | 98.87 |
| Qwen | Pool | all | moderate | poolact | gap0_mi | 98.87 | 98.87 | 36/36 | 9/9 | 98.87 |
| Qwen | Pool | all | tight | cached | gap0_bon | 98.15 | 98.15 | 36/36 | 9/9 | 90.76 |
| Qwen | Pool | all | tight | cached | gap0_mi | 90.76 | 90.76 | 36/36 | 9/9 | 90.76 |
| Qwen | Pool | all | tight | naive | gap0_bon | 98.52 | 98.52 | 36/36 | 9/9 | 90.62 |
| Qwen | Pool | all | tight | naive | gap0_mi | 90.62 | 90.62 | 36/36 | 9/9 | 90.62 |
| Qwen | Pool | all | tight | poolact | gap0_bon | 98.29 | 98.29 | 36/36 | 9/9 | 96.27 |
| Qwen | Pool | all | tight | poolact | gap0_mi | 96.27 | 96.27 | 36/36 | 9/9 | 96.27 |
| DeepSeek | ExpGym | all | free | single | gap0 | unknown (20/27) | 61.09 | 20/27 | — | 82.48 |
| DeepSeek | ExpGym | all | moderate | single | gap0 | unknown (25/27) | 74.02 | 25/27 | — | 79.94 |
| DeepSeek | ExpGym | all | tight | single | gap0 | unknown (25/27) | 75.81 | 25/27 | — | 81.87 |
| DeepSeek | ExpGym | nasbench101 | free | single | gap0 | unknown (7/9) | 60.10 | 7/9 | — | 77.27 |
| DeepSeek | ExpGym | nasbench101 | moderate | single | gap0 | 71.88 | 71.88 | 9/9 | — | 71.88 |
| DeepSeek | ExpGym | nasbench101 | tight | single | gap0 | 86.86 | 86.86 | 9/9 | — | 86.86 |
| DeepSeek | ExpGym | nasbench201 | free | single | gap0 | unknown (8/9) | 81.62 | 8/9 | — | 91.82 |
| DeepSeek | ExpGym | nasbench201 | moderate | single | gap0 | unknown (8/9) | 79.34 | 8/9 | — | 89.26 |
| DeepSeek | ExpGym | nasbench201 | tight | single | gap0 | 76.62 | 76.62 | 9/9 | — | 76.62 |
| DeepSeek | ExpGym | paramnet | free | single | gap0 | unknown (5/9) | 41.56 | 5/9 | — | 74.81 |
| DeepSeek | ExpGym | paramnet | moderate | single | gap0 | unknown (8/9) | 70.84 | 8/9 | — | 79.69 |
| DeepSeek | ExpGym | paramnet | tight | single | gap0 | unknown (7/9) | 63.94 | 7/9 | — | 82.21 |
| DeepSeek | Pool | all | moderate | cached | gap0_bon | unknown (3/9) | 64.13 | 25/36 | 3/9 | 56.61 |
| DeepSeek | Pool | all | moderate | cached | gap0_mi | unknown (3/9) | 39.31 | 25/36 | 3/9 | 56.61 |
| DeepSeek | Pool | all | moderate | naive | gap0_bon | unknown (1/9) | 44.40 | 21/36 | 1/9 | 40.16 |
| DeepSeek | Pool | all | moderate | naive | gap0_mi | unknown (1/9) | 23.43 | 21/36 | 1/9 | 40.16 |
| DeepSeek | Pool | all | moderate | poolact | gap0_bon | unknown (1/9) | 51.26 | 19/36 | 1/9 | 44.59 |
| DeepSeek | Pool | all | moderate | poolact | gap0_mi | unknown (1/9) | 23.53 | 19/36 | 1/9 | 44.59 |
| DeepSeek | Pool | all | tight | cached | gap0_bon | unknown (1/9) | 65.22 | 23/36 | 1/9 | 36.09 |
| DeepSeek | Pool | all | tight | cached | gap0_mi | unknown (1/9) | 23.06 | 23/36 | 1/9 | 36.09 |
| DeepSeek | Pool | all | tight | naive | gap0_bon | unknown (2/9) | 57.90 | 24/36 | 2/9 | 43.01 |
| DeepSeek | Pool | all | tight | naive | gap0_mi | unknown (2/9) | 28.68 | 24/36 | 2/9 | 43.01 |
| DeepSeek | Pool | all | tight | poolact | gap0_bon | unknown (2/9) | 91.33 | 23/36 | 2/9 | 74.99 |
| DeepSeek | Pool | all | tight | poolact | gap0_mi | unknown (2/9) | 47.91 | 23/36 | 2/9 | 74.99 |
| GPT (medium) | ExpGym | all | free | single | gap0 | 97.97 | 97.97 | 27/27 | — | 97.97 |
| GPT (medium) | ExpGym | all | moderate | single | gap0 | 96.61 | 96.61 | 27/27 | — | 96.61 |
| GPT (medium) | ExpGym | all | tight | single | gap0 | 91.66 | 91.66 | 27/27 | — | 91.66 |
| GPT (medium) | ExpGym | nasbench101 | free | single | gap0 | 98.38 | 98.38 | 9/9 | — | 98.38 |
| GPT (medium) | ExpGym | nasbench101 | moderate | single | gap0 | 98.32 | 98.32 | 9/9 | — | 98.32 |
| GPT (medium) | ExpGym | nasbench101 | tight | single | gap0 | 97.03 | 97.03 | 9/9 | — | 97.03 |
| GPT (medium) | ExpGym | nasbench201 | free | single | gap0 | 98.23 | 98.23 | 9/9 | — | 98.23 |
| GPT (medium) | ExpGym | nasbench201 | moderate | single | gap0 | 96.24 | 96.24 | 9/9 | — | 96.24 |
| GPT (medium) | ExpGym | nasbench201 | tight | single | gap0 | 92.26 | 92.26 | 9/9 | — | 92.26 |
| GPT (medium) | ExpGym | paramnet | free | single | gap0 | 97.31 | 97.31 | 9/9 | — | 97.31 |
| GPT (medium) | ExpGym | paramnet | moderate | single | gap0 | 95.27 | 95.27 | 9/9 | — | 95.27 |
| GPT (medium) | ExpGym | paramnet | tight | single | gap0 | 85.69 | 85.69 | 9/9 | — | 85.69 |
| GPT (medium) | Pool | all | moderate | cached | gap0_bon | 98.80 | 98.80 | 36/36 | 9/9 | 98.28 |
| GPT (medium) | Pool | all | moderate | cached | gap0_mi | 98.28 | 98.28 | 36/36 | 9/9 | 98.28 |
| GPT (medium) | Pool | all | moderate | naive | gap0_bon | 98.70 | 98.70 | 36/36 | 9/9 | 98.21 |
| GPT (medium) | Pool | all | moderate | naive | gap0_mi | 98.21 | 98.21 | 36/36 | 9/9 | 98.21 |
| GPT (medium) | Pool | all | moderate | poolact | gap0_bon | unknown (8/9) | 98.89 | 35/36 | 8/9 | 98.31 |
| GPT (medium) | Pool | all | moderate | poolact | gap0_mi | unknown (8/9) | 95.58 | 35/36 | 8/9 | 98.31 |
| GPT (medium) | Pool | all | tight | cached | gap0_bon | 98.30 | 98.30 | 36/36 | 9/9 | 96.05 |
| GPT (medium) | Pool | all | tight | cached | gap0_mi | 96.05 | 96.05 | 36/36 | 9/9 | 96.05 |
| GPT (medium) | Pool | all | tight | naive | gap0_bon | 98.20 | 98.20 | 36/36 | 9/9 | 96.64 |
| GPT (medium) | Pool | all | tight | naive | gap0_mi | 96.64 | 96.64 | 36/36 | 9/9 | 96.64 |
| GPT (medium) | Pool | all | tight | poolact | gap0_bon | 98.08 | 98.08 | 36/36 | 9/9 | 97.27 |
| GPT (medium) | Pool | all | tight | poolact | gap0_mi | 97.27 | 97.27 | 36/36 | 9/9 | 97.27 |

## 文件与重建

- [gap0_settings.csv](gap0_settings.csv)：完整原值、新效用、成员/池分母、条件均值。
- [missing_output_summary.csv](missing_output_summary.csv)：配置缺失、其他异常、终止原因的设置级计数，不含task/question ID。
- [GAP0_CHECKS.json](GAP0_CHECKS.json)：有限输入与聚合检查；[gap0.py](gap0.py)及[test_gap0.py](test_gap0.py)为生成器和窄测试。
- [build_summary.py](build_summary.py)与[test_summary.py](test_summary.py)：三主问题数据和展示适配；[SUMMARY_CHECKS.json](SUMMARY_CHECKS.json)绑定父报告与本版输入。

在本目录、CPython3.11.15下执行 `python3 -B gap0.py --check` 和 `python3 -B build_summary.py --check`。前者从冻结投影重建数值；父报告absolute_settings.csv须保留原相对位置与SHA。重建摘要不等于重新验证原模型回复的评分正确性，也不证明本次观察具有统计显著性。
