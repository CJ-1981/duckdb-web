# Acceptance Criteria - SPEC-CSV-001

## Overview

This document defines detailed acceptance criteria for the Enhanced CSV Connector with Encoding Detection, using Given-When-Then format for testable scenarios.

## AC-CSV-001: UTF-8 File Upload

**Requirement**: UR-CSV-001, ER-CSV-001

### Scenario: UTF-8 encoded CSV file upload

**Given**: A UTF-8 encoded CSV file named "data.csv" with valid data
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall detect encoding as UTF-8
**And**: Return session_id within 2 seconds
**And**: Response includes encoding_confidence >= 0.9
**And**: Response includes correct row_count and column_count

**Verification**:
- Automated test: `tests/test_api.py::test_upload_utf8_file`
- Test file: `tests/fixtures/utf8_data.csv`
- Assertion: encoding == "UTF-8"
- Assertion: encoding_confidence >= 0.9
- Assertion: response_time < 2.0 seconds

## AC-CSV-002: CP949 File Upload

**Requirement**: UR-CSV-001, ER-CSV-001

### Scenario: CP949 encoded CSV file with Korean characters

**Given**: A CP949 encoded CSV file named "korean_data.csv" with Korean text
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall detect encoding as CP949
**And**: Decode all Korean characters correctly
**And**: Return session_id with valid schema
**And**: No encoding errors in response

**Verification**:
- Automated test: `tests/test_api.py::test_upload_cp949_file`
- Test file: `tests/fixtures/cp949_korean.csv`
- Assertion: encoding == "CP949"
- Assertion: Korean characters in preview are correctly decoded
- Assertion: No UnicodeDecodeError exceptions

## AC-CSV-003: Type Inference

**Requirement**: UR-CSV-002

### Scenario: Automatic type inference for CSV columns

**Given**: A CSV file with columns of different data types
- Column 1: Integers (1, 2, 3)
- Column 2: Floats (1.5, 2.7, 3.14)
- Column 3: Strings ("apple", "banana", "cherry")
- Column 4: Booleans (true, false, true)
- Column 5: Dates (2026-01-01, 2026-01-02, 2026-01-03)

**When**: The file is uploaded and processing is complete
**Then**: The system shall infer correct types for each column
**And**: Schema endpoint returns accurate type information
**And**: Null values are handled without type conversion

**Verification**:
- Automated test: `tests/test_type_inference.py::test_type_inference_mixed_types`
- Test file: `tests/fixtures/mixed_types.csv`
- Assertion: Column 1 type == "Integer"
- Assertion: Column 2 type == "Float"
- Assertion: Column 3 type == "String"
- Assertion: Column 4 type == "Boolean"
- Assertion: Column 5 type == "Date"

## AC-CSV-004: Error Handling

**Requirement**: UR-CSV-003

### Scenario: Clear error messages for encoding failures

**Given**: A CSV file with corrupted or invalid encoding
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall return HTTP 400 Bad Request
**And**: Error message includes file name
**And**: Error message describes the encoding issue
**And**: Error message is actionable

**Verification**:
- Automated test: `tests/test_api.py::test_upload_corrupted_encoding`
- Test file: `tests/fixtures/corrupted_encoding.csv`
- Assertion: response.status_code == 400
- Assertion: "encoding" in error message (case-insensitive)
- Assertion: file name in error message

### Scenario: Invalid session ID error

**Given**: No existing session with ID "invalid-uuid"
**When**: GET /api/csv/preview/invalid-uuid is called
**Then**: The system shall return HTTP 404 Not Found
**And**: Error message indicates session not found
**And**: No stack traces exposed

**Verification**:
- Automated test: `tests/test_api.py::test_preview_invalid_session`
- Assertion: response.status_code == 404
- Assertion: "session" in error message (case-insensitive)

## AC-CSV-005: Large File Streaming

**Requirement**: ER-CSV-004, UR-CSV-007

### Scenario: Large file upload (>100MB) with streaming

**Given**: A CSV file larger than 100MB
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall return HTTP 202 Accepted immediately
**And**: Response includes session_id
**And**: Response includes estimated_completion time
**And**: File is processed in chunks without loading entire file into memory
**And**: Processing completes within 30 seconds

**Verification**:
- Automated test: `tests/test_api.py::test_upload_large_file_streaming`
- Test file: `tests/fixtures/large_file_100mb.csv` (generated)
- Assertion: response.status_code == 202
- Assertion: "session_id" in response
- Assertion: "estimated_completion" in response
- Assertion: memory_usage < 200MB (monitored during test)
- Assertion: processing_time < 30 seconds

### Scenario: Memory limits not exceeded

**Given**: Multiple concurrent file uploads
**When**: Total memory usage is monitored
**Then**: The system shall not exceed 2GB total memory
**And**: No MemoryError exceptions occur

**Verification**:
- Automated test: `tests/test_integration.py::test_concurrent_uploads_memory_limit`
- Assertion: peak_memory_usage < 2GB
- Assertion: no MemoryError exceptions

## AC-CSV-006: Preview API

**Requirement**: ER-CSV-002

### Scenario: Preview API returns first 100 rows

**Given**: A session with uploaded CSV file containing 1000 rows
**When**: GET /api/csv/preview/{session_id} is called
**Then**: The system shall return HTTP 200 OK
**And**: Response includes first 100 rows
**And**: Response includes column names
**And**: Request completes within 500ms

**Verification**:
- Automated test: `tests/test_api.py::test_preview_first_100_rows`
- Test file: `tests/fixtures/1000_rows.csv`
- Assertion: response.status_code == 200
- Assertion: len(response.json()["rows"]) == 100
- Assertion: "column_names" in response or rows have keys
- Assertion: response_time < 0.5 seconds

### Scenario: Preview API respects custom row limit

**Given**: A session with uploaded CSV file
**When**: GET /api/csv/preview/{session_id}?rows=50 is called
**Then**: The system shall return first 50 rows
**And**: Response indicates row_count == 50

**Verification**:
- Automated test: `tests/test_api.py::test_preview_custom_row_limit`
- Assertion: len(response.json()["rows"]) == 50

## AC-CSV-007: Schema API

**Requirement**: ER-CSV-003

### Scenario: Schema API returns column information

**Given**: A session with uploaded CSV file
**When**: GET /api/csv/schema/{session_id} is called
**Then**: The system shall return HTTP 200 OK
**And**: Response includes column names
**And**: Response includes inferred types
**And**: Response includes null count per column
**And**: Response includes encoding information
**And**: Request completes within 200ms

**Verification**:
- Automated test: `tests/test_api.py::test_schema_returns_column_info`
- Test file: `tests/fixtures/mixed_types.csv`
- Assertion: response.status_code == 200
- Assertion: "columns" in response
- Assertion: all columns have "name", "type", "nullable", "null_count"
- Assertion: "encoding" in response
- Assertion: "encoding_confidence" in response
- Assertion: response_time < 0.2 seconds

## AC-CSV-008: Session Expiration

**Requirement**: SR-CSV-001

### Scenario: Session expires after 30 minutes of inactivity

**Given**: A session created at time T
**When**: Current time is T + 31 minutes
**And**: No API calls have been made to this session
**And**: GET /api/csv/preview/{session_id} is called
**Then**: The system shall return HTTP 404 Not Found
**And**: Error message indicates session expired
**And**: Session is removed from memory

**Verification**:
- Automated test: `tests/test_session_manager.py::test_session_expiration_30_minutes`
- Mock time to advance 31 minutes
- Assertion: session not found in storage
- Assertion: HTTP 404 response

### Scenario: Session last access timestamp updates

**Given**: A session created at time T
**When**: GET /api/csv/preview/{session_id} is called at T + 20 minutes
**And**: Current time advances to T + 51 minutes
**And**: GET /api/csv/preview/{session_id} is called again
**Then**: The system shall return HTTP 200 OK (session still valid)
**And**: Session expiration time is T + 20 minutes + 30 minutes = T + 50 minutes

**Verification**:
- Automated test: `tests/test_session_manager.py::test_last_access_updates_expiration`
- Mock time to advance in steps
- Assertion: first call succeeds (HTTP 200)
- Assertion: second call at T+51 minutes fails (HTTP 404)

## AC-CSV-009: Maximum Concurrent Sessions

**Requirement**: SR-CSV-002

### Scenario: System rejects new sessions when limit reached

**Given**: 10 active sessions exist
**When**: An 11th file upload is attempted via POST /api/csv/upload
**Then**: The system shall return HTTP 503 Service Unavailable
**And**: Error message indicates maximum sessions reached
**And**: No new session is created

**Verification**:
- Automated test: `tests/test_api.py::test_max_concurrent_sessions`
- Create 10 sessions sequentially
- Attempt 11th upload
- Assertion: response.status_code == 503
- Assertion: "maximum" in error message (case-insensitive)
- Assertion: session count remains 10

### Scenario: New session allowed after expiration

**Given**: 10 active sessions exist
**When**: One session expires (30 minutes inactive)
**And**: An 11th file upload is attempted
**Then**: The system shall return HTTP 202 Accepted
**And**: New session is created successfully

**Verification**:
- Automated test: `tests/test_api.py::test_new_session_after_expiration`
- Create 10 sessions, expire one
- Attempt 11th upload
- Assertion: response.status_code == 202
- Assertion: new session_id is valid

## AC-CSV-010: Security - File Validation

**Requirement**: UR-CSV-005, UR-CSV-006

### Scenario: Reject executable files

**Given**: A file named "malicious.exe"
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall return HTTP 400 Bad Request
**And**: Error message indicates invalid file type
**And**: File is not processed

**Verification**:
- Automated test: `tests/test_api.py::test_upload_executable_file_rejected`
- Test file: `tests/fixtures/malicious.exe`
- Assertion: response.status_code == 400
- Assertion: "file type" in error message (case-insensitive)

### Scenario: Reject oversized files

**Given**: A file larger than 500MB
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall return HTTP 413 Payload Too Large
**And**: Error message indicates size limit
**And**: File is not processed

**Verification**:
- Automated test: `tests/test_api.py::test_upload_oversized_file_rejected`
- Test file: Generate 501MB file
- Assertion: response.status_code == 413
- Assertion: "size" in error message (case-insensitive)

### Scenario: Sanitize filename paths

**Given**: A file named "../../etc/passwd.csv"
**When**: The file is uploaded via POST /api/csv/upload
**Then**: The system shall sanitize the filename
**And**: Remove path traversal characters
**And**: Return safe filename in response

**Verification**:
- Automated test: `tests/test_api.py::test_filename_sanitization`
- Upload file with path traversal attempt
- Assertion: "filename" in response does not contain ".."
- Assertion: "filename" contains only safe characters

### Scenario: No stack traces in error responses

**Given**: Any error condition occurs
**When**: Error response is returned
**Then**: The system shall not include server stack traces
**And**: Error messages are user-friendly
**And**: No file system paths are exposed

**Verification**:
- Automated test: `tests/test_api.py::test_error_messages_no_stack_traces`
- Trigger various error conditions
- Assertion: "Traceback" not in response
- Assertion: "/" or "\\" not in error messages (no paths)

## AC-CSV-011: Performance - Memory Limits

**Requirement**: UR-CSV-007

### Scenario: Large file does not cause OOM

**Given**: A 100MB CSV file
**When**: The file is uploaded and processed
**Then**: The system shall not raise MemoryError
**And**: Peak memory usage < 2GB
**And**: Memory is released after processing

**Verification**:
- Automated test: `tests/test_integration.py::test_large_file_memory_usage`
- Test file: `tests/fixtures/large_file_100mb.csv`
- Monitor memory usage during test
- Assertion: no MemoryError exception
- Assertion: peak_memory < 2GB
- Assertion: memory released after completion

### Scenario: Streaming prevents full file load

**Given**: A 150MB CSV file
**When**: The file is uploaded
**Then**: The system shall read file in chunks
**And**: Never load entire file into memory
**And**: Memory usage remains stable during processing

**Verification**:
- Automated test: `tests/test_integration.py::test_streaming_memory_stability`
- Test file: `tests/fixtures/large_file_150mb.csv`
- Monitor memory usage at intervals
- Assertion: memory usage does not spike beyond baseline + chunk size
- Assertion: memory usage pattern shows periodic peaks (chunk processing)

## AC-CSV-012: Korean Encoding Support

**Requirement**: UR-CSV-001

### Scenario: CP949 Korean text decodes correctly

**Given**: A CP949 encoded CSV file with Korean characters
- Content: "이름,나이\n홍길동,30\n김철수,25"
**When**: The file is uploaded
**And**: Preview API is called
**Then**: All Korean characters display correctly
**And**: No mojibake (garbled text) occurs
**And**: String comparisons work correctly

**Verification**:
- Automated test: `tests/test_api.py::test_cp949_korean_decoding`
- Test file: `tests/fixtures/cp949_korean.csv`
- Assertion: preview contains "홍길동"
- Assertion: preview contains "김철수"
- Assertion: no "?" or replacement characters

### Scenario: EUC-KR Korean text decodes correctly

**Given**: An EUC-KR encoded CSV file with Korean characters
**When**: The file is uploaded
**And**: Preview API is called
**Then**: All Korean characters display correctly
**And**: No encoding errors occur

**Verification**:
- Automated test: `tests/test_api.py::test_euckr_korean_decoding`
- Test file: `tests/fixtures/euckr_korean.csv`
- Assertion: Korean characters in preview are correct
- Assertion: no UnicodeDecodeError exceptions

## AC-CSV-013: Type Inference Edge Cases

**Requirement**: UR-CSV-002

### Scenario: Null value handling

**Given**: A CSV file with null values (empty strings, "NULL", "null")
**When**: The file is uploaded
**Then**: Null values are not converted to strings
**And**: Null count is accurate in schema
**And**: Null values do not affect type inference

**Verification**:
- Automated test: `tests/test_type_inference.py::test_null_value_handling`
- Test file: `tests/fixtures/null_values.csv`
- Assertion: null_count > 0 in schema
- Assertion: empty strings are treated as null
- Assertion: type inference ignores null rows

### Scenario: Mixed-type columns default to String

**Given**: A CSV column with mixed types (integers and strings)
- Content: "value\n1\ntwo\n3"
**When**: Type inference is performed
**Then**: Column type is inferred as String
**And**: No type conversion errors occur

**Verification**:
- Automated test: `tests/test_type_inference.py::test_mixed_type_column_defaults_to_string`
- Test file: `tests/fixtures/mixed_type_column.csv`
- Assertion: column type == "String"

### Scenario: Boolean detection

**Given**: A CSV column with boolean values
- Content: "active\ntrue\nfalse\nTRUE\nFALSE"
**When**: Type inference is performed
**Then**: Column type is inferred as Boolean
**And**: Case-insensitive detection works

**Verification**:
- Automated test: `tests/test_type_inference.py::test_boolean_detection`
- Test file: `tests/fixtures/boolean_column.csv`
- Assertion: column type == "Boolean"
- Assertion: all variants detected correctly

## AC-CSV-014: Encoding Fallback Sequence

**Requirement**: SR-CSV-003

### Scenario: Low confidence triggers fallback

**Given**: A CSV file where chardet returns confidence < 0.7
**When**: Encoding detection is performed
**Then**: System attempts UTF-8 decoding first
**And**: Attempts CP949 decoding second
**And**: Attempts EUC-KR decoding third
**And**: Returns first successful decoding

**Verification**:
- Automated test: `tests/test_encoding_detector.py::test_low_confidence_fallback_sequence`
- Mock chardet to return confidence 0.5
- Mock decode attempts to succeed on CP949
- Assertion: UTF-8 attempted first
- Assertion: CP949 attempted second
- Assertion: final encoding == "CP949"

### Scenario: All fallback attempts fail

**Given**: A CSV file where all encoding attempts fail
**When**: Encoding detection is performed
**Then**: System returns clear error message
**And**: Does not crash or hang
**And**: Returns error to user

**Verification**:
- Automated test: `tests/test_encoding_detector.py::test_all_fallback_attempts_fail`
- Mock all decode attempts to raise UnicodeDecodeError
- Assertion: error message indicates encoding failure
- Assertion: no exception propagates to API

## Test Coverage Requirements

### Overall Coverage Target: 85%+

**Coverage by Module**:
- `encoding_detector.py`: 90%+ (critical path)
- `type_inference.py`: 90%+ (critical path)
- `session_manager.py`: 90%+ (critical path)
- `api.py`: 85%+ (integration layer)

### Coverage Types:
- **Line Coverage**: 85%+ minimum
- **Branch Coverage**: 80%+ minimum
- **Function Coverage**: 95%+ minimum

### Coverage Exclusions:
- Generated code (OpenAPI docs)
- Test fixtures and test data
- Mock objects and test utilities

## Quality Gates

### Pre-Commit Checks:
- [ ] pytest passes (100% tests passing)
- [ ] Coverage report shows 85%+
- [ ] ruff linting passes (zero warnings)
- [ ] black formatting applied
- [ ] isort imports organized

### Pre-Merge Checks:
- [ ] All acceptance criteria (AC-CSV-XXX) passing
- [ ] Integration tests passing
- [ ] Security audit passing (OWASP)
- [ ] Performance benchmarks passing
- [ ] Documentation complete

### Definition of Done:
- All AC-CSV-XXX scenarios automated
- Test coverage: 85%+ overall
- TRUST 5 pillars satisfied
- Zero known security vulnerabilities
- Performance targets met
- Code reviewed and approved
- Documentation complete (README, OpenAPI)

## Test Data Requirements

### Test Fixtures Directory: `tests/fixtures/`

**Required Test Files**:
1. `utf8_data.csv` - Standard UTF-8 encoded file
2. `cp949_korean.csv` - CP949 encoded with Korean text
3. `euckr_korean.csv` - EUC-KR encoded with Korean text
4. `mixed_types.csv` - Columns of different data types
5. `null_values.csv` - File with null value examples
6. `boolean_column.csv` - Boolean values in various cases
7. `1000_rows.csv` - 1000 rows for preview testing
8. `large_file_100mb.csv` - Generated for streaming tests
9. `corrupted_encoding.csv` - Invalid encoding for error tests
10. `malicious.exe` - Executable file for security tests

**Fixture Generation**:
- Large files generated programmatically
- Encoded files created with Python `codecs` module
- Fixture creation script: `tests/generate_fixtures.py`

## Verification Summary

### Automated Tests: 30+ scenarios
- Unit tests: 15+
- Integration tests: 10+
- End-to-end tests: 5+

### Manual Testing: 5 scenarios
- Large file monitoring (100MB+)
- Concurrent session stress test
- Memory profiling during streaming
- Performance benchmarking
- Korean encoding visual verification

### Success Metrics:
- [ ] All 14 AC-CSV-XXX criteria satisfied
- [ ] 85%+ test coverage achieved
- [ ] All TRUST 5 quality gates passed
- [ ] Zero security vulnerabilities
- [ ] Performance targets met
- [ ] Documentation complete
