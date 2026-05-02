# DuckDB Workflow Builder

A visual data analysis platform for building and executing DuckDB workflows through an intuitive drag-and-drop interface.

## Overview

The DuckDB Workflow Builder is a full-stack web application that enables users to create complex data processing pipelines visually without writing SQL code. Users can drag and drop nodes onto a canvas to build workflows that connect to multiple data sources, transform data using DuckDB's powerful analytical engine, and generate reports.

## Features

### Visual Workflow Builder
- **Drag-and-Drop Interface**: Intuitive canvas for constructing data processing pipelines
- **Node-Based Architecture**: Modular components for data sources, transformations, and outputs
- **Real-Time Validation**: Immediate feedback on workflow structure and connections
- **Keyboard Shortcuts**: Power user commands for efficient workflow construction
- **Mobile Support**: Touch-optimized interface with bottom panel navigation and scrollable content
  - Mobile workflow viewer with zoom controls and pan gestures
  - Bottom sheet panels for node details and execution results
  - Preview Data functionality for inspecting node samples on mobile
  - Responsive design adapts to phone, tablet, and desktop viewports

### Multi-Source Data Integration
- **Database Connectors**: 
  - Native support for **DuckDB**, **PostgreSQL**, **MySQL**, and **SQL Server**.
  - **Mock Data Mode**: Built-in mock data generators for all database types, allowing pipeline development without a live network connection.
- **File Import**: 
  - CSV files with automatic encoding detection (UTF-8, UTF-8-sig, CP949, EUC-KR)
  - Excel files (.xlsx, .xls) with multiple sheet support
  - JSON/JSONL files with nested structure handling
  - Parquet files with compression detection (snappy, gzip, brotli, lz4, zstd)
- **API Loading**: REST API integration with authentication (Bearer token, API key, Basic Auth)
- **Remote Data**: HTTP/HTTPS file downloads with streaming support
- **Schema Inference**: Automatic column type detection and validation

### Data Transformations
- **Aggregation**: Group by with SUM, AVG, MIN, MAX, COUNT functions
- **Joins**: INNER, LEFT, RIGHT, OUTER, CROSS joins between tables
- **Window Functions**: ROW_NUMBER, RANK, LAG, LEAD, running totals
- **Rolling Aggregates**: Moving averages and sums with configurable window sizes
- **Pivot Tables**: Cross-tabulation for multi-dimensional analysis

### Real-Time Data Processing
- **DuckDB Engine**: In-memory analytical database for fast query execution
- **Incremental Caching**: Smart node-level caching to avoid redundant computation
- **Streaming Support**: Process large datasets without loading entirely into memory
- **Query Optimization**: Automatic SQL generation with parameterized queries

### AI-Assisted Development
- **AI Pipeline Builder**: Generate complete multi-node workflows from a single natural language prompt.
- **Natural Language to SQL**: Convert plain English descriptions into SQL queries.
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Google (Gemini), Groq, and Cerebras.
- **Context-Aware**: AI understands your data schema and suggests relevant join keys and transformations.

### Workflow Persistence
- **Save/Load Workflows**: Store workflow definitions for future use
- **Export/Import**: Share workflows across teams and environments
- **Auto-Save**: Prevent data loss with automatic saving (planned feature)

### Production-Ready Monitoring
- **Structured Logging**: JSON-formatted logs with correlation IDs for distributed tracing
- **Health Checks**: Kubernetes-style probes (liveness, readiness, startup)
- **Prometheus Metrics**: Request count, latency, error rate, and business metrics
- **Performance Tracking**: Request timing and slow query detection
- **Observability**: Ready for integration with Grafana, Loki, ELK, or CloudWatch

## Sample Pipelines

The platform includes a rich collection of pre-built sample templates:

1.  **👥 Employee Retention Risk**: Joins HR CSV data with performance reviews to identify at-risk staff using conditional logic.
2.  **📈 Portfolio Rolling Returns**: Demonstrates advanced **Window Functions** for financial time-series analysis.
3.  **🔗 Multi-Channel Attribution**: Joins **Remote Parquet** files with **REST API** conversion data to calculate marketing ROAS.
4.  **🛡️ SQL Server Sales Analysis**: A complete flow from a SQL Server database to a generated PDF report.
5.  **🐬 MySQL E-commerce Sales**: Joins orders and products from MySQL for category sales analysis.

To load these, use the **Sample Pipelines** sidebar in the application.

### Automated Reporting
- **Report Builder**: Generate professional reports directly from your processed data.
- **Multiple Formats**: Export as **PDF** (with multi-language/Korean support) or **GitHub-flavored Markdown**.
- **Dynamic Sections**: Include data samples, descriptive statistics, and custom text sections automatically.
- **Results Export**: Download processed data as CSV, JSON, or Parquet for downstream use.

## Tech Stack

### Frontend
- **Next.js 16.2.1**: React framework with App Router
- **React 19**: UI library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: Component library
- **React Flow**: Workflow canvas visualization

### Backend
- **FastAPI**: Python web framework
- **DuckDB**: In-memory analytical database
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Testing
- **Playwright**: End-to-end testing
- **pytest**: Python unit testing with 130+ tests
  - Unit tests for Processor, connectors, and API endpoints
  - Integration tests for data workflows
  - API connector tests with mocking
  - File upload tests (CSV, Excel, JSON, Parquet)
  - Data transformation tests (pivot, group_by, merge, window functions)
- **Vitest**: TypeScript unit testing

## Getting Started

### Prerequisites

- **Node.js 18+** and **npm**
- **Python 3.11+**
- **Git**
- **ODBC Driver** (for SQL Server support)

**Monitoring Dependencies** (automatically installed):
- `structlog` - Structured JSON logging
- `prometheus-client` - Prometheus metrics collection

### Local Development

#### Quick Start

Clone the repository:
```bash
git clone https://github.com/CJ-1981/duckdb-web.git
cd duckdb-web
```

#### Linux/macOS

```bash
# Install dependencies
./install.sh

# Start development servers
./run.sh
```

#### Windows

```bash
# Install dependencies
install.bat

# Start development servers
run.bat
```

#### Manual Setup

**Backend Setup:**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn src.api.main:create_app --factory --reload --port 8000
```

**Frontend Setup:**
```bash
# Install Node dependencies
npm install

# Start frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Deployment

### Vercel Frontend + Local Backend

**Recommended for:** Free hosting, data privacy, full functionality

This architecture deploys the frontend to Vercel (free tier) while running the backend locally or on a cloud provider.

#### Setup Steps

1. **Deploy Frontend to Vercel:**
   ```bash
   npm run build
   vercel deploy
   ```

2. **Start Backend Locally:**
   ```bash
   python -m uvicorn src.api.main:create_app --factory --reload --port 8000
   ```

3. **Configure Backend URL in Vercel App:**
   - Open your deployed Vercel app
   - Click the **Settings** button in the toolbar
   - Enter your local backend URL (e.g., `http://localhost:8000`)
   - Click **Test & Save** to verify the connection

4. **Enable CORS:**
   - Update `src/api/main.py` to include your Vercel domain in `cors_origins`
   - Restart the backend

For detailed setup instructions, see [docs/LOCAL_BACKEND_SETUP.md](docs/LOCAL_BACKEND_SETUP.md)

### Full Cloud Deployment

**Backend Options:**
- **Railway**: $5-20/month
- **Render**: Free tier available
- **Fly.io**: Pay-as-you-go
- **AWS Lambda**: Serverless option

**Frontend:**
- **Vercel**: Free tier available
- **Netlify**: Free tier available

## Monitoring & Observability

The application includes production-ready monitoring and logging capabilities.

### Health Check Endpoints

Kubernetes-style health probes for deployment orchestration:

```bash
# Liveness probe - app is running
curl http://localhost:8000/health/live

# Readiness probe - can serve traffic
curl http://localhost:8000/health/ready

# Startup probe - initialization complete
curl http://localhost:8000/health/startup
```

### Prometheus Metrics

Application metrics exposed in Prometheus format:

```bash
# Enable metrics (set PROMETHEUS_ENABLED=true in .env)
curl http://localhost:8000/metrics
```

**Available Metrics:**
- HTTP request count, latency, and error rate by endpoint
- Database query timing and connection pool usage
- Business metrics: file uploads, SQL queries executed
- System metrics: memory, CPU usage

### Structured Logging

JSON-formatted logs with correlation IDs for distributed tracing:

```json
{
  "timestamp": "2026-05-01T19:18:21.458582Z",
  "level": "info",
  "message": "Request completed",
  "correlation_id": "abc123",
  "method": "POST",
  "path": "/api/workflow/execute",
  "status_code": 200,
  "duration_ms": 123
}
```

### Configuration

Add to your `.env` file:

```bash
# Application Environment
ENV=production

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance Monitoring
SLOW_REQUEST_THRESHOLD_MS=1000

# Prometheus Metrics
PROMETHEUS_ENABLED=true
```

### Log Aggregation

Compatible with:
- **Grafana Loki** (Recommended) - Lightweight, Prometheus integration
- **ELK Stack** - Enterprise log analytics
- **AWS CloudWatch** - Native AWS integration
- **Grafana Cloud** - Managed observability platform

## Development

### Project Structure

```
duckdb-web/
├── src/
│   ├── api/           # FastAPI backend
│   │   ├── routers/   # API endpoints
│   │   ├── monitoring/ # Monitoring & logging system
│   │   └── main.py    # Application entry point
│   ├── components/    # React components
│   │   ├── canvas/    # Workflow canvas
│   │   ├── nodes/     # Node types (input, output, sql, etc.)
│   │   └── panels/    # UI panels (settings, inspection)
│   └── lib/           # Utilities and helpers
├── tests/
│   ├── unit/          # Python unit tests
│   ├── integration/   # Integration tests
│   └── e2e/           # Playwright E2E tests
├── docs/              # Documentation
└── README.md          # This file
```

### Available Scripts

**Frontend:**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test         # Run Vitest tests
npm run test:e2e     # Run Playwright E2E tests
```

**Backend:**
```bash
python -m uvicorn src.api.main:create_app --factory --reload
pytest               # Run unit tests
pytest tests/integration/  # Run integration tests
```

### Windows Development Notes

If your project is in a OneDrive or cloud-synced folder, the batch scripts will detect this and warn you. For best performance:

1. **Move the project** to a non-cloud-synced location (e.g., `C:\projects\duckdb-web`)
2. **Set environment variable** to point to a custom virtual environment location:
   ```cmd
   set VENV_DIR=C:\venvs\duckdb-web
   install.bat
   ```

See [docs/WINDOWS_SETUP.md](docs/WINDOWS_SETUP.md) for detailed Windows setup instructions.

## Testing

### E2E Testing

```bash
# Install Playwright browsers
npx playwright install

# Run all E2E tests
npm run test:e2e

# Run specific test file
npx playwright test tests/e2e/canvas-nodes.spec.ts

# Run with UI
npx playwright test --ui
```

### Unit Testing

**Python:**
```bash
pytest tests/unit/
pytest --cov=src tests/unit/
```

**TypeScript:**
```bash
npm test
```

### Monitoring Tests

```bash
# Test monitoring endpoints
pytest tests/test_monitoring.py -v

# Test health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/startup

# Test metrics (when PROMETHEUS_ENABLED=true)
curl http://localhost:8000/metrics
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- **DuckDB** for the amazing analytical database engine
- **Next.js** team for the excellent React framework
- **shadcn/ui** for the beautiful component library
- **React Flow** for the workflow canvas visualization
