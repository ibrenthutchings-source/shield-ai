#!/bin/sh
set -e

echo "[entrypoint] waiting for DB to be ready..."
# Loop until scripts/healthcheck.py reports success
while true; do
  if python /app/scripts/healthcheck.py >/dev/null 2>&1; then
    echo "[entrypoint] DB is available"
    break
  fi
  echo "[entrypoint] DB not ready, sleeping 2s"
  sleep 2
done

# Exec the CMD
if [ "$#" -eq 0 ]; then
  # default
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000
else
  echo "[entrypoint] starting: $@"
  exec "$@"
fi
