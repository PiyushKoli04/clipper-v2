# ── Stage 1: Build React Frontend ──
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Serve FastAPI with Python 3.11 ──
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code and worker logic
COPY server/ ./server/
COPY worker/ ./worker/

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose port (Render sets $PORT dynamically)
ENV PORT=8000
EXPOSE 8000

# Run uvicorn server
CMD uvicorn server.app:app --host 0.0.0.0 --port ${PORT}

