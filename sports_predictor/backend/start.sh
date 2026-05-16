#!/bin/bash

echo "=== Running database migrations ==="
python -m alembic upgrade head || echo "Warning: migrations failed, continuing..."

echo "=== Creating admin user if needed ==="
python create_admin.py || echo "Warning: admin creation failed, continuing..."

echo "=== Starting server ==="
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1 \
  --loop uvloop \
  --http httptools
