# ==========================================
# Stage 1: Build the React/Vite Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy dependencies first for caching
COPY frontend/package*.json ./
RUN npm ci

# Copy frontend source code and compile
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Create the FastAPI Python Backend
# ==========================================
FROM python:3.12-slim

# Install system dependencies (build tools, sqlite, curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy backend dependencies first for caching
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Copy backend source code
COPY backend/app ./app
COPY backend/main.py ./

# Copy compiled frontend assets from Stage 1 into the backend's dist folder
COPY --from=frontend-builder /frontend/dist ./dist

# Create persistent data directories (for SQLite & uploads)
RUN mkdir -p /app/data /app/uploads /app/audio_uploads

# Set PATH to use the virtual environment built by uv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose server port
EXPOSE 8000

# Start server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
