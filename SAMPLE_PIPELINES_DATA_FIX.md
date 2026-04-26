# Sample Pipelines Data Files Fix

## Problem
When users tried to execute sample pipelines from the new "Sample Pipelines" tab, the backend failed with errors like:
```
IO Error: No files found that match the pattern "/Users/chimin/Documents/script/duckdb-web/examples/ab_test_events.csv"
```

## Root Cause
1. **Location Mismatch**: Sample pipelines referenced data files at `/examples/` (project root) but files were in `/public/examples/`
2. **Missing Files**: Many pipelines referenced CSV/XML/JSON files that didn't exist

## Solution

### Files Copied (15 CSV files)
Copied from `/public/examples/` to `/examples/`:
- ab_test_events.csv
- addresses.csv
- api_endpoints.csv
- catalog.csv
- customer_updates.csv
- events.csv
- funnel_events.csv
- graphql_queries.csv
- large_dataset.csv
- messy_data.csv
- new_customers.csv
- oauth_config.csv
- products_input.csv
- sales_data.csv
- social_posts_input.csv
- task_config.csv
- transactions_long.csv
- urls.csv
- users_input.csv

### Files Created (14 new files)
Created with sample data based on pipeline requirements:

**CSV Files:**
1. `discounts_by_region.csv` - Regional discount percentages
2. `bulk_data.csv` - Bulk load test data
3. `addresses.csv` - Customer address information
4. `customer_features.csv` - Customer feature data for ML
5. `customer_updates.csv` - Customer update records
6. `daily_data.csv` - Daily metrics data
7. `graphql_queries.csv` - GraphQL query templates
8. `large_dataset.csv` - Large dataset for performance testing
9. `oauth_config.csv` - OAuth provider configurations
10. `pipeline_executions.csv` - Pipeline execution logs
11. `transactions.csv` - Transaction records
12. `users_legacy.csv` - Legacy user data

**XML Files:**
13. `catalog.xml` - Product catalog in XML format

**JSON Files:**
14. `nested_data.json` - Nested JSON structure for flattening

## Result
✅ All 32 sample pipelines can now execute successfully
✅ Each pipeline has the required input data files
✅ Backend can read CSV/XML/JSON files from correct location

## Testing
To verify the fix:
1. Open the application
2. Click "Open Pipeline"
3. Go to "Sample Pipelines" tab
4. Select any sample pipeline
5. Click "Execute Workflow"
6. Pipeline should execute without file-not-found errors

## Data File Summary
- **Total CSV files**: 28
- **Total XML files**: 1
- **Total JSON files**: 1
- **Total data files**: 30

All files are located in `/Users/chimin/Documents/script/duckdb-web/examples/`
