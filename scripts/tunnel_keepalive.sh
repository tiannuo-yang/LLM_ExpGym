#!/bin/bash
# tunnel_keepalive.sh — Keep an SSH port-forward tunnel alive.
#
# Useful when running on a compute node that has restricted outbound internet,
# but a login node it can SSH into does have internet. Forwards a local port
# through the login node to ``openrouter.ai`` (or any host you choose).
#
# Usage:
#   ./scripts/tunnel_keepalive.sh LOGIN_NODE [LOCAL_PORT] [REMOTE_HOST] [REMOTE_PORT] [FAILOVER_NODE]
#
# Example:
#   ./scripts/tunnel_keepalive.sh login.cluster.example.org 8443 openrouter.ai 443 login2.cluster.example.org
#
# The script loops forever, restarting the tunnel whenever it drops, and
# alternates between LOGIN_NODE and FAILOVER_NODE if the latter is given.
# Kill with: pkill -f tunnel_keepalive or kill the PID.

if [[ -z "${1:-}" ]]; then
    echo "usage: $0 LOGIN_NODE [LOCAL_PORT] [REMOTE_HOST] [REMOTE_PORT] [FAILOVER_NODE]" >&2
    echo "       LOGIN_NODE is required (your cluster's login/jump host)." >&2
    exit 64
fi

LOGIN_NODE="$1"
LOCAL_PORT="${2:-8443}"
REMOTE_HOST="${3:-openrouter.ai}"
REMOTE_PORT="${4:-443}"
FAILOVER_NODE="${5:-}"

echo "[tunnel] forwarding localhost:${LOCAL_PORT} -> ${REMOTE_HOST}:${REMOTE_PORT} via ${LOGIN_NODE}"

CURRENT_NODE="$LOGIN_NODE"
while true; do
    ssh -L "${LOCAL_PORT}:${REMOTE_HOST}:${REMOTE_PORT}" \
        -N \
        -o ServerAliveInterval=30 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes \
        -o StrictHostKeyChecking=no \
        -o BatchMode=yes \
        "${CURRENT_NODE}" 2>&1

    echo "[tunnel] $(date): tunnel died (exit=$?), restarting in 5s..."
    sleep 5

    # Optional failover between two login nodes if FAILOVER_NODE was given.
    if [[ -n "$FAILOVER_NODE" ]]; then
        if [[ "$CURRENT_NODE" == "$LOGIN_NODE" ]]; then
            CURRENT_NODE="$FAILOVER_NODE"
        else
            CURRENT_NODE="$LOGIN_NODE"
        fi
        echo "[tunnel] $(date): trying ${CURRENT_NODE}"
    fi
done
