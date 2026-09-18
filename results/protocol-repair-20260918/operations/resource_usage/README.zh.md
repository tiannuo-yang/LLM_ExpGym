# 模型服务 GPU 分配账本

`resource_usage.csv` 和 `RESOURCE_USAGE.json` 来自固定的 4 个本轮 owned Slurm allocation，只读 `sacct`，每次刷新都核对作业名及当前用户归属。公开投影不含用户名、账号、节点、endpoint、绝对路径或凭证。

GPU hours = 实际分配 GPU 数 × sacct ElapsedRaw 秒数 / 3600。分配时长包括部署、模型加载、生成、空闲和等待验收，不能当作纯模型计算时长。HPO 与追加控制共享服务时，不重复累计这份 allocation。RUNNING 的数值是截至导出时的暂定值；作业结束后重新运行 exporter 可得到最终数值。

PENDING、未知 start/end、缺失 accounting/GPU 数保留 null（CSV 空字段），不填 0。`requested_gpu_count` 只是申请数，不代替实际分配数。美元成本始终 null，没有 GPU 到美元的换算。

在本目录父级运行 `python3 export_resource_usage.py` 可重复刷新。脚本只读取固定作业，不启动、取消或修改服务；读取或身份核验失败时保留上次成功导出。`MANIFEST.json` 固定本轮 CSV/JSON/说明及 exporter SHA。
