# Select Subtype Complex Expression Fix

## Problem Identified
The `select` subtype processes columns by splitting on commas, which breaks complex SQL expressions containing function calls with commas (like `try_cast(amount as DECIMAL(10,2))`).

**Error**:
```
DuckDB Error: Binder Error: Referenced column "try_cast(amount as DECIMAL(10" not found in FROM clause!
```

**Root Cause**:
```python
# Backend code at line 1960 in workflows.py
cols = [c.strip() for c in config.get("columns", "").split(',') if c.strip()]
# This splits: "try_cast(amount as DECIMAL(10,2)) as amount, category"
# Into: ["try_cast(amount as DECIMAL(10", "2)) as amount", "category"]
```

## Solution Applied
Changed the problematic `select` subtype node to `raw_sql` subtype in:
- `/public/examples/ingestion/csv_auto_detect_pipeline.json`

**Before** (❌ Broken):
```json
{
  "id": "transform-2",
  "data": {
    "label": "Infer Types",
    "subtype": "select",
    "config": {
      "columns": "try_cast(amount as DECIMAL(10,2)) as amount, try_cast(date as DATE) as date, try_cast(quantity as INTEGER) as quantity, category, product_name"
    }
  }
}
```

**After** (✅ Fixed):
```json
{
  "id": "transform-2",
  "data": {
    "label": "Infer Types",
    "subtype": "raw_sql",
    "config": {
      "sql": "SELECT try_cast(amount as DECIMAL(10,2)) as amount, try_cast(date as DATE) as date, try_cast(quantity as INTEGER) as quantity, category, product_name FROM {{input}}"
    }
  }
}
```

## Verification
- ✅ Only 1 pipeline affected (csv_auto_detect_pipeline.json)
- ✅ Other pipelines with complex expressions already use `raw_sql`
- ✅ Schema evolution pipeline uses `raw_sql` (no issue)
- ✅ XML flattening pipeline uses `raw_sql` (no issue)

## Technical Note
The `select` subtype should only be used for **simple column selections** without function calls containing commas:
- ✅ **Simple selections**: `"col1, col2, col3"`
- ❌ **Complex expressions**: `"try_cast(col1 as INT), func(col2, col3)"`

For complex expressions, use the `raw_sql` subtype instead.

## Status: ✅ FIXED
**Date**: 2025-04-25
**Files Modified**: 1 pipeline JSON file
**Impact**: CSV Auto-Detection pipeline now works correctly
