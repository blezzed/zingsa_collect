#!/usr/bin/env bash
set -euo pipefail

# Simple hourly PostGIS backup to a Windows SSH target.
# Configure via environment variables (examples below) and run from cron.
#
# Required:
#   REMOTE_USER, REMOTE_HOST
# Optional:
#   CONTAINER_NAME (default: nsdi_postgis)
#   DB_NAME (default: nsdi)
#   DB_USER (default: postgres)
#   REMOTE_DIR_SSH (default: ~/Documents/geospatial)
#   KEEP_HOURS (default: 168)
#   ENABLE_REMOTE_CLEANUP (default: 0)
#   REMOTE_DIR_WIN (only needed if ENABLE_REMOTE_CLEANUP=1)

CONTAINER_NAME="${CONTAINER_NAME:-nsdi_postgis}"
DB_NAME="${DB_NAME:-nsdi}"
DB_USER="${DB_USER:-postgres}"

REMOTE_USER="${REMOTE_USER:?set REMOTE_USER}"
REMOTE_HOST="${REMOTE_HOST:?set REMOTE_HOST}"
REMOTE_DIR_SSH="${REMOTE_DIR_SSH:-~/Documents/geospatial}"

KEEP_HOURS="${KEEP_HOURS:-168}"
ENABLE_REMOTE_CLEANUP="${ENABLE_REMOTE_CLEANUP:-0}"
REMOTE_DIR_WIN="${REMOTE_DIR_WIN:-}"

timestamp="$(date +'%Y%m%d_%H%M%S')"
tmp_dir="$(mktemp -d)"
dump_file="nsdi_${timestamp}.dump"
local_path="${tmp_dir}/${dump_file}"

cleanup() {
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

echo "Creating dump from ${CONTAINER_NAME}/${DB_NAME}..."
docker exec -t "${CONTAINER_NAME}" pg_dump -Fc -U "${DB_USER}" -d "${DB_NAME}" > "${local_path}"

echo "Ensuring remote directory exists..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR_SSH}"

echo "Uploading ${dump_file}..."
scp "${local_path}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR_SSH}/"

if [[ "${ENABLE_REMOTE_CLEANUP}" == "1" ]]; then
  if [[ -z "${REMOTE_DIR_WIN}" ]]; then
    echo "REMOTE_DIR_WIN is required when ENABLE_REMOTE_CLEANUP=1" >&2
    exit 1
  fi
  echo "Cleaning up backups older than ${KEEP_HOURS} hours on remote..."
  ssh "${REMOTE_USER}@${REMOTE_HOST}" \
    "powershell.exe -NoProfile -Command \"Get-ChildItem -Path '${REMOTE_DIR_WIN}' -Filter '*.dump' | Where-Object { \$_.LastWriteTime -lt (Get-Date).AddHours(-${KEEP_HOURS}) } | Remove-Item -Force\""
fi

echo "Backup complete: ${dump_file}"
