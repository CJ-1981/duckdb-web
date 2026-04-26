# SPEC-WORKFLOW-001: Workflow Automation System

## Metadata

- **SPEC ID**: SPEC-WORKFLOW-001
- **Title**: Workflow Automation System
- **Status**: Planned
- **Created**: 2026-04-24
- **Updated**: 2026-04-24
- **Author**: CJ-1981
- **Priority**: High
- **Issue Number**: TBD
- **Version**: 1.0.0

## History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-24 | Initial SPEC creation | CJ-1981 |

## Overview

### Purpose

Extend the DuckDB Workflow Builder with a comprehensive workflow automation system that enables users to schedule, execute, and monitor data processing pipelines without manual intervention. The system will support cron-based scheduling, background job processing, error handling with retry logic, and execution history tracking.

### Scope

**IN SCOPE:**
- Workflow definition and storage (JSON-based workflow templates)
- Job scheduling with cron expressions and interval-based triggers
- Background job execution engine with task queue
- Job status tracking and execution history
- Error handling with configurable retry logic
- Version control for workflow definitions
- REST API for workflow and job management
- Basic monitoring dashboard for job status

**OUT OF SCOPE:**
- Multi-tenant SaaS features (single-user system only)
- Real-time collaborative editing
- Workflow marketplace or sharing
- Complex conditional logic (if/else branching)
- Parallel execution of workflow steps
- Distributed execution across multiple servers
- Workflow debugging/profiling tools
- Custom scripting languages within workflows

### Dependencies

- **SPEC-CSV-001** (Enhanced CSV Connector): Provides encoding detection, type inference, and CSV import capabilities
- **Existing Workflow Canvas**: @xyflow/react visual workflow builder
- **DuckDB Processing Engine**: Core data processing capabilities

## Assumptions

### Technical Assumptions

1. **Queue System**: Redis will be available for task queue management (RQ or Celery)
2. **Database**: PostgreSQL will be used for workflow metadata and job history
3. **Single-Server Deployment**: All components run on a single server initially
4. **Cron Support**: APScheduler or similar for job scheduling
5. **Python 3.12+**: Current Python version requirement maintained

### Business Assumptions

1. **User Expertise**: Target users have basic technical knowledge but are not workflow automation experts
2. **Workflow Complexity**: Most workflows will be linear (step 1 → step 2 → step 3)
3. **Execution Frequency**: Most jobs run daily or weekly, not minute-by-minute
4. **Error Recovery**: Users want simple retry logic, not complex failure recovery strategies
5. **Monitoring Needs**: Basic status tracking is sufficient for MVP

### Integration Assumptions

1. **Existing API**: FastAPI backend already has authentication and user management
2. **Frontend Framework**: Next.js 16 with React 19 already in use
3. **Database Access**: SQLAlchemy 2.0+ already configured for PostgreSQL
4. **File Storage**: Local filesystem for workflow definitions initially

## Requirements

### User Requirements (UR-WORKFLOW-XXX)

#### UR-WORKFLOW-001: Workflow Definition Management
**WHEN** a user creates a workflow, **THE SYSTEM SHALL** provide a visual interface to define workflow steps, connections, and parameters.

**WHILE** a user is editing a workflow, **THE SYSTEM SHALL** auto-save changes every 30 seconds to prevent data loss.

**WHEN** a user saves a workflow, **THE SYSTEM SHALL** validate all node connections and required parameters before persisting.

**WHERE** a workflow references external data sources, **THE SYSTEM SHALL** validate connection strings and credentials during save.

#### UR-WORKFLOW-002: Workflow Version Control
**WHEN** a user saves an existing workflow, **THE SYSTEM SHALL** create a new version with timestamp and version number.

**WHEN** a user views workflow history, **THE SYSTEM SHALL** display all previous versions with creation timestamps.

**WHILE** a user is viewing workflow versions, **THE SYSTEM SHALL** allow comparison between any two versions.

**IF** a user wants to revert to a previous version, **THE SYSTEM SHALL** restore that version as the current working version.

#### UR-WORKFLOW-003: Job Scheduling
**WHEN** a user creates a scheduled job, **THE SYSTEM SHALL** support cron expression syntax for flexible scheduling.

**WHEN** a user creates an interval-based job, **THE SYSTEM SHALL** support predefined intervals (hourly, daily, weekly).

**WHILE** a user is configuring a schedule, **THE SYSTEM SHALL** validate cron expressions and provide next execution time preview.

**WHEN** a user sets a schedule, **THE SYSTEM SHALL** calculate and display the next 5 execution times.

**IF** a user provides an invalid cron expression, **THE SYSTEM SHALL** display a specific error message explaining the syntax error.

#### UR-WORKFLOW-004: Job Execution
**WHEN** a scheduled job triggers, **THE SYSTEM SHALL** execute the workflow in the background without blocking user interactions.

**WHEN** a user manually triggers a workflow, **THE SYSTEM SHALL** execute it immediately and provide real-time status updates.

**WHILE** a workflow is executing, **THE SYSTEM SHALL** update job status every 5 seconds.

**WHEN** a workflow completes successfully, **THE SYSTEM SHALL** store execution results and metadata.

**IF** a workflow fails during execution, **THE SYSTEM SHALL** capture error details and logs for debugging.

#### UR-WORKFLOW-005: Error Handling and Retry
**WHEN** a workflow step fails, **THE SYSTEM SHALL** automatically retry the step up to 3 times with exponential backoff (1s, 2s, 4s).

**WHILE** retrying a failed step, **THE SYSTEM SHALL** log each retry attempt with timestamp and error details.

**IF** all retry attempts fail, **THE SYSTEM SHALL** mark the job as failed and send a notification to the user.

**WHEN** a workflow fails, **THE SYSTEM SHALL** preserve partial results for inspection.

**WHERE** a workflow defines custom retry logic, **THE SYSTEM SHALL** use the user-defined retry configuration instead of defaults.

#### UR-WORKFLOW-006: Job Monitoring
**WHEN** a user views the job list, **THE SYSTEM SHALL** display all jobs with status, creation time, and last execution time.

**WHILE** a job is running, **THE SYSTEM SHALL** show real-time progress indicators and current step being executed.

**WHEN** a user clicks on a completed job, **THE SYSTEM SHALL** display detailed execution logs, results, and timing information.

**IF** a job has failed, **THE SYSTEM SHALL** highlight error messages and suggest common troubleshooting steps.

**WHEN** a user views job history, **THE SYSTEM SHALL** provide filtering and sorting by status, date range, and workflow type.

#### UR-WORKFLOW-007: Workflow Import/Export
**WHEN** a user exports a workflow, **THE SYSTEM SHALL** generate a JSON file containing the complete workflow definition.

**WHEN** a user imports a workflow, **THE SYSTEM SHALL** validate the JSON structure and compatibility before importing.

**WHERE** an imported workflow conflicts with an existing workflow name, **THE SYSTEM SHALL** prompt the user to rename or overwrite.

**IF** an imported workflow references data sources not available in the current environment, **THE SYSTEM SHALL** warn the user and mark those steps as invalid.

#### UR-WORKFLOW-008: Email Notifications
**WHEN** a scheduled job completes successfully, **THE SYSTEM SHALL** send an email notification if enabled by the user.

**WHEN** a job fails after all retries, **THE SYSTEM SHALL** send an immediate failure notification email.

**WHILE** sending notifications, **THE SYSTEM SHALL** include job name, status, execution time, and error details or result summary.

**IF** email delivery fails, **THE SYSTEM SHALL** log the failure and retry delivery up to 3 times.

### Engineering Requirements (ER-WORKFLOW-XXX)

#### ER-WORKFLOW-001: Backend Architecture
**THE SYSTEM SHALL** implement a task queue using Redis and RQ (Redis Queue) for background job processing.

**THE SYSTEM SHALL** use APScheduler for cron-based job scheduling with persistent job store in PostgreSQL.

**THE SYSTEM SHALL** implement a workflow execution engine that:
- Parses workflow JSON definitions
- Executes nodes in topological order
- Passes data between nodes via DuckDB temporary views
- Handles node failures gracefully with rollback

**THE SYSTEM SHALL** store workflow definitions as JSONB in PostgreSQL for efficient querying and versioning.

#### ER-WORKFLOW-002: Workflow Storage Schema
**THE SYSTEM SHALL** define the following database tables:

- `workflows`: workflow definitions and metadata
  - `id`: UUID primary key
  - `name`: unique workflow name
  - `description`: optional workflow description
  - `definition`: JSONB workflow structure (nodes, edges, parameters)
  - `version`: integer version number
  - `created_at`: timestamp
  - `updated_at`: timestamp
  - `created_by`: user reference

- `workflow_versions`: version history
  - `id`: UUID primary key
  - `workflow_id`: reference to workflows table
  - `version`: version number
  - `definition`: JSONB workflow structure at version
  - `created_at`: timestamp
  - `change_description`: optional commit message

- `jobs`: scheduled and manual job executions
  - `id`: UUID primary key
  - `workflow_id`: reference to workflows table
  - `name`: job name
  - `schedule_type`: enum (manual, cron, interval)
  - `schedule_expression`: cron expression or interval
  - `enabled`: boolean flag
  - `created_at`: timestamp
  - `next_run_at`: calculated next execution time

- `job_executions`: execution history and results
  - `id`: UUID primary key
  - `job_id`: reference to jobs table
  - `status`: enum (pending, running, completed, failed, cancelled)
  - `started_at`: timestamp
  - `completed_at`: nullable timestamp
  - `result`: JSONB execution results
  - `error_message`: nullable text for failure details
  - `retry_count`: integer tracking retry attempts
  - `execution_logs`: JSONB array of log entries

#### ER-WORKFLOW-003: API Design
**THE SYSTEM SHALL** implement the following REST API endpoints:

**Workflow Management:**
- `POST /api/v1/workflows` - Create new workflow
- `GET /api/v1/workflows` - List all workflows with pagination
- `GET /api/v1/workflows/{id}` - Get workflow by ID
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `GET /api/v1/workflows/{id}/versions` - Get workflow version history
- `POST /api/v1/workflows/{id}/rollback` - Revert to previous version
- `POST /api/v1/workflows/import` - Import workflow from JSON
- `GET /api/v1/workflows/{id}/export` - Export workflow as JSON

**Job Management:**
- `POST /api/v1/jobs` - Create scheduled job
- `GET /api/v1/jobs` - List all jobs with filters
- `GET /api/v1/jobs/{id}` - Get job details
- `PUT /api/v1/jobs/{id}` - Update job configuration
- `DELETE /api/v1/jobs/{id}` - Delete job
- `POST /api/v1/jobs/{id}/trigger` - Manually trigger job execution
- `POST /api/v1/jobs/{id}/enable` - Enable scheduled job
- `POST /api/v1/jobs/{id}/disable` - Disable scheduled job

**Execution Management:**
- `GET /api/v1/executions` - List job executions with filters
- `GET /api/v1/executions/{id}` - Get execution details
- `GET /api/v1/executions/{id}/logs` - Stream execution logs
- `POST /api/v1/executions/{id}/cancel` - Cancel running execution
- `GET /api/v1/executions/{id}/results` - Download execution results

**THE SYSTEM SHALL** use Pydantic v2 schemas for request/response validation.

**THE SYSTEM SHALL** implement OpenAPI documentation for all endpoints.

#### ER-WORKFLOW-004: Frontend Components
**THE SYSTEM SHALL** extend the existing React Flow canvas with workflow-specific features:

- Workflow sidebar for saving/loading workflows
- Schedule configuration dialog with cron expression builder
- Job list page with status indicators and filters
- Execution detail page with logs and results
- Version history viewer with diff highlighting
- Import/export workflow dialog

**THE SYSTEM SHALL** implement real-time updates using WebSocket or Server-Sent Events for running jobs.

**THE SYSTEM SHALL** use shadcn/ui components for consistent UI styling.

#### ER-WORKFLOW-005: Error Handling Strategy
**THE SYSTEM SHALL** implement a hierarchical error handling strategy:

1. **Node-Level Errors**: Retry individual nodes up to 3 times
2. **Workflow-Level Errors**: Mark workflow as failed, preserve partial results
3. **System-Level Errors**: Log to system logs, alert administrators

**THE SYSTEM SHALL** categorize errors into:
- **Transient Errors**: Retryable (network timeouts, temporary file locks)
- **Permanent Errors**: Fail immediately (invalid SQL, missing tables)
- **Configuration Errors**: Fail before execution (invalid cron expressions)

**THE SYSTEM SHALL** implement structured logging with:
- Timestamp for each log entry
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Job and execution ID context
- Error stack traces for failures

#### ER-WORKFLOW-006: Performance Requirements
**THE SYSTEM SHALL** support concurrent execution of at least 10 jobs simultaneously.

**THE SYSTEM SHALL** complete job status updates within 1 second of state changes.

**THE SYSTEM SHALL** execute workflows with 100 nodes or less in under 5 minutes (excluding data processing time).

**THE SYSTEM SHALL** serve the job list page within 2 seconds for up to 1000 jobs.

**THE SYSTEM SHALL** implement database indexes on frequently queried columns (job_id, status, created_at).

### System Requirements (SR-WORKFLOW-XXX)

#### SR-WORKFLOW-001: Scalability
**THE SYSTEM SHALL** handle up to 1000 scheduled jobs without performance degradation.

**THE SYSTEM SHALL** store up to 100,000 execution history records without query performance impact.

**THE SYSTEM SHALL** support workflow definitions up to 1MB in size.

**THE SYSTEM SHALL** process up to 50 concurrent job executions.

#### SR-WORKFLOW-002: Security
**THE SYSTEM SHALL** enforce authentication on all workflow and job management endpoints.

**THE SYSTEM SHALL** implement authorization checks to ensure users can only access their own workflows.

**THE SYSTEM SHALL** sanitize workflow definitions to prevent injection attacks (SQL, NoSQL, code injection).

**THE SYSTEM SHALL** encrypt sensitive credentials (database passwords, API keys) at rest in PostgreSQL.

**THE SYSTEM SHALL** validate all cron expressions against a whitelist to prevent denial-of-service attacks.

**THE SYSTEM SHALL** implement rate limiting on job execution endpoints (max 10 executions per minute per user).

#### SR-WORKFLOW-003: Reliability
**THE SYSTEM SHALL** achieve 99.5% uptime for the job scheduling service.

**THE SYSTEM SHALL** persist scheduled jobs in PostgreSQL to survive server restarts.

**THE SYSTEM SHALL** implement idempotent job execution to prevent duplicate processing on retry.

**THE SYSTEM SHALL** use database transactions for all state-changing operations to prevent data corruption.

**THE SYSTEM SHALL** implement health check endpoints for monitoring job scheduler and worker processes.

#### SR-WORKFLOW-004: Data Integrity
**THE SYSTEM SHALL** enforce referential integrity between workflows, jobs, and executions.

**THE SYSTEM SHALL** prevent deletion of workflows that have active scheduled jobs.

**THE SYSTEM SHALL** validate workflow definitions before saving to ensure all node references are valid.

**THE SYSTEM SHALL** implement foreign key constraints with appropriate ON DELETE rules.

**THE SYSTEM SHALL** use database-level constraints to enforce unique workflow names per user.

### Operations Requirements (OR-WORKFLOW-XXX)

#### OR-WORKFLOW-001: Monitoring
**THE SYSTEM SHALL** expose Prometheus metrics for:
- Job queue depth
- Job execution success/failure rates
- Average job execution duration
- Worker process health status

**THE SYSTEM SHALL** implement structured logging in JSON format for log aggregation.

**THE SYSTEM SHALL** provide API endpoints for system health checks:
- `/health` - Overall system health
- `/health/scheduler` - Job scheduler status
- `/health/workers` - Worker process status
- `/health/redis` - Redis connectivity
- `/health/database` - Database connectivity

#### OR-WORKFLOW-002: Maintenance
**THE SYSTEM SHALL** implement automatic cleanup of execution history older than 90 days (configurable).

**THE SYSTEM SHALL** provide database migration scripts for schema upgrades.

**THE SYSTEM SHALL** implement backup and restore procedures for workflow definitions.

**THE SYSTEM SHALL** provide admin APIs for:
- Manual job queue cleanup
- Worker process restart
- Execution history archival

#### OR-WORKFLOW-003: Deployment
**THE SYSTEM SHALL** provide Docker containers for:
- API server
- Worker process
- Redis instance
- PostgreSQL database

**THE SYSTEM SHALL** include Docker Compose configuration for local development.

**THE SYSTEM SHALL** support environment variable configuration for:
- Database connection strings
- Redis connection details
- Email SMTP settings
- Authentication credentials

**THE SYSTEM SHALL** implement graceful shutdown handling to complete running jobs before exit.

## Exclusions (What NOT to Build)

### Explicitly Out of Scope

1. **Multi-Tenant SaaS Features**
   - No user-to-user workflow sharing
   - No team collaboration features
   - No per-user resource quotas
   - No multi-tenant data isolation

2. **Advanced Workflow Features**
   - No conditional branching (if/else nodes)
   - No parallel execution paths
   - No sub-workflow or nested workflow support
   - No workflow debugging/profiling tools
   - No workflow templates marketplace

3. **Complex Error Recovery**
   - No manual intervention workflows
   - No approval gates for workflow steps
   - No rollback to intermediate workflow states
   - No complex retry strategies (circuit breakers, dead letter queues)

4. **Enterprise Features**
   - No SSO integration (beyond basic OAuth)
   - No audit logging for compliance
   - No workflow approval processes
   - No role-based workflow access control

5. **Distributed Execution**
   - No multi-server deployment
   - No load balancing for workers
   - No distributed task coordination
   - No remote workflow execution

## Non-Functional Requirements

### Performance
- Job list page load time: < 2 seconds for 1000 jobs
- Workflow save operation: < 1 second
- Job trigger to execution start: < 5 seconds
- API response time (p95): < 500ms for non-execution endpoints

### Maintainability
- Code coverage target: 85% for new workflow automation code
- Follow existing project coding standards (Ruff formatting, type hints)
- Comprehensive API documentation via OpenAPI/Swagger
- Inline code comments for complex workflow execution logic

### Usability
- Intuitive cron expression builder GUI
- Clear error messages with actionable suggestions
- Responsive design for mobile and desktop
- Keyboard shortcuts for power users

### Compatibility
- Python 3.12+ compatibility
- PostgreSQL 14+ compatibility
- Redis 6+ compatibility
- Modern browser support (Chrome 90+, Firefox 88+, Safari 14+)

## Success Criteria

### Functional Success
- Users can create, save, and load workflows through the UI
- Scheduled jobs execute at configured times without manual intervention
- Failed jobs retry automatically with exponential backoff
- Execution history provides complete audit trail of job runs
- Import/export enables workflow sharing across environments

### Technical Success
- Background job processing handles 10+ concurrent jobs
- Job scheduler survives server restarts without job loss
- Error handling prevents cascading failures
- API endpoints respond within performance targets
- Database queries remain efficient with 100K+ execution records

### Business Success
- Reduces manual data processing tasks by 80%
- Enables unattended overnight batch processing
- Provides visibility into job failures and execution trends
- Extensible architecture for future workflow features

## Related Documentation

- **SPEC-CSV-001**: Enhanced CSV Connector with encoding detection and type inference
- **Product Documentation**: `.moai/project/product.md`
- **Technology Stack**: `.moai/project/tech.md`
- **Project Structure**: `.moai/project/structure.md`

## Glossary

- **Workflow**: A directed acyclic graph (DAG) of data processing steps defined in the visual canvas
- **Job**: A scheduled or manual execution instance of a workflow
- **Execution**: A single run of a job with specific start/end times and results
- **Node**: A single operation in a workflow (data source, transformation, output)
- **Cron Expression**: A time-based job scheduling syntax (e.g., "0 8 * * *" for daily at 8 AM)
- **Task Queue**: A message queue system for background job processing
- **Worker**: A background process that executes jobs from the queue
- **Retry**: Automatic re-execution of a failed job or step with configurable delays
