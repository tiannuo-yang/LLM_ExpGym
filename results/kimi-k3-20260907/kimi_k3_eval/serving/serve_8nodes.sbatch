#!/usr/bin/env bash
#SBATCH --account=k2p
#SBATCH --partition=higherprio
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:8
#SBATCH --time=3-00:00:00
#SBATCH --job-name=k3-expgym-8n
#SBATCH --output=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving/logs/slurm-%j.log
set -euo pipefail
BASE=/lustrefs/users/chufan.shi/codex_space_tn/kimi_k3_eval/serving
IMAGE=/lustrefs/users/chufan.shi/codex_space/Tau_vision/.images/sglang_k3_cu12.sqsh
CKPT=/lustrefs/users/runner/chufan.shi/tau_vision/ckpts/Kimi-K3
[[ -x "$BASE/independent/.venv/bin/sglang" ]] || { echo 'Independent uv environment is absent'; exit 2; }
[[ -f "$BASE/manifests/padding-tests-passed.json" ]] || { echo 'Padding kernel validation gate is absent'; exit 2; }
mapfile -t K3_NODES < <(scontrol show hostnames "$SLURM_JOB_NODELIST")
[[ ${#K3_NODES[@]} -eq 8 ]] || { echo 'Expected exactly eight nodes'; exit 2; }
RUN_DIR="$BASE/runs/$SLURM_JOB_ID"
mkdir -p "$RUN_DIR"
python3 "$BASE/write_deployment.py" "$RUN_DIR" "${K3_NODES[@]}"
cp "$RUN_DIR/deployment.json" "$BASE/deployment.json"
PIDS=()
cleanup() {
  trap - EXIT INT TERM
  for k3_pid in "${PIDS[@]}"; do kill "$k3_pid" 2>/dev/null || true; done
  wait || true
}
trap cleanup EXIT INT TERM
for k3_rank in {0..7}; do
  k3_pair=$((k3_rank / 2))
  k3_local_rank=$((k3_rank % 2))
  k3_head="${K3_NODES[$((2 * k3_pair))]}"
  k3_head_ip=$(getent ahostsv4 "$k3_head" | awk 'NR == 1 {print $1}')
  srun --nodes=1 --ntasks=1 --cpu-bind=none --kill-on-bad-exit=1 \
    --nodelist="${K3_NODES[$k3_rank]}" \
    --output="$RUN_DIR/replica${k3_pair}-rank${k3_local_rank}.log" \
    --container-image="$IMAGE" \
    --container-mounts="$BASE:$BASE,$CKPT:/models/kimi-k3:ro" \
    bash "$BASE/serve_node.sh" "$k3_pair" "$k3_local_rank" "$k3_head_ip" &
  PIDS+=("$!")
done
# Router shares the first node; --overlap does not allocate additional nodes.
srun --overlap --nodes=1 --ntasks=1 --cpus-per-task=2 --cpu-bind=none \
  --nodelist="${K3_NODES[0]}" --output="$RUN_DIR/router.log" \
  --container-image="$IMAGE" --container-mounts="$BASE:$BASE" \
  bash "$BASE/run_router.sh" "$RUN_DIR/deployment.json" &
PIDS+=("$!")
wait -n "${PIDS[@]}"
echo 'An owned serving process exited; terminating only this deployment.'
exit 1
