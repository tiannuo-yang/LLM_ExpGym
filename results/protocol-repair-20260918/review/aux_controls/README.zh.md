# Search / Audit 与 Whois sweep 的终答控制流补跑审计

本包记录 **22 个完整槽、79 条成员轨迹**的补跑选择与执行前独立核验：主实验21槽，另有GLM Whois β=20 sweep 1槽。原模型在中间轮已经给出新规则能接受的终答，旧 parser 却继续交互，因此不能只重新评分旧终态来冒充新 runtime 的行为。选择依据是确定性的控制流差异；不按旧分数筛选，也不拼接单个池成员。

本包是版本、设置与等价证明，不是完成状态或新成绩表。实际补跑结果和正式采用关系见同次发布的 results/analysis 数据；失败保留，不以自动重采样追求更高分。

| 模型 | 范围 | 槽/成员 | 实际历史 source-tree | 新 source-tree / 提交 |
|---|---|---:|---|---|
| Qwen | 主实验 Audit 11槽、Search 1槽；含2个N1、10个N4 | 12 / 42 | `58f8663d…` | `cb2fe024…` / `ffca570…` |
| DeepSeek | 主实验 Audit Moderate PoolAct | 9 / 36 | `e9657547…` | `4f28d240…` / `885a5bd…` |
| GLM | Whois β=20、phantom_seed2第5题，独立 sweep N1 | 1 / 1 | `a7d5db96…` | `cb2fe024…` / `ffca570…` |

完整选择和旧槽到新 job 的固定映射在 [SELECTION.csv](SELECTION.csv)。[SCIENTIFIC_SETTINGS.json](SCIENTIFIC_SETTINGS.json) 保留每槽的新旧科学设置白名单：生成参数、实际 seed/order/rep、上下文和步数上限、预算、工具协议、任务和输入哈希、缓存隔离语义、重试参数及代码身份。没有复制原完整 config、内部 endpoint、credential、raw trace、完整 prompt 或 serving 启动配置。

Qwen 两个 N1 的原顺序/重复为 rep=1、2，对应 seed=2201、2202，按原选择器编译后精确选取原槽；没有把它们改成 rep=0。N1 原上下文上限未设置，N4为131072，均按原值保留。GLM sweep 原β20预算6000秒、seed2200、rep0及 provider prompt cache disabled 均保留，该槽不重复计入主实验。

## 统一修复核心与 DeepSeek 的历史 prompt

共同修复核心提交为 [0e6c51b6d86f42437038518c2fc8adc510901c0b](https://github.com/tiannuo-yang/LLM_ExpGym/commit/0e6c51b6d86f42437038518c2fc8adc510901c0b)。Qwen/GLM使用冻结运行包 [ffca5704580b75e254f6e52dd4fe9dff104b1be8](https://github.com/tiannuo-yang/LLM_ExpGym/commit/ffca5704580b75e254f6e52dd4fe9dff104b1be8)；DeepSeek使用独立运行快照 [885a5bd70dffe02b8dd610f1699e9f675da2b926](https://github.com/tiannuo-yang/LLM_ExpGym/commit/885a5bd70dffe02b8dd610f1699e9f675da2b926)。完整SHA与计划绑定在 [CODE_FREEZE.json](CODE_FREEZE.json)。

独立检查发现，DeepSeek原先实际采用的v4 Audit prompt已去除固定 `nda-11 / [3,7]` 工具调用示例，改为让模型依据当前文档选择验证。通用运行包继承了Qwen/Gemini历史v3中的固定示例。直接拿通用包补DeepSeek，会额外改变任务提示。

因此DeepSeek快照只把 `task_evidence_audit._build_context` 恢复为其历史函数字节；新终答、评分、投票、graph核心均保留。117个普通文件中只有该模块变化，去掉该函数后模块AST相同，其余文件字节相同。[DEEPSEEK_PROMPT_PRESERVATION.json](DEEPSEEK_PROMPT_PRESERVATION.json) 给出完整哈希；[历史函数源码片段](deepseek_historical_context_function.txt) 是仓库代码，不含任何具体任务文档或模型输出。正在运行的HPO97冻结源`cb2fe024…`未被修改。

统一指修复核心及同槽设置得到控制；本包不声称各模型的原始prompt、effort、tokenizer或实际计算量完全相同。历史模型间prompt差异被明确保留，避免把另一项提示改动混进本次parser对照。

## 独立核验结果

- [QWEN_SCIENCE_CHECKS.json](QWEN_SCIENCE_CHECKS.json)：12槽42成员的完整native system和任务context与原记录一致；254项独立设置/实际输入断言通过；6个受影响PoolAct池的4,248个控制序列图快照逐字节相同。
- [DEEPSEEK_SCIENCE_CHECKS.json](DEEPSEEK_SCIENCE_CHECKS.json)：9槽36成员使用恢复后的历史prompt，完整native system/context与原记录一致；198项断言通过；8,208个图快照逐字节相同。
- [GLM_SCIENCE_CHECKS.json](GLM_SCIENCE_CHECKS.json)：1槽1成员的旧source、原件、预算/生成/输入身份及完整native prompt核验通过；17项断言通过。单智能体不消费共享图。
- [AUX_LAUNCHER_INDEPENDENT_CHECK.json](AUX_LAUNCHER_INDEPENDENT_CHECK.json)：56个完全mock的机械核验通过，覆盖N1/N4模型身份、runtime/plan/matrix/bindings/root release、fresh/no-resume、完整完成集合、失败/异常留档、代码提交传播和禁止自动释放共用服务。实际模型/API/Slurm操作均为零。

图快照核验使用同一确定性工具记录顺序、两种显示方式、四个观察成员及可见时间边界，共 **12,456 个快照**；它证明这些已有记录对应的图显示等价，不冒充历史真实线程交错重建，也不预测新模型会作出同样行动。Qwen相关Audit key最长51字符，DeepSeek最长75字符，均未跨越旧80字符截断边界。Search图不包含HPO评估配置身份。

system与基础任务context分别按完整字节核验。部分原初始user消息还有当时共享图注入的后缀；审计保留该完整消息的SHA，并单独验证图渲染，没有删掉后缀后宣称原始完整模型输入完全相同。模型生成和并发排程仍是新的真实运行。

## 公开复算边界

默认只需要Python标准库和本目录：

```bash
python3 tools/verify_public_tables.py
```

检查22槽/79成员、21主实验+1独立sweep、公开科学设置与证据表连接、三个旧source与两个新runtime、计划/代码/launcher冻结身份，以及[ALLOWED.json](ALLOWED.json)中的文件哈希。此命令只核公开包的一致性，不重新读取私有原件或再次执行12,456个历史图快照。

原完整prompt、benchmark数据、trajectory和服务凭据不随该包公开。需要原件的独立审核脚本记录在 [SOURCE_PROVENANCE.json](SOURCE_PROVENANCE.json) 中，其哈希用于追踪本地复核；完整原件审计需要 local archives。来源字段中的本地路径如果出现，仅作归档标识，不是Git下载地址。
