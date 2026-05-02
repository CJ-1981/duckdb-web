# Monitoring System Quick Start Guide

## Overview

Production-ready monitoring system with health checks, metrics collection, and structured logging.

## Features

### 1. Health Check Endpoints
**Router Prefix:** `/health`

**Endpoints:**
- `GET /health/live` - Liveness probe (is app running?)
- `GET /health/ready` - Readiness probe (can serve traffic?)
- `GET /health/startup` - Startup probe (initialization complete?)

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-05-01T19:00:00+00:00",
  "version": "1.0.0"
}
```

**Kubernetes Integration:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 3
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 2. Prometheus Metrics
**Router Prefix:** `/metrics`

**Environment Variables:**
- `PROMETHEUS_ENABLED=true` - Enable metrics endpoint
- `PROMETHEUS_PATH=/metrics` - Metrics endpoint path (default)

**Metrics Collected:**
- `http_requests_total` - Request count by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Concurrent requests gauge
- `db_queries_total` - Database query count
- `db_query_duration_seconds` - Query timing
- `file_uploads_total` - File upload tracking
- `sql_queries_total` - SQL query execution

**Prometheus Configuration:**
```yaml
scrape_configs:
  - job_name: 'duckdb-processor'
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
```

### 3. Structured Logging
**Environment Variables:**
- `LOG_LEVEL=INFO` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT=json` - Log format (json, console)
- `LOG_PRETTY=false` - Pretty console output
- `ENV=development` - Environment name

**Usage:**
```python
from src.api.monitoring.logging_config import get_logger

logger = get_logger(__name__)
logger.info("User uploaded file", user_id=123, file_type="csv", size_mb=5.2)
```

**Log Output (JSON):**
```json
{
  "timestamp": "2026-05-01T19:00:00.000000Z",
  "level": "info",
  "app": "duckdb-processor",
  "environment": "development",
  "message": "User uploaded file",
  "user_id": 123,
  "file_type": "csv",
  "size_mb": 5.2,
  "filename": "app.py",
  "lineno": 42,
  "func_name": "upload_file"
}
```

## Integration

### FastAPI Integration
```python
from fastapi import FastAPI
from src.api.monitoring import health, endpoints, middleware, metrics

app = FastAPI()

# Include routers
app.include_router(health.router)
app.include_router(endpoints.router)

# Add metrics middleware
app.add_middleware(metrics.MetricsMiddleware)

# Add logging middleware
app.add_middleware(middleware.LoggingMiddleware)
```

### Custom Metrics
```python
from src.api.monitoring.metrics import timed, track_file_upload

@timed("select")
def get_users():
    return db.query("SELECT * FROM users")

# Track file uploads
track_file_upload(status="success", file_type="csv")
```

## Configuration

### Development (console logging)
```bash
export LOG_FORMAT=console
export LOG_PRETTY=true
export LOG_LEVEL=DEBUG
export PROMETHEUS_ENABLED=false
```

### Production (JSON logging + Prometheus)
```bash
export LOG_FORMAT=json
export LOG_LEVEL=INFO
export ENV=production
export PROMETHEUS_ENABLED=true
```

## Dependencies

**Install:**
```bash
pip3 install structlog prometheus-client
```

**Or add to requirements.txt:**
```
structlog>=24.1.0
prometheus-client>=0.20.0
```

## Testing

### Health Check
```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/startup
```

### Metrics (when enabled)
```bash
curl http://localhost:8000/metrics
```

### View Logs
```bash
# JSON logs (production)
kubectl logs -f deployment/duckdb-processor | jq

# Console logs (development)
kubectl logs -f deployment/duckdb-processor
```

## Grafana Dashboards

**Recommended Dashboards:**
1. FastAPI Metrics Dashboard
2. Python Application Performance
3. Business Metrics (file uploads, SQL queries)

**AlertManager Rules:**
```yaml
groups:
  - name: duckdb-processor
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        annotations:
          summary: "95th percentile latency above 1s"
```

## Troubleshooting

### Metrics endpoint returns 503
**Cause:** Prometheus client not installed or disabled
**Fix:**
```bash
pip3 install prometheus-client
export PROMETHEUS_ENABLED=true
```

### Health checks fail
**Cause:** Dependencies not initialized
**Fix:** Check readiness endpoint for detailed status:
```bash
curl http://localhost:8000/health/ready
```

### Logs not appearing
**Cause:** Log level too high
**Fix:** Lower log level:
```bash
export LOG_LEVEL=DEBUG
```

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌────────────────┐ │
│  │ Health Router│  │ Metrics Router │ │
│  └──────────────┘  └────────────────┘ │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     Metrics Middleware            │  │
│  │  - Request counting               │  │
│  │  - Latency tracking               │  │
│  │  - In-flight requests             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │     Logging Middleware            │  │
│  │  - Request ID generation          │  │
│  │  - Request/response logging       │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  structlog (JSON)     │
        │  + Prometheus Metrics │
        └───────────────────────┘
```

## Best Practices

1. **Always use structured logging** - Add context to every log entry
2. **Track critical operations** - File uploads, database queries, external API calls
3. **Use appropriate log levels** - DEBUG for dev, INFO for production
4. **Set up alerts** - Monitor error rate, latency, and dependency health
5. **Test health probes** - Ensure they work before deploying to production

## References

- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [structlog Documentation](https://www.structlog.org/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
