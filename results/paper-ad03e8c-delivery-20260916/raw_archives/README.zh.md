# 原始归档

这里集中保存报告 `ad03e8c42ca501016176ee1bc407b38499178506` 所用来源的完整既有归档。归档为实际文件副本，不是指向其他工作目录的软链接；没有重新打包、改写或删除历史尝试。

- `ARCHIVES.json` / `ARCHIVES.csv`：九个既有来源的归档入口、大小、SHA-256、成员清单、原始路径规则。Gemini 的冻结 snapshot 由独立的 `gemini_snapshot/` 入口补齐。
- `MEMBERS.csv`：九个既有来源每件原文件的 `cohort_id, archive_file, member_path, tar_member_path, bytes, sha256, original_path, member_inventory`。`archive_file` 和 `member_inventory` 相对于交付根目录；`member_path` 是原始 manifest 中的逻辑原件路径，`tar_member_path` 才是实际 tar 条目名。Kimi / GLM 旧格式的 tar 条目带 `data/` 前缀，现代格式两列相同。调用现代恢复器的 `--select` 使用 `member_path`；直接定位 tar 条目使用 `tar_member_path`。
- 每个 cohort 内的原始 manifest / INDEX 保持原字节。原始 API request/response、canonical trajectory、结果、终止证据和原归档选定的控制文件都保留；文件数不是实验数。

这些是来源级归档，包含本报告最终采用的数据，也保留被重跑替换的历史结果、失败尝试及原归档内的检查材料。最终报告采用关系应以交付根目录的逐任务来源表为准，不能把归档里所有结果重新平均。

此次对既有压缩包在复制时逐个核对 SHA-256；成员身份沿用固定来源清单，没有为重复验证再解开旧包。GPT 原始归档此前是本地归档，本次集中存放不等于已获公开发布许可；可公开状态见索引。

## 取出原件

以下命令从交付根目录运行。建议先查 `MEMBERS.csv`，选出需要的 `member_path`；常用 trajectory 已另行提供便于直接查看的副本，无须全量解包。

现代格式适用 Qwen、DeepSeek、GPT 原始来源以及四个定向重跑来源。把需要的路径组成 JSON 字符串数组 `selected-members.json`，例如 `["包内原件路径.json"]`，再运行：

```bash
python tools/modern/scripts/package_run.py verify \
  --manifest raw_archives/qwen_original/manifest.json \
  --archive-dir raw_archives/qwen_original \
  --select selected-members.json --restore-dir /absolute/new-output-dir
```

该工具核对全部归档，但只写出选定原件；不传 `--select` / `--restore-dir` 则只验证。恢复目录必须不存在。不要对 GPT 原始来源加 `--require-public-scan`。

Kimi / GLM 原始来源使用旧 collection 格式，必须用一并保留的原始恢复器，不能交给现代格式工具：

```bash
python tools/legacy/collection_restore_candidate_v2/restore_collection.py \
  --index raw_archives/kimi_original/INDEX.kimi-k3-composite-v1.json \
  --sha256 a462bde564618f52b46b863095bfed5d2a97eb9c3ce4c730a34ac6fdad91a0f7 \
  --output-dir /absolute/new-output-dir
```

GLM 改用 `raw_archives/glm_original/INDEX.json`，SHA-256 为 `9d4433461c3cf0a3017220003c2d70b5085e715c5db82303449d57e48c8cca09`。旧恢复器会恢复整个 collection，输出含按 bundle 分组的 payload；原路径归属见恢复后的 `OWNERSHIP_INDEX.json`。它可能创建很多小文件，日常查阅优先使用直接提供的 trajectory 或按索引定位单个原件。
