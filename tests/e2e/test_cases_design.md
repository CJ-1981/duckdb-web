# E2E Test Cases Design for DuckDB Web Platform

**Version**: 1.0.0
**Last Updated**: 2026-04-04
**Test Framework**: Playwright (TypeScript) + Pytest (Python)
**Total Test Cases**: 58

## Test Data Fixtures

### Standard CSV Datasets

```csv
# sales.csv (1000 rows)
id,product,category,quantity,price,date
1,Widget A,Electronics,5,29.99,2024-01-15
2,Gadget B,Office,3,15.50,2024-01-16
3,Tool C,Hardware,2,45.00,2024-01-17
...

# customers.csv (500 rows)
customer_id,name,email,country,registration_date
1,John Smith,john@example.com,USA,2023-01-15
2,Jane Doe,jane@example.co.uk,UK,2023-02-20
3,Bob Johnson,bob@example.ca,Canada,2023-03-10
...

# orders.csv (2000 rows)
order_id,customer_id,product_id,quantity,total,status
1001,1,P001,2,59.98,completed
1002,2,P002,1,29.99,pending
1003,3,P003,5,125.00,shipped
...

# edge_cases.csv (100 rows)
id,name,value,date,description
1,Normal Row,100,2024-01-01,Standard entry
2,,,Null values in multiple columns
3,"Special ""Chars""",50.5,2024-01-03,"Quoted, comma, text"
4,Émojis ñoño Ð,25,2024-01-04,UTF-8 characters
5,  Spaces  ,  150  , 2024-01-05 , Leading/trailing spaces
...
```

## Test Categories

### 1. Smoke Tests (5 tests)
**Purpose**: Quick validation of critical paths

| ID | Test Case | Description | Expected Result | Priority |
|----|-----------|-------------|-----------------|----------|
| SMOKE-001 | Application Load | Verify app loads and main canvas is visible | Page loads < 3s, canvas visible | P0 |
| SMOKE-002 | File Upload | Upload CSV file successfully | File appears in data panel, schema detected | P0 |
| SMOKE-003 | Create Simple Workflow | Input → Output workflow | Workflow executes, data exported | P0 |
| SMOKE-004 | Filter Operation | Input → Filter → Output | Filtered results correct | P0 |
| SMOKE-005 | SQL Execution | Input → SQL Node → Output | SQL query executes successfully | P0 |

---

### 2. Input Node Tests (8 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| INP-001 | CSV Upload - Basic | Upload standard CSV | sales.csv (1000 rows) | File processed, 1000 rows detected | rowCount === 1000 |
| INP-002 | CSV Upload - Empty File | Upload empty CSV | empty.csv (0 rows) | Graceful error message | Error displayed |
| INP-003 | CSV Upload - Large File | Upload large CSV (10MB) | large_sales.csv (100K rows) | File processed within 30s | Processing time < 30s |
| INP-004 | CSV Upload - Special Characters | UTF-8, quotes, commas | edge_cases.csv | Special chars preserved | Data integrity check |
| INP-005 | CSV Upload - No Header | CSV without header row | no_header.csv | Default column names (col1, col2...) | Columns named correctly |
| INP-006 | Excel Upload - .xlsx | Upload Excel file | sales.xlsx | File processed, sheets detected | Sheet selection available |
| INP-007 | Excel Upload - Multiple Sheets | File with 3 sheets | multi_sheet.xlsx | First sheet selected by default | Correct sheet data |
| INP-008 | File Upload - Invalid Format | Upload .pdf file | document.pdf | Error: unsupported format | Error message shown |

**Test Data Mapping**:
```
INP-001: sales.csv → Standard dataset
INP-002: empty.csv → 0 bytes, valid CSV structure
INP-003: large_sales.csv → Generated with script (100K rows)
INP-004: edge_cases.csv → Hand-crafted edge cases
INP-005: no_header.csv → 1,Alice,100\n2,Bob,200
INP-006: sales.xlsx → Converted from sales.csv
INP-007: multi_sheet.xlsx → Sheets: Jan, Feb, Mar
INP-008: document.pdf → 1KB PDF file
```

---

### 3. Filter Node Tests (10 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| FLT-001 | Filter - Greater Than | quantity > 10 | sales.csv | Rows with quantity > 10 | Count matches expected |
| FLT-002 | Filter - Less Than | price < 20 | sales.csv | Rows with price < 20 | Count matches expected |
| FLT-003 | Filter - Equals | status = 'completed' | orders.csv | Only completed orders | Status column filtered |
| FLT-004 | Filter - Not Equals | country != 'USA' | customers.csv | Non-USA customers | Country column filtered |
| FLT-005 | Filter - Contains | name contains 'Smith' | customers.csv | Names with 'Smith' | String match works |
| FLT-006 | Filter - Not Contains | email not contains '@temp' | customers.csv | No temp emails | Exclude pattern works |
| FLT-007 | Filter - Starts With | product starts with 'Widget' | sales.csv | Widget products only | Prefix match |
| FLT-008 | Filter - Null Values | Filter out null names | edge_cases.csv | Exclude null name rows | Nulls handled |
| FLT-009 | Filter - Date Range | date >= '2024-01-01' | sales.csv | Dates from 2024 onwards | Date comparison works |
| FLT-010 | Filter - Empty Result | Filter with no matches | sales.csv, quantity > 99999 | Empty result set | 0 rows, no error |

**Test Data Mapping**:
```
FLT-001: sales.csv WHERE quantity > 10 → Expect ~200 rows
FLT-002: sales.csv WHERE price < 20 → Expect ~300 rows
FLT-003: orders.csv WHERE status = 'completed' → Expect ~800 rows
FLT-004: customers.csv WHERE country != 'USA' → Expect ~350 rows
FLT-005: customers.csv WHERE name LIKE '%Smith%' → Expect ~15 rows
FLT-006: customers.csv WHERE email NOT LIKE '%temp%' → Expect ~450 rows
FLT-007: sales.csv WHERE product LIKE 'Widget%' → Expect ~250 rows
FLT-008: edge_cases.csv WHERE name IS NOT NULL → Expect ~95 rows
FLT-009: sales.csv WHERE date >= '2024-01-01' → Expect ~700 rows
FLT-010: sales.csv WHERE quantity > 99999 → Expect 0 rows
```

---

### 4. Aggregate Node Tests (8 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| AGG-001 | SUM Aggregation | Sum of quantities | sales.csv | Total quantity | Sum = expected value |
| AGG-002 | COUNT Aggregation | Count by category | sales.csv | Count per category | Correct counts |
| AGG-003 | AVG Aggregation | Average price | sales.csv | Mean price | Avg within 0.01 |
| AGG-004 | MIN/MAX Aggregation | Min/max prices | sales.csv | Range values | Min/max correct |
| AGG-005 | Group By Single Column | Group by category | sales.csv | One row per category | Category count matches |
| AGG-006 | Group By Multiple Columns | Category + date | sales.csv | Unique combinations | Correct grouping |
| AGG-007 | Aggregate with Filter | Filter then aggregate | sales.csv (q>100) | Aggregates on filtered | Two-step pipeline |
| AGG-008 | Aggregate - Null Handling | Aggregate with nulls | edge_cases.csv | Nulls ignored | No null in results |

**Test Data Mapping**:
```
AGG-001: sales.csv GROUP BY (none), SUM(quantity) → Expect total
AGG-002: sales.csv GROUP BY category, COUNT(*) → Expect count per category
AGG-003: sales.csv GROUP BY (none), AVG(price) → Expect mean
AGG-004: sales.csv GROUP BY (none), MIN(price), MAX(price) → Expect range
AGG-005: sales.csv GROUP BY category → Expect 5 categories
AGG-006: sales.csv GROUP BY category, date → Expect combinations
AGG-007: sales.csv → Filter(quantity>100) → SUM(quantity) → Filtered sum
AGG-008: edge_cases.csv GROUP BY name, SUM(value) → Nulls excluded
```

---

### 5. Join/Combine Node Tests (7 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| JIN-001 | Inner Join | Match rows by ID | sales.csv + orders.csv | Matched rows only | Inner join behavior |
| JIN-002 | Left Join | All from left table | sales.csv + orders.csv | All sales, matched orders | Left join behavior |
| JIN-003 | Union Combine | Combine two datasets | sales_q1.csv + sales_q2.csv | All rows from both | Row count = sum |
| JIN-004 | Join - No Matches | Join with no overlap | customers_a.csv + customers_b.csv | Empty result | 0 rows, no error |
| JIN-005 | Join - Multiple Matches | One-to-many join | customers.csv + orders.csv | Duplicated left rows | Cartesian expansion |
| JIN-006 | Join - Null Key Values | Join on nullable column | edge_cases.csv + sales.csv | Nulls don't match | Null handling |
| JIN-007 | Self Join | Join table to itself | sales.csv (as A, B) | Valid self-join | Alias support |

**Test Data Mapping**:
```
JIN-001: sales.csv INNER JOIN orders.csv ON id → Expect matched
JIN-002: sales.csv LEFT JOIN orders.csv ON id → Expect all sales
JIN-003: sales_q1.csv UNION sales_q2.csv → Expect combined
JIN-004: customers_a.csv (ids 1-100) JOIN customers_b.csv (ids 200-300) → Empty
JIN-005: customers.csv (1 row) JOIN orders.csv (5 orders) → 5 rows
JIN-006: edge_cases.csv (null ids) JOIN sales.csv → Nulls excluded
JIN-007: sales.csv AS a JOIN sales.csv AS b ON a.category = b.category
```

---

### 6. SQL Node Tests (10 tests)

| ID | Test Case | Description | Test Data | SQL Query | Expected Result |
|----|-----------|-------------|-----------|-----------|-----------------|
| SQL-001 | Basic SELECT | Simple select all | sales.csv | `SELECT * FROM {{input}}` | All rows returned |
| SQL-002 | SELECT with WHERE | Conditional select | sales.csv | `SELECT * FROM {{input}} WHERE quantity > 50` | Filtered rows |
| SQL-003 | GROUP BY with HAVING | Grouped aggregation | sales.csv | `SELECT category, SUM(quantity) FROM {{input}} GROUP BY category HAVING SUM(quantity) > 100` | Groups meeting condition |
| SQL-004 | JOIN in SQL | Manual join query | sales.csv + orders.csv | `SELECT * FROM {{input}} s JOIN orders o ON s.id = o.id` | Joined data |
| SQL-005 | Subquery | Nested query | sales.csv | `SELECT * FROM {{input}} WHERE price > (SELECT AVG(price) FROM {{input}})` | Rows above average |
| SQL-006 | Window Function | ROW_NUMBER() OVER | sales.csv | `SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY quantity DESC) as rn FROM {{input}}` | Row numbers added |
| SQL-007 | CTE (WITH Clause) | Common table expression | sales.csv | `WITH cte AS (SELECT * FROM {{input}} WHERE quantity > 10) SELECT * FROM cte` | CTE executed |
| SQL-008 | CASE WHEN | Conditional logic | sales.csv | `SELECT *, CASE WHEN quantity > 100 THEN 'high' ELSE 'low' END as level FROM {{input}}` | New column added |
| SQL-009 | Multiple Statements | SQL with semicolons | sales.csv | `SELECT * FROM {{input}} LIMIT 10; SELECT COUNT(*) FROM {{input}}` | First statement runs |
| SQL-010 | Invalid SQL Handling | Syntax error | sales.csv | `SELCT * FORM {{input}}` | Graceful error message |

**Test Data Mapping**:
```
SQL-001: SELECT * → All 1000 rows
SQL-002: WHERE quantity > 50 → ~100 rows
SQL-003: GROUP BY + HAVING → Categories with sum > 100
SQL-004: Self-contained join → Requires two inputs
SQL-005: Correlated subquery → Above average prices
SQL-006: Window function → Row numbers per category
SQL-007: WITH clause → CTE support
SQL-008: CASE WHEN → New level column
SQL-009: Multiple statements → First runs
SQL-010: Syntax error → Error: "syntax error near SELCT"
```

---

### 7. Output Node Tests (5 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| OUT-001 | CSV Export | Export to CSV | sales.csv | Valid CSV file | File downloadable |
| OUT-002 | JSON Export | Export to JSON | sales.csv | Valid JSON array | JSON structure valid |
| OUT-003 | Excel Export | Export to .xlsx | sales.csv | Valid Excel file | File downloadable |
| OUT-004 | Large Dataset Export | Export 100K rows | large_sales.csv | File created, size reasonable | Export time < 60s |
| OUT-005 | Preview Limit | Preview respects limit | sales.csv (limit 50) | Only 50 rows shown | Preview count = 50 |

**Test Data Mapping**:
```
OUT-001: CSV export → Validate format, headers, data
OUT-002: JSON export → Validate JSON structure
OUT-003: Excel export → Validate .xlsx format
OUT-004: 100K rows → File size ~10-20MB
OUT-005: Preview limit 50 → Only 50 rows returned
```

---

### 8. Edge Cases & Negative Tests (8 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| EDGE-001 | Circular Dependency | Node references itself | Any workflow | Error on validation | Circular dependency detected |
| EDGE-002 | Orphaned Node | Node with no connections | Isolated node | Warning shown | Orphan detected |
| EDGE-003 | Missing Required Field | Node without required config | Incomplete node | Validation error | Field missing error |
| EDGE-004 | Invalid Column Reference | Filter on non-existent column | sales.csv | Error: column not found | Column not found error |
| EDGE-005 | Division by Zero | Aggregate with division | sales.csv | NULL or error handled | No crash |
| EDGE-006 | Memory Limit | Very large dataset | huge.csv (1M rows) | Graceful handling | Out of memory error |
| EDGE-007 | Concurrent Workflow Execution | Execute 5 workflows simultaneously | Multiple files | All complete successfully | No race conditions |
| EDGE-008 | Network Timeout | Slow API response | Mock slow API | Timeout handling | Timeout error shown |

**Test Data Mapping**:
```
EDGE-001: Workflow: A → B → A → Error detected
EDGE-002: Node C with no edges → Warning shown
EDGE-003: Filter node without column → Validation error
EDGE-004: Filter on 'nonexistent' column → Error shown
EDGE-005: SUM(quantity) / 0 when quantity = 0 → NULL returned
EDGE-006: 1M row CSV → Memory limit handling
EDGE-007: 5 parallel executions → All succeed
EDGE-008: Mock 2min timeout → Timeout after configured time
```

---

### 9. Performance Tests (5 tests)

| ID | Test Case | Description | Test Data | Expected Result | Pass Criteria |
|----|-----------|-------------|-----------|-----------------|---------------|
| PERF-001 | Large File Processing | Process 100K rows | large_sales.csv | Completes in reasonable time | < 30 seconds |
| PERF-002 | Complex Workflow | 10+ node pipeline | sales.csv | Workflow executes efficiently | < 45 seconds |
| PERF-003 | Multiple Filters | 5 sequential filters | sales.csv | Linear time increase | ~5x single filter time |
| PERF-004 | Memory Usage | Monitor memory during execution | large_sales.csv | Memory stays within limit | < 2GB peak |
| PERF-005 | Concurrent Users | 10 simultaneous workflows | 10 different files | All complete without degradation | < 60s each |

**Test Data Mapping**:
```
PERF-001: 100K rows → < 30s processing time
PERF-002: 10 nodes (input, filter, agg, sort, join, sql, etc.) → < 45s
PERF-003: 5 filters → Time ≈ 5 × single filter
PERF-004: Memory profiling → Peak < 2GB
PERF-005: 10 concurrent sessions → No significant slowdown
```

---

## Test Implementation Priorities

### Phase 1: Critical Path (Week 1)
- SMOKE-001 to SMOKE-005
- INP-001, INP-004
- FLT-001, FLT-003, FLT-008
- AGG-001, AGG-002
- SQL-001, SQL-002, SQL-010
- OUT-001, OUT-005

### Phase 2: Core Functionality (Week 2)
- INP-002, INP-003, INP-006
- FLT-002, FLT-005, FLT-009, FLT-010
- AGG-003, AGG-004, AGG-008
- JIN-001, JIN-002, JIN-003
- SQL-003 to SQL-009
- OUT-002, OUT-003

### Phase 3: Edge Cases & Performance (Week 3)
- INP-005, INP-007, INP-008
- FLT-004, FLT-006, FLT-007
- AGG-005, AGG-006, AGG-007
- JIN-004 to JIN-007
- EDGE-001 to EDGE-008
- PERF-001 to PERF-005
- OUT-004

---

## Test Configuration

### Playwright Settings
```typescript
// playwright.config.ts
export default defineConfig({
  timeout: 60000,           // 60s default timeout
  expect: {
    timeout: 10000          // 10s assertion timeout
  },
  workers: 4,               // Parallel execution
  retries: 2,               // Retry failed tests
  reporter: [
    ['html'],
    ['json'],
    ['junit']
  ]
});
```

### Pytest Settings
```python
# pytest.ini
[pytest]
asyncio_mode = auto
timeout = 60
markers =
    smoke: Smoke tests
    input: Input node tests
    filter: Filter node tests
    aggregate: Aggregate node tests
    join: Join/combine node tests
    sql: SQL node tests
    output: Output node tests
    edge: Edge case tests
    performance: Performance tests
```

---

## Test Data Generation Scripts

### generate_test_data.py
```python
import csv
import random
from datetime import datetime, timedelta

def generate_sales_csv(rows=1000, filename='test_data/sales.csv'):
    products = ['Widget A', 'Gadget B', 'Tool C', 'Device D', 'Instrument E']
    categories = ['Electronics', 'Office', 'Hardware', 'Software', 'Accessories']

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'product', 'category', 'quantity', 'price', 'date'])

        base_date = datetime(2024, 1, 1)
        for i in range(1, rows + 1):
            writer.writerow([
                i,
                random.choice(products),
                random.choice(categories),
                random.randint(1, 100),
                round(random.uniform(10, 500), 2),
                (base_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            ])

if __name__ == '__main__':
    generate_sales_csv(1000)
    generate_sales_csv(100000, 'test_data/large_sales.csv')
```

---

## Expected Results & Pass Criteria Summary

### Success Criteria by Category

| Category | Pass Rate Target | Critical Tests | Total Tests |
|----------|------------------|----------------|-------------|
| Smoke | 100% | 5 | 5 |
| Input | 100% | 5 | 8 |
| Filter | 90% | 5 | 10 |
| Aggregate | 90% | 5 | 8 |
| Join | 85% | 4 | 7 |
| SQL | 90% | 6 | 10 |
| Output | 100% | 3 | 5 |
| Edge Cases | 80% | 4 | 8 |
| Performance | 80% | 3 | 5 |
| **Overall** | **90%** | **40** | **58** |

### Definition of Done per Test Case
1. Test automated in Playwright or Pytest
2. Test data fixture available
3. Expected results documented
4. Pass criteria defined
5. Test added to CI/CD pipeline
6. Test passes consistently (> 95% success rate)

---

## Appendix: Test Case Template

```markdown
### [TEST-ID]: [Test Case Name]

**Priority**: P0/P1/P2
**Type**: Smoke/Happy Path/Edge Case/Negative/Performance
**Node Type**: Input/Filter/Aggregate/Join/SQL/Output

**Description**:
[Brief description of what is being tested]

**Preconditions**:
- [ ] Application is running
- [ ] Test data is available
- [ ] User is logged in (if applicable)

**Test Steps**:
1. [Action]
2. [Action]
3. [Action]

**Test Data**:
- File: [filename]
- Row count: [N]
- Columns: [list]

**Expected Result**:
[What should happen]

**Pass Criteria**:
- [ ] Specific assertion 1
- [ ] Specific assertion 2
- [ ] Performance met (if applicable)

**Post-Conditions**:
- [ ] Cleanup completed
- [ ] State restored
```

---

## Change History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-04 | Initial test case design | workflow-validator |
