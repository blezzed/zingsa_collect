#!/usr/bin/env bash
# Create or update the zingsa-env and postgis-app Secrets on the k3s control plane.
# Usage: bash k8s/create-secret.sh /home/zingsa/Documents/zingsa_collect/.env
# Reusing the Docker .env is fine: the ConfigMap overrides its host, port, and URL keys.
set -euo pipefail

ENV_FILE="${1:-.env}"
NAMESPACE="${NAMESPACE:-zingsa}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG

[ -s "$ENV_FILE" ] || { echo "Env file not found or empty: ${ENV_FILE}" >&2; exit 1; }

env_value() {
  sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r' | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/"
}

for key in DJANGO_SECRET_KEY DJANGO_DB_PASSWORD MINIO_ROOT_USER MINIO_ROOT_PASSWORD \
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY MAINTENANCE_OWNER_TOKEN; do
  if [ -z "$(env_value "$key")" ]; then
    echo "${key} is required in ${ENV_FILE}" >&2
    exit 1
  fi
done

clean_env="$(mktemp)"
trap 'rm -f "$clean_env"' EXIT
# kubectl keeps quotes verbatim, while Docker Compose strips them. Strip them here too.
tr -d '\r' < "$ENV_FILE" \
  | sed -e "s/^\([A-Za-z_][A-Za-z0-9_]*\)=\"\(.*\)\"$/\1=\2/" \
        -e "s/^\([A-Za-z_][A-Za-z0-9_]*\)='\(.*\)'$/\1=\2/" > "$clean_env"

kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n "$NAMESPACE" create secret generic zingsa-env \
  --from-env-file="$clean_env" \
  --dry-run=client -o yaml | kubectl apply -f -

# CloudNativePG owner is zingsa_collect. The password matches DJANGO_DB_PASSWORD.
kubectl -n "$NAMESPACE" create secret generic postgis-app \
  --type=kubernetes.io/basic-auth \
  --from-literal=username=zingsa_collect \
  --from-literal=password="$(env_value DJANGO_DB_PASSWORD)" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets zingsa-env and postgis-app are in namespace ${NAMESPACE}."
