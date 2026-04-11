# Project Structure

## Architecture Overview

The DuckDB Workflow Builder follows **Clean Architecture principles** with **Domain-Driven Design (DDD)** patterns. The codebase is organized into distinct layers with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   Presentation Layer                 │
│  (Next.js Frontend: React Components, Canvas UI)    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────┐
│                    Application Layer                 │
│   (FastAPI Routes, Services, Auth, Middleware)      │
└────────────────────┬────────────────────────────────┘
                     │ Method Calls
┌────────────────────▼────────────────────────────────┐
│                      Domain Layer                    │
│  (Core Business Logic: Processors, Connectors)      │
└────────────────────┬────────────────────────────────┘
                     │ SQL Queries
┌────────────────────▼────────────────────────────────┐
│                   Infrastructure Layer                │
│        (DuckDB, PostgreSQL, MySQL, File System)      │
└─────────────────────────────────────────────────────┘
```

## Directory Structure

```
duckdb-web/
├── src/
│   ├── api/                    # Application Layer (25% of codebase)
│   │   ├── routes/             # REST API endpoints
│   │   │   ├── data.py         # File upload, CSV processing
│   │   │   ├── workflows.py    # Workflow execution, SQL preview
│   │   │   ├── jobs.py         # Background job management
│   │   │   ├── users.py        # User management
│   │   │   └── system.py       # Health check, system info
│   │   ├── services/           # Business service implementations
│   │   │   ├── workflow.py     # Workflow orchestration service
│   │   │   ├── job.py          # Job execution service
│   │   │   ├── users.py        # User service
│   │   │   └── notification.py # Notification service
│   │   ├── models/             # Database models (SQLAlchemy)
│   │   │   ├── user.py         # User entity
│   │   │   ├── workflow.py     # Workflow entity
│   │   │   ├── job.py          # Job entity
│   │   │   └── base.py         # Base model with common fields
│   │   ├── schemas/            # Pydantic schemas for validation
│   │   │   ├── workflow.py     # Workflow request/response schemas
│   │   │   ├── user.py         # User schemas
│   │   │   └── job.py          # Job schemas
│   │   ├── auth/               # Authentication & Authorization
│   │   │   ├── auth_service.py # Authentication logic
│   │   │   ├── permissions.py  # RBAC permissions
│   │   │   ├── rbac.py         # Role-based access control
│   │   │   ├── dependencies.py # FastAPI dependencies
│   │   │   └── decorators.py   # Route protection decorators
│   │   ├── cache/              # Caching layer
│   │   │   ├── manager.py      # Cache manager
│   │   │   ├── query_cache.py  # Query result caching
│   │   │   ├── session_cache.py # Session caching
│   │   │   ├── strategies.py   # Cache eviction strategies
│   │   │   └── metrics.py      # Cache performance metrics
│   │   ├── tasks/              # Background tasks (Celery-like)
│   │   │   ├── workflow.py     # Workflow execution tasks
│   │   │   ├── export.py       # Report generation tasks
│   │   │   └── mock_celery.py  # Mock implementation for development
│   │   ├── middleware/         # Request/response middleware
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── main.py             # FastAPI application factory
│   │
│   ├── core/                   # Domain Layer (40% of codebase)
│   │   ├── connectors/         # Data source connectors (Repository Pattern)
│   │   │   ├── base.py         # Abstract base connector interface
│   │   │   ├── csv.py          # CSV file connector with encoding detection
│   │   │   ├── database.py     # Generic database connector
│   │   │   ├── postgresql.py   # PostgreSQL-specific connector
│   │   │   └── mysql.py        # MySQL-specific connector
│   │   ├── processor/          # Data processing engine
│   │   │   ├── _processor.py   # Private processor implementation
│   │   │   ├── query.py        # SQL query execution and validation
│   │   │   ├── streaming.py    # Streaming data processing
│   │   │   ├── export.py       # Data export functionality
│   │   │   └── progress.py     # Progress tracking for long operations
│   │   ├── database/           # Database management
│   │   │   ├── pool.py         # Connection pooling
│   │   │   └── query.py        # Query builder utilities
│   │   ├── plugins/            # Plugin system for extensibility
│   │   │   ├── base.py         # Plugin base interface
│   │   │   ├── loader.py       # Plugin loader
│   │   │   └── registry.py     # Plugin registry
│   │   └── config/             # Configuration management
│   │       ├── loader.py       # Config loader from files/env
│   │       └── schema.py       # Configuration schema validation
│   │
│   ├── app/                    # Frontend Entry Point (Next.js App Router)
│   │   ├── page.tsx            # Main dashboard page
│   │   └── layout.tsx          # Root layout with providers
│   │
│   ├── components/            # React Components (30% of codebase)
│   │   ├── panels/             # UI panels for workflow configuration
│   │   │   ├── DataInspectionPanel.tsx    # Data preview and statistics
│   │   │   ├── AiSqlBuilderPanel.tsx      # AI-assisted SQL builder
│   │   │   └── AiPipelineBuilderPanel.tsx # Pipeline generation interface
│   │   └── workflow/
│   │       └── canvas.tsx     # Main workflow canvas (React Flow)
│   │
│   └── lib/                   # Frontend utilities
│       └── api.ts             # API client wrapper
│
├── tests/                     # Comprehensive Test Suite (5% of codebase)
│   ├── unit/                  # Unit tests with pytest
│   │   ├── test_csv_connector.py         # CSV connector tests
│   │   ├── test_config.py                # Configuration tests
│   │   ├── test_database.py              # Database tests
│   │   ├── test_plugin_registry.py       # Plugin system tests
│   │   └── test_sql_cache.py             # SQL caching tests
│   ├── integration/           # Integration tests
│   │   ├── test_csv_processing.py        # CSV processing integration
│   │   ├── test_postgresql_connector.py  # PostgreSQL integration
│   │   ├── test_mysql_connector.py       # MySQL integration
│   │   ├── test_processor_workflow.py    # Workflow processing
│   │   └── test_celery.py                # Background task integration
│   ├── e2e/                   # End-to-end tests with Playwright
│   │   ├── canvas-nodes.spec.ts          # Workflow canvas E2E
│   │   ├── edge-cases/                   # Edge case scenarios
│   │   │   ├── null-handling.spec.ts
│   │   │   └── special-chars.spec.ts
│   │   ├── nodes/                         # Node-specific E2E tests
│   │   │   ├── aggregate-node.spec.ts
│   │   │   ├── filter-node.spec.ts
│   │   │   ├── join-node.spec.ts
│   │   │   └── output-node.spec.ts
│   │   ├── smoke/
│   │   │   └── basic-workflow.spec.ts    # Smoke test
│   │   ├── fixtures/                     # Test fixtures and data
│   │   │   ├── assertions.ts              # Custom assertions
│   │   │   └── testData.ts                # Test data generators
│   │   ├── pages/                        # Page object models
│   │   │   ├── DataInspectionPanel.ts
│   │   │   └── WorkflowCanvas.ts
│   │   └── playwright.config.ts           # Playwright configuration
│   ├── api/                   # API route tests
│   │   ├── test_main.py                   # FastAPI app tests
│   │   ├── test_auth.py                   # Authentication tests
│   │   ├── test_workflows.py              # Workflow endpoint tests
│   │   ├── test_jobs.py                   # Job endpoint tests
│   │   ├── test_users.py                  # User endpoint tests
│   │   └── test_models.py                 # Model tests
│   ├── security/              # Security tests
│   │   └── test_injection.py              # SQL injection prevention tests
│   └── performance/           # Performance tests
│       ├── test_streaming.py              # Streaming performance
│       └── test_caching.py                # Cache performance
│
├── data/                     # Data files and reference implementations
│   └── workflows/
│       └── reference/
│           ├── validate_workflows.py     # Workflow validation reference
│           └── test_workflows.py          # Test workflow definitions
│
├── pyproject.toml            # Python project configuration
├── package.json              # Node.js dependencies
├── tsconfig.json             # TypeScript configuration
├── eslint.config.mjs         # ESLint configuration
├── run.sh                    # Development startup script
└── data-processor.py         # Standalone CSV processor CLI tool
```

## Module Organization and Boundaries

### Core Business Logic Layer (src/core/)

**Purpose:** Contains all business logic independent of the web framework. This layer has no dependencies on FastAPI or React.

**Key Modules:**

- **connectors/**: Repository pattern implementation for data access
  - Abstract `BaseConnector` interface defines the contract
  - Each connector (CSV, PostgreSQL, MySQL) implements this interface
  - Handles connection management, schema inference, data loading
  - Isolates database-specific code from business logic

- **processor/**: Data processing engine
  - `_processor.py`: Core workflow execution logic (private module)
  - `query.py`: SQL query execution, validation, and result formatting
  - `streaming.py`: Large dataset handling with chunked processing
  - `export.py`: Export to various formats (CSV, PDF, Markdown)
  - **Boundary:** Only communicates with connectors, never directly with API layer

- **plugins/**: Extensibility system
  - `base.py`: Plugin interface definition
  - `loader.py`: Dynamic plugin discovery and loading
  - `registry.py`: Central plugin registry
  - **Boundary:** Plugins are loaded at startup, isolated from request processing

### Application Layer (src/api/)

**Purpose:** Orchestrates business logic, handles HTTP concerns, implements authentication/authorization.

**Key Modules:**

- **routes/**: FastAPI route handlers
  - Thin controllers that delegate to services
  - Handle request/response validation with Pydantic
  - Implement error handling and HTTP status codes
  - **Boundary:** Only call services, never access core business logic directly

- **services/**: Business service implementations
  - `workflow.py`: Workflow CRUD and execution orchestration
  - `job.py`: Background job management
  - `notification.py`: User notifications
  - **Boundary:** Use core business logic, handle transaction boundaries

- **auth/**: Authentication and authorization
  - `auth_service.py`: Authentication logic (login, token validation)
  - `permissions.py`: Permission definitions
  - `rbac.py`: Role-based access control implementation
  - `dependencies.py`: FastAPI dependency injection for auth
  - `decorators.py`: Route protection decorators

### Presentation Layer (src/)

**Purpose:** User interface built with React and Next.js, communicates with backend via REST API.

**Key Modules:**

- **app/**: Next.js App Router structure
  - `page.tsx`: Main dashboard, entry point for the application
  - `layout.tsx`: Root layout with Redux/Zustand providers
  - **Boundary:** Only communicates via API calls to backend

- **components/panels/**: Feature-specific UI components
  - `DataInspectionPanel.tsx`: Data preview with statistics
  - `AiSqlBuilderPanel.tsx`: AI-powered SQL generation interface
  - `AiPipelineBuilderPanel.tsx`: Workflow pipeline generation
  - **Boundary:** Each component is self-contained with props for configuration

- **components/workflow/**: Workflow canvas and nodes
  - `canvas.tsx`: Main React Flow canvas with node manipulation
  - **Boundary:** Manages local state, syncs with backend via API

## Component Responsibilities

### Frontend Components

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| `page.tsx` | Main dashboard layout, workflow list | `canvas.tsx`, API calls |
| `canvas.tsx` | Workflow visual editor, node manipulation | `@xyflow/react`, panel components |
| `DataInspectionPanel.tsx` | Data preview, column statistics, pagination | API, data visualization |
| `AiSqlBuilderPanel.tsx` | Natural language to SQL conversion | LLM API, SQL validation |
| `AiPipelineBuilderPanel.tsx` | AI-generated workflow creation | LLM API, workflow API |

### Backend Services

| Service | Responsibility | Dependencies |
|----------|---------------|--------------|
| `workflow.py` | Workflow CRUD, execution orchestration | Core processors, job service |
| `job.py` | Background job lifecycle management | Task queue, cache |
| `auth_service.py` | User authentication, token management | Database models, encryption |
| `notification.py` | User notifications, alerts | Job service |

### Core Business Logic

| Module | Responsibility | Interface |
|--------|---------------|-----------|
| `connectors/` | Data source abstraction | `BaseConnector` protocol |
| `processor/query.py` | SQL execution, validation | DuckDB connection |
| `processor/streaming.py` | Large dataset handling | Chunking strategy |
| `plugins/` | Extensibility system | `Plugin` protocol |

## Data Flow

### Workflow Execution Flow

```
1. User Action (Frontend)
   ├─ canvas.tsx: User adds/configures node
   └─ POST /api/v1/workflows/execute

2. API Layer
   ├─ routes/workflows.py: Validate request
   ├─ services/workflow.py: Orchestrate execution
   └─ auth/dependencies.py: Check permissions

3. Domain Layer
   ├─ processor/query.py: Execute SQL transformations
   ├─ connectors/: Load data from sources
   └─ cache/: Check for cached results

4. Infrastructure
   ├─ DuckDB: Execute analytical queries
   └─ Database: Persist workflow/job state

5. Response
   └─ Return results to frontend for preview
```

### AI SQL Generation Flow

```
1. User Input (Frontend)
   └─ AiSqlBuilderPanel.tsx: Natural language request

2. API Layer
   ├─ POST /api/v1/workflows/ai-sql
   └─ Validate input, load schema context

3. Domain Layer
   ├─ processor/query.py: Build LLM prompt with schema
   ├─ Call external LLM API (OpenAI, Anthropic, etc.)
   └─ Validate generated SQL with EXPLAIN

4. Response
   └─ Return SQL and execution plan to frontend
```

## Key File Locations

| Purpose | File Path |
|---------|-----------|
| Backend entry point | `src/api/main.py` |
| Frontend entry point | `src/app/page.tsx` |
| Workflow execution | `src/api/routes/workflows.py` |
| Data processing core | `src/core/processor/query.py` |
| CSV connector | `src/core/connectors/csv.py` |
| Plugin interface | `src/core/plugins/base.py` |
| Test configuration | `tests/e2e/playwright.config.ts` |
| Standalone CLI tool | `data-processor.py` |

## Module Boundaries and Contract

### Connector Interface (Repository Pattern)

```python
# src/core/connectors/base.py
class BaseConnector(Protocol):
    """Abstract connector interface for all data sources."""
    
    def connect(self, connection_string: str) -> None:
        """Establish connection to data source."""
        
    def get_schema(self) -> Dict[str, str]:
        """Return column names and types."""
        
    def load_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Load data into pandas DataFrame."""
        
    def disconnect(self) -> None:
        """Close connection."""
```

### Service Layer Contract

Services receive domain objects, perform business logic, and return domain objects. They handle:
- Transaction boundaries
- Caching decisions
- Error handling and logging
- Permission checks (via auth layer)

### API Route Contract

Routes receive HTTP requests, validate with Pydantic, delegate to services, and return HTTP responses. They handle:
- Request/response serialization
- HTTP status codes
- Error mapping to HTTP responses
- Authentication/authorization (via dependencies)
