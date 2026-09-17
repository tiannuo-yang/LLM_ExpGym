# Gemini：ad03e8c 报告对应原始材料

此处固定到 2026-09-13 05:27:39.527814740 UTC 的报告快照，不引入后续结果。783 个计划槽位中，767 个完成并评分；1 个原始失败池保留，1 个已启动但未完成，14 个未启动。未知结果不补零。

- `original_v3/`：复用原始已关闭运行的完整 3 个分片，含 76 个完成项和 1 个失败项；保留其他被恢复槽位在原段留下的历史证据。原始成员哈希沿用旧 manifest；本次复制时核对所有压缩文件 SHA256，未重新全量解包。
- `recovery_v1/`：仅封存本快照选中的 691 个完成项。每个 completion receipt 声明的全部 API 请求/回复、agent trajectory、终态/评分证据和 worker 文件均在内；另含 completion/started 控制及固定 queue plan。其中 22,446 件有冻结 receipt 或 SOURCE_INDEX 的历史哈希绑定；691 份 `started.json` 完成任务控制文件另按本次封存记录身份。全部 23,137 件均完成一次成员流式验证，未全量恢复。
- `snapshot_controls/`：精确复制原快照的 SOURCE_INDEX、normalized、INPUTS 和 captured_metadata；后者是当时 controller、queue timeline、quota 与 oracle 的字节，不使用后来改变的在线控制文件。
- `MEMBERS.csv`：每个 archive/member → 原始绝对路径、大小、SHA256，便于与合并 CSV 联接。
- `RECOVERY_SELECTION.json`：选中的逻辑槽位、源 job、运行时间、结果/receipt 路径及全部文件绑定依据。
- `INDEX.json`：总计、每组验证范围、来源根目录及时间。

恢复 archive member 的原始路径：相应 manifest 的 `path` 加到该组 `original_root`；不要把 absolute source path 当作交付依赖。所有原件已在本目录的分片中。使用交付附带的 `package_run.py verify --manifest ... --archive-dir ...` 可验证；加 `--select` 和新建 `--restore-dir` 可按清单恢复所需原件。

边界：尚未完成的 recovery job 在原快照中没有逐 API payload 的冻结清单；其后续 dump 和后续失败结果没有被反写进此快照。快照中的状态、开始事件和未知端点完整保留。此包为私有本地交付，未做公开凭据扫描，不可直接上传 GitHub。
