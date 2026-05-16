#!/bin/bash
set -e

echo "=== Running database migrations ==="
python -m alembic upgrade head

echo "=== Starting server ==="
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 2 \
  --loop uvloop \
  --http httptools
