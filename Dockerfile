# ── Stage 1: build Svelte frontend ─────────────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ── Stage 2: production image ───────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir \
    "fastapi>=0.111" \
    "uvicorn[standard]>=0.30" \
    "sqlmodel>=0.0.19" \
    "openpyxl>=3.1" \
    "websockets>=12.0"

COPY backend/app ./app
COPY --from=frontend /build/dist ./frontend/dist

ENV DATABASE_URL="sqlite:////data/timecollector.db" \
    FRONTEND_DIST="/app/frontend/dist" \
    CORS_ORIGINS="*"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
