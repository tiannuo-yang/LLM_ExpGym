# GLM 异地分析：包外路径迁移工具

这三份原件作为本 leaf 的独立附属工具提供，不计入 37 包／71,634 原件，也不改写包内内容。无需为取得迁移工具另外下载 K3 leaf。

- [原 relocator v2 源码](evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/relocate.py)：SHA `94f866d34a07eecd0062c3c81698597d7b5845abab75e5d2758449d5f1b61f35`。
- [原使用说明](evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/README.zh.md)：SHA `cec19a92f7f961e7cc15af7961de100d47f400ac553892d91e9a6442b9c0427e`。
- [原 CPU 收据](evidence/workspace/portable_eval_20260908/source_cohorts/v4/portable_eval_20260908/operations/restart_user_20260909/analysis_relocation_candidate_v2/CPU_RECEIPT.json)：SHA `f3b8fbec8fff76532bebf42803ff7243aa6825f53be5e3857a5419599200a35c`。

先按完整交付说明完成公共恢复与原件路径／bytes／SHA 核验，再按上述原 README 为自己的恢复根准备精确 relocation spec，使用原工具的 `--spec`、外部核验的 `--sha256` 和不存在的 `--output-dir`。原 manifest、records、oracle、input_pins、source_index 及引用原件保持字节与 pins 不变；只生成新的路径映射和派生 source_index。不要直接套用其他机器的绝对路径或执行历史 operator argv。

工具仅负责迁移路径，不安装完整运行环境、不执行模型或评分，也不自动运行 AN2。原 AN2 代码、相对目录布局与原输入须从已核恢复件取得；之后需实际运行原分析器并比较全部输出，才能另行声明 GLM 异地复跑验收通过。本工具附属文件的存在及旧 CPU 收据不等于该验收已经完成。

三份原件保持原字节和历史状态。原 README／CPU 收据提到的其他说明、测试或日志不在本次三件补充中递归复制；这不是整条审计引用链已经闭合的声明。原 controls 子集排除的一份非实验 receipt 仍不公开，实验原始文件不因此减少。本页本身不授予扫描、恢复或模型操作权限。
