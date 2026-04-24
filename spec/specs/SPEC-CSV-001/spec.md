# SPEC-CSV-001: Enhanced CSV Connector with Encoding Detection

## Metadata

- **SPEC ID**: SPEC-CSV-001
- **Title**: Enhanced CSV Connector with Encoding Detection
- **Version**: 1.0.0
- **Status**: Planned
- **Created**: 2026-04-24
- **Updated**: 2026-04-24
- **Author**: CJ-1981
- **Priority**: High
- **Issue Number**: N/A
- **Related SPECs**: N/A
- **Estimated Effort**: 10-15 business days

## History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-24 | Initial SPEC creation | CJ-1981 |

## Overview

### Objective

Build a production-ready CSV connector that handles multiple character encodings, automatic type inference, and streaming for large files.

### Scope Constraints

This is a focused MVP with strict boundaries:
- **Duration**: 10-15 business days (2-3 weeks)
- **Files**: 3-5 Python files maximum
- **Test Files**: 2-3 test files
- **NO external dependencies**: No databases, APIs, or infrastructure
- **NO authentication**: Public API
- **NO frontend UI**: Backend API only
- **NO persistent storage**: In-memory sessions only

### Must-Have Features (MVP)

1. **Encoding Detection**: UTF-8, UTF-8-sig, CP949, EUC-KR support
2. **Type Inference**: Integer, Float, String, Boolean, Date, DateTime
3. **Streaming**: Files > 100MB streamed in chunks
4. **Error Handling**: Clear error messages for encoding issues
5. **FastAPI Endpoint**: POST /api/csv/upload with file upload
6. **Preview API**: GET /api/csv/preview/{session_id} for first 100 rows
7. **Schema API**: GET /api/csv/schema/{session_id} for column types

### Non-Goals (Explicitly OUT of Scope)

- No Excel/JSON/Parquet support (future SPEC)
- No database connectors (future SPEC)
- No workflow canvas (future SPEC)
- No authentication system (public API)
- No persistent storage (in-memory sessions only)
- No frontend UI components

## Assumptions

### Technical Assumptions

| Assumption | Confidence | Evidence Basis | Risk if Wrong |
|------------|------------|----------------|---------------|
| FastAPI is already installed in the project | High | Project structure shows FastAPI dependencies | Low - can add dependency |
| Python 3.10+ is available | High | Standard Python version for modern projects | Medium - may require version check |
| chardet library can detect Korean encodings | Medium | Library documentation supports CP949/EUC-KR | High - may need fallback implementation |
| Streaming files with 100MB+ files is feasible with 8GB RAM | Medium | Standard memory constraints | Medium - may need disk-based fallback |

### Business Assumptions

| Assumption | Confidence | Evidence Basis | Risk if Wrong |
|------------|------------|----------------|---------------|
| Users primarily work with UTF-8 and Korean encodings | High | Korean market context | Low - other encodings can be added later |
| Preview API returning 100 rows is sufficient for validation | Medium | Industry standard for data previews | Medium - may need configurable limit |
| In-memory sessions are adequate for MVP | High | Single-user workflow assumption | Medium - may need persistence in future |

### Team Assumptions

| Assumption | Confidence | Evidence Basis | Risk if Wrong |
|------------|------------|----------------|---------------|
| Developer has TDD experience | High | TRUST 5 framework requirement | Low - training available |
| Developer has FastAPI experience | Medium | Project uses FastAPI | Medium - may require learning time |
| Developer has Korean encoding experience | Low | Specialized knowledge | High - may require research |

### Integration Assumptions

| Assumption | Confidence | Evidence Basis | Risk if Wrong |
|------------|------------|----------------|---------------|
| data-processor.py has existing CSV functionality | High | User provided context | Low - can verify during implementation |
| No conflicts with existing data processing code | Medium | Limited context on existing code | Medium - may need refactoring |
| Current project structure supports API additions | High | Standard FastAPI project structure | Low - minor adjustments possible |

## Environment

### Technical Environment

- **Language**: Python 3.10+
- **Framework**: FastAPI
- **Testing**: pytest with 85%+ coverage requirement
- **Type Checking**: mypy (optional but recommended)

### Development Methodology

- **Approach**: TDD (Test-Driven Development)
- **Coverage Target**: 85%+
- **Quality Gates**: TRUST 5 framework (Tested, Readable, Unified, Secured, Trackable)

### Dependencies

- FastAPI (existing)
- chardet (encoding detection)
- pandas (data processing, existing)
- aiofiles (async file operations)

## Requirements (EARS Format)

### Ubiquitous Requirements

**UR-CSV-001: Encoding Detection**
The system **shall** detect character encoding from CSV file metadata and content.
- UTF-8, UTF-8-sig, CP949, EUC-KR support required
- Fallback to UTF-8 if detection fails
- Encoding detection timeout: 5 seconds maximum

**UR-CSV-002: Type Inference**
The system **shall** infer column data types from sample data.
- Integer, Float, String, Boolean, Date, DateTime types
- Minimum 1000 rows sampled for inference
- Null values handled correctly (no null-to-string conversion)

**UR-CSV-003: Error Handling**
The system **shall** provide clear error messages for encoding and parsing failures.
- Error messages include file name, line number, and specific issue
- Error messages support Korean text for Korean encoding issues
- HTTP 400 for client errors, 500 for server errors

**UR-CSV-004: Session Management**
The system **shall** maintain in-memory sessions for uploaded files.
- Session ID: UUID v4
- Session timeout: 30 minutes of inactivity
- Maximum concurrent sessions: 10

**UR-CSV-005: Input Validation**
The system **shall** validate all file uploads before processing.
- File size limit: 500MB maximum
- File type validation: CSV extension or MIME type
- Filename validation: Sanitize paths, prevent directory traversal

### Event-Driven Requirements

**ER-CSV-001: File Upload Processing**
**When** a file is uploaded via POST /api/csv/upload,
Then the system **shall**:
1. Validate file size and type
2. Detect character encoding
3. Infer column types
4. Store data in in-memory session
5. Return session ID within 2 seconds for files < 10MB

**ER-CSV-002: Preview Request Processing**
**When** a preview is requested via GET /api/csv/preview/{session_id},
Then the system **shall**:
1. Validate session exists and is not expired
2. Return first 100 rows as JSON
3. Include column names in response
4. Complete request within 500ms

**ER-CSV-003: Schema Request Processing**
**When** a schema is requested via GET /api/csv/schema/{session_id},
Then the system **shall**:
1. Validate session exists and is not expired
2. Return column names and inferred types
3. Include null count per column
4. Complete request within 200ms

**ER-CSV-004: Large File Streaming**
**When** a file larger than 100MB is uploaded,
Then the system **shall**:
1. Process file in chunks of 10MB
2. Update session status during processing
3. Return 202 Accepted immediately with session ID
4. Complete processing within 30 seconds

### State-Driven Requirements

**SR-CSV-001: Session Expiration**
**While** a session has been inactive for 30 minutes,
the system **shall** automatically clean up the session and release memory.

**SR-CSV-002: Maximum Concurrent Sessions**
**While** the system has 10 active sessions,
the system **shall** reject new uploads with HTTP 503 Service Unavailable
until a session expires or is explicitly cleaned up.

**SR-CSV-003: Encoding Fallback**
**When** encoding detection fails with confidence < 0.7,
Then the system **shall**:
1. Attempt UTF-8 decoding first
2. Attempt CP949 decoding second
3. Attempt EUC-KR decoding third
4. Return error if all attempts fail

### Unwanted Requirements

**UR-CSV-006: Security Constraints**
The system **shall not**:
- Accept executable files or scripts
- Write uploaded files to disk beyond temporary processing
- Expose server file system through error messages
- Allow session ID enumeration (use UUID v4)

**UR-CSV-007: Performance Constraints**
The system **shall not**:
- Load entire file into memory for files > 100MB
- Block the event loop during file processing
- Return preview data beyond 100 rows

### Optional Requirements

**OR-CSV-001: Encoding Confidence Reporting**
**Where** encoding detection is performed,
the system **should** include confidence score in the schema response.

**OR-CSV-002: Customizable Preview Limit**
**Where** preview API is called,
the system **should** support optional query parameter ?rows=N
to limit returned rows (default: 100, max: 1000).

## Exclusions (What NOT to Build)

### Explicit Out-of-Scope Features

1. **Excel Support**: No .xlsx or .xls file processing (future SPEC)
2. **JSON/Parquet Support**: No other data formats (future SPEC)
3. **Database Connectors**: No PostgreSQL, MySQL, or DuckDB connections (future SPEC)
4. **Authentication**: No user accounts, API keys, or OAuth (public API)
5. **Persistent Storage**: No database or file-based session storage (in-memory only)
6. **Frontend UI**: No React/Vue components or HTML pages (backend API only)
7. **Workflow Canvas**: No visual drag-and-drop interface (future SPEC)
8. **Data Transformation**: No column mapping, filtering, or aggregation (future SPEC)
9. **Export Functionality**: No CSV export or download APIs (future SPEC)
10. **Real-time Updates**: No WebSocket support for processing progress (future SPEC)

## Specifications

### API Endpoints

#### POST /api/csv/upload

**Description**: Upload a CSV file for processing

**Request**:
- Method: POST
- Content-Type: multipart/form-data
- Body: file (CSV file)

**Response** (200 OK):
```json
{
  "session_id": "uuid-v4",
  "filename": "data.csv",
  "encoding": "UTF-8",
  "encoding_confidence": 0.95,
  "row_count": 1000,
  "column_count": 5,
  "status": "ready"
}
```

**Response** (202 Accepted):
```json
{
  "session_id": "uuid-v4",
  "filename": "large_file.csv",
  "status": "processing",
  "estimated_completion": "2026-04-24T10:05:00Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid file type or size
- 413 Payload Too Large: File exceeds 500MB
- 503 Service Unavailable: Maximum concurrent sessions reached

#### GET /api/csv/preview/{session_id}

**Description**: Get first 100 rows of uploaded CSV

**Request**:
- Method: GET
- Parameter: session_id (path parameter)
- Query: ?rows=N (optional, default 100, max 1000)

**Response** (200 OK):
```json
{
  "session_id": "uuid-v4",
  "rows": [
    {"col1": "value1", "col2": "value2"},
    {"col1": "value3", "col2": "value4"}
  ],
  "row_count": 100
}
```

**Error Responses**:
- 404 Not Found: Session not found or expired
- 400 Bad Request: Invalid session ID format

#### GET /api/csv/schema/{session_id}

**Description**: Get schema information (column names and types)

**Request**:
- Method: GET
- Parameter: session_id (path parameter)

**Response** (200 OK):
```json
{
  "session_id": "uuid-v4",
  "columns": [
    {
      "name": "id",
      "type": "Integer",
      "nullable": false,
      "null_count": 0
    },
    {
      "name": "name",
      "type": "String",
      "nullable": true,
      "null_count": 5
    }
  ],
  "encoding": "UTF-8",
  "encoding_confidence": 0.95,
  "row_count": 1000,
  "column_count": 5
}
```

**Error Responses**:
- 404 Not Found: Session not found or expired

### Data Types

**Supported Types**:
- Integer: Whole numbers (int64)
- Float: Decimal numbers (float64)
- String: Text values (str)
- Boolean: true/false values (bool)
- Date: Date only (YYYY-MM-DD)
- DateTime: Date and time (YYYY-MM-DD HH:MM:SS)

**Type Inference Rules**:
1. Try Integer: All values parse as int, not null
2. Try Float: All values parse as float, not null
3. Try Boolean: All values are "true"/"false" (case-insensitive)
4. Try Date: All values match ISO 8601 date format
5. Try DateTime: All values match ISO 8601 datetime format
6. Default to String: If all above fail

### Encoding Detection

**Supported Encodings**:
1. UTF-8 (with and without BOM)
2. CP949 (Korean)
3. EUC-KR (Korean)

**Detection Algorithm**:
1. Use chardet library for detection
2. If confidence >= 0.7: Use detected encoding
3. If confidence < 0.7: Try fallback sequence (SR-CSV-003)
4. Timeout: 5 seconds maximum
5. Fallback: UTF-8 if all attempts fail

### Session Management

**Session Lifecycle**:
1. Created on file upload (UUID v4)
2. Active state: Processing or Ready
3. Expires after 30 minutes of inactivity
4. Automatic cleanup of expired sessions

**Session Storage**:
- In-memory dictionary: {session_id: session_data}
- Maximum 10 concurrent sessions
- Session data includes:
  - File data (streamed for large files)
  - Encoding information
  - Schema information
  - Preview data (first 100 rows)
  - Creation timestamp
  - Last access timestamp

### Security Considerations

**Input Validation**:
- File size limit: 500MB
- File type: .csv extension or text/csv MIME type
- Filename sanitization: Remove path separators, restrict to alphanumeric
- Session ID: UUID v4 format validation

**Error Handling**:
- No file system paths in error messages
- No server stack traces in client responses
- Generic error messages for security-sensitive failures

**Resource Limits**:
- Maximum concurrent sessions: 10
- Maximum file size: 500MB
- Session timeout: 30 minutes
- Processing timeout: 30 seconds for large files

## Success Criteria

- All UR-XXX, ER-XXX, SR-XXX requirements satisfied
- Test coverage: 85%+ across all modules
- Upload API handles 100MB+ files without OOM errors
- Korean (CP949/EUC-KR) files decode correctly
- Preview API returns within 500ms for standard files
- All acceptance criteria (AC-CSV-XXX) pass
- TRUST 5 quality gates passed
- Zero security vulnerabilities (OWASP compliance)

## Traceability Matrix

| Requirement | Acceptance Criteria | Test Case |
|-------------|---------------------|-----------|
| UR-CSV-001 | AC-CSV-001, AC-CSV-002 | test_utf8_detection, test_cp949_detection |
| UR-CSV-002 | AC-CSV-003 | test_type_inference |
| UR-CSV-003 | AC-CSV-004 | test_error_handling |
| ER-CSV-001 | AC-CSV-001, AC-CSV-002, AC-CSV-005 | test_upload_api |
| ER-CSV-002 | AC-CSV-006 | test_preview_api |
| ER-CSV-003 | AC-CSV-007 | test_schema_api |
| ER-CSV-004 | AC-CSV-005 | test_large_file_streaming |
| SR-CSV-001 | AC-CSV-008 | test_session_expiration |
| SR-CSV-002 | AC-CSV-009 | test_max_concurrent_sessions |
| UR-CSV-006 | AC-CSV-010 | test_security_file_validation |
| UR-CSV-007 | AC-CSV-011 | test_performance_memory_limits |
