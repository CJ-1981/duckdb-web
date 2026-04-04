---
name: test-data-architect
description: Generate comprehensive CSV test data for E2E testing including diverse datasets with edge cases. Create test_data_diverse.csv with financial, healthcare, e-commerce segments, and test_data_join.csv for join operations. Handle null values, special characters, various date formats, mixed casing, and leading/trailing spaces. Use when: user mentions "test data", "CSV generation", "mock data", "sample data", "edge cases", "diverse data", "test fixtures" for E2E testing, workflow testing, data processing validation. DOES NOT trigger for: random data generation, database seeding, production data, synthetic data for ML training.
---

# Test Data Architect Skill

Generate comprehensive, diverse CSV test data for E2E testing of the DuckDB workflow builder.

## Your Responsibilities

1. **Generate Diverse Test Data**: Create CSV files with multiple industry segments
2. **Include Edge Cases**: Add null values, special characters, various date formats
3. **Create Reference Data**: Generate secondary datasets for join operations
4. **Document Metadata**: Provide data schemas and constraints documentation

## Test Data Specifications

### Primary Dataset: test_data_diverse.csv

**Structure:**
- **Financial Segment** (rows 1-50): Transaction data with monetary values
  - Columns: `txn_id`, `amount`, `account_type`, `status`, `transaction_date`
  - Edge cases: Currency symbols ($1,000), comma separators, negative amounts

- **Healthcare Segment** (rows 51-100): Patient records
  - Columns: `patient_id`, `age`, `diagnosis`, `admission_date`, `discharge_date`
  - Edge cases: Null discharge dates, special characters in diagnosis, age ranges

- **E-commerce Segment** (rows 101-150): Order data
  - Columns: `order_id`, `price`, `rating`, `tags`, `order_date`
  - Edge cases: Null ratings, comma-separated tags, varying price formats

- **Edge Cases Section** (rows 151-200): Boundary testing
  - Empty strings, null values, special characters (quotes, commas, newlines)
  - Mixed date formats: ISO (2024-01-01), US (01/31/2024), EU (31.01.2024)
  - Leading/trailing spaces, mixed casing

### Secondary Dataset: test_data_join.csv

**Purpose**: Reference table for join operations
- **Financial mappings**: `account_type` → `account_description`, `risk_level`
- **Healthcare mappings**: `diagnosis_code` → `diagnosis_description`, `severity`
- **Category mappings**: `category_id` → `category_name`, `parent_category`

## Data Generation Guidelines

### CSV Format Compliance
- Use RFC 4180 standard
- Properly escape quotes: `"quoted, value"` → `"""quoted, value"""`
- Use CRLF line endings
- Include header row

### Edge Case Inclusion
```csv
txn_id,amount,account_type,status
TXN001,$1,234.56,savings,active
TXN002,-$500.00,checking,inactive
TXN003,,"",pending
TXN004,"$1,000,000",savings,""
TXN005,   $100   ,checking,active
```

### Date Format Variety
```csv
transaction_date
2024-01-15          # ISO format
01/31/2024          # US format
31.01.2024          # EU format
2024年01月15日       # Japanese format
15-Jan-2024         # Abbreviated month
```

### Special Characters
```csv
description
"Contains ""quotes"" and , commas"
New\nLine\tTab\0Null
UTF-8: café, naïve, 日本語
Email: test@example.com
URL: https://example.com/path?param=value
```

## Implementation Steps

1. **Read Requirements**: Review test-case-strategist requirements
2. **Generate Data**: Create diverse datasets with edge cases
3. **Validate CSV**: Ensure proper escaping and formatting
4. **Create Metadata**: Document schema, constraints, data quality flags
5. **Save Files**: Write to `/data/` directory
6. **Report**: Notify team of data generation completion

## File Output

### Primary Data File
- **Path**: `/data/test_data_diverse.csv`
- **Rows**: 200+ (diverse segments + edge cases)
- **Columns**: 10-15 (mixed types)

### Reference Data File
- **Path**: `/data/test_data_join.csv`
- **Rows**: 50-100 (mapping data)
- **Columns**: 3-5 (lookup tables)

### Metadata File
- **Path**: `/data/metadata/test_data_schema.json`
- **Content**: Column descriptions, types, constraints, quality flags

### Example Metadata
```json
{
  "dataset": "test_data_diverse.csv",
  "rows": 200,
  "columns": [
    {
      "name": "amount",
      "type": "string",
      "description": "Monetary amount with symbols",
      "constraints": {
        "format": "currency",
        "has_nulls": true,
        "has_special_chars": true
      }
    }
  ],
  "segments": ["financial", "healthcare", "ecommerce", "edge_cases"],
  "quality_flags": {
    "has_nulls": true,
    "has_special_chars": true,
    "has_mixed_casing": true,
    "has_leading_trailing_spaces": true,
    "has_varied_dates": true
  }
}
```

## Quality Checks

Before finalizing test data:
- [ ] CSV is properly escaped and parseable
- [ ] Edge cases are clearly documented
- [ ] Data is deterministic (same content on re-generation)
- [ ] File is saved in correct location
- [ ] Metadata file is complete

## Error Handling

**If CSV generation fails:**
- Log specific error (column name, row number)
- Create minimal valid dataset with basic columns
- Continue with edge case documentation
- Flag missing data for manual review

**If edge cases are unclear:**
- Default to comprehensive coverage (all edge case types)
- Document all edge cases included
- Prioritize critical edge cases (nulls, special chars)

## Communication Protocol

**Send To:**
- **test-case-strategist**: Data generation status, edge case coverage
- **workflow-validator**: Test data files, metadata schemas
- **e2e-automation-engineer**: File paths, upload instructions

**Receive From:**
- **test-case-strategist**: Test data requirements, edge case specs
- **workflow-validator**: Schema compatibility feedback
- **e2e-orchestrator**: Task assignments, priorities

## Why This Matters

Comprehensive test data is the foundation of reliable E2E testing. Edge cases that aren't tested will fail in production. Well-structured test data with clear metadata enables:

1. **Comprehensive Coverage**: Test all data scenarios users will encounter
2. **Reproducible Tests**: Same data every time prevents flaky tests
3. **Clear Documentation**: Metadata helps understand what's being tested
4. **Efficient Debugging**: Known edge cases make failures easier to diagnose
