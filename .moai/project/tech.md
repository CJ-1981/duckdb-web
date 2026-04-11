# Technology Stack

## Overview

The DuckDB Workflow Builder uses a modern, type-safe full-stack architecture with Python on the backend and TypeScript/React on the frontend. The technology choices prioritize developer experience, performance, and extensibility.

### Primary Language Breakdown
- **Python (45%)**: Backend API, data processing, database connectors
- **TypeScript/JavaScript (45%)**: Frontend UI, API client, workflow canvas
- **SQL/DuckDB (10%)**: Query generation, data transformation logic

---

## Backend Stack

### Core Framework

**FastAPI** (Python web framework)
- **Version**: Latest (0.115+)
- **Rationale**: Modern async/await support, automatic OpenAPI documentation, type hints with Pydantic, high performance
- **Key Features Used**:
  - `asyncio` for I/O-bound operations
  - `Depends()` for dependency injection
  - BackgroundTasks for async job execution
  - Automatic request validation with Pydantic v2
  - OpenAPI/Swagger UI at `/docs`

**ASGI Server**
- **Uvicorn**: Production ASGI server with uvloop for performance
- **Development**: `uvicorn --reload` for hot-reloading during development
- **Production**: `gunicorn` with uvicorn workers for multiprocessing

### Database and Data Processing

**DuckDB** (Primary analytical database)
- **Version**: Latest
- **Rationale**: In-memory analytical database with SQL compatibility, columnar storage for fast aggregations, zero external dependencies
- **Use Cases**: 
  - Workflow node execution
  - SQL query processing
  - Data transformations (joins, aggregations, filtering)
  - Result caching

**SQLAlchemy** (ORM and database abstraction)
- **Version**: 2.0+
- **Rationale**: Database-agnostic ORM, async support, connection pooling
- **Use Cases**:
  - User and workflow persistence
  - Job queue management
  - Database connector abstraction for PostgreSQL/MySQL

**Pandas** (Data manipulation)
- **Version**: Latest
- **Rationale**: Standard for data manipulation in Python, integrates with DuckDB
- **Use Cases**:
  - CSV processing and validation
  - Data type inference
  - Export formatting

### Data Validation and Serialization

**Pydantic v2** (Data validation)
- **Version**: 2.9+
- **Rationale**: Type-safe data validation, performance improvements in v2, automatic JSON schema generation
- **Key Features Used**:
  - `model_validate()` (replaces `parse_obj`)
  - `model_validate_json()` (replaces `parse_raw`)
  - `ConfigDict` with `from_attributes=True`, `populate_by_name=True`
  - Annotated validators with `AfterValidator`
  - `model_validator(mode="after")` for cross-field validation

### Authentication and Security

**Built-in FastAPI Security**
- **OAuth2**: Password flow with Bearer tokens
- **Password Hashing**: `passlib` with bcrypt
- **JWT**: Token-based authentication (planned: integrate `python-jose`)
- **RBAC**: Role-based access control implementation in `src/api/auth/rbac.py`

### Testing Framework

**pytest** (Python testing)
- **Version**: Latest
- **Coverage Target**: 85%+ with `pytest-cov`
- **Key Features Used**:
  - `pytest-asyncio` for async test support
  - `@pytest.mark.parametrize` for data-driven tests
  - `pytest-mock` for mocking external services
  - Fixture factories for flexible test data

### Code Quality and Linting

**Ruff** (Fast Python linter and formatter)
- **Version**: Latest
- **Rationale**: 10-100x faster than flake8, combines linting and formatting
- **Configuration**: `pyproject.toml`
- **Usage**:
  ```bash
  ruff check src/          # Linting
  ruff format src/         # Formatting (replaces black)
  ```

**Type Checking**
- **mypy** or **pyright** (both supported)
- **Configuration**: Strict mode enabled
- **Integration**: CI/CD pipeline type checking

---

## Frontend Stack

### Core Framework

**Next.js 16** (React framework)
- **Version**: 16.x (latest)
- **Rationale**: Server-side rendering, excellent TypeScript support, zero-config build system
- **Features Used**:
  - App Router (not Pages Router)
  - Server Components for performance
  - API routes for backend proxy (if needed)
  - Built-in optimization (code splitting, image optimization)

**React 19** (UI library)
- **Version**: 19.x (latest)
- **Rationale**: Latest features including improved server components, actions, and form handling

**TypeScript** (Type safety)
- **Version**: Latest
- **Configuration**: `tsconfig.json` with strict mode enabled
- **Rationale**: Catch errors at compile time, better IDE support, self-documenting code

### Workflow Canvas

**@xyflow/react** (React Flow)
- **Version**: Latest (formerly `reactflow`)
- **Rationale**: Industry-standard library for node-based visual editors, highly customizable, excellent performance
- **Use Cases**:
  - Visual workflow builder canvas
  - Node drag-and-drop
  - Edge connections between nodes
  - Custom node components for each operation type

### UI Components

**shadcn/ui** patterns
- **Rationale**: Copy-paste components with full customization, no npm dependency, built on Radix UI primitives
- **Components Used**: 
  - Panels and dialogs
  - Forms and inputs
  - Data tables
  - Toasts and notifications

**Lucide React** (Icons)
- **Version**: Latest
- **Rationale**: Consistent icon set, tree-shakeable, MIT license

### Data Visualization

**Recharts** (Charts)
- **Version**: Latest
- **Rationale**: React-friendly charting library, composable components
- **Use Cases**: Data distribution charts, statistics visualization (planned feature)

### State Management

**React Context** (Built-in)
- **Rationale**: Sufficient for current state complexity, avoids extra dependencies
- **Future**: May add Zustand or Redux Toolkit if state grows

### API Client

**Custom API wrapper** (`src/lib/api.ts`)
- **Features**: Type-safe API calls, error handling, retry logic
- **Future**: Consider integrating `@tanstack/react-query` for server state management

### Testing Framework

**Playwright** (E2E testing)
- **Version**: Latest
- **Rationale**: Cross-browser E2E testing, fast execution, auto-waiting for elements
- **Configuration**: `tests/e2e/playwright.config.ts`
- **Usage**:
  ```bash
  npm run test:e2e          # Run all E2E tests
  npm run test:e2e:ui       # Run with UI mode
  ```

### Code Quality

**ESLint** (JavaScript/TypeScript linting)
- **Version**: Latest
- **Configuration**: `eslint.config.mjs`
- **Rules**: TypeScript-specific rules, React hooks rules, import sorting

**TypeScript Compiler**
- **Strict mode**: Enabled in `tsconfig.json`
- **Path aliases**: `@/` maps to `src/`
- **Next.js plugin**: Optimized type checking

---

## Build and Deployment

### Development Workflow

**Startup Script**: `run.sh`
```bash
#!/bin/bash
# Start both backend and frontend in parallel
python -m uvicorn src.api.main:create_app --reload --port 8000 &
npm run dev -- -p 3000
```

**Backend Development**:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.api.main:create_app --reload --port 8000
```

**Frontend Development**:
```bash
npm install
npm run dev  # Next.js dev server on port 3000
```

### Production Build

**Frontend**:
```bash
npm run build    # Creates .next/ directory with optimized build
npm start        # Production server (uses Next.js standalone server)
```

**Backend**:
```bash
gunicorn src.api.main:create_app -w 4 -k uvicorn.workers.UvicornWorker
```

### Deployment Options

**Docker** (Recommended for production):
- Multi-stage Dockerfile for both frontend and backend
- Frontend: Nginx serving static Next.js build
- Backend: Gunicorn with uvicorn workers
- Environment variables for configuration

**Manual Deployment**:
- Frontend: Vercel, Netlify, or any Node.js hosting
- Backend: Heroku, AWS ECS, DigitalOcean App Platform

---

## Key Dependencies by Category

### Backend Dependencies

**Data Processing**:
- `duckdb` - In-memory analytical database
- `sqlalchemy` - ORM and database abstraction
- `pandas` - Data manipulation and analysis
- `tabulate` - Pretty table formatting

**Web Framework**:
- `fastapi` - Modern Python web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation and serialization
- `python-multipart` - File upload support

**Testing**:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking support

**Code Quality**:
- `ruff` - Linting and formatting
- `mypy` - Type checking (optional: pyright)

**Database**:
- `psycopg2-binary` - PostgreSQL adapter
- `pymysql` - MySQL connector
- `cryptography` - Password hashing

### Frontend Dependencies

**Core Framework**:
- `next` - React framework
- `react` - UI library
- `react-dom` - React DOM renderer
- `typescript` - Type checking

**Workflow Canvas**:
- `@xyflow/react` - Node-based visual editor

**UI Components**:
- `lucide-react` - Icon library
- `recharts` - Data visualization (planned)
- `tailwindcss` - Utility-first CSS (via Next.js)
- `clsx` / `classcat` - Conditional class names

**API and Data**:
- `axios` or `fetch` - HTTP client (built-in fetch used)
- `stable-hash` - Deterministic hashing for caching

**Testing**:
- `@playwright/test` - E2E testing
- `@types/node` - Node.js type definitions

---

## Dev Environment Requirements

### System Requirements

- **Operating System**: macOS, Linux, Windows (WSL2 recommended)
- **Python**: 3.12+ (3.13+ recommended for JIT and GIL-free mode)
- **Node.js**: 20.x LTS or 22.x LTS
- **Memory**: 8GB RAM minimum (16GB recommended for large datasets)
- **Disk**: 500MB for dependencies + workspace

### Python Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; import duckdb; print('Ready!')"
```

### Node.js Environment Setup

```bash
# Install dependencies
npm install

# Verify installation
npm run build    # Should compile without errors
```

### IDE Configuration

**VS Code Extensions**:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- ESLint (dbaeumer.vscode-eslint)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
- Playwright Test for VSCode (ms-playwright.playwright)

**VS Code Settings** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "typescript.tsdk": "node_modules/typescript/lib",
  "editor.formatOnSave": true
}
```

---

## Configuration Files

### Backend Configuration

**pyproject.toml**:
```toml
[project]
name = "duckdb-workflow-builder"
version = "0.1.0"
requires-python = ">=3.12"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Frontend Configuration

**tsconfig.json**:
```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2022",
    "module": "ESNext",
    "jsx": "preserve",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

**package.json** scripts:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint src/",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

---

## Performance Considerations

### Backend Optimization

- **Connection Pooling**: SQLAlchemy connection pooling for database connectors
- **Query Caching**: Result caching with TTL and LRU eviction
- **Streaming**: Chunked data processing for large files
- **Async I/O**: All database operations use async/await

### Frontend Optimization

- **Code Splitting**: Next.js automatic code splitting by route
- **Lazy Loading**: Dynamic imports for heavy components
- **Memoization**: React.memo for expensive components
- **Bundle Size**: Tree-shaking with ES modules

### DuckDB Optimization

- **In-Memory Processing**: All data processed in-memory for speed
- **Columnar Storage**: Efficient aggregations and analytics
- **Query Optimization**: Automatic query planning and optimization

---

## Security Considerations

### Backend Security

- **SQL Injection Prevention**: Parameterized queries, identifier quoting, EXPLAIN-based validation
- **Input Validation**: Pydantic schemas validate all inputs
- **CORS**: Configured for development domains
- **Authentication**: JWT-based auth (RBAC implementation)
- **File Upload**: Size limits, type validation, virus scanning (planned)

### Frontend Security

- **XSS Prevention**: React automatic escaping
- **CSRF**: Token-based CSRF protection (planned)
- **Content Security Policy**: Next.js CSP headers (configured)
- **Dependency Scanning**: `npm audit` for vulnerable packages

---

## Monitoring and Observability (Planned)

### Backend Metrics

- Cache hit/miss ratios
- Query execution times
- Workflow execution metrics
- Error rates and types

### Frontend Metrics

- Page load times
- Component render times
- API response times
- User interaction tracking

### Logging

- **Python**: `logging` module with structured logging
- **JavaScript**: Console logging with log levels
- **Centralized**: Future integration with ELK or CloudWatch

---

## Future Technology Additions

### Near-Term (Roadmap)

1. **Redis**: Distributed caching for multi-instance deployments
2. **Celery**: Production task queue for background jobs
3. **PostgreSQL**: Primary database for workflows and user data
4. **Docker**: Containerized deployment with Docker Compose

### Long-Term (Exploration)

1. **Kubernetes**: Orchestration for scaling
2. **GraphQL**: Alternative to REST for complex queries
3. **WebSockets**: Real-time workflow execution updates
4. **Prometheus/Grafana**: Metrics and monitoring dashboard
