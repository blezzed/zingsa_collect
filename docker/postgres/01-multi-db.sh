#!/usr/bin/env bash
set -euo pipefail

echo "=== [PostGIS init] Setting up NSDI database and user ==="

# Helper: create role if missing, set password
create_or_alter_user() {
  local user="$1" pass="$2"
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname='${user}'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
       "CREATE USER ${user} WITH PASSWORD '${pass}';"

  # always ensure password is up to date
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
    "ALTER USER ${user} WITH PASSWORD '${pass}';"
}

# Helper: create db if missing, set owner
create_db_if_missing() {
  local db="$1" owner="$2"
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
       "CREATE DATABASE ${db} OWNER ${owner};"
}

# Ensure env vars are present
: "${DJANGO_DB_NAME:?DJANGO_DB_NAME is required}"
: "${DJANGO_DB_USER:?DJANGO_DB_USER is required}"
: "${DJANGO_DB_PASSWORD:?DJANGO_DB_PASSWORD is required}"

echo "→ Creating/Updating Django user and database..."

# Django / NSDI DB
create_or_alter_user "${DJANGO_DB_USER}" "${DJANGO_DB_PASSWORD}"
create_db_if_missing "${DJANGO_DB_NAME}" "${DJANGO_DB_USER}"

echo "→ Enabling extensions on ${DJANGO_DB_NAME}..."

# Useful extensions for GeoDjango/PostGIS
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "${DJANGO_DB_NAME}" -c \
  'CREATE EXTENSION IF NOT EXISTS "postgis";
   CREATE EXTENSION IF NOT EXISTS "postgis_topology";
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS "pgcrypto";'

echo "=== [PostGIS init] Done ==="
