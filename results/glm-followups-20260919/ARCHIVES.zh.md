# 公开档案定位与本地恢复

[主报告](README.zh.md) · [详细报告](DETAILS.zh.md) · [公开总索引](archive/ARCHIVE_INDEX.json) · [完整成员→分片映射](archive/MEMBERS.csv) · [92片身份](archive/SHARDS.csv)

本次只发布报告、指标、SVG与安全metadata；原始API dumps、私有配置及92个压缩分片不在Git。公开映射保留原件的study-relative路径、bytes、SHA和分片身份，不把索引的公开扫描当作本地原始包已获公开许可。共四个包、92片、1,356,265,462压缩字节；41,929物理存储条目、41,920唯一原路径，重复条目不增加实验或费用。

正式范围为原917/2729加同版Max417/417，合计1334/3146；技术21/63独立。25项外部data/code只存固定身份，未声称payload已入包。读取成绩优先[210设置](metrics/unified_settings.csv)、[417配对](metrics/same_version_pairs.csv)、[轨迹标量](metrics/trajectory_pairs.json)和[具体案例](TRAJECTORIES.zh.md)。

恢复某个原件时，先用study-relative路径查MEMBERS的path，按shard_id连接SHARDS取得分片path，再取本地对应分片，以记录的bytes/SHA验证，只恢复所需成员。不同job的科学slot与参数可在[1334行非敏感参数](reproduce/PARAMETERS.public.jsonl)查到。不要因报告更新重复解压或重评分所有raw。已封本地总索引SHA为 `04af2ec3f6f429ef356c2cd56fad00976598aa09dae2d11a6ab5ec271b46b456`；公开投影自己的SHA另列，不能冒称与原件逐字相同。

本地归档已完成单次seal与完整stream verify，原三包未重封。本地记录与本公开投影的范围、来源和身份见[来源说明](PROVENANCE.md)；原始包继续local-only。

后续[图件修订v2](FIGURES.zh.md)不反写上述四个冻结包：新增SVG、绘图脚本、逐点CSV、图注和复核记录随Git修订保存，身份列于[当前图件索引](figures/FIGURE_INDEX.json)与[公开文件索引](PUBLICATION_INDEX.json)。本地PDF/PNG及其SHA另存study-relative `analysis/paper-figures-v2/FIGURE_INDEX.json`；未把它们描述为旧92个分片的成员。
