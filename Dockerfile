# ============================================================
# Stage 1: Build Next.js static frontend
# ============================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /build

# Install dependencies first (layer caching)
COPY package.json package-lock.json* ./
RUN npm install

# Copy all source needed for build
COPY next.config.ts tsconfig.json postcss.config.mjs ./
COPY src/app/ src/app/
COPY src/components/ src/components/
COPY src/hooks/ src/hooks/
COPY src/lib/ src/lib/
COPY public/ public/

RUN npm run build

# ============================================================
# Stage 2: Python runtime with built frontend
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Install system deps for reportlab, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source
COPY src/ src/

# Copy built frontend from stage 1
COPY --from=frontend-builder /build/out ./out

# Create runtime directories
RUN mkdir -p uploads downloads

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
EXPOSE 8000

# Run FastAPI (serves API + static frontend from out/)
CMD ["uvicorn", "src.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
