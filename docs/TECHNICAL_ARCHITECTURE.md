# DuckDB Web Workflow Builder - Technical Architecture

## System Architecture Overview

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Next.js 16   │  │ React 19     │  │ React Flow   │      │
│  │ App Router   │  │ Components   │  │ Workflows    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ FastAPI      │  │ WebSocket    │  │ Middleware   │      │
│  │ REST API     │  │ Real-time    │  │ Auth/CORS    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Workflow     │  │ Reporting    │  │ Data Quality │      │
│  │ Engine       │  │ Service      │  │ Engine       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Analytics    │  │ Scheduling   │  │ Notification │      │
│  │ Service      │  │ Service      │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Data Processing Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DuckDB       │  │ Pandas       │  │ NumPy        │      │
│  │ In-Memory DB │  │ Data Frames  │  │ Computing    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Task Queue Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Celery       │  │ Redis        │  │ Task Store   │      │
│  │ Worker Pool  │  │ Message      │  │ PostgreSQL   │      │
│  │              │  │ Broker       │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Enhanced Component Architecture

### Professional Reporting Service

```python
class ReportingService:
    """
    Professional reporting service with template-based report generation.
    
    Components:
    - TemplateEngine: Jinja2-based template processing
    - ChartGenerator: Plotly chart generation
    - PDFGenerator: WeasyPrint PDF rendering
    - ExcelFormatter: OpenPyXL Excel formatting
    """
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.chart_generator = ChartGenerator()
        self.pdf_generator = PDFGenerator()
        self.excel_formatter = ExcelFormatter()
    
    async def generate_report(
        self,
        template_id: str,
        data_source: DataSource,
        config: ReportConfig
    ) -> ReportResult:
        """Generate professional report from template and data."""
        # Load template
        template = await self.template_engine.load(template_id)
        
        # Process data
        processed_data = await self._process_data(data_source, config)
        
        # Generate charts
        charts = await self.chart_generator.generate(
            processed_data,
            config.chart_config
        )
        
        # Render report
        report = await self.template_engine.render(
            template,
            data=processed_data,
            charts=charts,
            branding=config.branding
        )
        
        # Export to format
        result = await self._export_report(
            report,
            format=config.format,
            filename=config.filename
        )
        
        return result
```

### Data Quality Engine

```python
class DataQualityEngine:
    """
    Automated data profiling and quality validation.
    
    Features:
    - Completeness checking
    - Consistency validation
    - Uniqueness verification
    - Outlier detection
    """
    
    def __init__(self):
        self.profiler = DataProfiler()
        self.validator = DataValidator()
        self.cleaner = DataCleaner()
    
    async def profile_data(
        self,
        dataframe: pd.DataFrame,
        columns: List[str]
    ) -> DataProfile:
        """Generate comprehensive data profile."""
        profile = DataProfile()
        
        # Completeness analysis
        profile.completeness = self.profiler.check_completeness(
            dataframe, columns
        )
        
        # Consistency analysis
        profile.consistency = self.profiler.check_consistency(
            dataframe, columns
        )
        
        # Uniqueness analysis
        profile.uniqueness = self.profiler.check_uniqueness(
            dataframe, columns
        )
        
        # Validity analysis
        profile.validity = self.profiler.check_validity(
            dataframe, columns
        )
        
        return profile
    
    async def apply_rules(
        self,
        dataframe: pd.DataFrame,
        rules: List[QualityRule]
    ) -> CleanedData:
        """Apply data quality rules and return cleaned data."""
        for rule in rules:
            dataframe = await self.cleaner.apply_rule(
                dataframe, rule
            )
        
        return CleanedData(
            data=dataframe,
            applied_rules=rules,
            quality_score=self._calculate_quality(dataframe)
        )
```

### Analytics and Insights Service

```python
class AnalyticsService:
    """
    Business intelligence and KPI calculation engine.
    
    Features:
    - Trend analysis
    - Growth rate calculation
    - Anomaly detection
    - Pattern recognition
    - Insight generation
    """
    
    def __init__(self):
        self.kpi_calculator = KPICalculator()
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.insight_generator = InsightGenerator()
    
    async def calculate_kpis(
        self,
        data: pd.DataFrame,
        kpi_configs: List[KPIConfig]
    ) -> KPIResults:
        """Calculate KPIs based on configuration."""
        results = KPIResults()
        
        for config in kpi_configs:
            if config.type == "trend":
                kpi = await self.kpi_calculator.calculate_trend(
                    data, config.metric, config.time_column
                )
            elif config.type == "growth_rate":
                kpi = await self.kpi_calculator.calculate_growth_rate(
                    data, config.metric, config.baseline
                )
            elif config.type == "anomaly_detection":
                kpi = await self.anomaly_detector.detect_anomalies(
                    data, config.metric, config.method
                )
            
            results.add_kpi(kpi)
        
        return results
    
    async def generate_insights(
        self,
        data: pd.DataFrame,
        kpi_results: KPIResults
    ) -> List[Insight]:
        """Generate actionable insights from data and KPIs."""
        insights = []
        
        # Pattern recognition
        patterns = await self.insight_generator.detect_patterns(data)
        insights.extend(patterns)
        
        # Trend analysis
        trends = await self.trend_analyzer.analyze_trends(data)
        insights.extend(trends)
        
        # Correlation analysis
        correlations = await self.insight_generator.find_correlations(data)
        insights.extend(correlations)
        
        # Generate recommendations
        for insight in insights:
            insight.recommendation = await self._generate_recommendation(
                insight
            )
        
        return insights
```

---

## Database Schema

### Enhanced Schema for Professional Features

```sql
-- Report Templates
CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_public BOOLEAN DEFAULT false
);

CREATE INDEX idx_report_templates_type ON report_templates(template_type);
CREATE INDEX idx_report_templates_public ON report_templates(is_public);

-- Workflow Templates
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    template_config JSONB NOT NULL,
    parameters JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

-- Data Quality Rules
CREATE TABLE data_quality_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_quality_rules_type ON data_quality_rules(rule_type);
CREATE INDEX idx_quality_rules_active ON data_quality_rules(active);

-- Scheduled Workflows
CREATE TABLE scheduled_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflows(id),
    schedule_config JSONB NOT NULL,
    notification_config JSONB,
    active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scheduled_workflows_active ON scheduled_workflows(active);
CREATE INDEX idx_scheduled_workflows_next_run ON scheduled_workflows(next_run_at);

-- Dashboards
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    access_type VARCHAR(20) DEFAULT 'private',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dashboards_access ON dashboards(access_type);
CREATE INDEX idx_dashboards_owner ON dashboards(created_by);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Report Generation History
CREATE TABLE report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES report_templates(id),
    workflow_id UUID REFERENCES workflows(id),
    format VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    file_path TEXT,
    error_message TEXT,
    generated_at TIMESTAMP DEFAULT NOW(),
    generated_by UUID REFERENCES users(id)
);

CREATE INDEX idx_report_history_template ON report_history(template_id);
CREATE INDEX idx_report_history_workflow ON report_history(workflow_id);
CREATE INDEX idx_report_history_generated ON report_history(generated_at);
```

---

## API Architecture

### RESTful API Design

```
/api/v2/
├── /auth/
│   ├── /login
│   ├── /logout
│   └── /refresh
├── /workflows/
│   ├── / (list, create)
│   ├── /{id}/ (get, update, delete)
│   ├── /{id}/execute
│   └── /templates/
├── /reports/
│   ├── /generate (POST)
│   ├── /templates/
│   ├── /history/
│   └── /download/{id}
├── /data-quality/
│   ├── /profile (POST)
│   ├── /rules/
│   └── /clean (POST)
├── /analytics/
│   ├── /kpis/calculate (POST)
│   ├── /insights/generate (POST)
│   └── /trends/analyze (POST)
├── /dashboards/
│   ├── / (list, create)
│   ├── /{id}/ (get, update, delete)
│   └── /{id}/share
└── /schedules/
    ├── / (list, create)
    └── /{id}/ (get, update, delete, pause, resume)
```

### WebSocket Events

```javascript
// Real-time workflow updates
socket.on('workflow.started', (data) => {
  console.log('Workflow started:', data.workflow_id);
});

socket.on('workflow.progress', (data) => {
  updateProgressBar(data.progress, data.node_id);
});

socket.on('workflow.completed', (data) => {
  showResults(data.results);
});

// Real-time KPI updates
socket.on('kpi.updated', (data) => {
  updateDashboardWidget(data.widget_id, data.value);
});

// Real-time alerts
socket.on('alert.triggered', (data) => {
  showAlert(data.alert_type, data.message);
});
```

---

## Performance Optimization

### Caching Strategy

```python
# Redis caching layer
class CacheManager:
    def __init__(self):
        self.redis = Redis(host='localhost', port=6379, db=0)
        self.default_ttl = 3600  # 1 hour
    
    async def cache_report_template(self, template_id: str, template: dict):
        """Cache report template for fast access."""
        key = f"template:{template_id}"
        await self.redis.setex(
            key,
            self.default_ttl,
            json.dumps(template)
        )
    
    async def cache_kpi_results(self, kpi_id: str, results: dict):
        """Cache KPI calculation results."""
        key = f"kpi:{kpi_id}"
        await self.redis.setex(
            key,
            1800,  # 30 minutes
            json.dumps(results)
        )
    
    async def invalidate_data_cache(self, table_name: str):
        """Invalidate all caches related to a data table."""
        pattern = f"data:{table_name}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

### Query Optimization

```python
# DuckDB query optimization
class QueryOptimizer:
    def optimize_query(self, query: str, data_size: int) -> str:
        """Optimize query based on data size."""
        if data_size > 1_000_000:  # Large dataset
            # Add parallel execution hints
            query = f"SET threads=4;\n{query}"
            
            # Use columnar scanning
            query = query.replace("SELECT *", "SELECT column1, column2")
        
        elif data_size > 100_000:  # Medium dataset
            # Add result caching
            query = f"SET enable_object_cache=true;\n{query}"
        
        return query
```

---

## Security Architecture

### Authentication and Authorization

```python
# JWT-based authentication
class AuthService:
    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token."""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

# Role-based access control
class AuthorizationService:
    def check_permission(
        self,
        user: User,
        resource: str,
        action: str
    ) -> bool:
        """Check if user has permission for action on resource."""
        role_permissions = {
            'admin': ['*'],
            'analyst': ['read', 'create', 'execute'],
            'viewer': ['read']
        }
        
        user_permissions = role_permissions.get(user.role, [])
        return '*' in user_permissions or action in user_permissions
```

### Data Encryption

```python
# Sensitive data encryption
class EncryptionService:
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.GCM(nonce),
            backend=default_backend()
        )
        ciphertext = cipher.encryptor().update(data.encode()) + cipher.encryptor().finalize()
        return base64.b64encode(ciphertext).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.GCM(nonce),
            backend=default_backend()
        )
        decrypted = cipher.decryptor().update(base64.b64decode(encrypted_data)) + cipher.decryptor().finalize()
        return decrypted.decode()
```

---

## Monitoring and Observability

### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_counter = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

# Business metrics
report_generation_duration = Histogram(
    'report_generation_duration_seconds',
    'Report generation duration',
    ['template_type', 'format']
)

data_quality_score = Gauge(
    'data_quality_score',
    'Current data quality score',
    ['table_name']
)

workflow_execution_duration = Histogram(
    'workflow_execution_duration_seconds',
    'Workflow execution duration',
    ['workflow_type']
)
```

### Logging Strategy

```python
# Structured logging
import structlog

logger = structlog.get_logger()

# Log workflow execution
logger.info(
    "workflow_execution_started",
    workflow_id=workflow_id,
    user_id=user.id,
    workflow_type=workflow.type,
    timestamp=datetime.utcnow().isoformat()
)

# Log report generation
logger.info(
    "report_generation_completed",
    report_id=report_id,
    template_id=template_id,
    format=format,
    duration_seconds=duration,
    file_size_bytes=file_size
)

# Log errors
logger.error(
    "workflow_execution_failed",
    workflow_id=workflow_id,
    error_type=error.__class__.__name__,
    error_message=str(error),
    traceback=traceback.format_exc()
)
```

---

*Technical Architecture Version: 2.0.0*  
*Last Updated: 2026-04-26*