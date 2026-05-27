#!/usr/bin/env bash
set -e

echo "Waiting for database..."
until python - << 'PYCODE'
import os
import psycopg2

db_name = os.getenv("DJANGO_DB_NAME", "zingsa_collect")
db_user = os.getenv("DJANGO_DB_USER", "zingsa_collect")
db_password = os.getenv("DJANGO_DB_PASSWORD", "zingsa_collect")
db_host = os.getenv("DJANGO_DB_HOST", "postgis")
db_port = int(os.getenv("DJANGO_DB_PORT", "5432"))

conn = psycopg2.connect(
    dbname=db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
)
conn.close()
PYCODE
do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is up!"

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8005 config.asgi:application