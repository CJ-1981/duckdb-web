# Implementation Plan: SPEC-WORKFLOW-001

## Metadata

- **SPEC ID**: SPEC-WORKFLOW-001
- **Document Type**: Implementation Plan
- **Version**: 1.0.0
- **Created**: 2026-04-24
- **Updated**: 2026-04-24
- **Author**: CJ-1981

## Overview

This implementation plan outlines the phased development of the Workflow Automation System for the DuckDB Workflow Builder. The system will be delivered in 4 phases over approximately 3 weeks, prioritizing core workflow storage and job execution before advanced monitoring features.

## Implementation Phases

### Phase 1: Foundation (Week 1) - Priority: HIGH

**Goal**: Establish database schema, core backend models, and basic API endpoints.

#### 1.1 Database Schema and Models
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Create SQLAlchemy models for workflows, workflow_versions, jobs, job_executions
- Define database migrations using Alembic
- Implement foreign key relationships and constraints
- Add database indexes for performance
- Create Pydantic v2 schemas for request/response validation

**Deliverables**:
- `src/api/models/workflow.py`
- `src/api/models/job.py`
- `src/api/schemas/workflow.py`
- `src/api/schemas/job.py`
- Alembic migration scripts

**Acceptance Criteria**:
- All models successfully create tables in PostgreSQL
- Foreign key constraints prevent orphaned records
- Pydantic schemas validate all required fields
- Database indexes improve query performance by 50%+

#### 1.2 Workflow CRUD API
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Implement FastAPI routes for workflow CRUD operations
- Add authentication and authorization middleware
- Implement workflow versioning logic
- Add request validation with Pydantic
- Write comprehensive unit tests

**Deliverables**:
- `src/api/routes/workflows.py`
- `tests/api/test_workflows.py`
- API documentation via OpenAPI

**Acceptance Criteria**:
- All CRUD endpoints functional (Create, Read, Update, Delete, List)
- Version history created on each workflow update
- Users can only access their own workflows
- API responses follow consistent schema
- Unit tests achieve 85%+ coverage

#### 1.3 Workflow Import/Export
**Priority**: MEDIUM
**Effort**: 1 day

**Tasks**:
- Implement JSON serialization/deserialization for workflows
- Add validation for imported workflow structures
- Handle naming conflicts during import
- Implement export endpoint with proper content-type headers

**Deliverables**:
- Import/export endpoints in workflows.py
- Import validation logic
- Test fixtures for sample workflows

**Acceptance Criteria**:
- Workflows export to valid JSON files
- Imported workflows validate structure and compatibility
- Naming conflicts prompt user for resolution
- Exported files can be successfully re-imported

### Phase 2: Job Scheduling and Execution (Week 2) - Priority: HIGH

**Goal**: Implement background job processing with cron scheduling and retry logic.

#### 2.1 Task Queue Setup
**Priority**: HIGH
**Effort**: 1 day

**Tasks**:
- Install and configure Redis for task queue
- Integrate RQ (Redis Queue) for background jobs
- Create worker process configuration
- Implement job queue monitoring endpoints
- Add Docker Compose services for Redis

**Deliverables**:
- `src/api/tasks/queue.py`
- Worker startup scripts
- Docker Compose configuration updates
- Health check endpoints for queue status

**Acceptance Criteria**:
- Redis connection stable and persistent
- Workers process jobs from queue successfully
- Health checks report queue depth and worker status
- Workers gracefully shutdown on interrupt signals

#### 2.2 Job Scheduling Engine
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Integrate APScheduler for cron-based scheduling
- Implement job persistence in PostgreSQL
- Add schedule validation logic (cron expressions)
- Calculate next execution times
- Enable/disable scheduled jobs
- Handle scheduler recovery after restart

**Deliverables**:
- `src/api/services/scheduler.py`
- Schedule validation utilities
- Scheduler health monitoring
- Test suite for schedule calculations

**Acceptance Criteria**:
- Valid cron expressions trigger jobs at correct times
- Invalid schedules rejected with clear error messages
- Scheduler survives restarts without job loss
- Next execution times calculated accurately
- Jobs can be enabled/disabled dynamically

#### 2.3 Workflow Execution Engine
**Priority**: HIGH
**Effort**: 3 days

**Tasks**:
- Implement workflow parsing from JSON definitions
- Create node execution engine with topological sort
- Pass data between nodes via DuckDB temporary views
- Handle node failures with retry logic
- Implement execution logging and status tracking
- Create result storage and retrieval

**Deliverables**:
- `src/api/services/execution.py`
- Node executor with retry logic
- Execution logger with structured output
- Error handling and rollback logic
- Integration tests for complete workflows

**Acceptance Criteria**:
- Workflows execute in correct topological order
- Data flows correctly between connected nodes
- Failed nodes retry up to 3 times with exponential backoff
- Execution logs captured at each step
- Partial results preserved on failure
- Results retrievable via API

#### 2.4 Job Management API
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Implement CRUD endpoints for jobs
- Add manual trigger endpoint
- Create job listing with filters (status, date range)
- Implement job execution history endpoint
- Add job enable/disable endpoints
- Write comprehensive tests

**Deliverables**:
- `src/api/routes/jobs.py`
- `src/api/routes/executions.py`
- `tests/api/test_jobs.py`
- `tests/api/test_executions.py`

**Acceptance Criteria**:
- Jobs can be created, updated, deleted, and listed
- Manual triggers execute workflows immediately
- Job history shows all executions with filters
- Jobs can be enabled/disabled without deletion
- API responses include execution status and timestamps

### Phase 3: Frontend Integration (Week 2-3) - Priority: HIGH

**Goal**: Extend React Flow canvas with workflow management UI and job monitoring dashboard.

#### 3.1 Workflow Management UI
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Add workflow save/load buttons to canvas toolbar
- Implement workflow list page with search
- Create workflow version history viewer
- Add import/export workflow dialogs
- Implement auto-save with visual indicator

**Deliverables**:
- `src/components/workflow/WorkflowSidebar.tsx`
- `src/app/workflows/page.tsx`
- `src/components/workflow/VersionHistory.tsx`
- API integration functions

**Acceptance Criteria**:
- Workflows save with validation feedback
- Workflow list displays with pagination
- Version history shows timestamps and diffs
- Import/export dialogs handle file selection
- Auto-save indicator visible during editing

#### 3.2 Job Scheduling UI
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Create job creation/editing dialog
- Implement cron expression builder GUI
- Add job list page with status indicators
- Create job detail page with execution history
- Implement enable/disable job toggles

**Deliverables**:
- `src/components/jobs/JobScheduleDialog.tsx`
- `src/components/jobs/CronBuilder.tsx`
- `src/app/jobs/page.tsx`
- `src/app/jobs/[id]/page.tsx`

**Acceptance Criteria**:
- Cron builder provides intuitive interface
- Next execution times preview correctly
- Job list shows status with color coding
- Job details display schedule and history
- Enable/disable toggles update immediately

#### 3.3 Execution Monitoring UI
**Priority**: MEDIUM
**Effort**: 2 days

**Tasks**:
- Create execution detail page with logs
- Implement real-time status updates (WebSocket/SSE)
- Add progress indicators for running jobs
- Display execution results with data tables
- Implement error highlighting and troubleshooting tips

**Deliverables**:
- `src/app/executions/[id]/page.tsx`
- `src/components/executions/ExecutionLogs.tsx`
- `src/components/executions/RealTimeProgress.tsx`
- WebSocket integration for live updates

**Acceptance Criteria**:
- Execution logs display with timestamps
- Real-time updates show progress every 5 seconds
- Completed executions show results in tables
- Failed executions highlight errors with solutions
- Data tables support pagination and export

### Phase 4: Monitoring and Notifications (Week 3) - Priority: MEDIUM

**Goal**: Add system monitoring, email notifications, and operational tooling.

#### 4.1 Email Notifications
**Priority**: MEDIUM
**Effort**: 1 day

**Tasks**:
- Implement email service with SMTP integration
- Create email templates for success/failure notifications
- Add notification preferences to jobs
- Implement email delivery retry logic
- Add notification delivery status tracking

**Deliverables**:
- `src/api/services/notification.py`
- Email templates (HTML/text)
- Notification settings in job schema
- Tests for email delivery

**Acceptance Criteria**:
- Success emails sent on job completion
- Failure emails sent immediately after retries exhausted
- Emails include job details and execution summary
- Delivery failures logged and retried
- Users can enable/disable notifications per job

#### 4.2 System Monitoring
**Priority**: MEDIUM
**Effort**: 1 day

**Tasks**:
- Expose Prometheus metrics for job queue and executions
- Implement structured JSON logging
- Create health check endpoints
- Add worker process monitoring
- Implement execution history cleanup job

**Deliverables**:
- `src/api/metrics.py`
- Health check endpoints
- Log aggregation configuration
- Cleanup job scheduled task

**Acceptance Criteria**:
- Prometheus endpoints expose queue depth and success rates
- Health checks return 200 for healthy services
- Logs structured in JSON format
- Execution history auto-deletes after 90 days
- Worker failures alert via logs

#### 4.3 Error Handling and Recovery
**Priority**: MEDIUM
**Effort**: 1 day

**Tasks**:
- Implement error categorization (transient/permanent)
- Add retry configuration to workflow nodes
- Create error message library with solutions
- Implement partial result preservation
- Add rollback logic for failed workflows

**Deliverables**:
- Error handling utilities
- Error message documentation
- Retry configuration schema
- Rollback logic in execution engine

**Acceptance Criteria**:
- Transient errors retry automatically
- Permanent errors fail immediately with clear messages
- Partial results accessible after failure
- Rollback restores database state on failure
- Error messages include troubleshooting steps

#### 4.4 Testing and Documentation
**Priority**: HIGH
**Effort**: 2 days

**Tasks**:
- Write comprehensive integration tests
- Create E2E tests for complete workflows
- Document API endpoints with examples
- Write user guide for workflow automation
- Create troubleshooting documentation

**Deliverables**:
- `tests/integration/test_workflow_execution.py`
- `tests/e2e/workflow-automation.spec.ts`
- API documentation updates
- User guide markdown files
- Troubleshooting guide

**Acceptance Criteria**:
- Integration tests cover complete workflow lifecycle
- E2E tests validate user workflows from creation to execution
- API documentation includes request/response examples
- User guide explains all features with screenshots
- Troubleshooting guide covers common errors

## Technical Approach

### Architecture Decisions

**Task Queue**: RQ (Redis Queue) over Celery
- **Rationale**: Simpler setup, better suited for single-server deployment, sufficient for MVP scale
- **Trade-off**: Celery provides more advanced features but adds complexity

**Job Scheduler**: APScheduler with PostgreSQL job store
- **Rationale**: Native Python integration, persistent storage, mature library
- **Trade-off**: Less feature-rich than enterprise schedulers (Quartz, Airflow)

**Workflow Storage**: JSONB in PostgreSQL
- **Rationale**: Efficient querying, native JSON support, ACID compliance
- **Trade-off**: Less flexible than document store for complex nested structures

**Real-time Updates**: Server-Sent Events (SSE) over WebSockets
- **Rationale**: Simpler implementation, sufficient for unidirectional status updates
- **Trade-off**: WebSockets support bidirectional communication but add complexity

### Performance Optimization

**Database**:
- Index on `(user_id, created_at)` for job queries
- Partition job_executions table by created_at (monthly partitions)
- Connection pooling with SQLAlchemy (max 20 connections)

**Caching**:
- Cache workflow definitions in Redis (TTL: 1 hour)
- Cache cron expression parsing results
- Cache next execution time calculations

**Query Optimization**:
- Use `select_for_update()` to prevent race conditions in job scheduling
- Batch execution history inserts for bulk operations
- Lazy load execution logs (only when requested)

### Error Handling Strategy

**Retry Logic**:
- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
- Transient errors: retry (network timeouts, temporary file locks)
- Permanent errors: fail immediately (invalid SQL, missing tables)
- Configuration errors: validate before execution

**Rollback Strategy**:
- Database transactions for all state changes
- DuckDB temporary views for intermediate results
- Cleanup temporary views on failure or completion
- Preserve partial results in separate schema

## Risk Mitigation

### Technical Risks

**Risk**: Redis single point of failure
- **Mitigation**: Implement Redis persistence (AOF), monitor Redis health
- **Contingency**: Queue jobs in PostgreSQL if Redis unavailable

**Risk**: Worker process crashes during execution
- **Mitigation**: Implement worker health monitoring, auto-restart workers
- **Contingency**: Job timeout and recovery on restart

**Risk**: Database connection exhaustion under load
- **Mitigation**: Connection pooling, limit concurrent executions
- **Contingency**: Queue jobs when pool exhausted

**Risk**: Cron scheduling drift over time
- **Mitigation**: Use UTC for all scheduling, sync with NTP
- **Contingency**: Recalculate next run times on scheduler restart

### Operational Risks

**Risk**: Execution history storage grows unbounded
- **Mitigation**: Automated cleanup job (90-day retention), configurable retention policy
- **Contingency**: Manual archival scripts for long-term storage

**Risk**: Email delivery failures go unnoticed
- **Mitigation**: Log delivery failures, retry 3 times, alert on persistent failures
- **Contingency**: Webhook notifications as fallback

**Risk**: Concurrent job execution exceeds system resources
- **Mitigation**: Limit concurrent jobs (configurable, default: 10), resource monitoring
- **Contingency**: Queue excess jobs, execute when capacity available

## Quality Assurance

### Testing Strategy

**Unit Tests** (pytest):
- All models, schemas, and services
- Focus on business logic validation
- Target: 85%+ code coverage

**Integration Tests** (pytest):
- Complete workflow execution lifecycle
- Database transactions and rollback
- Job scheduling and triggering
- API endpoint integration

**E2E Tests** (Playwright):
- User workflows from UI to execution
- Job creation and scheduling
- Execution monitoring and error handling
- Import/export workflows

**Performance Tests** (locust):
- 100 concurrent job executions
- 1000 job list page load
- Sustained load over 1 hour

### Code Quality Standards

**Python Backend**:
- Ruff formatting and linting
- Type hints with mypy strict mode
- Docstrings for all public functions
- Pydantic v2 for validation

**TypeScript Frontend**:
- ESLint with TypeScript rules
- Strict mode enabled
- Component documentation
- Consistent naming conventions

**Security**:
- Input validation on all endpoints
- SQL injection prevention
- Authentication/authorization on all routes
- Credential encryption at rest

## Deployment Strategy

### Development Environment
```bash
# Start all services
docker-compose up -d

# Run backend
python -m uvicorn src.api.main:create_app --reload --port 8000

# Run frontend
npm run dev

# Start worker
python -m rq worker --url redis://localhost:6379/0
```

### Production Deployment

**Docker Containers**:
- `api-server`: FastAPI application (gunicorn + uvicorn workers)
- `worker`: RQ worker process (4 workers per container)
- `redis`: Redis for task queue
- `postgres`: PostgreSQL for data persistence

**Environment Variables**:
```
DATABASE_URL=postgresql://user:pass@localhost/duckdb_workflow
REDIS_URL=redis://localhost:6379/0
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@example.com
SMTP_PASSWORD=secret
SECRET_KEY=<random-32-byte-string>
```

**Health Checks**:
- `/health` - Overall system health
- `/health/scheduler` - Job scheduler status
- `/health/workers` - Worker process status
- `/health/redis` - Redis connectivity
- `/health/database` - Database connectivity

## Success Metrics

### Functional Metrics
- Users can create and schedule workflows without errors
- 95%+ of scheduled jobs execute at configured times
- Failed jobs retry and recover or fail gracefully with clear errors
- Execution history provides complete audit trail

### Performance Metrics
- Job list page loads in < 2 seconds for 1000 jobs
- Workflow save completes in < 1 second
- Job trigger to execution starts in < 5 seconds
- API p95 response time < 500ms (non-execution endpoints)

### Quality Metrics
- 85%+ test coverage for new code
- Zero critical security vulnerabilities
- 99.5% uptime for job scheduling service
- User-reported bugs < 5 per month

## Dependencies and Blockers

### External Dependencies
- Redis 6+ installed and accessible
- PostgreSQL 14+ database available
- SMTP server for email notifications
- Python 3.12+ runtime
- Node.js 20+ runtime

### Internal Dependencies
- SPEC-CSV-001 (Enhanced CSV Connector) completed
- Existing workflow canvas (@xyflow/react) stable
- Authentication system functional
- Database migrations applied

### Potential Blockers
- Redis installation issues in production environment
- PostgreSQL connection pooling configuration
- SMTP server access for notifications
- Worker process stability under load

## Contingency Plans

### If Redis unavailable:
- Fall back to database-backed queue (slower but functional)
- Queue jobs in `job_queue` table with worker polling

### If email delivery fails:
- Log failures persistently
- Provide in-app notification center
- Implement webhook notifications as alternative

### If worker crashes:
- Supervisor process auto-restarts workers
- Jobs timeout and requeue on worker recovery
- Execution history preserved across restarts

### If database connection exhausted:
- Throttle new job submissions
- Return 503 Service Unavailable with retry header
- Alert operations team via monitoring

## Timeline Summary

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Foundation | 5 days | HIGH | None |
| Phase 2: Job Scheduling | 8 days | HIGH | Phase 1 |
| Phase 3: Frontend Integration | 6 days | HIGH | Phase 2 |
| Phase 4: Monitoring | 5 days | MEDIUM | Phase 3 |

**Total Duration**: Approximately 18 working days (3.6 weeks)

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4

**Parallel Opportunities**:
- Phase 3.2 (Job UI) can start during Phase 2.4 (Job API)
- Phase 4.1 (Email) can be deferred to post-MVP if needed

## Next Steps

1. **Immediate**: Set up development environment with Redis and PostgreSQL
2. **Week 1**: Implement Phase 1 (Foundation) - database models and CRUD API
3. **Week 2**: Implement Phase 2 (Job Scheduling) - task queue and execution engine
4. **Week 3**: Implement Phase 3 (Frontend) and Phase 4 (Monitoring)
5. **Testing**: Comprehensive testing throughout all phases
6. **Documentation**: Update API docs and user guide incrementally
