#!/usr/bin/env sh
set -e

echo "[LostLink Boot] Applying database migrations (alembic upgrade head)..."
cd /app/backend
alembic upgrade head

echo "[LostLink Boot] Populating seed records and accounts..."
python scripts/seed_staging.py || true

echo "[LostLink Boot] Launching FastAPI application (single worker for in-memory index)..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --proxy-headers --forwarded-allow-ips="*"

