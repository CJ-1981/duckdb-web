# DuckDB Web Application - Implementation Plan

**Date:** 2026-04-18  
**Project:** DuckDB-based Data Processing Web Application  
**Status:** Implementation Roadmap

---

## Executive Summary

This document outlines the strategic implementation plan for completing missing data processing features in the DuckDB web application. The plan prioritizes quick wins while building toward a comprehensive data processing platform.

**Current State:**
- ✅ 55/55 backend unit tests passing
- ✅ Excel file support implemented
- ❌ Database loading not implemented (PostgreSQL/MySQL connectors exist but not integrated)
- ❌ API loading not implemented
- ❌ JSON/JSONL/Parquet connectors missing
- ❌ Advanced transformation features incomplete

---

## Phase 1: Test Suite Health Check

### 1.1 Current Status
- **Backend Unit Tests:** 55/55 passing ✓
- **Unknown:** API tests, E2E tests, integration tests

### 1.2 Actions Required
```bash
# Run full test suite
pytest tests/ -v --tb=short

# Check test coverage by category
pytest tests/api/ -v
pytest tests/e2e/ -v
pytest tests/integration/ -v
```

### 1.3 Expected Outcomes
- Identify any failing tests
- Categorize failures by type (API, E2E, integration)
- Establish baseline for regression testing

### 1.4 Success Criteria
- All test categories run without environment errors
- Failing tests documented with root cause
- Test coverage report generated

---

## Phase 2: Database Loading Implementation (Quick Win)

### 2.1 Current State
- `load_database()` raises `NotImplementedError`
- PostgreSQL connector exists: `src/core/connectors/postgresql.py`
- MySQL connector exists: `src/core/connectors/mysql.py`
- Database connector base: `src/core/connectors/database.py`

### 2.2 Implementation Plan

#### Step 1: Integrate PostgreSQL Connector
```python
# In src/core/processor/_processor.py
def load_database(
    self,
    connection_string: str,
    query: str,
    table_name: Optional[str] = None
) -> pd.DataFrame:
    """Load data from database query"""
    from ..connectors.postgresql import PostgreSQLConnector
    from ..connectors.mysql import MySQLConnector
    
    # Detect database type from connection string
    if connection_string.startswith('postgresql://'):
        connector = PostgreSQLConnector()
    elif connection_string.startswith('mysql://'):
        connector = MySQLConnector()
    else:
        raise ValueError(f"Unsupported database: {connection_string}")
    
    # Use connector to load data
    target_table = table_name or 'data'
    self._table_name = target_table
    
    # Execute query and load into DuckDB
    rows = list(connector.read(connection_string, query))
    self._create_table_from_rows(rows, target_table)
    self._insert_rows(rows, target_table)
    
    return self.preview()
```

#### Step 2: Create Database Connector Tests
```python
# tests/integration/test_database_loading.py
def test_postgresql_loading():
    """Test PostgreSQL data loading"""
    processor = Processor()
    result = processor.load_database(
        connection_string="postgresql://user:pass@localhost:5432/testdb",
        query="SELECT * FROM users LIMIT 100"
    )
    assert len(result) > 0

def test_mysql_loading():
    """Test MySQL data loading"""
    processor = Processor()
    result = processor.load_database(
        connection_string="mysql://user:pass@localhost:3306/testdb",
        query="SELECT * FROM products LIMIT 100"
    )
    assert len(result) > 0
```

### 2.3 Success Criteria
- PostgreSQL and MySQL loading functional
- Unit tests pass
- Integration tests with actual databases (using docker-compose test setup)
- Error handling for connection failures
- Type inference from database schema

### 2.4 Estimated Effort: 2-3 hours

---

## Phase 3: JSON/JSONL Connector Implementation (Quick Win)

### 3.1 Requirements
- Support JSON file loading
- Support JSONL (JSON Lines) format
- Handle nested structures appropriately
- Infer types from JSON schema

### 3.2 Implementation Plan

#### Step 1: Create JSON Connector
```python
# src/core/connectors/json.py
class JSONConnector(BaseConnector):
    """JSON/JSONL file connector"""
    
    def read_json(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Read JSON file"""
        with open(file_path) as f:
            data = json.load(f)
            if isinstance(data, list):
                yield from data
            elif isinstance(data, dict):
                # Handle nested structure
                yield data
    
    def read_jsonl(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """Read JSON Lines file"""
        with open(file_path) as f:
            for line in f:
                yield json.loads(line)
```

#### Step 2: Add load_json Method
```python
# In src/core/processor/_processor.py
def load_json(
    self,
    json_path: str,
    table_name: Optional[str] = None,
    format: str = 'json'
) -> pd.DataFrame:
    """Load JSON or JSONL file"""
    from ..connectors.json import JSONConnector
    
    connector = JSONConnector()
    target_table = table_name or 'data'
    self._table_name = target_table
    
    if format == 'jsonl':
        rows = list(connector.read_jsonl(json_path))
    else:
        rows = list(connector.read_json(json_path))
    
    self._create_table_from_rows(rows, target_table)
    self._insert_rows(rows, target_table)
    
    return self.preview()
```

### 3.3 Success Criteria
- JSON file loading works
- JSONL file loading works
- Nested structure handling (flatten to columns)
- Type inference from JSON data types
- Unit tests with sample JSON files

### 3.4 Estimated Effort: 2-3 hours

---

## Phase 4: API Loading Implementation

### 4.1 Requirements
- Support REST API data loading
- Handle pagination
- Support authentication (Bearer tokens, API keys)
- Handle rate limiting
- Cache API responses

### 4.2 Implementation Plan

#### Step 1: Create API Connector
```python
# src/core/connectors/api.py
class APIConnector(BaseConnector):
    """REST API connector"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
    
    def fetch_data(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        paginate: bool = False,
        page_size: int = 100
    ) -> Iterator[Dict[str, Any]]:
        """Fetch data from REST API"""
        import requests
        
        self.session = requests.Session()
        
        if paginate:
            yield from self._fetch_paginated(url, headers, params, page_size)
        else:
            response = self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            yield from response.json()
    
    def _fetch_paginated(self, url, headers, params, page_size):
        """Handle paginated API responses"""
        page = 1
        while True:
            response = self.session.get(
                url,
                headers=headers,
                params={**(params or {}), 'page': page, 'per_page': page_size},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if not data or (isinstance(data, list) and len(data) == 0):
                break
            
            yield from data if isinstance(data, list) else [data]
            page += 1
```

#### Step 2: Add load_api Method
```python
# In src/core/processor/_processor.py
def load_api(
    self,
    api_url: str,
    table_name: Optional[str] = None,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    paginate: bool = False,
    page_size: int = 100
) -> pd.DataFrame:
    """Load data from REST API"""
    from ..connectors.api import APIConnector
    
    connector = APIConnector()
    target_table = table_name or 'api_data'
    self._table_name = target_table
    
    rows = list(connector.fetch_data(
        api_url,
        method=method,
        headers=headers,
        params=params,
        paginate=paginate,
        page_size=page_size
    ))
    
    self._create_table_from_rows(rows, target_table)
    self._insert_rows(rows, target_table)
    
    return self.preview()
```

### 4.3 Success Criteria
- GET request loading works
- Authentication header support
- Pagination handling
- Error handling for HTTP errors
- Rate limiting awareness
- Integration tests with mock APIs

### 4.4 Estimated Effort: 4-5 hours

---

## Phase 5: Parquet Connector Implementation

### 5.1 Requirements
- Support Parquet file loading
- Handle column pruning (load only needed columns)
- Preserve schema information
- Efficient for large datasets

### 5.2 Implementation Plan

#### Step 1: Create Parquet Connector
```python
# src/core/connectors/parquet.py
class ParquetConnector(BaseConnector):
    """Parquet file connector"""
    
    def read_parquet(
        self,
        file_path: str,
        columns: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Read Parquet file"""
        import pyarrow.parquet as pq
        
        table = pq.read_table(file_path, columns=columns)
        df = table.to_pandas()
        
        for _, row in df.iterrows():
            yield row.to_dict()
```

#### Step 2: Add load_parquet Method
```python
# In src/core/processor/_processor.py
def load_parquet(
    self,
    parquet_path: str,
    table_name: Optional[str] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load Parquet file"""
    from ..connectors.parquet import ParquetConnector
    
    connector = ParquetConnector()
    target_table = table_name or 'data'
    self._table_name = target_table
    
    rows = list(connector.read_parquet(parquet_path, columns=columns))
    
    self._create_table_from_rows(rows, target_table)
    self._insert_rows(rows, target_table)
    
    return self.preview()
```

### 5.3 Success Criteria
- Parquet file loading works
- Column selection support
- Large file handling
- Type preservation from Parquet schema

### 5.4 Estimated Effort: 2-3 hours

---

## Phase 6: Advanced Data Transformation Features

### 6.1 Current State
- Basic transformations: filter, aggregate, pivot exist
- Some methods partially implemented

### 6.2 Implementation Plan

#### Step 1: Complete Transform Methods
```python
# Ensure these work properly:
- transform() - Add Python lambda/function support
- join() - Support INNER, LEFT, RIGHT, OUTER, CROSS joins
- unpivot() - Reverse pivot operation
```

#### Step 2: Advanced Aggregations
```python
def aggregate_advanced(
    self,
    group_by: Union[str, List[str]],
    aggregations: Dict[str, List[tuple]]
) -> pd.DataFrame:
    """
    Advanced aggregation with multiple functions
    
    Example:
        processor.aggregate_advanced(
            'region',
            {'amount': ['SUM', 'AVG', 'COUNT']}
        )
    """
    # Build dynamic SQL with multiple aggregations
```

#### Step 3: Window Functions
```python
def window_function(
    self,
    operation: str,
    column: str,
    partition_by: Optional[List[str]] = None,
    order_by: Optional[List[str]] = None,
    frame: Optional[str] = None
) -> pd.DataFrame:
    """
    Apply SQL window functions
    
    Example:
        processor.window_function(
            'RANK',
            'sales',
            partition_by=['region'],
            order_by=['date']
        )
    """
```

### 6.3 Success Criteria
- All transformation methods functional
- Unit tests for each transformation
- Integration tests with real data

### 6.4 Estimated Effort: 4-5 hours

---

## Phase 7: Test Coverage Enhancement

### 7.1 Excel Support Integration Tests
```python
# tests/integration/test_excel_integration.py
def test_excel_to_duckdb_flow():
    """Test complete Excel to DuckDB workflow"""
    processor = Processor()
    processor.load_excel('test.xlsx')
    result = processor.sql("SELECT region, SUM(amount) FROM data GROUP BY region")
    assert len(result) > 0

def test_excel_with_transformations():
    """Test Excel loading with transformations"""
    processor = Processor()
    processor.load_excel('test.xlsx')
    processor.filter("amount > 1000")
    processor.aggregate('region', 'amount', 'SUM')
    assert 'sum_amount' in processor.preview().columns
```

### 7.2 E2E Test Scenarios
```python
# tests/e2e/test_data_pipeline_e2e.py
def test_csv_to_csv_pipeline():
    """Test CSV -> transform -> CSV export"""
    processor = Processor()
    processor.load_csv('input.csv')
    processor.filter("status = 'active'")
    processor.export_csv('output.csv')
    assert Path('output.csv').exists()

def test_database_to_parquet_pipeline():
    """Test Database -> transform -> Parquet"""
    processor = Processor()
    processor.load_database(...)
    processor.aggregate('category', 'value', 'SUM')
    processor.export_parquet('output.parquet')
```

### 7.3 Performance Benchmarks
```python
# tests/performance/test_benchmarks.py
def test_large_csv_loading():
    """Benchmark large CSV loading (>1M rows)"""
    start = time.time()
    processor = Processor()
    processor.load_csv('large.csv')
    duration = time.time() - start
    
    assert duration < 30  # Should load in under 30 seconds
```

### 7.4 Estimated Effort: 3-4 hours

---

## Phase 8: Documentation Updates

### 8.1 API Documentation
```python
# Update FastAPI OpenAPI docs
@app.post("/api/v1/load-csv")
async def load_csv(file: UploadFile):
    """
    Load CSV file into DuckDB
    
    - Supports .csv files with custom delimiters
    - Automatic type inference
    - Returns table schema and row count
    """
```

### 8.2 User Guides
```markdown
# docs/user_guide.md

## Loading Data

### CSV Files
\`\`\`python
from src.core.processor import Processor

processor = Processor()
processor.load_csv('data.csv')
\`\`\`

### Excel Files
\`\`\`python
processor.load_excel('data.xlsx', sheet_name='Sheet1')
\`\`\`

### Database Queries
\`\`\`python
processor.load_database(
    connection_string="postgresql://...",
    query="SELECT * FROM users"
)
\`\`\`
```

### 8.3 Estimated Effort: 2-3 hours

---

## Implementation Roadmap

### Sprint 1: Quick Wins (Week 1)
1. ✅ Test Suite Health Check
2. ✅ Database Loading Implementation
3. ✅ JSON/JSONL Connector

**Deliverables:**
- All test categories running
- PostgreSQL/MySQL loading functional
- JSON/JSONL support complete

### Sprint 2: Core Features (Week 2)
1. ✅ API Loading Implementation
2. ✅ Parquet Connector
3. ✅ Advanced Transformations

**Deliverables:**
- REST API data loading
- Parquet file support
- Complete transformation suite

### Sprint 3: Quality & Documentation (Week 3)
1. ✅ Integration Tests
2. ✅ E2E Test Scenarios
3. ✅ Documentation Updates

**Deliverables:**
- Comprehensive test coverage
- User guides and API docs
- Performance benchmarks

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database connection issues | High | Use docker-compose for test databases, graceful error handling |
| API rate limiting | Medium | Implement exponential backoff, caching |
| Large file memory issues | High | Streaming support, chunked processing |
| Type inference accuracy | Medium | User override options, schema validation |

---

## Success Metrics

### Quantitative
- All unit tests passing (>95% coverage)
- Integration tests passing (>80% scenarios)
- API response time < 2 seconds
- File loading: < 30 seconds for 1M rows

### Qualitative
- Clean, documented codebase
- Consistent API design
- Comprehensive error messages
- User-friendly documentation

---

## Next Steps

**Immediate (This Week):**
1. Run full test suite and document results
2. Integrate PostgreSQL/MySQL connectors
3. Implement JSON/JSONL connector

**Short-term (Next 2 Weeks):**
1. Implement API loading
2. Add Parquet support
3. Complete transformation features

**Long-term (Next Month):**
1. Comprehensive test coverage
2. Performance optimization
3. User documentation

---

## Appendix

### A. File Structure
```
src/core/connectors/
├── base.py (exists)
├── csv.py (exists)
├── csv_pandas.py (exists)
├── excel.py (✓ implemented)
├── postgresql.py (exists, not integrated)
├── mysql.py (exists, not integrated)
├── database.py (exists)
├── json.py (to be created)
├── parquet.py (to be created)
└── api.py (to be created)
```

### B. Test Status Tracking
| Category | Status | Count | Pass | Fail |
|----------|--------|-------|------|------|
| Backend Unit | ✓ | 55 | 55 | 0 |
| API | ? | ? | ? | ? |
| E2E | ? | ? | ? | ? |
| Integration | ? | ? | ? | ? |

---

**This plan is a living document and will be updated as implementation progresses.**
