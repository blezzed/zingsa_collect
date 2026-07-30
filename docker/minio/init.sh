#!/bin/sh
set -e

MINIO_ROOT_USER="${MINIO_ROOT_USER:-minioadmin}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-minioadmin}"

until /usr/bin/mc alias set local "http://minio:9000" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "Waiting for MinIO..."
  sleep 2
done

/usr/bin/mc mb --ignore-existing local/zingsa-collect-media
/usr/bin/mc anonymous set public local/zingsa-collect-media
echo "MinIO bucket ready."
