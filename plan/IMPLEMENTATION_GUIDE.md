# Implementation Guide for DuckDB Web Workflow Builder Enhancements

This guide provides detailed implementation instructions for the enhancement features outlined in the roadmap. It includes code snippets, configuration examples, and step-by-step implementation processes.

---

## 1. Professional Reporting System Implementation

### 1.1 Backend Implementation

#### 1.1.1 Report Template Engine

Create `src/core/processor/reporting.py`:

```python
"""
Professional Reporting Module

Handles report generation with templates, charts, and insights.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import pandas as pd
import duckdb
from jinja2 import Environment, FileSystemLoader, Template
import plotly.graph_objects as go
import plotly.express as px
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

class ReportTemplateEngine:
    """Template-based report generation engine"""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
            autoescape=True
        )
        
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context"""
        template = self._jinja_env.get_template(template_name)
        return template.render(**context)
    
    def generate_pdf_report(
        self,
        query: str,
        template_name: str,
        config: Dict[str, Any]
    ) -> bytes:
        """Generate PDF report from query results"""
        # Execute query
        df = self._connection.execute(query).df()
        
        # Generate insights
        insights = self._generate_insights(df)
        
        # Create charts
        charts = self._create_charts(df, config.get('charts', []))
        
        # Prepare context
        context = {
            'data': df,
            'insights': insights,
            'charts': charts,
            'config': config,
            'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Render HTML
        html_content = self.render_template(template_name, context)
        
        # Convert to PDF
        css = CSS(string=self._get_report_css())
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
        
        return pdf_bytes
    
    def _generate_insights(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate automated insights from data"""
        insights = []
        
        # Basic statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            insights.append({
                'type': 'statistical',
                'title': 'Data Summary',
                'description': f"Dataset contains {len(df)} records with {len(numeric_cols)} numeric columns",
                'metrics': {
                    'total_records': len(df),
                    'numeric_columns': len(numeric_cols),
                    'missing_values': df.isnull().sum().sum()
                }
            })
        
        # Trend analysis (if time column exists
        time_cols = df.select_dtypes(include=['datetime']).columns
        if len(time_cols) > 0:
            insights.append({
                'type': 'temporal',
                'title': 'Time Series Analysis',
                'description': f"Data contains {len(time_cols)} time-based columns",
                'recommendations': ['Consider temporal aggregations', 'Check for seasonality patterns']
            })
        
        return insights
    
    def _create_charts(self, df: pd.DataFrame, chart_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create charts based on configuration"""
        charts = []
        
        for config in chart_configs:
            chart_type = config.get('type', 'bar')
            
            if chart_type == 'bar':
                fig = px.bar(df, x=config['x'], y=config['y'])
            elif chart_type == 'line':
                fig = px.line(df, x=config['x'], y=config['y'])
            elif chart_type == 'pie':
                fig = px.pie(df, values=config['values'], names=config['names'])
            else:
                continue
            
            # Update layout
            fig.update_layout(
                title=config.get('title', ''),
                height=400
            )
            
            charts.append({
                'type': chart_type,
                'config': config,
                'html': fig.to_html(include_plotlyjs='cdn')
            })
        
        return charts
    
    def _get_report_css(self) -> str:
        """Get CSS styles for reports"""
        return """
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .chart { margin: 20px 0; }
        .insight { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        """

class ReportManager:
    """Manages report templates and generation"""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection
        self._template_engine = ReportTemplateEngine(connection)
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load available report templates"""
        return {
            'executive_summary': {
                'file': 'executive_summary.html',
                'description': 'Executive summary with key metrics and insights'
            },
            'financial_report': {
                'file': 'financial_report.html',
                'description': 'Financial performance analysis with charts'
            },
            'sales_analytics': {
                'file': 'sales_analytics.html',
                'description': 'Sales data analysis with trend charts'
            }
        }
    
    def generate_report(
        self,
        report_type: str,
        query: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a report of specified type"""
        if report_type not in self._templates:
            raise ValueError(f"Unknown report type: {report_type}")
        
        config = config or {}
        
        # Generate PDF
        pdf_bytes = self._template_engine.generate_pdf_report(
            query=query,
            template_name=self._templates[report_type]['file'],
            config=config
        )
        
        # Generate insights
        df = self._connection.execute(query).df()
        insights = self._template_engine._generate_insights(df)
        
        return {
            'type': 'pdf',
            'data': pdf_bytes,
            'size': len(pdf_bytes),
            'insights': insights,
            'template': report_type
        }
```

#### 1.1.2 Report Templates

Create `src/core/processor/templates/executive_summary.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Executive Summary</title>
    <style>{{ report_css }}</style>
</head>
<body>
    <div class="header">
        <h1>Executive Summary Report</h1>
        <p>Generated on {{ generated_at }}</p>
    </div>
    
    <div class="section">
        <h2>Key Metrics</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Trend</th>
                </tr>
            </thead>
            <tbody>
                {% for metric in key_metrics %}
                <tr>
                    <td>{{ metric.name }}</td>
                    <td>{{ metric.value }}</td>
                    <td>{{ metric.trend }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>Insights</h2>
        {% for insight in insights %}
        <div class="insight">
            <h3>{{ insight.title }}</h3>
            <p>{{ insight.description }}</p>
            {% if insight.recommendations %}
            <ul>
                {% for rec in insight.recommendations %}
                <li>{{ rec }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2>Visualizations</h2>
        {% for chart in charts %}
        <div class="chart">
            {{ chart.html|safe }}
        </div>
        {% endfor %}
    </div>
</body>
</html>
```

### 1.2 Frontend Implementation

#### 1.2.1 Report Component

Create `src/components/reports/ReportGenerator.tsx`:

```typescript
import React, { useState } from 'react';
import { Button, Select, Input, Tabs, Card } from 'antd';
import { DownloadOutlined, EyeOutlined } from '@ant-design/icons';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';

const { Option } = Select;
const { TabPane } = Tabs;

interface ReportConfig {
  type: string;
  title: string;
  query: string;
  charts: ChartConfig[];
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie';
  x?: string;
  y?: string;
  values?: string;
  names?: string;
  title: string;
}

const ReportGenerator: React.FC = () => {
  const [reportType, setReportType] = useState<string>('executive_summary');
  const [reportTitle, setReportTitle] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [previewHtml, setPreviewHtml] = useState<string>('');

  const reportTemplates = [
    { value: 'executive_summary', label: 'Executive Summary' },
    { value: 'financial_report', label: 'Financial Report' },
    { value: 'sales_analytics', label: 'Sales Analytics' },
  ];

  const handleGenerateReport = async () => {
    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: reportType,
          title: reportTitle,
          query,
          charts,
        }),
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportTitle || 'report'}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const handlePreview = async () => {
    try {
      const response = await fetch('/api/reports/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: reportType,
          query,
          charts,
        }),
      });

      const html = await response.text();
      setPreviewHtml(html);
    } catch (error) {
      console.error('Error generating preview:', error);
    }
  };

  return (
    <div className="report-generator">
      <Card title="Report Generator">
        <Tabs defaultActiveKey="1">
          <TabPane tab="Configuration" key="1">
            <div style={{ marginBottom: 16 }}>
              <label>Report Type:</label>
              <Select
                value={reportType}
                onChange={setReportType}
                style={{ width: '100%', marginTop: 8 }}
              >
                {reportTemplates.map(template => (
                  <Option key={template.value} value={template.value}>
                    {template.label}
                  </Option>
                ))}
              </Select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label>Report Title:</label>
              <Input
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="Enter report title"
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label>SQL Query:</label>
              <ReactQuill
                value={query}
                onChange={setQuery}
                theme="snow"
                style={{ height: 200 }}
              />
            </div>

            <div style={{ marginBottom: 16 }}>
              <label>Charts:</label>
              {/* Chart configuration UI would go here */}
            </div>

            <div style={{ display: 'flex', gap: 16 }}>
              <Button
                type="primary"
                icon={<EyeOutlined />}
                onClick={handlePreview}
              >
                Preview
              </Button>
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleGenerateReport}
              >
                Generate PDF
              </Button>
            </div>
          </TabPane>

          <TabPane tab="Preview" key="2">
            {previewHtml ? (
              <iframe
                srcDoc={previewHtml}
                style={{ width: '100%', height: '600px', border: 'none' }}
              />
            ) : (
              <p>Generate a preview to see your report</p>
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default ReportGenerator;
```

### 1.3 API Endpoints

Add to `src/api/routes/reports.py`:

```python
"""
Report API Routes
"""

from fastapi import APIRouter, HTTPException, UploadFile
from typing import Dict, Any, List
import tempfile
import uuid

from ..models.base import get_processor
from ..schemas.report import ReportGenerateRequest, ReportPreviewRequest

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate")
async def generate_report(request: ReportGenerateRequest) -> Dict[str, Any]:
    """Generate a professional report"""
    try:
        processor = get_processor()
        
        # Generate report
        result = processor.report_manager.generate_report(
            report_type=request.type,
            query=request.query,
            config=request.dict(exclude={'type', 'query'})
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(result['data'])
            tmp_file.flush()
            
            return {
                "success": True,
                "file_path": tmp_file.name,
                "size": result['size'],
                "insights": result['insights'],
                "template": request.type
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview")
async def preview_report(request: ReportPreviewRequest) -> Dict[str, Any]:
    """Generate report preview as HTML"""
    try:
        processor = get_processor()
        
        # Generate HTML preview
        df = processor._connection.execute(request.query).df()
        insights = processor.report_manager._template_engine._generate_insights(df)
        
        return {
            "success": True,
            "html": processor.report_manager.render_template(
                f"{request.type}.html",
                {
                    "data": df,
                    "insights": insights,
                    "charts": [],
                    "config": {},
                    "generated_at": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 2. Data Quality System Implementation

### 2.1 Backend Implementation

#### 2.1.1 Data Quality Engine

Create `src/core/processor/data_quality.py`:

```python
"""
Data Quality Module

Automated data validation, cleaning, and quality reporting.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
import duckdb

logger = logging.getLogger(__name__)

class QualityRuleType(Enum):
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    TIMELINESS = "timeliness"

@dataclass
class QualityRule:
    """Data quality rule definition"""
    name: str
    type: QualityRuleType
    column: str
    parameters: Dict[str, Any]
    threshold: float = 0.8
    active: bool = True

@dataclass
class QualityResult:
    """Quality check result"""
    rule_name: str
    passed: bool
    score: float
    message: str
    details: Dict[str, Any]
    severity: str = "info"  # info, warning, error

class DataQualityEngine:
    """Automated data quality checking and cleaning"""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        self._connection = connection
        self._rules: Dict[str, QualityRule] = {}
        self._default_rules = self._create_default_rules()
    
    def _create_default_rules(self) -> Dict[str, QualityRule]:
        """Create default data quality rules"""
        return {
            'null_check': QualityRule(
                name="Null Value Check",
                type=QualityRuleType.COMPLETENESS,
                column="*",
                parameters={"max_null_percentage": 0.05},
                threshold=0.95
            ),
            'duplicate_check': QualityRule(
                name="Duplicate Record Check",
                type=QualityRuleType.UNIQUENESS,
                column="*",
                parameters={},
                threshold=1.0
            ),
            'data_type_check': QualityRule(
                name="Data Type Validation",
                type=QualityRuleType.VALIDITY,
                column="*",
                parameters={},
                threshold=0.95
            )
        }
    
    def add_rule(self, rule: QualityRule) -> None:
        """Add a custom quality rule"""
        self._rules[rule.name] = rule
    
    def validate_data(self, table_name: str, rules: Optional[List[str]] = None) -> List[QualityResult]:
        """Validate data against quality rules"""
        results = []
        
        # Get table schema
        df_info = self._connection.execute(f"PRAGMA table_info('{table_name}')").df()
        columns = df_info['name'].tolist()
        
        # Determine rules to check
        rules_to_check = rules or list(self._default_rules.keys()) + list(self._rules.keys())
        
        for rule_name in rules_to_check:
            if rule_name in self._default_rules:
                rule = self._default_rules[rule_name]
                result = self._check_rule(rule, table_name, columns)
                results.append(result)
            elif rule_name in self._rules:
                rule = self._rules[rule_name]
                result = self._check_rule(rule, table_name, columns)
                results.append(result)
        
        return results
    
    def _check_rule(self, rule: QualityRule, table_name: str, columns: List[str]) -> QualityResult:
        """Check a single quality rule"""
        try:
            if rule.type == QualityRuleType.COMPLETENESS:
                return self._check_completeness(rule, table_name)
            elif rule.type == QualityRuleType.UNIQUENESS:
                return self._check_uniqueness(rule, table_name)
            elif rule.type == QualityRuleType.VALIDITY:
                return self._check_validity(rule, table_name)
            else:
                return QualityResult(
                    rule_name=rule.name,
                    passed=False,
                    score=0.0,
                    message=f"Unsupported rule type: {rule.type}",
                    details={},
                    severity="warning"
                )
        except Exception as e:
            return QualityResult(
                rule_name=rule.name,
                passed=False,
                score=0.0,
                message=f"Error checking rule: {str(e)}",
                details={},
                severity="error"
            )
    
    def _check_completeness(self, rule: QualityRule, table_name: str) -> QualityResult:
        """Check data completeness (null values)"""
        max_null_pct = rule.parameters.get('max_null_percentage', 0.05)
        
        # Check for null values
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            SUM(CASE WHEN {rule.column} IS NULL THEN 1 ELSE 0 END) as null_count,
            SUM(CASE WHEN {rule.column} IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as null_percentage
        FROM {table_name}
        """
        
        result = self._connection.execute(query).fetchone()
        total_rows, null_count, null_pct = result
        
        score = max(0, 1 - (null_pct / 100))
        passed = score >= rule.threshold
        
        return QualityResult(
            rule_name=rule.name,
            passed=passed,
            score=score,
            message=f"Null percentage: {null_pct:.2f}%" if passed else f"Exceeds threshold {max_null_pct*100}%",
            details={
                "total_rows": total_rows,
                "null_count": null_count,
                "null_percentage": null_pct,
                "threshold": rule.threshold
            },
            severity="error" if not passed else "info"
        )
    
    def _check_uniqueness(self, rule: QualityRule, table_name: str) -> QualityResult:
        """Check data uniqueness (duplicates)"""
        query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT {rule.column}) as distinct_count,
            (COUNT(DISTINCT {rule.column}) * 100.0 / COUNT(*)) as uniqueness_score
        FROM {table_name}
        """
        
        result = self._connection.execute(query).fetchone()
        total_rows, distinct_count, uniqueness_score = result
        
        score = uniqueness_score / 100
        passed = score >= rule.threshold
        
        return QualityResult(
            rule_name=rule.name,
            passed=passed,
            score=score,
            message=f"Uniqueness score: {uniqueness_score:.2f}%" if passed else f"Below threshold {rule.threshold*100}%",
            details={
                "total_rows": total_rows,
                "distinct_count": distinct_count,
                "uniqueness_score": uniqueness_score,
                "threshold": rule.threshold
            },
            severity="warning" if not passed else "info"
        )
    
    def clean_data(self, table_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Clean data based on configuration"""
        cleaned_table = f"{table_name}_cleaned"
        operations = []
        
        # Remove duplicates
        if config.get('remove_duplicates', False):
            duplicate_columns = config.get('duplicate_columns', ['*'])
            if '*' in duplicate_columns:
                query = f"""
                SELECT DISTINCT * FROM {table_name}
                """
                operations.append("Removed duplicate records")
            else:
                columns_str = ', '.join(duplicate_columns)
                query = f"""
                SELECT DISTINCT {columns_str}, * FROM {table_name}
                GROUP BY {columns_str}
                """
                operations.append(f"Removed duplicates by columns: {columns_str}")
            
            self._connection.execute(f"CREATE TABLE {cleaned_table} AS {query}")
        
        # Handle null values
        if config.get('handle_nulls', False):
            null_strategy = config.get('null_strategy', 'drop')
            
            if null_strategy == 'drop':
                query = f"""
                SELECT * FROM {table_name}
                WHERE {self._build_null_conditions(config.get('null_columns', []))}
                """
                operations.append("Dropped records with null values")
            elif null_strategy == 'fill':
                fill_values = config.get('fill_values', {})
                operations.extend([f"Filled {col} with {value}" for col, value in fill_values.items()])
                
                # Build query with fill values
                select_parts = []
                for col in self._get_table_columns(table_name):
                    if col in fill_values:
                        select_parts.append(f"COALESCE({col}, {fill_values[col]}) as {col}")
                    else:
                        select_parts.append(col)
                
                query = f"SELECT {', '.join(select_parts)} FROM {table_name}"
            
            if 'cleaned_table' not in locals():
                self._connection.execute(f"CREATE TABLE {cleaned_table} AS {query}")
        
        if 'cleaned_table' not in locals():
            self._connection.execute(f"CREATE TABLE {cleaned_table} AS SELECT * FROM {table_name}")
        
        return {
            "original_table": table_name,
            "cleaned_table": cleaned_table,
            "operations": operations,
            "summary": self._generate_cleaning_summary(cleaned_table)
        }
    
    def _build_null_conditions(self, columns: List[str]) -> str:
        """Build WHERE clause conditions for null handling"""
        conditions = []
        for col in columns:
            conditions.append(f"{col} IS NOT NULL")
        return " AND ".join(conditions)
    
    def _get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        df_info = self._connection.execute(f"PRAGMA table_info('{table_name}')").df()
        return df_info['name'].tolist()
    
    def _generate_cleaning_summary(self, table_name: str) -> Dict[str, Any]:
        """Generate summary of cleaning results"""
        query = f"""
        SELECT 
            COUNT(*) as row_count,
            (SELECT COUNT(*) FROM {table_name.split('_')[0]}) as original_count
        FROM {table_name}
        """
        
        result = self._connection.execute(query).fetchone()
        row_count, original_count = result
        
        return {
            "rows_after_cleaning": row_count,
            "rows_before_cleaning": original_count,
            "rows_removed": original_count - row_count,
            "reduction_percentage": ((original_count - row_count) / original_count * 100) if original_count > 0 else 0
        }

class QualityDashboard:
    """Data quality dashboard and reporting"""
    
    def __init__(self, engine: DataQualityEngine):
        self._engine = engine
    
    def get_quality_score(self, table_name: str) -> Dict[str, Any]:
        """Calculate overall data quality score"""
        results = self._engine.validate_data(table_name)
        
        # Calculate weighted score
        total_score = sum(r.score for r in results)
        max_score = len(results)
        overall_score = total_score / max_score if max_score > 0 else 0
        
        # Categorize quality
        if overall_score >= 0.9:
            grade = "A"
            status = "Excellent"
        elif overall_score >= 0.8:
            grade = "B"
            status = "Good"
        elif overall_score >= 0.7:
            grade = "C"
            status = "Fair"
        else:
            grade = "D"
            status = "Poor"
        
        return {
            "overall_score": overall_score,
            "grade": grade,
            "status": status,
            "rule_results": results,
            "summary": {
                "total_rules": len(results),
                "passed_rules": sum(1 for r in results if r.passed),
                "failed_rules": sum(1 for r in results if not r.passed)
            }
        }
    
    def generate_quality_report(self, table_name: str) -> str:
        """Generate HTML quality report"""
        quality_score = self.get_quality_score(table_name)
        
        html_template = f"""
        <html>
        <head>
            <title>Data Quality Report - {table_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f8ff; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; }}
                .grade {{ font-size: 48px; color: {self._get_grade_color(quality_score['grade'])}; }}
                .result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
                .passed {{ border-color: #4caf50; }}
                .failed {{ border-color: #f44336; }}
                .warning {{ border-color: #ff9800; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Data Quality Report</h1>
                <h2>Table: {table_name}</h2>
                <div class="score">Score: {quality_score['overall_score']:.2%}</div>
                <div class="grade">{quality_score['grade']}</div>
                <div>Status: {quality_score['status']}</div>
            </div>
            
            <div class="summary">
                <h3>Summary</h3>
                <p>Total Rules: {quality_score['summary']['total_rules']}</p>
                <p>Passed: {quality_score['summary']['passed_rules']}</p>
                <p>Failed: {quality_score['summary']['failed_rules']}</p>
            </div>
            
            <div class="details">
                <h3>Rule Results</h3>
                {self._render_rule_results(quality_score['rule_results'])}
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _get_grade_color(self, grade: str) -> str:
        """Get color for grade"""
        colors = {
            'A': '#4caf50',
            'B': '#2196f3',
            'C': '#ff9800',
            'D': '#f44336'
        }
        return colors.get(grade, '#666')
    
    def _render_rule_results(self, results: List[QualityResult]) -> str:
        """Render rule results as HTML"""
        html = ""
        for result in results:
            css_class = result.passed and "passed" or result.severity
            html += f"""
            <div class="result {css_class}">
                <h4>{result.rule_name}</h4>
                <p>Score: {result.score:.2%}</p>
                <p>{result.message}</p>
            </div>
            """
        return html
```

### 2.2 Frontend Implementation

#### 2.2.1 Quality Dashboard Component

Create `src/components/quality/DataQualityDashboard.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Table, Alert, Button, Modal, Form, Input, Select, Space } from 'antd';
import { ExclamationCircleOutlined, CheckCircleOutlined, WarningOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

interface QualityRule {
  name: string;
  type: string;
  passed: boolean;
  score: number;
  message: string;
  severity: 'info' | 'warning' | 'error';
}

interface QualityReport {
  overall_score: number;
  grade: string;
  status: string;
  summary: {
    total_rules: number;
    passed_rules: number;
    failed_rules: number;
  };
  rule_results: QualityRule[];
}

interface CleaningConfig {
  remove_duplicates: boolean;
  null_strategy: 'drop' | 'fill';
  null_columns: string[];
  fill_values: Record<string, any>;
}

const DataQualityDashboard: React.FC = () => {
  const [table, setTable] = useState<string>('');
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [cleaningModalVisible, setCleaningModalVisible] = useState<boolean>(false);
  const [cleaningConfig, setCleaningConfig] = useState<CleaningConfig>({
    remove_duplicates: false,
    null_strategy: 'drop',
    null_columns: [],
    fill_values: {}
  });

  const tables = ['sales', 'customers', 'products', 'orders'];

  const fetchQualityReport = async () => {
    if (!table) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/data-quality/report?table=${table}`);
      const data = await response.json();
      setQualityReport(data);
    } catch (error) {
      console.error('Error fetching quality report:', error);
    } finally {
      setLoading(false);
    }
  };

  const performDataCleaning = async () => {
    if (!table) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/data-quality/clean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table,
          config: cleaningConfig
        }),
      });

      const result = await response.json();
      Alert.success('Data cleaning completed successfully!');
      setCleaningModalVisible(false);
      fetchQualityReport(); // Refresh quality report
    } catch (error) {
      console.error('Error cleaning data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return <ExclamationCircleOutlined style={{ color: '#f44336' }} />;
      case 'warning': return <WarningOutlined style={{ color: '#ff9800' }} />;
      default: return <InfoCircleOutlined style={{ color: '#2196f3' }} />;
    }
  };

  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      'A': '#4caf50',
      'B': '#2196f3',
      'C': '#ff9800',
      'D': '#f44336'
    };
    return colors[grade] || '#666';
  };

  return (
    <div className="data-quality-dashboard">
      <Card title="Data Quality Dashboard">
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Table Selection */}
          <Row gutter={16}>
            <Col span={8}>
              <label>Select Table:</label>
              <Select
                value={table}
                onChange={setTable}
                style={{ width: '100%' }}
              >
                {tables.map(t => (
                  <Option key={t} value={t}>{t}</Option>
                ))}
              </Select>
            </Col>
            <Col span={8}>
              <Button
                type="primary"
                onClick={fetchQualityReport}
                loading={loading}
                disabled={!table}
              >
                Generate Quality Report
              </Button>
            </Col>
            <Col span={8}>
              <Button
                type="default"
                onClick={() => setCleaningModalVisible(true)}
                disabled={!qualityReport || qualityReport.overall_score > 0.8}
              >
                Clean Data
              </Button>
            </Col>
          </Row>

          {/* Quality Score */}
          {qualityReport && (
            <Row gutter={16}>
              <Col span={12}>
                <Card title="Overall Quality Score">
                  <Progress
                    type="circle"
                    percent={qualityReport.overall_score * 100}
                    strokeColor={getGradeColor(qualityReport.grade)}
                    format={(percent) => `${(percent || 0).toFixed(0)}%`}
                  />
                  <div style={{ textAlign: 'center', marginTop: 16 }}>
                    <span style={{ fontSize: '24px', fontWeight: 'bold', color: getGradeColor(qualityReport.grade) }}>
                      {qualityReport.grade}
                    </span>
                    <p>{qualityReport.status}</p>
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Summary">
                  <Row>
                    <Col span={8}>
                      <div style={{ textAlign: 'center' }}>
                        <p>{qualityReport.summary.total_rules}</p>
                        <p>Total Rules</p>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center', color: '#4caf50' }}>
                        <p>{qualityReport.summary.passed_rules}</p>
                        <p>Passed</p>
                      </div>
                    </Col>
                    <Col span={8}>
                      <div style={{ textAlign: 'center', color: '#f44336' }}>
                        <p>{qualityReport.summary.failed_rules}</p>
                        <p>Failed</p>
                      </div>
                    </Col>
                  </Row>
                </Card>
              </Col>
            </Row>
          )}

          {/* Rule Results */}
          {qualityReport && (
            <Card title="Rule Results">
              <Table
                dataSource={qualityReport.rule_results}
                rowKey="name"
                columns={[
                  {
                    title: 'Rule',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text, record: QualityRule) => (
                      <Space>
                        {getSeverityIcon(record.severity)}
                        {text}
                      </Space>
                    )
                  },
                  {
                    title: 'Score',
                    dataIndex: 'score',
                    key: 'score',
                    render: (score: number) => `${(score * 100).toFixed(1)}%`
                  },
                  {
                    title: 'Status',
                    dataIndex: 'passed',
                    key: 'passed',
                    render: (passed: boolean) => 
                      passed ? 
                        <CheckCircleOutlined style={{ color: '#4caf36' }} /> : 
                        <ExclamationCircleOutlined style={{ color: '#f44336' }} />
                  },
                  {
                    title: 'Message',
                    dataIndex: 'message',
                    key: 'message'
                  }
                ]}
                pagination={false}
              />
            </Card>
          )}
        </Space>
      </Card>

      {/* Data Cleaning Modal */}
      <Modal
        title="Data Cleaning Configuration"
        visible={cleaningModalVisible}
        onCancel={() => setCleaningModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setCleaningModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="clean" type="primary" onClick={performDataCleaning} loading={loading}>
            Clean Data
          </Button>
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="Remove Duplicates">
            <Switch
              checked={cleaningConfig.remove_duplicates}
              onChange={(checked) => setCleaningConfig({...cleaningConfig, remove_duplicates: checked})}
            />
          </Form.Item>

          <Form.Item label="Null Value Handling">
            <Select
              value={cleaningConfig.null_strategy}
              onChange={(value) => setCleaningConfig({...cleaningConfig, null_strategy: value})}
            >
              <Option value="drop">Drop records with nulls</Option>
              <Option value="fill">Fill with values</Option>
            </Select>
          </Form.Item>

          {cleaningConfig.null_strategy === 'fill' && (
            <Form.Item label="Fill Values">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="Column name"
                  value={Object.keys(cleaningConfig.fill_values)[0] || ''}
                  onChange={(e) => {
                    const col = e.target.value;
                    setCleaningConfig({
                      ...cleaningConfig,
                      fill_values: { ...cleaningConfig.fill_values, [col]: 'default_value' }
                    });
                  }}
                />
              </Space>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default DataQualityDashboard;
```

---

## 3. Deployment and Integration

### 3.1 Configuration Updates

Update `config.yaml`:

```yaml
# Enhanced configuration for new features
enhancements:
  reporting:
    enabled: true
    templates_dir: "src/core/processor/templates"
    default_format: "pdf"
    chart_types: ["bar", "line", "pie", "scatter"]
    max_charts_per_report: 10
  
  data_quality:
    enabled: true
    default_rules:
      - null_check
      - duplicate_check
      - data_type_check
    cleaning:
      auto_remove_duplicates: false
      default_null_strategy: "drop"
      fill_values:
        customer_name: "Unknown"
        email: "no_email@example.com"
  
  analytics:
    enabled: true
    kpi_thresholds:
      conversion_rate: 0.05
      customer_retention: 0.8
      revenue_growth: 0.1
    insights:
      max_insights_per_report: 5
      auto_generate: true

# Database configuration for new tables
database:
  tables:
    report_templates:
      columns:
        id: "UUID PRIMARY KEY"
        name: "VARCHAR(255) NOT NULL"
        description: "TEXT"
        template_type: "VARCHAR(50)"
        content: "JSONB"
        created_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        updated_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    
    workflow_templates:
      columns:
        id: "UUID PRIMARY KEY"
        name: "VARCHAR(255) NOT NULL"
        description: "TEXT"
        template_config: "JSONB"
        created_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        updated_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    
    data_quality_rules:
      columns:
        id: "UUID PRIMARY KEY"
        name: "VARCHAR(255) NOT NULL"
        rule_type: "VARCHAR(50)"
        configuration: "JSONB"
        active: "BOOLEAN DEFAULT true"
        created_at: "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
```

### 3.2 Database Migration

Create `alembic/versions/add_enhancement_tables.py`:

```python
"""Add enhancement tables

Revision ID: add_enhancement_tables
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_enhancement_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create report_templates table
    op.create_table('report_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create workflow_templates table
    op.create_table('workflow_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create data_quality_rules table
    op.create_table('data_quality_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('data_quality_rules')
    op.drop_table('workflow_templates')
    op.drop_table('report_templates')
```

### 3.3 Environment Setup

Update `requirements.txt`:

```
# Core dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
duckdb==0.9.2
pydantic==2.5.0
pandas==2.1.4

# Reporting
jinja2==3.1.2
plotly==5.17.0
weasyprint==60.2
Pillow==10.1.0
openpyxl==3.1.2

# Data Quality
numpy==1.25.2
scikit-learn==1.3.2

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Development
ruff==0.1.9
black==23.11.0
mypy==1.7.1
```

---

## 4. Testing Strategy

### 4.1 Unit Tests

Create `tests/unit/test_reporting.py`:

```python
"""Test cases for reporting module"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
import tempfile
import os

from src.core.processor.reporting import ReportTemplateEngine, ReportManager

@pytest.fixture
def mock_connection():
    """Mock DuckDB connection"""
    mock_conn = Mock()
    mock_conn.execute.return_value.df.return_value = pd.DataFrame({
        'product': ['A', 'B', 'C'],
        'sales': [100, 200, 150],
        'date': pd.date_range('2023-01-01', periods=3)
    })
    return mock_conn

@pytest.fixture
def report_engine(mock_connection):
    """Report template engine fixture"""
    return ReportTemplateEngine(mock_connection)

def test_report_template_engine_initialization(report_engine):
    """Test report template engine initialization"""
    assert report_engine._connection is not None
    assert report_engine._jinja_env is not None

@patch('src.core.processor.reporting.HTML')
def test_generate_pdf_report(mock_html, report_engine):
    """Test PDF report generation"""
    # Mock HTML generation
    mock_html_instance = Mock()
    mock_html.return_value = mock_html_instance
    mock_html_instance.write_pdf.return_value = b'pdf_content'
    
    # Mock render_template
    report_engine.render_template = Mock(return_value='rendered_html')
    
    # Generate report
    result = report_engine.generate_pdf_report(
        query="SELECT * FROM sales",
        template_name="test_template.html",
        config={'charts': []}
    )
    
    # Verify PDF content
    assert result == b'pdf_content'
    mock_html.assert_called_once()
    mock_html_instance.write_pdf.assert_called_once()

def test_generate_insights(report_engine):
    """Test insight generation"""
    df = pd.DataFrame({
        'product': ['A', 'B', 'C'],
        'sales': [100, 200, 150],
        'date': pd.date_range('2023-01-01', periods=3)
    })
    
    insights = report_engine._generate_insights(df)
    
    assert len(insights) > 0
    assert any(insight['type'] == 'statistical' for insight in insights)
    assert any(insight['type'] == 'temporal' for insight in insights)

def test_create_charts(report_engine):
    """Test chart creation"""
    df = pd.DataFrame({
        'product': ['A', 'B', 'C'],
        'sales': [100, 200, 150]
    })
    
    chart_configs = [
        {'type': 'bar', 'x': 'product', 'y': 'sales', 'title': 'Sales by Product'}
    ]
    
    charts = report_engine._create_charts(df, chart_configs)
    
    assert len(charts) == 1
    assert charts[0]['type'] == 'bar'
    assert 'html' in charts[0]
```

### 4.2 Integration Tests

Create `tests/integration/test_data_quality.py`:

```python
"""Integration tests for data quality module"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from src.core.processor.data_quality import DataQualityEngine, QualityRule, QualityRuleType

@pytest.fixture
def test_db():
    """Create test database"""
    db_path = tempfile.mktemp(suffix='.db')
    import duckdb
    conn = duckdb.connect(db_path)
    
    # Create test table
    conn.execute("""
    CREATE TABLE test_table (
        id INTEGER,
        name VARCHAR(100),
        age INTEGER,
        email VARCHAR(100),
        created_date DATE
    )
    """)
    
    # Insert test data
    conn.execute("""
    INSERT INTO test_table VALUES 
        (1, 'Alice', 25, 'alice@example.com', '2023-01-01'),
        (2, 'Bob', 30, 'bob@example.com', '2023-01-02'),
        (3, 'Charlie', 35, NULL, '2023-01-03'),
        (4, 'Alice', 25, 'alice@example.com', '2023-01-04')  -- Duplicate
    """)
    
    yield conn
    os.unlink(db_path)

def test_data_quality_engine_initialization(test_db):
    """Test data quality engine initialization"""
    engine = DataQualityEngine(test_db)
    assert len(engine._default_rules) == 3

def test_null_value_check(test_db):
    """Test null value checking"""
    engine = DataQualityEngine(test_db)
    
    rule = QualityRule(
        name="Null Check",
        type=QualityRuleType.COMPLETENESS,
        column="email",
        parameters={"max_null_percentage": 0.1}
    )
    
    result = engine._check_rule(rule, "test_table", ["id", "name", "age", "email", "created_date"])
    
    assert result.rule_name == "Null Check"
    assert not result.passed  # Should fail due to 25% null rate
    assert result.score < 0.8
    assert "Exceeds threshold" in result.message

def test_duplicate_check(test_db):
    """Test duplicate checking"""
    engine = DataQualityEngine(test_db)
    
    rule = QualityRule(
        name="Duplicate Check",
        type=QualityRuleType.UNIQUENESS,
        column="id",
        parameters={}
    )
    
    result = engine._check_rule(rule, "test_table", ["id", "name", "age", "email", "created_date"])
    
    assert result.rule_name == "Duplicate Check"
    assert result.passed  # IDs are unique
    assert result.score == 1.0

def test_data_cleaning(test_db):
    """Test data cleaning functionality"""
    engine = DataQualityEngine(test_db)
    
    config = {
        'remove_duplicates': True,
        'null_strategy': 'drop',
        'null_columns': ['email']
    }
    
    result = engine.clean_data("test_table", config)
    
    assert result['original_table'] == 'test_table'
    assert 'cleaned_table' in result
    assert 'Removed duplicate records' in result['operations']
    assert 'Dropped records with null values' in result['operations']
    
    # Verify cleaning results
    summary = result['summary']
    assert summary['rows_after_cleaning'] == 2  # 4 original - 1 duplicate - 1 null = 2
    assert summary['rows_removed'] == 2

def test_quality_dashboard(test_db):
    """Test quality dashboard functionality"""
    engine = DataQualityEngine(test_db)
    dashboard = QualityDashboard(engine)
    
    # Get quality score
    score = dashboard.get_quality_score("test_table")
    
    assert 'overall_score' in score
    assert 'grade' in score
    assert 'status' in score
    assert 'rule_results' in score
    assert len(score['rule_results']) > 0
    
    # Generate quality report
    report = dashboard.generate_quality_report("test_table")
    assert '<html>' in report
    assert 'Data Quality Report' in report
```

---

## 5. Monitoring and Maintenance

### 5.1 Performance Monitoring

Add monitoring to `src/api/metrics.py`:

```python
"""
Enhanced metrics for monitoring new features
"""

import time
from functools import wraps
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class FeatureMetrics:
    """Metrics collection for enhanced features"""
    
    def __init__(self):
        self.counters = {}
        self.histograms = {}
        self.gauges = {}
    
    def increment(self, metric_name: str, value: int = 1) -> None:
        """Increment counter metric"""
        if metric_name not in self.counters:
            self.counters[metric_name] = 0
        self.counters[metric_name] += value
    
    def histogram(self, metric_name: str, value: float) -> None:
        """Record histogram metric"""
        if metric_name not in self.histograms:
            self.histograms[metric_name] = []
        self.histograms[metric_name].append(value)
    
    def gauge(self, metric_name: str, value: float) -> None:
        """Set gauge metric"""
        self.gauges[metric_name] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            'counters': self.counters,
            'gauges': self.gauges,
            'histograms': {}
        }
        
        # Calculate histogram statistics
        for name, values in self.histograms.items():
            if values:
                summary['histograms'][name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'p95': sorted(values)[int(len(values) * 0.95)]
                }
        
        return summary

# Global metrics instance
metrics = FeatureMetrics()

def monitor_performance(metric_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.histogram(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.histogram(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_error")
                logger.error(f"Error in {metric_name}: {str(e)}")
                raise
        return async_wrapper
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.histogram(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.histogram(f"{metric_name}_duration", duration)
                metrics.increment(f"{metric_name}_error")
                logger.error(f"Error in {metric_name}: {str(e)}")
                raise
        return sync_wrapper
    return decorator

# Export metrics endpoint
@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get current metrics"""
    return metrics.get_summary()
```

### 5.2 Error Handling

Enhance error handling in `src/api/middleware/error_handler.py`:

```python
"""
Enhanced error handling for new features
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorCode:
    """Error codes for enhanced features"""
    REPORT_GENERATION_FAILED = "REPORT_001"
    DATA_QUALITY_CHECK_FAILED = "QUALITY_001"
    WORKFLOW_EXECUTION_FAILED = "WORKFLOW_001"
    INVALID_TEMPLATE = "TEMPLATE_001"
    INSIGHT_GENERATION_FAILED = "INSIGHT_001"
    EXPORT_FAILED = "EXPORT_001"

class ErrorResponse:
    """Standardized error response"""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code

async def enhanced_exception_handler(request: Request, exc: Exception) -> Response:
    """Enhanced exception handler for new features"""
    
    if isinstance(exc, HTTPException):
        # Standard FastAPI exceptions
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {}
                }
            }
        )
    
    # Feature-specific exceptions
    error_map = {
        "ReportGenerationError": ErrorResponse(
            code=ErrorCode.REPORT_GENERATION_FAILED,
            message="Report generation failed",
            status_code=422
        ),
        "DataQualityError": ErrorResponse(
            code=ErrorCode.DATA_QUALITY_CHECK_FAILED,
            message="Data quality check failed",
            status_code=400
        ),
        "TemplateError": ErrorResponse(
            code=ErrorCode.INVALID_TEMPLATE,
            message="Invalid template specified",
            status_code=400
        )
    }
    
    error_type = type(exc).__name__
    if error_type in error_map:
        error = error_map[error_type]
        logger.error(f"Feature error {error.code}: {error.message}")
        
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details
                }
            }
        )
    
    # Generic exception
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": {}
            }
        }
    )
```

---

## 6. Conclusion

This implementation guide provides the technical foundation for enhancing the DuckDB Web Workflow Builder with professional reporting, data quality features, and business intelligence capabilities. The code examples, configuration examples, and testing strategies ensure a smooth implementation process.

Key benefits of this implementation:
- **Professional Reports**: Generate PDF reports with charts and insights
- **Data Quality Automation**: Automated validation and cleaning of data
- **Enhanced User Experience**: Intuitive interfaces for report generation and quality management
- **Scalable Architecture**: Modular design allows for easy extension
- **Comprehensive Testing**: Unit and integration tests ensure reliability

The implementation follows best practices for maintainability, scalability, and user experience, positioning the tool as a professional end-to-end data processing solution.