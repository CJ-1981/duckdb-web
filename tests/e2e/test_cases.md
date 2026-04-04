# E2E Test Cases for Data Analyst Web

## Test Metadata

- **Version**: 1.0.0
- **Last Updated**: 2026-04-04
- **Total Tests**: 58
- **Coverage**: All node types, edge cases, performance scenarios

## Test Categories

1. **Smoke Tests** (8 tests) - Quick sanity checks
2. **Happy Path** (16 tests) - Core user workflows
3. **Edge Cases** (20 tests) - Null handling, special chars, date formats
4. **Negative Tests** (10 tests) - Invalid inputs, error handling
5. **Performance Tests** (4 tests) - Large datasets, complex workflows

---

## 1. SMOKE TESTS

### TC-001: API Health Check
**Priority**: High
**Description**: Verify the API backend is responsive

**Preconditions**:
- Backend server is running on localhost:8000

**Test Steps**:
1. Send GET request to `http://localhost:8000/api/v1/health`
2. Verify response status is 200
3. Verify response contains `status: "ok"`

**Expected Results**:
- Status code: 200
- Response body: `{"status": "ok"}`

**Pass Criteria**:
- [ ] Response received within 1 second
- [ ] Status code is 200
- [ ] Response contains status field

**Dependencies**: None
**Test Data**: None

---

### TC-002: Simple CSV Upload
**Priority**: High
**Description**: Upload a basic CSV file with standard headers

**Preconditions**:
- Backend server is running
- Test CSV file exists with columns: id, name, value

**Test Steps**:
1. Create CSV with 3 rows of data
2. POST to `/api/v1/data/upload` with file
3. Verify response contains file_path

**Expected Results**:
- Status code: 200
- Response contains `file_path` string
- File path is valid

**Pass Criteria**:
- [ ] Upload succeeds
- [ ] File path returned
- [ ] No error messages

**Dependencies**: TC-001
**Test Data Reference**: `smoke_simple.csv`

---

### TC-003: Single Filter Node
**Priority**: High
**Description**: Execute workflow with one filter condition

**Preconditions**:
- CSV file uploaded successfully

**Test Steps**:
1. Create workflow: Input -> Filter (value > 100) -> Output
2. POST to `/api/v1/workflows/execute`
3. Verify row_count in response

**Expected Results**:
- Status code: 200
- row_count matches expected filtered rows
- Preview data contains only filtered values

**Pass Criteria**:
- [ ] Execution succeeds
- [ ] row_count is accurate
- [ ] Preview data matches filter condition

**Dependencies**: TC-002
**Test Data Reference**: `smoke_simple.csv`

---

### TC-004: Single Aggregate Node
**Priority**: High
**Description**: Execute workflow with one aggregation

**Preconditions**:
- CSV file uploaded successfully

**Test Steps**:
1. Create workflow: Input -> Aggregate (SUM value by category) -> Output
2. POST to `/api/v1/workflows/execute`
3. Verify aggregation results

**Expected Results**:
- Status code: 200
- Aggregated values are correct
- Group by categories are preserved

**Pass Criteria**:
- [ ] Execution succeeds
- [ ] SUM values are correct
- [ ] Categories are grouped properly

**Dependencies**: TC-002
**Test Data Reference**: `smoke_simple.csv`

---

### TC-005: Basic Join Operation
**Priority**: High
**Description**: Join two CSV files on a common key

**Preconditions**:
- Two CSV files uploaded with common key column

**Test Steps**:
1. Upload both CSV files
2. Create workflow: Input1 + Input2 -> Join (inner) -> Output
3. POST to `/api/v1/workflows/execute`

**Expected Results**:
- Status code: 200
- Joined data contains columns from both files
- Row count matches expected inner join result

**Pass Criteria**:
- [ ] Execution succeeds
- [ ] Columns from both sources present
- [ ] Row count is correct for inner join

**Dependencies**: TC-002
**Test Data Reference**: `smoke_join_left.csv`, `smoke_join_right.csv`

---

### TC-006: Raw SQL Node
**Priority**: Medium
**Description**: Execute custom SQL query

**Preconditions**:
- CSV file uploaded successfully

**Test Steps**:
1. Create workflow: Input -> Raw SQL (SELECT * WHERE value > 100) -> Output
2. POST to `/api/v1/workflows/execute`
3. Verify SQL execution results

**Expected Results**:
- Status code: 200
- Results match expected SQL output

**Pass Criteria**:
- [ ] SQL executes successfully
- [ ] Results are as expected
- [ ] No SQL syntax errors

**Dependencies**: TC-002
**Test Data Reference**: `smoke_simple.csv`

---

### TC-007: CSV Export
**Priority**: High
**Description**: Export workflow result to CSV format

**Preconditions**:
- Workflow executed successfully

**Test Steps**:
1. Create workflow ending with Output node (format: CSV)
2. POST to `/api/v1/workflows/execute`
3. Verify response includes download URL or data

**Expected Results**:
- Status code: 200
- CSV format is valid
- Data matches workflow result

**Pass Criteria**:
- [ ] Export succeeds
- [ ] CSV format is valid
- [ ] Data integrity maintained

**Dependencies**: TC-003
**Test Data Reference**: `smoke_simple.csv`

---

### TC-008: JSON Export
**Priority**: Medium
**Description**: Export workflow result to JSON format

**Preconditions**:
- Workflow executed successfully

**Test Steps**:
1. Create workflow ending with Output node (format: JSON)
2. POST to `/api/v1/workflows/execute`
3. Verify response includes valid JSON

**Expected Results**:
- Status code: 200
- JSON format is valid
- Data matches workflow result

**Pass Criteria**:
- [ ] Export succeeds
- [ ] JSON format is valid
- [ ] Data integrity maintained

**Dependencies**: TC-003
**Test Data Reference**: `smoke_simple.csv`

---

## 2. HAPPY PATH TESTS

### TC-101: Multi-Step Data Pipeline
**Priority**: High
**Description**: Complete ETL pipeline with multiple transformations

**Preconditions**:
- Source CSV with dirty data uploaded

**Test Steps**:
1. Upload CSV with dirty data (extra spaces, mixed case)
2. Create workflow: Input -> Clean -> Filter -> Aggregate -> Output
3. Execute workflow
4. Verify each transformation step

**Expected Results**:
- All transformations apply correctly
- Final output is clean and aggregated
- Row count decreases through pipeline

**Pass Criteria**:
- [ ] Clean node removes spaces
- [ ] Filter node applies condition
- [ ] Aggregate node groups correctly
- [ ] Output format is correct

**Dependencies**: TC-002
**Test Data Reference**: `happy_dirty_data.csv`

---

### TC-102: Chained Filters
**Priority**: High
**Description**: Multiple filter nodes in sequence

**Preconditions**:
- CSV uploaded with multiple filterable columns

**Test Steps**:
1. Create workflow: Input -> Filter1 -> Filter2 -> Filter3 -> Output
2. Each filter applies different condition
3. Execute workflow
4. Verify cumulative filtering

**Expected Results**:
- All filter conditions apply
- Row count decreases with each filter
- Final data meets all conditions

**Pass Criteria**:
- [ ] All filters execute
- [ ] Cumulative effect is correct
- [ ] Row count is accurate

**Dependencies**: TC-002
**Test Data Reference**: `happy_multi_column.csv`

---

### TC-103: Multiple Aggregations
**Priority**: High
**Description**: Aggregate with multiple functions (SUM, AVG, COUNT)

**Preconditions**:
- CSV with numeric data uploaded

**Test Steps**:
1. Create workflow: Input -> Aggregate (SUM, AVG, COUNT) -> Output
2. Group by category column
3. Execute workflow
4. Verify all aggregations

**Expected Results**:
- All three aggregation functions work
- Results are mathematically correct
- Group by preserves categories

**Pass Criteria**:
- [ ] SUM is correct
- [ ] AVG is correct
- [ ] COUNT is correct
- [ ] Categories are preserved

**Dependencies**: TC-002
**Test Data Reference**: `happy_numeric.csv`

---

### TC-104: Left Join Handling
**Priority**: High
**Description**: Left join preserves all left table rows

**Preconditions**:
- Two CSV files uploaded

**Test Steps**:
1. Create workflow with LEFT JOIN
2. Left table has more rows than right
3. Execute workflow
4. Verify NULL handling for unmatched rows

**Expected Results**:
- All left table rows present
- Unmatched rows have NULL for right columns
- Matched rows have data from both tables

**Pass Criteria**:
- [ ] All left rows present
- [ ] NULL values for unmatched
- [ ] Matched data is correct

**Dependencies**: TC-005
**Test Data Reference**: `happy_left_big.csv`, `happy_right_small.csv`

---

### TC-105: Self-Join Pattern
**Priority**: Medium
**Description**: Join table to itself for hierarchical data

**Preconditions**:
- CSV with hierarchical structure uploaded

**Test Steps**:
1. Upload single CSV with parent-child relationships
2. Create workflow: Input -> Self-Join on id/parent_id -> Output
3. Execute workflow
4. Verify hierarchical linking

**Expected Results**:
- Parent-child relationships linked
- No data duplication
- Circular references handled

**Pass Criteria**:
- [ ] Self-join executes
- [ ] Relationships are correct
- [ ] No infinite loops

**Dependencies**: TC-002
**Test Data Reference**: `happy_hierarchical.csv`

---

### TC-106: Case When Transformation
**Priority**: High
**Description**: Create derived column using CASE WHEN logic

**Preconditions**:
- CSV uploaded with numeric column

**Test Steps**:
1. Create workflow: Input -> Case When (value > 1000: 'High', else: 'Low') -> Output
2. Execute workflow
3. Verify new column values

**Expected Results**:
- New column added
- Values match CASE conditions
- ELSE case handles unmatched

**Pass Criteria**:
- [ ] New column exists
- [ ] High values marked correctly
- [ ] Low values marked correctly
- [ ] NULL values handled

**Dependencies**: TC-002
**Test Data Reference**: `happy_numeric.csv`

---

### TC-107: Computed Column
**Priority**: High
**Description**: Add computed column using expression

**Preconditions**:
- CSV with numeric columns uploaded

**Test Steps**:
1. Create workflow: Input -> Computed (col1 * col2) -> Output
2. Execute workflow
3. Verify calculation accuracy

**Expected Results**:
- New column with computed values
- Calculations are mathematically correct
- NULL handling is appropriate

**Pass Criteria**:
- [ ] Column added
- [ ] Values are correct
- [ ] NULL inputs handled

**Dependencies**: TC-002
**Test Data Reference**: `happy_numeric.csv`

---

### TC-108: Window Function
**Priority**: Medium
**Description**: Apply window function for ranking

**Preconditions**:
- CSV with groupable data uploaded

**Test Steps**:
1. Create workflow: Input -> Window (ROW_NUMBER over partition) -> Output
2. Execute workflow
3. Verify ranking logic

**Expected Results**:
- Row numbers assigned
- Partition boundaries respected
- Order by clause applied

**Pass Criteria**:
- [ ] Row numbers sequential
- [ ] Partitions restart counting
- [ ] Order is correct

**Dependencies**: TC-002
**Test Data Reference**: `happy_groupable.csv`

---

### TC-109: Distinct Operation
**Priority**: Medium
**Description**: Remove duplicate rows

**Preconditions**:
- CSV with duplicate rows uploaded

**Test Steps**:
1. Create workflow: Input -> Distinct -> Output
2. Execute workflow
3. Verify duplicates removed

**Expected Results**:
- Duplicate rows removed
- One instance of each unique row kept
- Row count reduced appropriately

**Pass Criteria**:
- [ ] Duplicates removed
- [ ] Unique rows preserved
- [ ] Count is correct

**Dependencies**: TC-002
**Test Data Reference**: `happy_duplicates.csv`

---

### TC-110: Column Rename
**Priority**: Medium
**Description**: Rename multiple columns

**Preconditions**:
- CSV with poorly named columns uploaded

**Test Steps**:
1. Create workflow: Input -> Rename (multiple mappings) -> Output
2. Execute workflow
3. Verify new column names

**Expected Results**:
- Columns renamed correctly
- Data integrity maintained
- Old names not accessible

**Pass Criteria**:
- [ ] All columns renamed
- [ ] Data unchanged
- [ ] New names in output

**Dependencies**: TC-002
**Test Data Reference**: `happy_poor_names.csv`

---

### TC-111: Sort Operation
**Priority**: Medium
**Description**: Sort data by single column

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow: Input -> Sort (column ASC) -> Output
2. Execute workflow
3. Verify sort order

**Expected Results**:
- Data sorted by specified column
- ASC order applied correctly
- NULL values positioned correctly

**Pass Criteria**:
- [ ] Data is sorted
- [ ] Order is ASC
- [ ] NULLs handled

**Dependencies**: TC-002
**Test Data Reference**: `happy_sortable.csv`

---

### TC-112: Multi-Column Sort
**Priority**: Medium
**Description**: Sort by multiple columns

**Preconditions**:
- CSV uploaded with multiple sortable columns

**Test Steps**:
1. Create workflow: Input -> Sort (col1 ASC, col2 DESC) -> Output
2. Execute workflow
3. Verify multi-column sort

**Expected Results**:
- Primary sort on col1
- Secondary sort on col2 within col1 groups
- Direction respected for each

**Pass Criteria**:
- [ ] Primary sort correct
- [ ] Secondary sort correct
- [ ] Directions respected

**Dependencies**: TC-002
**Test Data Reference**: `happy_multi_sort.csv`

---

### TC-113: Limit Operation
**Priority**: Medium
**Description**: Limit result set size

**Preconditions**:
- CSV with many rows uploaded

**Test Steps**:
1. Create workflow: Input -> Limit (100) -> Output
2. Execute workflow
3. Verify row count

**Expected Results**:
- Exactly 100 rows returned
- Data represents first 100 rows
- No data loss beyond limit

**Pass Criteria**:
- [ ] Row count is 100
- [ ] Data is correct subset
- [ ] No truncation errors

**Dependencies**: TC-002
**Test Data Reference**: `happy_large.csv`

---

### TC-114: Select Columns
**Priority**: High
**Description**: Select specific columns from dataset

**Preconditions**:
- CSV with many columns uploaded

**Test Steps**:
1. Create workflow: Input -> Select (col1, col2, col3) -> Output
2. Execute workflow
3. Verify only selected columns present

**Expected Results**:
- Only specified columns in output
- All selected columns present
- Data integrity maintained

**Pass Criteria**:
- [ ] Only selected columns
- [ ] All selected present
- [ ] Data unchanged

**Dependencies**: TC-002
**Test Data Reference**: `happy_wide.csv`

---

### TC-115: Clean Trim Operation
**Priority**: High
**Description**: Remove leading/trailing spaces from text

**Preconditions**:
- CSV with dirty text data uploaded

**Test Steps**:
1. Create workflow: Input -> Clean (trim) -> Output
2. Execute workflow
3. Verify spaces removed

**Expected Results**:
- Leading spaces removed
- Trailing spaces removed
- Internal spaces preserved

**Pass Criteria**:
- [ ] Leading spaces gone
- [ ] Trailing spaces gone
- [ ] Internal spaces kept

**Dependencies**: TC-002
**Test Data Reference**: `happy_spaces.csv`

---

### TC-116: Clean Numeric Operation
**Priority**: High
**Description**: Convert text numbers to numeric format

**Preconditions**:
- CSV with currency/formatted numbers uploaded

**Test Steps**:
1. Create workflow: Input -> Clean (numeric) -> Output
2. Execute workflow
3. Verify numeric conversion

**Expected Results**:
- Currency symbols removed
- Commas removed
- Values are numeric

**Pass Criteria**:
- [ ] Symbols removed
- [ ] Commas removed
- [ ] Values are numeric

**Dependencies**: TC-002
**Test Data Reference**: `happy_currency.csv`

---

## 3. EDGE CASE TESTS

### TC-201: NULL Value Handling in Filter
**Priority**: High
**Description**: Filter operations with NULL values

**Preconditions**:
- CSV with NULL values uploaded

**Test Steps**:
1. Create workflow: Input -> Filter (column IS NOT NULL) -> Output
2. Execute workflow
3. Verify NULL rows excluded

**Expected Results**:
- Rows with NULL values excluded
- Non-NULL rows included
- Count matches expected

**Pass Criteria**:
- [ ] NULLs excluded
- [ ] Non-NULLs included
- [ ] Count correct

**Dependencies**: TC-002
**Test Data Reference**: `edge_nulls.csv`

---

### TC-202: NULL Value Handling in Aggregate
**Priority**: High
**Description**: Aggregate functions with NULL values

**Preconditions**:
- CSV with NULL values in numeric columns uploaded

**Test Steps**:
1. Create workflow: Input -> Aggregate (SUM column) -> Output
2. Execute workflow
3. Verify NULL handling

**Expected Results**:
- NULL values ignored in SUM
- COUNT excludes NULLs
- AVG calculated on non-NULL values

**Pass Criteria**:
- [ ] SUM ignores NULLs
- [ ] COUNT excludes NULLs
- [ ] AVG correct

**Dependencies**: TC-002
**Test Data Reference**: `edge_nulls.csv`

---

### TC-203: NULL Value Handling in Join
**Priority**: High
**Description**: Join operations with NULL key values

**Preconditions**:
- CSV with NULL values in join columns uploaded

**Test Steps**:
1. Create workflow with INNER JOIN on column with NULLs
2. Execute workflow
3. Verify NULL handling

**Expected Results**:
- NULL keys don't match
- Rows with NULL keys excluded
- Join condition respects NULL semantics

**Pass Criteria**:
- [ ] NULL keys unmatched
- [ ] Non-NULL keys matched
- [ ] Join semantics correct

**Dependencies**: TC-005
**Test Data Reference**: `edge_join_nulls.csv`

---

### TC-204: Special Characters in Column Names
**Priority**: High
**Description**: Column names with spaces, special chars

**Preconditions**:
- CSV with special character column names uploaded

**Test Steps**:
1. Upload CSV with columns like "First Name", "Email Address"
2. Create workflow using these columns
3. Execute workflow
4. Verify columns accessible

**Expected Results**:
- Special characters quoted properly
- Columns accessible in filters
- Columns accessible in aggregates

**Pass Criteria**:
- [ ] Names quoted
- [ ] Accessible in filter
- [ ] Accessible in aggregate

**Dependencies**: TC-002
**Test Data Reference**: `edge_special_names.csv`

---

### TC-205: Special Characters in Data
**Priority**: High
**Description**: Data values with quotes, commas, newlines

**Preconditions**:
- CSV with special character values uploaded

**Test Steps**:
1. Upload CSV with quoted strings, commas in values
2. Create workflow using these values
3. Execute workflow
4. Verify data integrity

**Expected Results**:
- Quotes preserved correctly
- Commas in values not split
- Newlines handled properly

**Pass Criteria**:
- [ ] Quotes preserved
- [ ] Commas not split
- [ ] Newlines handled

**Dependencies**: TC-002
**Test Data Reference**: `edge_special_chars.csv`

---

### TC-206: Empty CSV File
**Priority**: Medium
**Description**: Handle CSV with no data rows

**Preconditions**:
- Empty CSV file prepared

**Test Steps**:
1. Upload CSV with only headers
2. Create workflow: Input -> Output
3. Execute workflow
4. Verify graceful handling

**Expected Results**:
- Upload succeeds
- Workflow executes
- Row count is 0
- No errors thrown

**Pass Criteria**:
- [ ] Upload succeeds
- [ ] Execution succeeds
- [ ] Row count 0
- [ ] No errors

**Dependencies**: TC-001
**Test Data Reference**: `edge_empty.csv`

---

### TC-207: Single Row CSV
**Priority**: Medium
**Description**: Handle CSV with one data row

**Preconditions**:
- Single row CSV prepared

**Test Steps**:
1. Upload CSV with one data row
2. Create workflow with aggregations
3. Execute workflow
4. Verify results

**Expected Results**:
- Aggregations work with single row
- Results are mathematically correct
- No division by zero errors

**Pass Criteria**:
- [ ] Aggregation works
- [ ] Results correct
- [ ] No errors

**Dependencies**: TC-002
**Test Data Reference**: `edge_single_row.csv`

---

### TC-208: Very Long String Values
**Priority**: Medium
**Description**: Handle text values exceeding typical length

**Preconditions**:
- CSV with long text values uploaded

**Test Steps**:
1. Upload CSV with 10,000+ character strings
2. Create workflow: Input -> Filter -> Output
3. Execute workflow
4. Verify long strings handled

**Expected Results**:
- Long strings preserved
- No truncation
- Operations work correctly

**Pass Criteria**:
- [ ] Strings preserved
- [ ] No truncation
- [ ] Operations work

**Dependencies**: TC-002
**Test Data Reference**: `edge_long_strings.csv`

---

### TC-209: Unicode and Emoji Characters
**Priority**: Medium
**Description**: Handle non-ASCII characters

**Preconditions**:
- CSV with unicode/emoji uploaded

**Test Steps**:
1. Upload CSV with emoji, Chinese characters, etc.
2. Create workflow: Input -> Output
3. Execute workflow
4. Verify character integrity

**Expected Results**:
- Unicode characters preserved
- Emoji characters preserved
- No encoding corruption

**Pass Criteria**:
- [ ] Unicode preserved
- [ ] Emoji preserved
- [ ] No corruption

**Dependencies**: TC-002
**Test Data Reference**: `edge_unicode.csv`

---

### TC-210: Date Format Variations
**Priority**: High
**Description**: Handle various date formats

**Preconditions**:
- CSV with mixed date formats uploaded

**Test Steps**:
1. Upload CSV with ISO, US, EU date formats
2. Create workflow filtering on dates
3. Execute workflow
4. Verify date parsing

**Expected Results**:
- ISO dates parse correctly
- US format parsed if specified
- EU format parsed if specified
- Invalid dates handled

**Pass Criteria**:
- [ ] ISO dates work
- [ ] US format works
- [ ] EU format works
- [ ] Invalid handled

**Dependencies**: TC-002
**Test Data Reference**: `edge_dates.csv`

---

### TC-211: Numeric Precision
**Priority**: High
**Description**: Handle high precision decimal values

**Preconditions**:
- CSV with high precision decimals uploaded

**Test Steps**:
1. Upload CSV with 10+ decimal place values
2. Create workflow with SUM aggregation
3. Execute workflow
4. Verify precision maintained

**Expected Results**:
- Precision maintained in calculations
- No floating point errors
- Rounding is correct

**Pass Criteria**:
- [ ] Precision maintained
- [ ] No float errors
- [ ] Rounding correct

**Dependencies**: TC-002
**Test Data Reference**: `edge_decimals.csv`

---

### TC-212: Scientific Notation
**Priority**: Medium
**Description**: Handle numbers in scientific notation

**Preconditions**:
- CSV with scientific notation numbers uploaded

**Test Steps**:
1. Upload CSV with values like 1.23E+10
2. Create workflow with numeric operations
3. Execute workflow
4. Verify parsing

**Expected Results**:
- Scientific notation parsed
- Calculations correct
- Output format appropriate

**Pass Criteria**:
- [ ] Parsed correctly
- [ ] Calculations correct
- [ ] Format appropriate

**Dependencies**: TC-002
**Test Data Reference**: `edge_scientific.csv`

---

### TC-213: Boolean Values
**Priority**: Medium
**Description**: Handle various boolean representations

**Preconditions**:
- CSV with boolean values uploaded

**Test Steps**:
1. Upload CSV with true/false, 1/0, yes/no
2. Create workflow filtering on boolean
3. Execute workflow
4. Verify boolean handling

**Expected Results**:
- true/false recognized
- 1/0 recognized
- yes/no recognized
- Filtering works correctly

**Pass Criteria**:
- [ ] true/false works
- [ ] 1/0 works
- [ ] yes/no works
- [ ] Filtering correct

**Dependencies**: TC-002
**Test Data Reference**: `edge_booleans.csv`

---

### TC-214: Large Integer Values
**Priority**: Medium
**Description**: Handle integers beyond 32-bit range

**Preconditions**:
- CSV with large integers uploaded

**Test Steps**:
1. Upload CSV with values > 2^31
2. Create workflow with SUM aggregation
3. Execute workflow
4. Verify no overflow

**Expected Results**:
- Large integers handled
- No overflow errors
- Calculations correct

**Pass Criteria**:
- [ ] No overflow
- [ ] Values correct
- [ ] Calculations correct

**Dependencies**: TC-002
**Test Data Reference**: `edge_large_ints.csv`

---

### TC-215: Mixed Data Types in Column
**Priority**: High
**Description**: Handle columns with mixed types

**Preconditions**:
- CSV with mixed types in same column uploaded

**Test Steps**:
1. Upload CSV with strings and numbers in same column
2. Create workflow with numeric operation
3. Execute workflow
4. Verify type coercion

**Expected Results**:
- Non-numeric values become NULL
- Numeric values processed
- No crashes on mixed data

**Pass Criteria**:
- [ ] Non-numeric NULL
- [ ] Numeric processed
- [ ] No crashes

**Dependencies**: TC-002
**Test Data Reference**: `edge_mixed_types.csv`

---

### TC-216: Duplicate Column Names
**Priority**: Medium
**Description**: Handle CSV with duplicate column names

**Preconditions**:
- CSV with duplicate column names prepared

**Test Steps**:
1. Upload CSV with duplicate column names
2. Create workflow using columns
3. Execute workflow
4. Verify column disambiguation

**Expected Results**:
- Duplicate names handled
- Columns accessible with qualifiers
- No ambiguity errors

**Pass Criteria**:
- [ ] Duplicates handled
- [ ] Accessible with qualifier
- [ ] No ambiguity

**Dependencies**: TC-002
**Test Data Reference**: `edge_dup_columns.csv`

---

### TC-217: Missing Columns
**Priority**: High
**Description**: Handle missing columns in operations

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow referencing non-existent column
2. Execute workflow
3. Verify error handling

**Expected Results**:
- Clear error message
- Workflow doesn't crash
- Invalid column identified

**Pass Criteria**:
- [ ] Error message clear
- [ ] No crash
- [ ] Column identified

**Dependencies**: TC-002
**Test Data Reference**: `edge_simple.csv`

---

### TC-218: All NULL Column
**Priority**: Medium
**Description**: Handle column with all NULL values

**Preconditions**:
- CSV with all-NULL column uploaded

**Test Steps**:
1. Upload CSV where column X is all NULL
2. Create workflow aggregating column X
3. Execute workflow
4. Verify handling

**Expected Results**:
- Aggregation returns NULL or 0
- No errors thrown
- Other columns unaffected

**Pass Criteria**:
- [ ] Returns NULL/0
- [ ] No errors
- [ ] Other columns OK

**Dependencies**: TC-002
**Test Data Reference**: `edge_all_nulls.csv`

---

### TC-219: Inconsistent Row Lengths
**Priority**: High
**Description**: Handle CSV with varying row lengths

**Preconditions**:
- CSV with inconsistent rows uploaded

**Test Steps**:
1. Upload CSV with varying column counts per row
2. Create workflow: Input -> Output
3. Execute workflow
4. Verify padding/truncation

**Expected Results**:
- Short rows padded with NULL
- Long rows truncated to header
- No data loss beyond truncation

**Pass Criteria**:
- [ ] Short rows padded
- [ ] Long rows truncated
- [ ] No crashes

**Dependencies**: TC-002
**Test Data Reference**: `edge_variable_rows.csv`

---

### TC-220: Different Line Endings
**Priority**: Low
**Description**: Handle CR, LF, CRLF line endings

**Preconditions**:
- CSV with mixed line endings prepared

**Test Steps**:
1. Upload CSV with mixed line endings
2. Create workflow: Input -> Output
3. Execute workflow
4. Verify parsing

**Expected Results**:
- All line endings handled
- Row count correct
- No parsing errors

**Pass Criteria**:
- [ ] All endings handled
- [ ] Count correct
- [ ] No parse errors

**Dependencies**: TC-002
**Test Data Reference**: `edge_line_endings.csv`

---

## 4. NEGATIVE TESTS

### TC-301: Invalid File Format
**Priority**: High
**Description**: Upload non-CSV file

**Preconditions**:
- Backend server running

**Test Steps**:
1. Attempt to upload .txt file with random content
2. Verify error response
3. Check no invalid data processed

**Expected Results**:
- Upload rejected
- Clear error message
- No data processed

**Pass Criteria**:
- [ ] Upload rejected
- [ ] Error clear
- [ ] No processing

**Dependencies**: TC-001
**Test Data Reference**: `neg_invalid.txt`

---

### TC-302: Corrupted CSV Data
**Priority**: High
**Description**: Upload malformed CSV

**Preconditions**:
- Backend server running

**Test Steps**:
1. Upload CSV with unmatched quotes
2. Verify graceful error handling
3. Check system stability

**Expected Results**:
- Error returned
- System remains stable
- No partial data loaded

**Pass Criteria**:
- [ ] Error returned
- [ ] System stable
- [ ] No partial load

**Dependencies**: TC-001
**Test Data Reference**: `neg_malformed.csv`

---

### TC-303: Invalid SQL Syntax
**Priority**: High
**Description**: Execute Raw SQL node with syntax error

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with invalid SQL
2. POST to `/api/v1/workflows/execute`
3. Verify error handling

**Expected Results**:
- Clear SQL error message
- Workflow fails gracefully
- System remains responsive

**Pass Criteria**:
- [ ] SQL error clear
- [ ] Graceful failure
- [ ] System responsive

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

### TC-304: Invalid Column Reference
**Priority**: High
**Description**: Reference non-existent column in filter

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with filter on non-existent column
2. Execute workflow
3. Verify error message

**Expected Results**:
- Column not found error
- Invalid column identified
- No crash

**Pass Criteria**:
- [ ] Error clear
- [ ] Column identified
- [ ] No crash

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

### TC-305: Invalid Filter Operator
**Priority**: Medium
**Description**: Use unsupported operator in filter

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with invalid operator (e.g., "BETWEEN")
2. Execute workflow
3. Verify error handling

**Expected Results**:
- Operator not supported error
- Valid operators listed
- No crash

**Pass Criteria**:
- [ ] Error clear
- [ ] Operators listed
- [ ] No crash

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

### TC-306: Division by Zero in Computed Column
**Priority**: Medium
**Description**: Create computed column with division by zero

**Preconditions**:
- CSV with zero values uploaded

**Test Steps**:
1. Create workflow: Computed (col1 / 0)
2. Execute workflow
3. Verify handling

**Expected Results**:
- Returns NULL or infinity
- No crash
- Clear result

**Pass Criteria**:
- [ ] Returns NULL/inf
- [ ] No crash
- [ ] Result clear

**Dependencies**: TC-002
**Test Data Reference**: `neg_with_zero.csv`

---

### TC-307: Invalid Join Key
**Priority**: High
**Description**: Join on non-existent column

**Preconditions**:
- Two CSVs uploaded

**Test Steps**:
1. Create workflow joining on non-existent column
2. Execute workflow
3. Verify error message

**Expected Results**:
- Column not found error
- Tables identified
- No crash

**Pass Criteria**:
- [ ] Error clear
- [ ] Tables identified
- [ ] No crash

**Dependencies**: TC-005
**Test Data Reference**: `neg_simple1.csv`, `neg_simple2.csv`

---

### TC-308: Invalid Aggregation Function
**Priority**: Medium
**Description**: Use unsupported aggregation function

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with invalid aggregation (e.g., "MEDIAN")
2. Execute workflow
3. Verify error handling

**Expected Results**:
- Function not supported error
- Valid functions listed
- No crash

**Pass Criteria**:
- [ ] Error clear
- [ ] Functions listed
- [ ] No crash

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

### TC-309: Circular Workflow
**Priority**: Low
**Description**: Create workflow with circular dependencies

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow where A -> B -> C -> A
2. Execute workflow
3. Verify cycle detection

**Expected Results**:
- Cycle detected error
- Circular path identified
- No infinite loop

**Pass Criteria**:
- [ ] Cycle detected
- [ ] Path identified
- [ ] No infinite loop

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

### TC-310: Multiple Input Nodes
**Priority**: Medium
**Description**: Workflow with multiple unconnected input nodes

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with 2 input nodes not connected
2. Execute workflow
3. Verify handling

**Expected Results**:
- Workflow processes connected path
- Orphan node ignored or error
- Clear behavior

**Pass Criteria**:
- [ ] Connected processed
- [ ] Orphan handled
- [ ] Behavior clear

**Dependencies**: TC-002
**Test Data Reference**: `neg_simple.csv`

---

## 5. PERFORMANCE TESTS

### TC-401: Large Dataset Processing
**Priority**: High
**Description**: Process CSV with 100,000+ rows

**Preconditions**:
- Large CSV file prepared (100K+ rows)

**Test Steps**:
1. Upload 100K row CSV
2. Create workflow: Input -> Filter -> Aggregate -> Output
3. Execute workflow
4. Measure execution time

**Expected Results**:
- Execution completes within 30 seconds
- Memory usage remains reasonable
- Results are accurate

**Pass Criteria**:
- [ ] Completes in 30s
- [ ] Memory reasonable
- [ ] Results accurate

**Dependencies**: TC-001
**Test Data Reference**: `perf_100k.csv`

---

### TC-402: Complex Workflow Execution
**Priority**: High
**Description**: Execute workflow with 20+ nodes

**Preconditions**:
- CSV uploaded

**Test Steps**:
1. Create workflow with 20 transformation nodes
2. Include various node types
3. Execute workflow
4. Measure execution time

**Expected Results**:
- All nodes execute successfully
- Execution completes within reasonable time
- No memory leaks

**Pass Criteria**:
- [ ] All nodes execute
- [ ] Time reasonable
- [ ] No leaks

**Dependencies**: TC-002
**Test Data Reference**: `perf_moderate.csv`

---

### TC-403: Concurrent Workflow Execution
**Priority**: Medium
**Description**: Execute multiple workflows simultaneously

**Preconditions**:
- Multiple CSVs uploaded

**Test Steps**:
1. Submit 5 workflow requests concurrently
2. Monitor execution
3. Verify all complete successfully

**Expected Results**:
- All workflows execute
- No resource conflicts
- Results are accurate

**Pass Criteria**:
- [ ] All execute
- [ ] No conflicts
- [ ] Results accurate

**Dependencies**: TC-001
**Test Data Reference**: `perf_concurrent_1.csv` through `perf_concurrent_5.csv`

---

### TC-404: Memory Efficiency
**Priority**: Medium
**Description**: Monitor memory usage during large operations

**Preconditions**:
- Large CSV prepared (50MB+)

**Test Steps**:
1. Upload large CSV
2. Execute complex workflow
3. Monitor memory usage
4. Verify cleanup

**Expected Results**:
- Memory usage stays within bounds
- Memory released after execution
- No leaks detected

**Pass Criteria**:
- [ ] Usage bounded
- [ ] Memory released
- [ ] No leaks

**Dependencies**: TC-001
**Test Data Reference**: `perf_50mb.csv`

---

## Test Execution Notes

### Test Data Location
All test data files should be located in `/tests/e2e/fixtures/`

### Execution Order
Tests should be executed in dependency order:
1. Smoke Tests (TC-001 to TC-008)
2. Happy Path (TC-101 to TC-116)
3. Edge Cases (TC-201 to TC-220)
4. Negative Tests (TC-301 to TC-310)
5. Performance Tests (TC-401 to TC-404)

### Parallel Execution
Tests can be run in parallel if they don't share:
- Uploaded file paths
- Database connections
- Server resources

### Cleanup
After each test:
- Delete uploaded files
- Clear temporary tables
- Reset workflow state

---

**Document Version**: 1.0.0
**Author**: test-case-strategist agent
**Date**: 2026-04-04
