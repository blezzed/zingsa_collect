#!/usr/bin/env bash
# Move ZINGSA Collect data from the Docker Compose stack into k3s.
# Run on the k3s control plane after the first successful deploy.
#
#   bash scripts/migrate-docker-to-k3s.sh preflight   # read-only checks
#   bash scripts/migrate-docker-to-k3s.sh db          # stops Docker app, copies PostGIS
#   bash scripts/migrate-docker-to-k3s.sh media       # mirrors the MinIO bucket
#   bash scripts/migrate-docker-to-k3s.sh cutover     # starts k3s app, smoke-tests
#   bash scripts/migrate-docker-to-k3s.sh all         # the four phases in order
#   bash scripts/migrate-docker-to-k3s.sh rollback    # k3s app to 0, Docker app back on
#
# Downtime starts at "db" (Docker web/worker/beat stop) and ends after "cutover".
# Docker PostGIS and MinIO are left running, untouched, for rollback.
set -euo pipefail

NAMESPACE="${NAMESPACE:-zingsa}"
KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG

DOCKER_POSTGIS="${DOCKER_POSTGIS:-zingsa_collect_postgis}"
DOCKER_MINIO_ENDPOINT="${DOCKER_MINIO_ENDPOINT:-http://127.0.0.1:9018}"
DOCKER_APP_CONTAINERS=(zingsa_collect_web zingsa_collect_worker zingsa_collect_beat)
DB_NAME="${DB_NAME:-zingsa_collect}"
DB_OWNER="${DB_OWNER:-zingsa_collect}"
BUCKET="${BUCKET:-zingsa-collect-media}"
NODE_IP="${NODE_IP:-172.16.3.24}"
K8S_MINIO_ENDPOINT="${K8S_MINIO_ENDPOINT:-http://${NODE_IP}:30918}"
WEB_URL="${WEB_URL:-http://${NODE_IP}:30206}"
DUMP_OUT="${DUMP_OUT:-$HOME/zingsa_collect_docker.dump}"
POD_DUMP="/var/lib/postgresql/data/zingsa_restore.dump"

KUBECTL=(kubectl -n "$NAMESPACE")

log() { printf '[%s] %s\n' "$(date -Iseconds)" "$*"; }
die() { log "ERROR: $*"; exit 1; }

# Exact row counts for every public table, one "table|count" line each.
ROW_COUNTS_SQL="SELECT table_name || '|' || (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM public.%I', table_name), false, true, '')))[1]::text FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name <> 'spatial_ref_sys' ORDER BY table_name"

primary_pod() {
  "${KUBECTL[@]}" get pod -l cnpg.io/cluster=postgis,cnpg.io/instanceRole=primary \
    -o jsonpath='{.items[0].metadata.name}'
}

k8s_psql() {
  "${KUBECTL[@]}" exec -i "$(primary_pod)" -c postgres -- psql -v ON_ERROR_STOP=1 -d "$DB_NAME" "$@"
}

docker_psql() {
  docker exec -i "$DOCKER_POSTGIS" psql -U postgres -d "$DB_NAME" "$@"
}

secret_value() {
  "${KUBECTL[@]}" get secret zingsa-env -o "jsonpath={.data.$1}" | base64 -d
}

scale_k8s_app() {
  "${KUBECTL[@]}" scale deploy/web deploy/worker deploy/beat --replicas="$1"
}

cmd_preflight() {
  command -v docker >/dev/null || die "docker not found"
  command -v kubectl >/dev/null || die "kubectl not found"

  log "Docker Collect containers"
  docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'NAMES|zingsa_collect_' || true
  docker inspect -f '{{.State.Running}}' "$DOCKER_POSTGIS" | grep -qx true \
    || die "${DOCKER_POSTGIS} is not running"

  log "k3s Collect resources"
  "${KUBECTL[@]}" wait --for=condition=Ready cluster/postgis --timeout=120s \
    || die "CloudNativePG cluster postgis is not Ready. Deploy first."
  "${KUBECTL[@]}" get deploy web worker beat minio redis >/dev/null \
    || die "Deployments are missing. Deploy first."
  [ -n "$(primary_pod)" ] || die "No primary pod for cluster postgis"

  log "Source database size"
  docker_psql -Atc "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'))"
  log "Source user count"
  docker_psql -Atc "SELECT count(*) FROM accounts_user"
  log "Preflight OK. Nothing was changed."
}

cmd_db() {
  log "Stopping Docker web, worker, beat. Downtime starts now."
  docker stop "${DOCKER_APP_CONTAINERS[@]}" >/dev/null
  log "Scaling k3s web, worker, beat to 0 so nothing writes during the restore"
  scale_k8s_app 0
  "${KUBECTL[@]}" wait --for=delete pod -l 'app in (web,worker,beat)' --timeout=180s || true

  log "Dumping ${DOCKER_POSTGIS}/${DB_NAME} to ${DUMP_OUT}"
  docker exec -i "$DOCKER_POSTGIS" pg_dump -Fc -U postgres -d "$DB_NAME" > "$DUMP_OUT"
  [ -s "$DUMP_OUT" ] || die "Dump is empty"
  ls -lh "$DUMP_OUT"

  local pod
  pod="$(primary_pod)"
  log "Copying dump into ${pod}"
  "${KUBECTL[@]}" exec -i "$pod" -c postgres -- sh -c "cat > ${POD_DUMP}" < "$DUMP_OUT"

  log "Clearing tables the first deploy created (DROP OWNED BY ${DB_OWNER})"
  k8s_psql -c "DROP OWNED BY ${DB_OWNER} CASCADE;"

  # Extensions already exist from bootstrap; their objects and spatial_ref_sys rows are skipped.
  log "Restoring into CloudNativePG as ${DB_OWNER}"
  "${KUBECTL[@]}" exec -i "$pod" -c postgres -- sh -c "
    set -eu
    pg_restore -l ${POD_DUMP} \
      | grep -Ev ' topology |spatial_ref_sys|postgis_topology| EXTENSION ' > /tmp/zingsa_restore.list
    set +e
    pg_restore -d ${DB_NAME} --no-owner --no-privileges --role=${DB_OWNER} \
      -L /tmp/zingsa_restore.list ${POD_DUMP}
    echo \"pg_restore exit code: \$?\"
    rm -f ${POD_DUMP} /tmp/zingsa_restore.list
  "

  log "Comparing row counts, Docker vs k3s"
  local source_counts target_counts
  source_counts="$(docker_psql -Atc "$ROW_COUNTS_SQL")"
  target_counts="$(k8s_psql -Atc "$ROW_COUNTS_SQL")"
  if ! diff <(printf '%s\n' "$source_counts") <(printf '%s\n' "$target_counts"); then
    die "Row counts differ (lines above). Docker is still stopped; run rollback or fix and rerun db."
  fi
  log "All $(printf '%s\n' "$source_counts" | wc -l) tables match. Next: media"
}

cmd_media() {
  local user password
  user="$(secret_value MINIO_ROOT_USER)"
  password="$(secret_value MINIO_ROOT_PASSWORD)"
  [ -n "$user" ] && [ -n "$password" ] || die "MINIO_ROOT_USER / MINIO_ROOT_PASSWORD missing from zingsa-env"

  # Both MinIO servers use the root credentials from the Docker .env that built zingsa-env.
  log "Mirroring ${BUCKET}: ${DOCKER_MINIO_ENDPOINT} -> ${K8S_MINIO_ENDPOINT}"
  docker run --rm --network host \
    -e SRC="$DOCKER_MINIO_ENDPOINT" -e DST="$K8S_MINIO_ENDPOINT" \
    -e MC_USER="$user" -e MC_PASSWORD="$password" -e BUCKET="$BUCKET" \
    --entrypoint /bin/sh minio/mc:latest -c '
      set -eu
      mc alias set src "$SRC" "$MC_USER" "$MC_PASSWORD" >/dev/null
      mc alias set dst "$DST" "$MC_USER" "$MC_PASSWORD" >/dev/null
      mc mb --ignore-existing "dst/$BUCKET"
      mc anonymous set public "dst/$BUCKET"
      mc mirror --overwrite --preserve "src/$BUCKET" "dst/$BUCKET"
      echo "source:"; mc du "src/$BUCKET"
      echo "target:"; mc du "dst/$BUCKET"
    '
  log "Media mirrored. Next: cutover"
}

cmd_cutover() {
  log "Starting k3s web, worker, beat (web runs migrate on startup)"
  scale_k8s_app 1
  "${KUBECTL[@]}" rollout status deploy/web --timeout=600s
  "${KUBECTL[@]}" rollout status deploy/worker --timeout=300s
  "${KUBECTL[@]}" rollout status deploy/beat --timeout=300s

  local path code failed=0
  for path in /admin/login/ /api/schema/ /; do
    code="$(curl -sS -o /dev/null -w '%{http_code}' "${WEB_URL}${path}" || echo 000)"
    log "GET ${path} -> ${code}"
    case "$code" in 2*|3*) ;; *) failed=1 ;; esac
  done
  [ "$failed" -eq 0 ] || die "Smoke test failed. Check: kubectl -n ${NAMESPACE} logs deploy/web"

  cat <<EOF

Cutover done. Collect is served from k3s:
  LAN:    http://172.16.3.24:30206
  Public: http://41.174.184.62:30206 (the router must forward 30206)

Docker web/worker/beat are stopped. Docker PostGIS and MinIO still run for rollback.
When k3s has been stable for a while:
  cd /home/zingsa/Documents/zingsa_collect && docker compose down
Mobile clients and anything else pointing at :8206 must move to :30206.
EOF
}

cmd_rollback() {
  log "Scaling k3s web, worker, beat to 0"
  scale_k8s_app 0
  log "Starting Docker web, worker, beat"
  docker start "${DOCKER_APP_CONTAINERS[@]}" >/dev/null
  log "Rolled back. Collect is served from Docker on :8206 again."
}

case "${1:-}" in
  preflight) cmd_preflight ;;
  db) cmd_db ;;
  media) cmd_media ;;
  cutover) cmd_cutover ;;
  all) cmd_preflight; cmd_db; cmd_media; cmd_cutover ;;
  rollback) cmd_rollback ;;
  *)
    echo "Usage: bash scripts/migrate-docker-to-k3s.sh {preflight|db|media|cutover|all|rollback}" >&2
    exit 1
    ;;
esac
