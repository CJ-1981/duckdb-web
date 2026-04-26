# Sample Pipelines SQL Template Fix

## Problem Identified
Sample pipelines were failing with DuckDB syntax errors because they used incorrect SQL template placeholder format:
```
DuckDB Error: Parser Error: syntax error at or near "{"
LINE 1: ... FROM {input_table} LIMIT 10
```

## Root Cause
The backend workflow executor expects SQL template placeholders in the format `{{input}}` (double curly braces), but the sample pipelines were using `{input_table}` (single curly braces with a different name).

## Solution Applied
Created and executed `fix_sql_placeholders.py` script to:
1. Scan all 32 pipeline JSON files in `/public/examples/`
2. Replace `{input_table}` with `{{input}}` in SQL queries
3. Update 17 pipeline files with corrected SQL template syntax

## Files Fixed (17 pipelines)
1. `sample_user_enrichment_pipeline.json` - Fixed SQL in transform-1
2. `csv_auto_detect_pipeline.json` - Fixed SQL in transform-1
3. `data_validation_pipeline.json` - Fixed SQL in transform-2
4. `data_profiling_pipeline.json` - Fixed SQL in transform-1, transform-2
5. `schema_evolution_pipeline.json` - Fixed SQL in transform-3
6. `pivot_table_pipeline.json` - Fixed SQL in transform-1
7. `data_cleaning_pipeline.json` - Fixed SQL in transform-1, transform-2, transform-3
8. `parallel_processing_pipeline.json` - Fixed SQL in transform-1
9. `dynamic_parallel_tasks_pipeline.json` - Fixed SQL in transform-1
10. `conditional_branching_pipeline.json` - Fixed SQL in transform-1, transform-2, transform-3
11. `ml_inference_pipeline.json` - Fixed SQL in transform-1
12. `database_bulk_load_pipeline.json` - Fixed SQL in transform-1
13. `nested_json_flatten_pipeline.json` - Fixed SQL in transform-1
14. `xml_hierarchical_flatten_pipeline.json` - Fixed SQL in transform-1, transform-2, transform-4
15. `pipeline_failure_alerting_pipeline.json` - Fixed SQL in transform-1
16. `funnel_analysis_pipeline.json` - Fixed SQL in transform-1
17. `ab_test_analysis_pipeline.json` - Fixed SQL in transform-1, filter-1

## Template Variable Formats

### Correct Format (✓)
- `{{input}}` - Single input reference
- `{{input1}}`, `{{input2}}` - Multiple input references
- `{column_name}` - URL template variables (for batch_request nodes)

### Incorrect Format (✗)
- `{input_table}` - Old format that caused syntax errors
- `{input}` - Single braces don't work in SQL context

## Backend Processing Logic
Located in `/src/api/routes/workflows.py` at line 1698:
```python
elif subtype == "raw_sql":
    raw_sql = config.get("sql", "")
    if raw_sql:
        # Support multi-input placeholders: {{input1}}, {{input2}}, etc.
        all_preds = predecessors.get(node_id, [])
        processed_sql = raw_sql

        # Replace indexed placeholders
        for idx, pred_id in enumerate(all_preds, start=1):
            cached = _NODE_CACHE.get(pred_id)
            if cached:
                table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                processed_sql = processed_sql.replace(f"{{{{input{idx}}}}}", table_ref)

        # Backward compatible: {{input}} → first predecessor
        if "{{input}}" in processed_sql and all_preds:
            cached = _NODE_CACHE.get(all_preds[0])
            if cached:
                table_ref = f'"{cached["table_name"].replace('"', '""')}"'
                processed_sql = processed_sql.replace("{{input}}", table_ref)
```

## Testing Verification
✓ SQL placeholders now match backend expectations
✓ JSON path expressions (`response->>'$.name'`) work correctly
✓ URL template variables (`{user_id}`) remain unchanged (correct format)
✓ Multi-input pipelines use proper indexed placeholders

## Result
All 32 sample pipelines now have correct SQL template syntax and should execute without DuckDB syntax errors.

## Status: ✅ COMPLETE
**Date**: 2025-04-25
**Files Modified**: 17 pipeline JSON files
**Script**: `fix_sql_placeholders.py`
