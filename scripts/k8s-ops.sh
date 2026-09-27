#!/usr/bin/env bash
# Toggle maintenance or scale the app. Redis, PostGIS, and MinIO stay up.
set -euo pipefail

NAMESPACE="${NAMESPACE:-zingsa}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG

usage() {
  echo "Usage: bash scripts/k8s-ops.sh {maintenance|maintenance-off|stop|start}" >&2
  exit 1
}

snapshot() {
  kubectl -n "$NAMESPACE" get deploy || true
  kubectl -n "$NAMESPACE" get pods || true
}
trap snapshot EXIT

cmd="${1:-}"
case "$cmd" in
  maintenance)
    kubectl -n "$NAMESPACE" set env deploy/web deploy/worker deploy/beat MAINTENANCE_MODE=1
    kubectl -n "$NAMESPACE" rollout status deploy/web --timeout=240s
    kubectl -n "$NAMESPACE" rollout status deploy/worker --timeout=180s
    kubectl -n "$NAMESPACE" rollout status deploy/beat --timeout=180s
    ;;
  maintenance-off)
    kubectl -n "$NAMESPACE" set env deploy/web deploy/worker deploy/beat MAINTENANCE_MODE=0
    kubectl -n "$NAMESPACE" rollout status deploy/web --timeout=240s
    kubectl -n "$NAMESPACE" rollout status deploy/worker --timeout=180s
    kubectl -n "$NAMESPACE" rollout status deploy/beat --timeout=180s
    ;;
  stop)
    kubectl -n "$NAMESPACE" scale deploy/web deploy/worker deploy/beat --replicas=0
    ;;
  start)
    kubectl -n "$NAMESPACE" scale deploy/web deploy/worker deploy/beat --replicas=1
    kubectl -n "$NAMESPACE" rollout status deploy/web --timeout=240s
    kubectl -n "$NAMESPACE" rollout status deploy/worker --timeout=180s
    kubectl -n "$NAMESPACE" rollout status deploy/beat --timeout=180s
    ;;
  *)
    usage
    ;;
esac
