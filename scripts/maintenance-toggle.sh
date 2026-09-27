#!/usr/bin/env bash
# Toggle ZINGSA Collect maintenance mode via env file (owner token stays unchanged).
#
# Usage on VPS (from the project directory):
#   bash scripts/maintenance-toggle.sh on
#   bash scripts/maintenance-toggle.sh off
#   bash scripts/maintenance-toggle.sh status
#
# Env file location (prefer secrets outside the git checkout):
#   export COLLECT_ENV_FILE=/etc/zingsa_collect/zingsa_collect.env
#   # also accepts NSDI_ENV_FILE for operators used to the NSDI script name
#
# Compose mode:
#   COLLECT_COMPOSE_MODE=dev   (default)  -> docker-compose.yml only (bind mount)
#   COLLECT_COMPOSE_MODE=prod             -> + docker-compose.prod.yml if present
#   # also accepts NSDI_COMPOSE_MODE
#
# If the env file is root-owned and not writable by your user:
#   sudo -E bash scripts/maintenance-toggle.sh on
# or keep a writable runtime copy and point COLLECT_ENV_FILE at it.

set -euo pipefail

ACTION="${1:-status}"
ENV_FILE="${COLLECT_ENV_FILE:-${NSDI_ENV_FILE:-.env}}"
MODE="${COLLECT_COMPOSE_MODE:-${NSDI_COMPOSE_MODE:-dev}}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

if [[ "$MODE" == "prod" ]]; then
  if [[ -f docker-compose.prod.yml ]]; then
    COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
  else
    echo "WARNING: docker-compose.prod.yml not found; using docker-compose.yml only." >&2
    COMPOSE=(docker compose -f docker-compose.yml)
  fi
else
  COMPOSE=(docker compose -f docker-compose.yml)
fi

_get_mode() {
  grep -E '^MAINTENANCE_MODE=' "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '\r' || true
}

_set_mode() {
  local value="$1"
  if grep -q '^MAINTENANCE_MODE=' "$ENV_FILE"; then
    sed -i "s/^MAINTENANCE_MODE=.*/MAINTENANCE_MODE=${value}/" "$ENV_FILE"
  else
    printf '\nMAINTENANCE_MODE=%s\n' "${value}" >> "$ENV_FILE"
  fi
}

_ensure_owner_token() {
  if ! grep -q '^MAINTENANCE_OWNER_TOKEN=' "$ENV_FILE" \
    || grep -qE '^MAINTENANCE_OWNER_TOKEN=$' "$ENV_FILE" \
    || grep -qE '^MAINTENANCE_OWNER_TOKEN=change-me' "$ENV_FILE"; then
    echo "WARNING: MAINTENANCE_OWNER_TOKEN is missing or still a placeholder in $ENV_FILE" >&2
    echo "Set a long random token before relying on owner bypass." >&2
  fi
}

_recreate_app() {
  # Collect services that load Django settings / serve public traffic.
  "${COMPOSE[@]}" up -d --force-recreate web worker beat
}

case "$ACTION" in
  on)
    _ensure_owner_token
    _set_mode 1
    echo "MAINTENANCE_MODE=1 written to $ENV_FILE (compose=$MODE)"
    export COLLECT_ENV_FILE="$ENV_FILE"
    export NSDI_ENV_FILE="$ENV_FILE"
    _recreate_app
    echo "Web/worker/beat recreated. Public traffic should see HTTP 503."
    ;;
  off)
    _set_mode 0
    echo "MAINTENANCE_MODE=0 written to $ENV_FILE (compose=$MODE)"
    export COLLECT_ENV_FILE="$ENV_FILE"
    export NSDI_ENV_FILE="$ENV_FILE"
    _recreate_app
    echo "Maintenance disabled."
    ;;
  status)
    echo "COLLECT_ENV_FILE=$ENV_FILE"
    echo "COLLECT_COMPOSE_MODE=$MODE"
    echo "MAINTENANCE_MODE=$(_get_mode)"
    ;;
  *)
    echo "Usage: $0 {on|off|status}" >&2
    exit 1
    ;;
esac
