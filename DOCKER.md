# Docker Guide

## Quick Start

```bash
# Build the image
docker build -t duckdb-web .

# Run the container
docker run -p 8000:8000 duckdb-web
```

Open [http://localhost:8000](http://localhost:8000) for the app, or [http://localhost:8000/docs](http://localhost:8000/docs) for the API reference.

## Architecture

The Dockerfile uses a **multi-stage build**:

```
Stage 1: node:22-alpine     → npm install + next build → static HTML/JS/CSS in out/
Stage 2: python:3.12-slim   → pip install + copy src/ + copy out/ from stage 1
```

The final image runs a single FastAPI + uvicorn process that serves both the API and the static frontend.

```
Browser → :8000 → uvicorn → /api/*  → FastAPI routes
                            → /*     → static files from out/
```

## Commands

### Build

```bash
# Standard build
docker build -t duckdb-web .

# Build without cache (force full rebuild)
docker build --no-cache -t duckdb-web .

# Build with a specific tag
docker build -t duckdb-web:v1.0 .
```

### Run

```bash
# Basic run (ephemeral - data lost on stop)
docker run -p 8000:8000 duckdb-web

# Run with persistent data volumes
docker run -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/downloads:/app/downloads \
  duckdb-web

# Run in background
docker run -d --name duckdb-web -p 8000:8000 duckdb-web

# Run with custom port
docker run -p 9000:8000 duckdb-web
```

### Manage

```bash
# View running containers
docker ps

# Stop container
docker stop duckdb-web

# Remove container
docker rm duckdb-web

# View logs
docker logs duckdb-web

# Follow logs in real-time
docker logs -f duckdb-web
```

## Volumes

| Container Path | Purpose | Persistent? |
|---|---|---|
| `/app/uploads` | Uploaded source files (CSV, Excel, etc.) | No (use `-v`) |
| `/app/downloads` | Generated reports and exports | No (use `-v`) |

To persist data across container restarts:

```bash
docker run -p 8000:8000 \
  -v duckdb-uploads:/app/uploads \
  -v duckdb-downloads:/app/downloads \
  duckdb-web
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PYTHONUNBUFFERED` | `1` | Disable Python output buffering |
| `PYTHONPATH` | `/app` | Python module search path |

## Docker Compose

Create a `docker-compose.yml` for convenience:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./downloads:/app/downloads
```

Then:

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

## Image Details

- **Base**: `python:3.12-slim` (Debian)
- **Size**: ~1 GB
- **Runtime**: uvicorn (ASGI)
- **Port**: 8000

## Troubleshooting

### Port already in use

```bash
# Use a different host port
docker run -p 9000:8000 duckdb-web

# Or find what's using port 8000
lsof -i :8000
```

### Build fails on frontend stage

```bash
# If you see "Module not found" errors, check that all source
# directories are included in the Dockerfile COPY commands:
#   src/app/, src/components/, src/hooks/, src/lib/, public/
```

### Build fails on Python stage

```bash
# Check requirements.txt is valid
pip install --dry-run -r requirements.txt
```

### Container exits immediately

```bash
# Check logs for the error
docker logs duckdb-web
```

## .dockerignore

The `.dockerignore` file excludes unnecessary files from the build context:

```
.venv/           # Python virtual environment
node_modules/    # NPM dependencies (rebuilt in container)
.git/            # Git history
__pycache__/     # Python bytecode cache
tests/           # Test files not needed at runtime
.claude/         # IDE/agent config
```
