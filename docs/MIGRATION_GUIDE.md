# Migration Guide: Upgrading to Enhanced Features

## Overview

This guide helps you migrate from the basic DuckDB Web Workflow Builder to the enhanced version with professional reporting, data quality automation, and business intelligence features.

---

## Migration Checklist

### Pre-Migration Preparation

- [ ] Backup your current workflows and data
- [ ] Review new features and API changes
- [ ] Plan migration timeline (recommended: 2-4 weeks)
- [ ] Test migration in staging environment first
- [ ] Notify users of upcoming changes and downtime

### System Requirements

**Before Migration:**
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

**New Requirements:**
- Python 3.13+
- Additional disk space (5GB for templates and charts)
- More memory (8GB RAM recommended for large reports)

---

## Step 1: Environment Setup

### 1.1 Install New Dependencies

```bash
# Backend dependencies
pip install jinja2==3.1.2
pip install plotly==5.17.0
pip install weasyprint==60.2
pip install scikit-learn==1.3.2
pip install prophet==1.1.4

# Frontend dependencies
npm install react-chartjs-2@^5.2.0
npm install react-pdf@^7.2.0
npm install zustand@^4.4.7
```

### 1.2 Database Schema Migration

```bash
# Run migration script
python migrations/migrate_to_v2.py

# Expected output:
# ✓ Creating report_templates table
# ✓ Creating workflow_templates table
# ✓ Creating data_quality_rules table
# ✓ Creating scheduled_workflows table
# ✓ Creating dashboards table
# ✓ Creating audit_logs table
# ✓ Migration completed successfully
```

### 1.3 Update Configuration Files

```yaml
# config/production.yaml
reporting:
  enabled: true
  templates_path: /var/lib/duckdb-web/templates
  export_path: /var/lib/duckdb-web/exports
  max_file_size: 100MB

data_quality:
  enabled: true
  auto_profile: true
  quality_threshold: 0.85

analytics:
  enabled: true
  cache_ttl: 1800
  max_kpi_calculations: 100

scheduling:
  enabled: true
  celery_broker: redis://localhost:6379/0
  celery_backend: redis://localhost:6379/1
```

---

## Step 2: Data Migration

### 2.1 Migrate Existing Workflows

Your existing workflows will continue to work, but you can enhance them with new features:

```python
# Old workflow (still works)
workflow = Workflow("sales_analysis")
workflow.add_node("import_csv", "data.csv")
workflow.add_node("sql_query", "SELECT * FROM data")
results = workflow.execute()

# Enhanced workflow (new features)
workflow = Workflow("sales_analysis_enhanced")
workflow.add_node("import_csv", "data.csv")
workflow.add_node("data_quality", "profile_and_clean")
workflow.add_node("sql_query", "SELECT * FROM cleaned_data")
workflow.add_node("analytics", "calculate_kpis")
workflow.add_node("report", "generate_executive_summary")
results = workflow.execute()
```

### 2.2 Migrate Export Configurations

**Old Export Code:**
```python
exporter = DataExporter(connection)
exporter.export_csv("output.csv", query="SELECT * FROM results")
```

**New Export Code:**
```python
reporter = ReportingService()
reporter.generate_report(
    template_id="executive_summary",
    data_source="results",
    config={
        "format": "pdf",
        "include_charts": True,
        "filename": "output_report"
    }
)
```

---

## Step 3: API Migration

### 3.1 API Version Changes

**Old API (v1):**
```
POST /api/v1/export
GET /api/v1/workflows/:id
```

**New API (v2):**
```
POST /api/v2/reports/generate
GET /api/v2/workflows/:id
POST /api/v2/analytics/kpis/calculate
POST /api/v2/data-quality/profile
```

### 3.2 Breaking Changes

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| `/api/v1/export` | `/api/v2/reports/generate` | Enhanced parameters |
| `/api/v1/workflows/run` | `/api/v2/workflows/:id/execute` | Same functionality |
| *N/A* | `/api/v2/data-quality/profile` | New endpoint |
| *N/A* | `/api/v2/analytics/insights/generate` | New endpoint |

### 3.3 Authentication Changes

**Old API Key:**
```http
Authorization: ApiKey your-api-key-here
```

**New JWT Token:**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Migration Code:**
```python
# Old authentication
headers = {"Authorization": f"ApiKey {API_KEY}"}

# New authentication
token = auth_service.create_access_token(user_id)
headers = {"Authorization": f"Bearer {token}"}
```

---

## Step 4: Feature Migration

### 4.1 Migrating Basic Exports to Professional Reports

**Before: Simple CSV Export**
```python
# Basic export
exporter = DataExporter(connection)
exporter.export_csv("sales_report.csv", query=sales_query)
```

**After: Professional PDF Report**
```python
# Professional report with charts
report_config = {
    "template_id": "sales_analytics",
    "data_source": sales_results,
    "format": "pdf",
    "include_charts": True,
    "chart_types": ["bar", "line", "pie"],
    "branding": {
        "logo": "/path/to/logo.png",
        "colors": ["#1f77b4", "#ff7f0e"]
    }
}

reporter = ReportingService()
report_result = await reporter.generate_report(**report_config)
```

### 4.2 Adding Data Quality Automation

**Before: Manual Data Validation**
```python
# Manual validation
query = "SELECT * FROM data WHERE revenue > 0"
results = connection.execute(query)
```

**After: Automated Data Quality**
```python
# Automated profiling and cleaning
quality_engine = DataQualityEngine()

# Profile data
profile = await quality_engine.profile_data(
    dataframe=df,
    columns=["revenue", "quantity", "date"]
)

# Apply quality rules
rules = [
    QualityRule(type="completeness", column="revenue", threshold=0.8),
    QualityRule(type="outlier_detection", column="revenue", method="iqr")
]

cleaned_data = await quality_engine.apply_rules(df, rules)
```

### 4.3 Adding Business Intelligence

**Before: Manual KPI Calculation**
```python
# Manual calculation
total_revenue = df["revenue"].sum()
avg_revenue = df["revenue"].mean()
```

**After: Automated KPIs and Insights**
```python
# Automated KPI calculation
analytics = AnalyticsService()

kpi_config = [
    KPIConfig(type="trend", metric="revenue", time_column="date"),
    KPIConfig(type="growth_rate", metric="revenue", baseline="previous_quarter"),
    KPIConfig(type="anomaly_detection", metric="revenue", method="prophet")
]

kpi_results = await analytics.calculate_kpis(df, kpi_config)

# Generate insights
insights = await analytics.generate_insights(df, kpi_results)
```

---

## Step 5: Frontend Migration

### 5.1 Component Updates

**Old Components:**
```tsx
import { WorkflowBuilder } from '@/components/workflow-builder';
import { ExportButton } from '@/components/export-button';
```

**New Components:**
```tsx
import { WorkflowBuilder } from '@/components/workflow-builder';
import { ReportGenerator } from '@/components/reports/ReportGenerator';
import { DataQualityPanel } from '@/components/data-quality/QualityPanel';
import { DashboardViewer } from '@/components/dashboards/DashboardViewer';
import { KPIMonitor } from '@/components/analytics/KPIMonitor';
```

### 5.2 State Management Migration

**Old (local state):**
```tsx
const [workflows, setWorkflows] = useState<Workflow[]>([]);
```

**New (Zustand store):**
```tsx
import useWorkflowStore from '@/stores/workflow-store';
import useReportStore from '@/stores/report-store';

const workflows = useWorkflowStore(state => state.workflows);
const generateReport = useReportStore(state => state.generateReport);
```

---

## Step 6: Testing

### 6.1 Migration Testing Checklist

**Functionality Tests:**
- [ ] Create and execute workflow
- [ ] Generate professional report
- [ ] Run data quality profiling
- [ ] Calculate KPIs and generate insights
- [ ] Create and share dashboard
- [ ] Schedule automated workflow

**Integration Tests:**
- [ ] API authentication and authorization
- [ ] WebSocket real-time updates
- [ ] File upload and export
- [ ] Email notifications
- [ ] Scheduled task execution

**Performance Tests:**
- [ ] Report generation time (< 30s for standard reports)
- [ ] Data quality profiling time (< 10s for 100K rows)
- [ ] Dashboard loading time (< 3s for 5 widgets)
- [ ] API response time (< 500ms for p95)

### 6.2 Rollback Plan

If migration fails:

```bash
# Rollback database schema
python migrations/rollback_v2.py

# Restore previous version
git checkout tags/v1.0.0

# Restart services
systemctl restart duckdb-web
systemctl restart celery-worker
```

---

## Step 7: User Training

### 7.1 New Features Overview

**For Report Creators:**
- Professional report generation with templates
- Custom branding and formatting
- Interactive chart creation
- Scheduled report delivery

**For Data Analysts:**
- Automated data quality profiling
- Data cleaning rules
- Outlier detection
- Data validation

**For Business Users:**
- KPI dashboards
- Trend analysis
- Insight generation
- Automated alerts

### 7.2 Training Resources

- **Video Tutorials**: 15-minute feature overviews
- **Interactive Demo**: Sample workflows and reports
- **Documentation**: Comprehensive user guides
- **Support Chat**: In-app help and Q&A

---

## Step 8: Post-Migration

### 8.1 Monitoring

**Key Metrics to Monitor:**
- Report generation success rate
- Data quality score trends
- KPI calculation performance
- User adoption rates

**Alert Thresholds:**
- Report generation failure rate > 5%
- Data quality score < 0.80
- API response time > 2s
- Scheduled task failure rate > 2%

### 8.2 Optimization

**Week 1-2:** Monitor performance and user feedback
**Week 3-4:** Optimize based on usage patterns
**Month 2-3:** Implement advanced features and customizations

---

## Troubleshooting

### Common Migration Issues

**Issue 1: Database Migration Fails**
```bash
# Solution: Check database permissions
GRANT ALL PRIVILEGES ON DATABASE duckdb_web TO duckdb_user;

# Re-run migration
python migrations/migrate_to_v2.py --force
```

**Issue 2: Report Generation Times Out**
```python
# Solution: Increase timeout and optimize query
config = {
    "timeout": 60,  # Increase from 30 to 60 seconds
    "optimize_query": True,
    "use_cache": True
}
```

**Issue 3: Authentication Errors**
```python
# Solution: Update API keys to JWT tokens
old_api_key = "your-old-api-key"
new_token = auth_service.migrate_api_key(old_api_key)
```

**Issue 4: Frontend Build Fails**
```bash
# Solution: Clear cache and reinstall dependencies
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Support and Resources

**Documentation:**
- API Reference: `/docs/API_DOCUMENTATION.md`
- User Guides: `/docs/USER_GUIDE_*.md`
- Technical Architecture: `/docs/TECHNICAL_ARCHITECTURE.md`

**Support Channels:**
- Email: support@duckdb-workflow.com
- Slack: #duckdb-workflow-support
- Issues: GitHub Issues

**Migration Support:**
- Dedicated migration specialist
- Custom migration planning
- On-site training available

---

*Migration Guide Version: 2.0.0*  
*Last Updated: 2026-04-26*  
*Migrates From: v1.0.0*  
*Migrates To: v2.0.0*