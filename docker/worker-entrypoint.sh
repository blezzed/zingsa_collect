#!/usr/bin/env bash
set -e

echo "Waiting for database..."
until python - << 'PYCODE'
import os
import psycopg2

conn = psycopg2.connect(
    dbname=os.getenv("DJANGO_DB_NAME", "zingsa_collect"),
    user=os.getenv("DJANGO_DB_USER", "zingsa_collect"),
    password=os.getenv("DJANGO_DB_PASSWORD", "zingsa_collect"),
    host=os.getenv("DJANGO_DB_HOST", "postgis"),
    port=int(os.getenv("DJANGO_DB_PORT", "5432")),
)
conn.close()
PYCODE
do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Starting Celery worker…"
exec celery -A config.celery:app worker -l info --concurrency=2
