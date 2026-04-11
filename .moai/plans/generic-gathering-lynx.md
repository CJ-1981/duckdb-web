# Automatic Type Detection for DuckDB Workflow Builder

## Context

Users encounter type casting errors when using aggregate functions like `SUM()` on CSV columns that contain Korean number formats:

```
Error: sum(VARCHAR) - No function matches
Line: SUM(헌금총액) AS 총_헌금액
```

**Root Cause:**
- CSV files are loaded with `ALL_VARCHAR=TRUE` flag (src/api/routes/workflows.py:607, 611, 1203, 1207, 1428)
- Korean number formats (commas, currency symbols) are not handled
- Existing CSVConnector type inference exists but is not used in workflows
- Type inference doesn't account for formatted numbers (e.g., "1,234,567", "₩1,000")

**Impact:**
- Users must manually cast columns with `TRY_CAST(REPLACE(col, ',', '') AS DOUBLE)`
- Aggregate functions fail without explicit type casting
- Poor UX for Korean data formats

## Current State

### Existing Type Inference
**File:** `src/core/connectors/csv.py` (Lines 143-212)

The `_infer_type()` method supports:
- INTEGER, FLOAT, BOOLEAN, DATE, VARCHAR detection
- Missing value handling
- But **NOT** Korean number formats (commas, currency symbols)

### Current Workflow CSV Loading
**File:** `src/api/routes/workflows.py` (Lines 607, 611, 1203, 1207, 1428)

```python
# Current approach - forces all VARCHAR
conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE)", [file_path])
```

## Proposed Solution

### Phase 1: Enhance Type Inference (src/core/connectors/csv.py)

**Update `_infer_type()` method to handle:**

1. **Korean Number Formats:**
   - Remove commas: "1,234,567" → 1234567
   - Remove currency symbols: "₩1,000" → 1000, "$100" → 100
   - Handle negative numbers: "(1,000)" → -1000

2. **New Type Detection:**
   ```python
   def _infer_type(self, values: List[str]) -> str:
       # Try INTEGER with format cleaning
       cleaned = self._clean_korean_numbers(values)
       try:
           for v in cleaned:
               int(v)
           return 'INTEGER'
       except ValueError:
           pass

       # Try DOUBLE with format cleaning
       try:
           for v in cleaned:
               float(v)
           return 'DOUBLE'
       except ValueError:
           pass

       # ... existing BOOLEAN, DATE, VARCHAR logic
   ```

3. **Add Helper Method:**
   ```python
   def _clean_korean_number(self, value: str) -> str:
       """Clean Korean number format for type inference"""
       if not value:
           return '0'

       # Remove common Korean formatting
       cleaned = value
       cleaned = cleaned.replace(',', '')      # Remove commas
       cleaned = cleaned.replace('₩', '')      # Remove Won symbol
       cleaned = cleaned.replace('$', '')      # Remove dollar
       cleaned = cleaned.replace('¥', '')      # Remove yen
       cleaned = cleaned.strip()

       # Handle negative numbers in parentheses: (1,000) → -1000
       if cleaned.startswith('(') and cleaned.endswith(')'):
           cleaned = '-' + cleaned[1:-1]

       return cleaned
   ```

### Phase 2: Modify Workflow CSV Loading (src/api/routes/workflows.py)

**Replace `ALL_VARCHAR=TRUE` with schema inference:**

**Current (Lines 607-613):**
```python
conn.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE)", [file_path])
```

**New Approach:**
```python
# 1. Infer schema from CSV
from src.core.connectors.csv import CSVConnector

connector = CSVConnector()
schema = connector.infer_schema(file_path)

# 2. Build CAST expressions per column
cast_expressions = []
for col_name, col_type in schema.items():
    quoted_name = f'"{col_name}"'
    if col_type == 'INTEGER':
        # Clean Korean format and cast to INTEGER
        cast_expressions.append(f"TRY_CAST(REPLACE(REPLACE({quoted_name}, ',', ''), '₩', '') AS INTEGER) AS {quoted_name}")
    elif col_type == 'DOUBLE':
        cast_expressions.append(f"TRY_CAST(REPLACE(REPLACE({quoted_name}, ',', ''), '₩', '') AS DOUBLE) AS {quoted_name}")
    else:
        cast_expressions.append(quoted_name)

# 3. Create table with proper types
sql = f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT {', '.join(cast_expressions)} FROM read_csv_auto(?, ALL_VARCHAR=TRUE)"
conn.execute(sql, [file_path])
```

### Phase 3: Add Fallback Safety

**For columns that fail conversion, use original value:**
```python
# Use COALESCE with TRY_CAST for safety
CASE
  WHEN TRY_CAST(REPLACE(REPLACE(col, ',', ''), '₩', '') AS DOUBLE) IS NOT NULL
    THEN TRY_CAST(REPLACE(REPLACE(col, ',', ''), '₩', '') AS DOUBLE)
  ELSE NULL
END AS col
```

### Phase 4: Optimize Performance

**Sample-based inference for large files:**
```python
def infer_schema(self, file_path: str, max_rows: int = 1000) -> Dict[str, str]:
    """
    Infer schema from CSV file (sample-based for performance)

    Args:
        file_path: Path to CSV file
        max_rows: Maximum rows to sample (default: 1000)

    Returns:
        Dictionary mapping column names to inferred types
    """
    # Read only first max_rows for type detection
    rows = []
    with open(file_path, 'r', encoding=self.encoding, newline='') as f:
        reader = csv.DictReader(f, delimiter=self.delimiter)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            rows.append(row)

    # ... rest of inference logic
```

**Cache inferred schemas:**
```python
# Global cache for CSV schemas
_CSV_SCHEMA_CACHE: Dict[str, Dict[str, str]] = {}
_FILE_SIZE_CACHE: Dict[str, int] = {}

def get_or_infer_schema(file_path: str) -> Dict[str, str]:
    """Get cached schema or infer from CSV"""
    # Check cache first
    if file_path in _CSV_SCHEMA_CACHE:
        return _CSV_SCHEMA_CACHE[file_path]

    # Determine sample size based on file size
    file_size = os.path.getsize(file_path)
    sample_rows = 1000 if file_size > 100 * 1024 * 1024 else None  # 100MB threshold

    connector = CSVConnector()
    schema = connector.infer_schema(file_path, max_rows=sample_rows)
    _CSV_SCHEMA_CACHE[file_path] = schema
    return schema
```

## User Requirements

✅ **Type Detection:** Always enabled by default for all CSV files
✅ **Performance:** Sample first 1000 rows for large files (>100MB)
✅ **UI:** Show detected types in Data Inspection Panel with manual override capability

## Implementation Plan

1. **`src/core/connectors/csv.py`** (Lines 143-212)
   - Add `_clean_korean_number()` method
   - Update `_infer_type()` to clean numbers before type detection
   - Add support for currency symbols and formatted numbers

2. **`src/api/routes/workflows.py`** (Lines 607-613, 1203-1208, 1428)
   - Import CSVConnector
   - Replace `ALL_VARCHAR=TRUE` calls with schema inference
   - Add CAST expressions for detected types
   - Handle Korean number formats in CAST expressions

### Backward Compatibility

- **Fallback to ALL_VARCHAR=TRUE** if type inference fails
- **TRY_CAST** for safe conversion (returns NULL on failure)
- **Preserve existing behavior** for files without formatted numbers
- **No breaking changes** to existing workflows

### UI Implementation

### Data Inspection Panel Updates
**File:** `src/components/panels/DataInspectionPanel.tsx`

**Add Type Display and Override:**

```typescript
// Add type information to column display
interface ColumnTypeDef {
  column_name: string;
  column_type: string;  // DuckDB type: INTEGER, DOUBLE, VARCHAR, etc.
  inferred_type?: string;  // Auto-detected type (if different)
  can_override: boolean;   // Whether user can change type
}

// Add type selector UI
function TypeSelector({ column, onTypeChange }: TypeSelectorProps) {
  const types = ['INTEGER', 'DOUBLE', 'VARCHAR', 'DATE', 'BOOLEAN'];

  return (
    <select
      value={column.inferred_type || column.column_type}
      onChange={(e) => onTypeChange(column.column_name, e.target.value)}
      className="type-selector"
    >
      {types.map(type => (
        <option key={type} value={type}>{type}</option>
      ))}
    </select>
  );
}

// Show detected vs actual type
function TypeInfo({ column }: { column: ColumnTypeDef }) {
  const hasOverride = column.inferred_type && column.inferred_type !== column.column_type;

  return (
    <div className="type-info">
      <span className={`type-badge ${column.column_type.toLowerCase()}`}>
        {column.column_type}
      </span>
      {hasOverride && (
        <span className="inferred-type">
          → Detected: {column.inferred_type}
        </span>
      )}
    </div>
  );
}
```

### Backend API for Type Info
**File:** `src/api/routes/workflows.py`

**Add new endpoint:**
```python
@router.get("/column-types/{file_path}")
async def get_column_types(file_path: str):
    """Get detected column types for a CSV file"""
    try:
        connector = CSVConnector()
        schema = connector.infer_schema(file_path, max_rows=1000)

        return {
            "status": "success",
            "file_path": file_path,
            "columns": [
                {
                    "name": col,
                    "detected_type": dtype,
                    "can_override": True
                }
                for col, dtype in schema.items()
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## Testing Strategy

1. **Test Korean Number Formats:**
   ```sql
   -- Test CSV with: "헌금총액"
   -- Data: "1,000", "₩2,500", "(3,000)"
   -- Expected: Detect as DOUBLE/INTEGER, convert successfully
   ```

2. **Test Aggregate Functions:**
   ```sql
   -- Should work without manual casting:
   SELECT SUM(헌금총액) AS total FROM {{input}}
   ```

3. **Test Type Detection:**
   - INTEGER: "1", "100", "1,234"
   - DOUBLE: "1.5", "1,234.56", "₩1,234.56"
   - VARCHAR: "text", "mixed123abc"

4. **Test Edge Cases:**
   - Empty values
   - Mixed formats in same column
   - NULL values
   - Very large numbers

## Verification

After implementation:

### 1. Unit Tests
```python
# Test Korean number cleaning
def test_clean_korean_number():
    connector = CSVConnector()
    assert connector._clean_korean_number("1,000") == "1000"
    assert connector._clean_korean_number("₩1,234,567") == "1234567"
    assert connector._clean_korean_number("(1,000)") == "-1000"
    assert connector._clean_korean_number("$100") == "100"

# Test type inference with Korean formats
def test_infer_type_korean_numbers():
    connector = CSVConnector()
    assert connector._infer_type(["1,000", "2,000", "3,000"]) == "INTEGER"
    assert connector._infer_type(["₩1,234.56", "₩2,345.67"]) == "DOUBLE"
    assert connector._infer_type(["text", "more text"]) == "VARCHAR"
```

### 2. Integration Tests
- Upload CSV with Korean numbers (e.g., 헌금총액 column with "₩1,000,000")
- Create Aggregate node with `SUM(헌금총액)`
- Execute workflow - should succeed without manual casting
- Check logs for type detection messages
- Verify results - sums should be calculated correctly

### 3. End-to-End Tests
```sql
-- Test Case 1: Korean Money Format
-- CSV data: "헌금총액" column with "₩1,000,000", "₩2,500,000"
-- Query: SELECT SUM(헌금총액) FROM {{input}}
-- Expected: Returns 3500000.0 (DOUBLE)

-- Test Case 2: Mixed Formats
-- CSV data: "연락처" with "010-1234-5678", "02-1234-5678"
-- Query: SELECT 연락처 FROM {{input}} LIMIT 5
-- Expected: Preserves VARCHAR type

-- Test Case 3: Currency Symbols
-- CSV data: "가격" with "$100", "$200", "$300"
-- Query: SELECT AVG(가격) FROM {{input}}
-- Expected: Returns 200.0 (DOUBLE)
```

## Summary

**Problem:** Korean number formats (commas, currency symbols) cause SUM() errors
**Root Cause:** CSVs loaded as VARCHAR with ALL_VARCHAR=TRUE
**Solution:** Auto-detect types, clean Korean formats, apply proper casting
**Impact:** Users can aggregate Korean data without manual TRY_CAST

**Files Modified:**
- `src/core/connectors/csv.py` - Enhanced type inference
- `src/api/routes/workflows.py` - Schema-aware CSV loading
- `src/components/panels/DataInspectionPanel.tsx` - Type display UI

**Key Features:**
- ✅ Always-on automatic type detection
- ✅ Korean number format support (commas, currency symbols)
- ✅ Performance optimized (sample first 1000 rows)
- ✅ UI shows detected types with override capability
- ✅ Backward compatible with existing workflows
- ✅ Safe conversion using TRY_CAST

**Testing:**
- Unit tests for number cleaning and type inference
- Integration tests with Korean CSV files
- End-to-end tests for aggregate functions

## Benefits

✅ **Automatic** - No manual TRY_CAST needed
✅ **Korean-friendly** - Handles commas, currency symbols
✅ **Safe** - Uses TRY_CAST, falls back on failure
✅ **Fast** - Caches schemas for performance
✅ **Compatible** - No breaking changes to existing workflows
