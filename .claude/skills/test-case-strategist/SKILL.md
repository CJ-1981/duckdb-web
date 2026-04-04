---
name: test-case-strategist
description: Design comprehensive E2E test cases for DuckDB workflow builder covering all node types (input, filter, aggregate, join, SQL, output) with edge cases, happy paths, and negative scenarios. Create test case specifications with clear steps, expected results, and pass criteria. Use when: user mentions "test cases", "test scenarios", "test design", "test coverage", "test planning", "testing strategy" for E2E testing, workflow validation, UI testing. DOES NOT trigger for: unit test design, API test design, manual test cases without automation context.
---

# Test Case Strategist Skill

Design comprehensive E2E test cases that verify all workflow builder functionality with clear pass/fail criteria.

## Your Responsibilities

1. **Analyze Requirements**: Review product specs and user stories
2. **Design Test Cases**: Create test scenarios for all node types
3. **Map Test Data**: Link test cases to specific data scenarios
4. **Document Specifications**: Write clear test case documentation
5. **Prioritize Tests**: Order by risk and business impact

## Test Case Categories

### 1. Smoke Tests (5-10 tests)
**Purpose**: Quick sanity check of critical functionality
**Duration**: < 5 minutes total
**Examples**:
- Upload CSV and preview data
- Add single filter node and run
- Verify data preview panel displays
- Run basic workflow and check output

### 2. Happy Path Tests (15-20 tests)
**Purpose**: Verify core user workflows work correctly
**Duration**: < 15 minutes total
**Examples**:
- **Input Node**: Upload CSV, verify schema detection
- **Filter Node**: Filter by single condition, verify results
- **Aggregate Node**: Group by column, calculate sum/avg/count
- **Join Node**: Join two tables, verify combined data
- **SQL Node**: Execute custom query, verify results
- **Multi-Node Workflow**: Chain 3+ nodes, verify end-to-end flow

### 3. Edge Case Tests (20-30 tests)
**Purpose**: Verify robust handling of unusual data
**Duration**: < 20 minutes total
**Examples**:
- **Null Handling**: Filter/aggregate with null values
- **Special Characters**: Data with quotes, commas, newlines
- **Date Formats**: Various date format parsing
- **Empty Results**: Filters that return zero rows
- **Large Datasets**: 1000+ row performance
- **Mixed Types**: Columns with multiple data types

### 4. Negative Tests (10-15 tests)
**Purpose**: Verify error handling and validation
**Duration**: < 10 minutes total
**Examples**:
- **Invalid File**: Upload non-CSV file
- **Malformed CSV**: Upload broken CSV file
- **Invalid SQL**: Execute SQL with syntax errors
- **Circular Dependencies**: Create workflow loops
- **Invalid Connections**: Connect incompatible nodes

### 5. Performance Tests (5-10 tests)
**Purpose**: Verify system handles realistic data volumes
**Duration**: < 15 minutes total
**Examples**:
- **Large CSV**: Upload 10MB+ file
- **Complex Workflow**: 10+ node workflow
- **Memory Stress**: Multiple concurrent workflows
- **Response Time**: Verify < 3s for simple operations

## Test Case Template

Each test case must include:

```markdown
### Test Case: TC-XXX - [Title]

**Priority**: High/Medium/Low
**Category**: Smoke/Happy Path/Edge Case/Negative/Performance
**Node Types**: input, filter, aggregate, join, sql, output
**Estimated Duration**: 30s

**Preconditions**:
- Application is running at http://localhost:3000
- Test data file exists: /data/test_data_diverse.csv
- No active workflows in the canvas

**Test Steps**:
1. Navigate to application homepage
2. Click "Upload CSV" button
3. Select file: /data/test_data_diverse.csv
4. Verify data preview appears with 200 rows
5. Add "Filter" node to canvas
6. Configure filter: `amount > 1000`
7. Connect input node to filter node
8. Click "Run Workflow" button
9. Wait for execution to complete
10. Verify filtered results display

**Expected Result**:
- Data preview shows original 200 rows
- Filter node added to canvas with visual connection
- After execution, results show rows where amount > 1000
- Row count is less than original 200 rows

**Pass Criteria**:
- [ ] CSV uploads successfully
- [ ] Data preview displays correct row count
- [ ] Filter node connects to input node
- [ ] Workflow executes without errors
- [ ] Results show filtered data (rows < 200)

**Test Data**: /data/test_data_diverse.csv (rows 1-50, financial segment)

**Dependencies**: None

**Cleanup**:
- Clear workflow canvas
- Close any open modals/panels
```

## Node-Specific Test Cases

### Input Node Tests
```markdown
- TC-INP-001: Upload valid CSV file
- TC-INP-002: Upload invalid file format
- TC-INP-003: Upload CSV with special characters
- TC-INP-004: Upload CSV with varied date formats
- TC-INP-005: Verify schema auto-detection
- TC-INP-006: Verify data preview panel
```

### Filter Node Tests
```markdown
- TC-FILT-001: Filter by single condition (amount > 1000)
- TC-FILT-002: Filter by multiple conditions (amount > 1000 AND status = 'active')
- TC-FILT-003: Filter with null values
- TC-FILT-004: Filter returns zero rows
- TC-FILT-005: Filter with special characters in condition
- TC-FILT-006: Case-sensitive filtering
- TC-FILT-007: Filter on date column
```

### Aggregate Node Tests
```markdown
- TC-AGG-001: Simple SUM aggregation
- TC-AGG-002: Group by single column with SUM
- TC-AGG-003: Group by multiple columns with COUNT
- TC-AGG-004: Aggregate with null values
- TC-AGG-005: Multiple aggregations (SUM, AVG, COUNT)
- TC-AGG-006: Aggregate on filtered data
```

### Join Node Tests
```markdown
- TC-JOIN-001: Inner join on single key
- TC-JOIN-002: Left join with unmatched rows
- TC-JOIN-003: Join on multiple keys
- TC-JOIN-004: Join with null values in key column
- TC-JOIN-005: Self-join
- TC-JOIN-006: Join three tables
```

### SQL Node Tests
```markdown
- TC-SQL-001: Simple SELECT query
- TC-SQL-002: Query with WHERE clause
- TC-SQL-003: Query with GROUP BY and HAVING
- TC-SQL-004: Query with subquery
- TC-SQL-005: Invalid SQL syntax (error handling)
- TC-SQL-006: Query with JOIN
```

### Output Node Tests
```markdown
- TC-OUT-001: Export results as CSV
- TC-OUT-002: Export results as JSON
- TC-OUT-003: Verify data format integrity
- TC-OUT-004: Export with large dataset
```

## Implementation Steps

1. **Review Requirements**: Read product specs and user stories
2. **Analyze Existing Workflows**: Review `/data/workflows/*.json`
3. **Map Test Data**: Identify edge cases in test_data_diverse.csv
4. **Design Test Cases**: Create test specifications for each node type
5. **Prioritize**: Order tests by risk (critical path → edge cases → negative)
6. **Document**: Write test cases to `/tests/e2e/test_cases.md`
7. **Validate**: Review with e2e-automation-engineer for feasibility

## File Output

### Test Case Specification
- **Path**: `/tests/e2e/test_cases.md`
- **Format**: Markdown with test case template
- **Content**: 50-60 test cases across all categories

### Test Data Requirements
- **Path**: `/tests/e2e/test_data_requirements.md`
- **Content**: Edge cases, data types, row counts needed

### Expected Results
- **Path**: `/tests/e2e/expected_results.json`
- **Content**: Expected row counts, column schemas for each test

## Quality Checks

Before finalizing test cases:
- [ ] Each test has clear pass/fail criteria
- [ ] Tests are independent (no dependencies between tests)
- [ ] Test steps are unambiguous and specific
- [ ] Expected results are measurable and verifiable
- [ ] Test data requirements are documented
- [ ] Critical path tests are prioritized

## Error Handling

**If requirements are ambiguous:**
- Create comprehensive tests covering all interpretations
- Document assumptions made
- Flag for user review

**If node type documentation is incomplete:**
- Write characterization tests to document actual behavior
- Note gaps in documentation
- Suggest improvements to product docs

**If test automation is infeasible:**
- Mark as manual test with clear execution steps
- Document why automation isn't possible
- Suggest UI changes to enable automation

## Communication Protocol

**Send To:**
- **test-data-architect**: Test data requirements, edge case specifications
- **e2e-automation-engineer**: Test case specifications, validation criteria
- **workflow-validator**: Workflow JSON requirements for test scenarios
- **e2e-orchestrator**: Test plan completion, coverage report

**Receive From:**
- **e2e-orchestrator**: Test planning task assignments, requirements
- **e2e-automation-engineer**: Test feasibility feedback, automation constraints

## Why This Matters

Well-designed test cases are the blueprint for reliable automation. Clear specifications prevent ambiguity, enable parallel work, and ensure comprehensive coverage. Good test design:

1. **Prevents Ambiguity**: Clear steps eliminate interpretation errors
2. **Enables Parallel Work**: Automation can start while design continues
3. **Ensures Coverage**: Systematic design prevents missed scenarios
4. **Facilitates Maintenance**: Clear documentation aids future updates
