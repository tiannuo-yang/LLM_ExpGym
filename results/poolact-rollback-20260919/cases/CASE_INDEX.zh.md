# 固定案例与新评分

原稿案例作为固定解释性样例保留；新主分数与全部代表候选另行重算，不以最大分差重新选例。[四个单体端点与来源 SHA](fixed_case_scores.csv)。

## Search query diversity

Qwen，phantom_seed2 第 31 题。Free 的前四个不同查询返回同一文章，16 次可见反馈覆盖 11 篇不同文章。新评分 Free F1=0.333333333333，Tight F1=0.333333333333。该例解释动作字符串不同不等于观测不同；不是额外预算必然提升的因果证据。[全量候选规则与新代表索引](../search/representative_case_index.csv)。

## HPO delivery

DeepSeek，NAS101 C，seed 2208。保留同一 Free/Tight 槽位，新 Gap0 为 0 / 91.1569504881，严格分数状态为 False / True。原可见评估与停止事件保存在完整 486 行为导出中，获取和交付不能混为一谈。[27 对交付变化](deepseek_paired_delivery.csv)。

## Audit evidence completion and PoolAct coverage sharing

Qwen 文档 10、顺序 1、nda-13 和 Kimi Moderate 审计文档 3 的完整新旧证据、投票、候选 membership 与总体配对数由 [Audit 全量重算](../audit/README.zh.md)核验。原始动作历史与可见共享消息不因离线新评分而改写。
