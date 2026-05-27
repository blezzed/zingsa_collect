#!/usr/bin/env bash
set -e

echo "Waiting for database…"
until python -c "import psycopg2, os; psycopg2.connect(dbname=os.getenv('DJANGO_DB_NAME','zingsa_collect'), user=os.getenv('DJANGO_DB_USER','zingsa_collect'), password=os.getenv('DJANGO_DB_PASSWORD','zingsa_collect'), host='postgis', port=int('5432')).close()" 2>/dev/null; do
  echo "Waiting for database…"
  sleep 2
done

echo "Starting Celery beat…"
exec celery -A config.celery:app beat -l info
