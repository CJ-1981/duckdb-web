# E2E Test Data Requirements

## Overview

This document specifies the test data requirements for all E2E test cases defined in `test_cases.md`. Each test case references specific test data files that must contain the data types and edge cases described here.

## Test Data Location

All test data files should be stored in:
```
/tests/e2e/fixtures/
```

---

## 1. SMOKE TEST DATA

### smoke_simple.csv
**Purpose**: Basic CSV for simple operations

**Requirements**:
- 3-5 rows of data
- Columns: `id`, `name`, `value`
- Data types: INTEGER, VARCHAR, INTEGER
- Sample data:
  ```csv
  id,name,value
  1,Alice,100
  2,Bob,200
  3,Charlie,150
  ```

**Used by**: TC-002, TC-003, TC-004, TC-006, TC-007, TC-008

---

### smoke_join_left.csv
**Purpose**: Left table for join operations

**Requirements**:
- 5 rows
- Columns: `id`, `name`, `value`
- Include some IDs not in right table

**Used by**: TC-005

---

### smoke_join_right.csv
**Purpose**: Right table for join operations

**Requirements**:
- 3-4 rows
- Columns: `id`, `location`
- Some IDs not in left table
- Sample data:
  ```csv
  id,location
  1,NYC
  2,LA
  3,CHI
  ```

**Used by**: TC-005

---

## 2. HAPPY PATH TEST DATA

### happy_dirty_data.csv
**Purpose**: Data requiring cleaning operations

**Requirements**:
- 10-15 rows
- Columns: `id`, `name`, `amount`, `status`
- Edge cases:
  - Leading/trailing spaces in name
  - Mixed case values
  - Currency symbols ($)
  - Commas in numbers
  - Various date formats

**Used by**: TC-101

---

### happy_multi_column.csv
**Purpose**: Multiple filterable columns

**Requirements**:
- 20+ rows
- Columns: `id`, `category`, `status`, `priority`, `amount`
- Diverse values for filtering:
  - Multiple categories
  - Various statuses
  - Priority levels
  - Numeric amounts

**Used by**: TC-102

---

### happy_numeric.csv
**Purpose**: Numeric data for aggregations

**Requirements**:
- 50+ rows
- Columns: `category`, `value1`, `value2`, `value3`
- Data:
  - 5-10 categories
  - Positive and negative numbers
  - Decimals
  - Some NULL values
- Target: SUM, AVG, COUNT should all work

**Used by**: TC-103, TC-106, TC-107

---

### happy_left_big.csv
**Purpose**: Larger table for left join

**Requirements**:
- 10+ rows
- Columns: `id`, `name`, `value`
- Some IDs not in right table

**Used by**: TC-104

---

### happy_right_small.csv
**Purpose**: Smaller table for left join

**Requirements**:
- 5-7 rows
- Columns: `id`, `location`
- Subset of IDs from left table

**Used by**: TC-104

---

### happy_hierarchical.csv
**Purpose**: Self-join for hierarchical data

**Requirements**:
- 10 rows
- Columns: `id`, `name`, `parent_id`
- Structure:
  - Root nodes (parent_id = NULL)
  - Child nodes
  - Grandchild nodes
- Sample:
  ```csv
  id,name,parent_id
  1,CEO,NULL
  2,CTO,1
  3,CFO,1
  4,Engineering,2
  5,Finance,3
  ```

**Used by**: TC-105

---

### happy_groupable.csv
**Purpose**: Data for window functions

**Requirements**:
- 20+ rows
- Columns: `department`, `employee`, `salary`, `hire_date`
- Multiple employees per department
- Varying salaries
- Different hire dates

**Used by**: TC-108

---

### happy_duplicates.csv
**Purpose**: Data with duplicate rows

**Requirements**:
- 10 rows with 3-4 duplicate sets
- Columns: `id`, `name`, `value`
- Exact duplicate rows
- Near-duplicates (case differences)

**Used by**: TC-109

---

### happy_poor_names.csv
**Purpose**: Columns with poor naming

**Requirements**:
- 5-10 rows
- Columns: `a`, `b`, `c`, `d` or generic names
- Rename mappings: a->first_name, b->last_name, etc.

**Used by**: TC-110

---

### happy_sortable.csv
**Purpose**: Single column sorting

**Requirements**:
- 20+ rows
- Columns: `id`, `name`, `score`
- Scores: mix of low, medium, high
- Some NULL values

**Used by**: TC-111

---

### happy_multi_sort.csv
**Purpose**: Multi-column sorting

**Requirements**:
- 30+ rows
- Columns: `category`, `priority`, `name`
- Multiple categories
- Priorities within categories
- Names within priority

**Used by**: TC-112

---

### happy_large.csv
**Purpose**: Dataset for limit operation

**Requirements**:
- 500+ rows
- Columns: `id`, `data1`, `data2`
- Sequential data

**Used by**: TC-113

---

### happy_wide.csv
**Purpose**: Many columns for select operation

**Requirements**:
- 5-10 rows
- 20+ columns: `col1`, `col2`, ..., `col20`
- Various data types

**Used by**: TC-114

---

### happy_spaces.csv
**Purpose**: Data with extra spaces

**Requirements**:
- 10 rows
- Columns: `id`, `name`, `description`
- Leading spaces in name
- Trailing spaces in description
- Internal spaces preserved

**Used by**: TC-115

---

### happy_currency.csv
**Purpose**: Currency/formatted numbers

**Requirements**:
- 10 rows
- Columns: `id`, `item`, `price`
- Prices like: $1,200.50, €500.00, £1,000

**Used by**: TC-116

---

## 3. EDGE CASE TEST DATA

### edge_nulls.csv
**Purpose**: NULL value handling

**Requirements**:
- 10-15 rows
- Columns: `id`, `name`, `value`, `category`
- Mix of NULL and non-NULL values
- NULL in different positions
- All NULL column

**Used by**: TC-201, TC-202, TC-218

---

### edge_join_nulls.csv
**Purpose**: NULL values in join keys

**Requirements**:
- Two CSVs with NULL in join column
- Left: 5 rows with some NULL ids
- Right: 5 rows with some NULL ids

**Used by**: TC-203

---

### edge_special_names.csv
**Purpose**: Special characters in column names

**Requirements**:
- 5 rows
- Columns: `First Name`, `Last Name`, `Email Address`, `Phone Number`
- Spaces in names
- Special characters

**Used by**: TC-204

---

### edge_special_chars.csv
**Purpose**: Special characters in data

**Requirements**:
- 10 rows
- Columns: `id`, `text`, `description`
- Values with:
  - Commas: "Smith, John"
  - Quotes: 'He said "hello"'
  - Newlines: "Line 1\nLine 2"
  - Tabs: "Col1\tCol2"

**Used by**: TC-205

---

### edge_empty.csv
**Purpose**: Empty CSV file

**Requirements**:
- Headers only
- Columns: `id`, `name`, `value`
- No data rows

**Used by**: TC-206

---

### edge_single_row.csv
**Purpose**: Single data row

**Requirements**:
- Header + 1 data row
- Columns: `id`, `name`, `value`
- Valid data

**Used by**: TC-207

---

### edge_long_strings.csv
**Purpose**: Very long text values

**Requirements**:
- 5 rows
- Columns: `id`, `short`, `long`
- Long column: 10,000+ characters
- Repeat patterns for verification

**Used by**: TC-208

---

### edge_unicode.csv
**Purpose**: Unicode and emoji characters

**Requirements**:
- 10 rows
- Columns: `id`, `text`, `emoji`
- Chinese characters
- Arabic text
- Emoji: 😀 🎉 ❤️
- Accented characters

**Used by**: TC-209

---

### edge_dates.csv
**Purpose**: Various date formats

**Requirements**:
- 15 rows
- Columns: `id`, `date_iso`, `date_us`, `date_eu`, `date_invalid`
- Formats:
  - ISO: 2023-01-15
  - US: 01/15/2023
  - EU: 15.01.2023
  - Invalid: 99/99/9999

**Used by**: TC-210

---

### edge_decimals.csv
**Purpose**: High precision decimals

**Requirements**:
- 10 rows
- Columns: `id`, `value`
- Values with 10+ decimal places
- Example: 123.123456789012345

**Used by**: TC-211

---

### edge_scientific.csv
**Purpose**: Scientific notation numbers

**Requirements**:
- 10 rows
- Columns: `id`, `value`
- Values: 1.23E+10, 4.56E-5, etc.

**Used by**: TC-212

---

### edge_booleans.csv
**Purpose**: Various boolean representations

**Requirements**:
- 10 rows
- Columns: `id`, `bool_tf`, `bool_10`, `bool_yn`
- Values: true/false, 1/0, yes/no

**Used by**: TC-213

---

### edge_large_ints.csv
**Purpose**: Large integer values

**Requirements**:
- 5 rows
- Columns: `id`, `big_int`
- Values > 2^31
- Example: 3000000000

**Used by**: TC-214

---

### edge_mixed_types.csv
**Purpose**: Mixed types in same column

**Requirements**:
- 10 rows
- Columns: `id`, `mixed_column`
- Values: "123", "abc", "456", "def"

**Used by**: TC-215

---

### edge_dup_columns.csv
**Purpose**: Duplicate column names

**Requirements**:
- 5 rows
- Columns with duplicates: `id`, `name`, `value`, `name`
- CSV parser must handle

**Used by**: TC-216

---

### edge_simple.csv
**Purpose**: Simple CSV for negative tests

**Requirements**:
- 3-5 rows
- Columns: `id`, `name`, `value`
- Clean data

**Used by**: TC-217, TC-303, TC-304, TC-305, TC-306, TC-308, TC-309, TC-310

---

### edge_all_nulls.csv
**Purpose**: Column with all NULL values

**Requirements**:
- 5 rows
- Columns: `id`, `all_null_column`, `value`
- all_null_column: all NULL or empty

**Used by**: TC-218

---

### edge_variable_rows.csv
**Purpose**: Inconsistent row lengths

**Requirements**:
- Some rows with 3 columns
- Some rows with 5 columns
- Some rows with 2 columns
- Header: `col1`, `col2`, `col3`

**Used by**: TC-219

---

### edge_line_endings.csv
**Purpose**: Different line endings

**Requirements**:
- 5 rows
- Mix of CR, LF, CRLF
- Same content, different endings

**Used by**: TC-220

---

## 4. NEGATIVE TEST DATA

### neg_invalid.txt
**Purpose**: Invalid file format

**Requirements**:
- Text file with random content
- Not CSV format
- Binary or random text

**Used by**: TC-301

---

### neg_malformed.csv
**Purpose**: Malformed CSV

**Requirements**:
- Unmatched quotes
- Unclosed strings
- Invalid CSV structure

**Used by**: TC-302

---

### neg_simple.csv
**Purpose**: Simple CSV for negative tests

**Requirements**:
- 3-5 rows
- Columns: `id`, `name`, `value`
- Clean data for testing invalid operations

**Used by**: TC-303, TC-304, TC-305, TC-306, TC-308, TC-309, TC-310

---

### neg_with_zero.csv
**Purpose**: Data with zero values

**Requirements**:
- 5 rows
- Columns: `id`, `numerator`, `denominator`
- Some denominators = 0

**Used by**: TC-306

---

### neg_simple1.csv, neg_simple2.csv
**Purpose**: Two CSVs for join tests

**Requirements**:
- 5 rows each
- Different schemas
- No common keys for some tests

**Used by**: TC-307

---

## 5. PERFORMANCE TEST DATA

### perf_100k.csv
**Purpose**: Large dataset for performance

**Requirements**:
- 100,000+ rows
- Columns: `id`, `category`, `value`, `timestamp`
- 10-20 categories
- Random values
- File size: ~10-20MB

**Used by**: TC-401

---

### perf_moderate.csv
**Purpose**: Moderate size for complex workflows

**Requirements**:
- 10,000 rows
- Multiple columns
- Various data types

**Used by**: TC-402

---

### perf_concurrent_1.csv through perf_concurrent_5.csv
**Purpose**: Concurrent execution tests

**Requirements**:
- 5 similar CSVs
- 5,000 rows each
- Similar structure

**Used by**: TC-403

---

### perf_50mb.csv
**Purpose**: Large file for memory testing

**Requirements**:
- File size: 50MB+
- Columns: `id`, `data1`, `data2`, ..., `data10`
- Mix of data types
- Target: 500,000+ rows

**Used by**: TC-404

---

## Data Generation Guidelines

### Automated Generation

For large datasets (perf_*.csv), use automated generation:

```python
import random
import csv

def generate_large_csv(filename, rows):
    categories = ['A', 'B', 'C', 'D', 'E']
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'category', 'value', 'timestamp'])
        for i in range(rows):
            writer.writerow([
                i,
                random.choice(categories),
                random.uniform(0, 1000),
                f'2023-01-01 {i%24}:{i%60}:{i%60}'
            ])
```

### CSV Standards

All CSV files must:
- Use UTF-8 encoding
- Have headers in first row
- Use comma as delimiter
- Quote strings containing commas
- Use standard CSV escaping

### Fixtures Directory Structure

```
/tests/e2e/fixtures/
├── smoke/
│   ├── smoke_simple.csv
│   ├── smoke_join_left.csv
│   └── smoke_join_right.csv
├── happy/
│   ├── happy_dirty_data.csv
│   ├── happy_multi_column.csv
│   └── ...
├── edge/
│   ├── edge_nulls.csv
│   ├── edge_special_chars.csv
│   └── ...
├── negative/
│   ├── neg_invalid.txt
│   └── neg_malformed.csv
└── performance/
    ├── perf_100k.csv
    └── perf_50mb.csv
```

---

## Test Data Validation

Before running tests, validate test data:

1. **File existence**: All files exist
2. **Format validity**: Valid CSV format
3. **Row counts**: Match specifications
4. **Column names**: Match specifications
5. **Encoding**: UTF-8 encoding

---

**Document Version**: 1.0.0
**Author**: test-case-strategist agent
**Date**: 2026-04-04
