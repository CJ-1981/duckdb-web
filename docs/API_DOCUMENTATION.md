# DuckDB Web Workflow Builder - API Documentation

## Enhanced Features API Reference

### Professional Reporting APIs

#### Generate PDF Report

```http
POST /api/v1/reports/generate/pdf
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "template_id": "executive-summary",
  "data_source": "workflow_results",
  "parameters": {
    "title": "Q1 Sales Report",
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-03-31"
    },
    "include_charts": true,
    "chart_types": ["bar", "line", "pie"],
    "branding": {
      "logo": "data:image/png;base64,...",
      "colors": ["#1f77b4", "#ff7f0e", "#2ca02c"]
    }
  }
}
```

**Response:**
```json
{
  "report_id": "rpt_20260426_001",
  "status": "completed",
  "download_url": "/api/v1/reports/download/rpt_20260426_001",
  "metadata": {
    "pages": 15,
    "size_bytes": 2048576,
    "generated_at": "2026-04-26T10:30:00Z"
  }
}
```

#### Generate Excel Report

```http
POST /api/v1/reports/generate/excel
Content-Type: application/json
```

**Request Body:**
```json
{
  "template_id": "financial-performance",
  "data_source": "workflow_results",
  "sheets": [
    {
      "name": "Summary",
      "type": "pivot_table",
      "data": "revenue_by_region"
    },
    {
      "name": "Charts",
      "type": "charts",
      "charts": [
        {
          "type": "line",
          "title": "Revenue Trend",
          "data_range": "A1:B12"
        }
      ]
    }
  ]
}
```

---

### Data Quality APIs

#### Profile Data

```http
POST /api/v1/data-quality/profile
Content-Type: application/json
```

**Request Body:**
```json
{
  "table_name": "sales_data",
  "columns": ["revenue", "quantity", "region", "date"]
}
```

**Response:**
```json
{
  "profile_id": "prof_20260426_001",
  "results": {
    "completeness": {
      "score": 0.95,
      "missing_values": {
        "revenue": 150,
        "quantity": 75
      }
    },
    "consistency": {
      "score": 0.88,
      "issues": [
        {
          "column": "date",
          "issue": "inconsistent_format",
          "affected_rows": 250
        }
      ]
    },
    "uniqueness": {
      "score": 1.0,
      "duplicate_keys": 0
    },
    "validity": {
      "score": 0.92,
      "outliers": {
        "revenue": {
          "count": 12,
          "threshold": "3σ"
        }
      }
    }
  }
}
```

#### Apply Data Quality Rules

```http
POST /api/v1/data-quality/rules/apply
Content-Type: application/json
```

**Request Body:**
```json
{
  "table_name": "sales_data",
  "rules": [
    {
      "type": "completeness",
      "column": "revenue",
      "action": "remove_rows",
      "threshold": 0.8
    },
    {
      "type": "outlier_detection",
      "column": "revenue",
      "method": "iqr",
      "action": "flag"
    },
    {
      "type": "standardization",
      "column": "date",
      "target_format": "ISO 8601"
    }
  ]
}
```

---

### Analytics and Insights APIs

#### Calculate KPIs

```http
POST /api/v1/analytics/kpis/calculate
Content-Type: application/json
```

**Request Body:**
```json
{
  "data_source": "sales_data",
  "kpis": [
    {
      "type": "trend",
      "metric": "revenue",
      "time_column": "date",
      "period": "monthly"
    },
    {
      "type": "growth_rate",
      "metric": "quantity",
      "baseline": "previous_quarter"
    },
    {
      "type": "anomaly_detection",
      "metric": "revenue",
      "method": "prophet"
    }
  ]
}
```

**Response:**
```json
{
  "kpi_id": "kpi_20260426_001",
  "results": [
    {
      "type": "trend",
      "metric": "revenue",
      "data": [
        {"period": "2026-01", "value": 1250000, "change": 0.05},
        {"period": "2026-02", "value": 1320000, "change": 0.06},
        {"period": "2026-03", "value": 1410000, "change": 0.07}
      ]
    },
    {
      "type": "growth_rate",
      "metric": "quantity",
      "value": 0.12,
      "baseline": "Q4 2025"
    },
    {
      "type": "anomaly_detection",
      "metric": "revenue",
      "anomalies": [
        {
          "date": "2026-02-15",
          "value": 85000,
          "expected": 65000,
          "severity": "high"
        }
      ]
    }
  ]
}
```

#### Generate Insights

```http
POST /api/v1/analytics/insights/generate
Content-Type: application/json
```

**Response:**
```json
{
  "insight_id": "ins_20260426_001",
  "insights": [
    {
      "type": "pattern",
      "description": "Revenue increased 15% in March due to seasonal demand",
      "confidence": 0.92,
      "recommendation": "Increase inventory for March 2027"
    },
    {
      "type": "correlation",
      "description": "Strong positive correlation (0.87) between marketing spend and revenue",
      "confidence": 0.89,
      "recommendation": "Allocate 20% more budget to marketing"
    }
  ]
}
```

---

### Workflow Automation APIs

#### Create Scheduled Workflow

```http
POST /api/v1/workflows/schedule
Content-Type: application/json
```

**Request Body:**
```json
{
  "workflow_id": "wf_daily_sales_report",
  "schedule": {
    "frequency": "daily",
    "time": "08:00",
    "timezone": "UTC"
  },
  "notifications": {
    "on_success": {
      "email": ["manager@company.com"],
      "attach_report": true
    },
    "on_failure": {
      "email": ["admin@company.com"],
      "include_error_logs": true
    }
  },
  "parameters": {
    "date_range": "yesterday",
    "template": "daily_sales_summary"
  }
}
```

#### Execute Workflow Template

```http
POST /api/v1/workflows/templates/execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "template_id": "customer_segmentation",
  "parameters": {
    "min_cluster_size": 50,
    "max_clusters": 8,
    "features": ["age", "income", "purchase_frequency"]
  },
  "output_config": {
    "destination": "customer_segments_table",
    "create_dashboard": true
  }
}
```

---

### Dashboard APIs

#### Create Dashboard

```http
POST /api/v1/dashboards/create
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Executive Sales Dashboard",
  "description": "Real-time sales metrics and KPIs",
  "widgets": [
    {
      "type": "chart",
      "chart_type": "line",
      "title": "Revenue Trend",
      "data_source": "kpis/revenue_trend",
      "refresh_interval": 300
    },
    {
      "type": "metric",
      "title": "Total Revenue",
      "data_source": "kpis/total_revenue",
      "format": "currency"
    },
    {
      "type": "table",
      "title": "Top Products",
      "data_source": "products/top_selling",
      "rows": 10
    }
  ],
  "filters": [
    {
      "field": "date_range",
      "type": "date_picker",
      "default": "last_30_days"
    },
    {
      "field": "region",
      "type": "multi_select",
      "options": ["North", "South", "East", "West"]
    }
  ]
}
```

#### Share Dashboard

```http
POST /api/v1/dashboards/{dashboard_id}/share
Content-Type: application/json
```

**Request Body:**
```json
{
  "access_type": "public",
  "permissions": ["view"],
  "embed_options": {
    "allow_filters": true,
    "allow_export": true,
    "theme": "light"
  }
}
```

---

### Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid data source configuration",
    "details": {
      "field": "data_source",
      "issue": "Table 'sales_data' not found"
    },
    "request_id": "req_20260426_123456"
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR`: Invalid request parameters
- `NOT_FOUND`: Requested resource not found
- `AUTHORIZATION_ERROR`: Authentication/authorization failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Authentication

All API requests require authentication using Bearer token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens can be obtained via:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "secure_password"
}
```

---

## Rate Limiting

- **Standard Users**: 100 requests/minute
- **Premium Users**: 1000 requests/minute
- **Enterprise**: Custom limits

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1714108800
```

---

## Webhooks

Configure webhooks for real-time notifications:

```http
POST /api/v1/webhooks/create
Content-Type: application/json

{
  "events": ["workflow.completed", "report.ready"],
  "url": "https://your-app.com/webhook",
  "secret": "webhook_secret_key"
}
```

---

*API Version: 2.0.0*  
*Last Updated: 2026-04-26*  
*Base URL: https://api.duckdb-workflow.com/v1*