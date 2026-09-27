#!/usr/bin/env bash
# Run on the k3s control plane. Imports IMAGE_REF into containerd and rolls the app.
set -euo pipefail

: "${IMAGE_REF:?IMAGE_REF is required}"

KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG
NAMESPACE="${NAMESPACE:-zingsa}"
SKIP_PULL="${SKIP_PULL:-0}"
KEEP_IMAGE_COUNT="${KEEP_IMAGE_COUNT:-2}"
K8S_DIR="${K8S_DIR:-}"

tar_path=""
cleanup() {
  if [ -n "${tar_path}" ] && [ -f "${tar_path}" ]; then
    rm -f "${tar_path}"
  fi
}
trap cleanup EXIT

kubectl_bin() {
  if command -v kubectl >/dev/null 2>&1; then
    command kubectl "$@"
    return
  fi
  if command -v k3s >/dev/null 2>&1; then
    k3s kubectl "$@"
    return
  fi
  echo "kubectl not found" >&2
  return 127
}

# Privileged docker-run chroot: the shell user often cannot call k3s directly,
# but can talk to docker. The container sees the host filesystem at /host.
k3s_ctr() {
  if command -v k3s >/dev/null 2>&1 && k3s ctr version >/dev/null 2>&1; then
    k3s ctr "$@"
    return
  fi
  local quoted
  quoted="$(printf '%q ' "$@")"
  docker run --rm --privileged --pid=host \
    -v /:/host \
    alpine:3.20 \
    chroot /host /bin/sh -c \
    "if [ -x /usr/local/bin/k3s ]; then K3S=/usr/local/bin/k3s; elif [ -x /usr/bin/k3s ]; then K3S=/usr/bin/k3s; else K3S=k3s; fi; \"\$K3S\" ctr ${quoted}"
}

control_plane_hostname() {
  local name=""
  name="$(kubectl_bin get nodes -l node-role.kubernetes.io/control-plane -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [ -z "$name" ]; then
    name="$(kubectl_bin get nodes -l node-role.kubernetes.io/master -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  fi
  if [ -z "$name" ]; then
    name="$(kubectl_bin get nodes -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  fi
  printf '%s' "$name"
}

apply_manifests() {
  local apply_dir node
  apply_dir="$(mktemp -d)"
  cp -a "${K8S_DIR}/." "${apply_dir}/"
  if grep -R -q --include='*.yaml' 'REPLACE_WITH_NODE_HOSTNAME' "${apply_dir}"; then
    node="$(control_plane_hostname)"
    if [ -z "$node" ]; then
      echo "kubectl get nodes did not return a control-plane hostname." >&2
      exit 1
    fi
    case "$node" in
      *[!A-Za-z0-9._-]*)
        echo "Refusing unexpected node hostname: ${node}" >&2
        exit 1
        ;;
    esac
    echo "nodeSelector kubernetes.io/hostname=${node}"
    grep -R -l --include='*.yaml' 'REPLACE_WITH_NODE_HOSTNAME' "${apply_dir}" | while read -r file; do
      sed -i "s/REPLACE_WITH_NODE_HOSTNAME/${node}/g" "$file"
    done
  fi
  kubectl_bin apply -k "${apply_dir}"
}

prune_old_images() {
  local repo="$1"
  local keep="$2"
  local -a newest_ids=()
  local line created id ref
  local -a keep_ids=()

  while IFS=$'\t' read -r created id ref; do
    [ -n "$id" ] || continue
    case "$ref" in
      "${repo}:"*) ;;
      *) continue ;;
    esac
    local already=0
    local seen
    for seen in "${newest_ids[@]+"${newest_ids[@]}"}"; do
      if [ "$seen" = "$id" ]; then
        already=1
      fi
    done
    if [ "$already" -eq 0 ]; then
      newest_ids+=("$id")
    fi
  done < <(docker images "$repo" --format $'{{.CreatedAt}}\t{{.ID}}\t{{.Repository}}:{{.Tag}}' | sort -r)

  local index=0
  for id in "${newest_ids[@]+"${newest_ids[@]}"}"; do
    if [ "$index" -lt "$keep" ]; then
      keep_ids+=("$id")
    fi
    index=$((index + 1))
  done

  while IFS=$'\t' read -r created id ref; do
    [ -n "$ref" ] || continue
    case "$ref" in
      "${repo}:"*) ;;
      *) continue ;;
    esac
    local drop=1
    local kept
    for kept in "${keep_ids[@]+"${keep_ids[@]}"}"; do
      if [ "$kept" = "$id" ]; then
        drop=0
      fi
    done
    if [ "$drop" -eq 1 ]; then
      docker rmi "$ref" || true
    fi
  done < <(docker images "$repo" --format $'{{.CreatedAt}}\t{{.ID}}\t{{.Repository}}:{{.Tag}}')

  local keep_refs
  keep_refs="$(docker images "$repo" --format '{{.Repository}}:{{.Tag}}' || true)"
  local img short
  while read -r img; do
    [ -n "$img" ] || continue
    short="${img#docker.io/}"
    case "$short" in
      "${repo}:"*) ;;
      *) continue ;;
    esac
    if ! printf '%s\n' "$keep_refs" | grep -Fxq "$short"; then
      k3s_ctr -n k8s.io images rm "$img" || true
    fi
  done < <(k3s_ctr -n k8s.io images ls -q || true)
}

if [ "$SKIP_PULL" != "1" ]; then
  if [ -n "${DOCKERHUB_USERNAME:-}" ] && [ -n "${DOCKERHUB_TOKEN:-}" ]; then
    printf '%s' "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
  fi
  docker pull "$IMAGE_REF"
fi

repo="${IMAGE_REF%:*}"
latest_ref="${repo}:latest"
tar_path="$(mktemp /tmp/zingsa-collect-image.XXXXXX.tar)"
if [ "$IMAGE_REF" = "$latest_ref" ]; then
  docker save -o "$tar_path" "$IMAGE_REF"
else
  docker tag "$IMAGE_REF" "$latest_ref"
  docker save -o "$tar_path" "$IMAGE_REF" "$latest_ref"
fi
k3s_ctr -n k8s.io images import "$tar_path"

if [ -n "$K8S_DIR" ] && [ -d "$K8S_DIR" ]; then
  apply_manifests
fi

kubectl_bin -n "$NAMESPACE" set image "deploy/web" "web=${IMAGE_REF}"
kubectl_bin -n "$NAMESPACE" set image "deploy/worker" "worker=${IMAGE_REF}"
kubectl_bin -n "$NAMESPACE" set image "deploy/beat" "beat=${IMAGE_REF}"
kubectl_bin -n "$NAMESPACE" rollout status deploy/web --timeout=240s
kubectl_bin -n "$NAMESPACE" rollout status deploy/worker --timeout=180s
kubectl_bin -n "$NAMESPACE" rollout status deploy/beat --timeout=180s

prune_old_images "$repo" "$KEEP_IMAGE_COUNT" || echo "Image prune failed; deploy is still complete." >&2
