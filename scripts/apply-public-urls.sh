#!/usr/bin/env bash
# Re-apply the ConfigMap and restart app pods so public URL changes take effect.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAMESPACE="${NAMESPACE:-zingsa}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG

kubectl apply -f "${ROOT}/k8s/01-configmap.yaml"
kubectl -n "$NAMESPACE" rollout restart deploy/web deploy/worker deploy/beat
kubectl -n "$NAMESPACE" rollout status deploy/web --timeout=240s
kubectl -n "$NAMESPACE" rollout status deploy/worker --timeout=180s
kubectl -n "$NAMESPACE" rollout status deploy/beat --timeout=180s

echo "Live public URL keys:"
kubectl -n "$NAMESPACE" get configmap zingsa-app-config -o go-template='{{range $k, $v := .data}}{{$k}}={{$v}}{{"\n"}}{{end}}' \
  | grep -E '^(SITE_URL|FRONTEND_URL|DJANGO_CSRF_TRUSTED_ORIGINS|DJANGO_ALLOWED_HOSTS|AWS_S3_CUSTOM_DOMAIN)='
