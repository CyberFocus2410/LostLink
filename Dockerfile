# ==============================================================================
# Multi-Stage Production Dockerfile for LostLink
# Single-Service: Builds React 19 Frontend + Serves via FastAPI (Single Worker)
# ==============================================================================

# Stage 1: Build the React PWA Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim AS runner

# Install essential system runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend static assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Default port for Render / container platforms
ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    ENV=production

EXPOSE 8000

# Container entrypoint script: runs Alembic migrations then launches Uvicorn (1 worker)
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]

