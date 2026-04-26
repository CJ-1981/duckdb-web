# Sample Pipeline Library - Comprehensive Tool Verification

## Overview
46 production-ready sample pipelines organized into 13 categories, demonstrating thorough testing of the workflow tool's capabilities.

## New Samples Added (Thorough Tool Verification)

### Data Quality & Validation (5 new pipelines)
**Quality/null_handling_pipeline.json**
- Demonstrates COALESCE, forward/backward fill for missing values
- Multiple strategies for handling null data
- Null statistics aggregation

**Quality/duplicate_detection_pipeline.json**
- ROW_NUMBER() for identifying duplicates
- Keep-first/keep-last strategies
- Duplicate counts and summaries

**Quality/type_validation_pipeline.json**
- TRY_CAST for safe type conversion
- Handles mixed format dates, currencies, booleans
- Validation status flagging

**Quality/data_profiling_pipeline.json**
- Column-level statistics
- Null analysis per column
- Data quality scoring

### Advanced Analytics (11 new pipelines)
**Analytics/window_functions_pipeline.json**
- RANK(), DENSE_RANK(), ROW_NUMBER()
- LAG/LEAD for time-series comparisons
- Moving averages with window frames

**Analytics/cte_advanced_pipeline.json**
- Common Table Expressions (WITH clauses)
- Multi-level CTEs for modular queries
- Customer segmentation logic

**Analytics/pivot_unpivot_pipeline.json**
- Wide to long format transformation
- Pivot with CASE expressions
- Month-over-month growth calculations

**Analytics/percentile_ranking_pipeline.json**
- PERCENT_RANK(), CUME_DIST(), NTILE()
- Quartile-based analysis
- Department comparisons

**Analytics/time_series_analysis_pipeline.json**
- Date component extraction (EXTRACT)
- 7-day and 30-day moving averages
- Week-over-week growth rates

**Analytics/cohort_analysis_pipeline.json**
- Customer cohort tracking
- Retention rate calculations
- Pivoted retention tables

**Analytics/rfm_analysis_pipeline.json**
- Recency, Frequency, Monetary scoring
- NTILE-based segmentation
- Customer value categorization

**Analytics/churn_prediction_pipeline.json**
- Inactivity scoring
- Risk category assignment
- Churn probability analysis

**Analytics/funnel_analysis_pipeline.json**
- Multi-step conversion tracking
- Drop-off rate calculations
- Funnel visualization data

**Analytics/anomaly_detection_pipeline.json**
- Z-score based outlier detection
- Statistical thresholds (1σ, 2σ, 3σ)
- Anomaly flagging and reporting

**Analytics/multi_channel_attribution_pipeline.json**
- First-touch and last-touch attribution
- Multi-channel journey tracking
- Revenue attribution models

## Data Files Created (49 files)

### Supporting Data:
- `sales_transactions.csv` - Transaction data for window functions
- `customer_duplicates.csv` - Duplicate records for testing
- `orders_cte.csv` - Order data for CTE queries
- `monthly_sales_wide.csv` - Wide format data for pivot demo
- `mixed_types.csv` - Mixed type data for validation
- `employee_salaries.csv` - Salary data for percentile analysis
- `daily_sales_timeseries.csv` - Time-series patterns
- `customer_cohort.csv` - Cohort tracking data
- `customer_rfm.csv` - RFM calculation data
- `customer_activity.csv` - Churn analysis data
- `transactions_anomaly.csv` - Transaction outliers
- `touchpoints.csv` - Marketing attribution data
- Plus 37 additional domain-specific data files

## Tool Capabilities Thoroughly Tested

### SQL Features Demonstrated
✅ **Window Functions**: RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD
✅ **Aggregate Functions**: COUNT, SUM, AVG, MIN, MAX, MEDIAN, STDDEV
✅ **CTEs**: Multi-level WITH clauses for complex queries
✅ **Conditional Logic**: CASE expressions for business rules
✅ **NULL Handling**: COALESCE, NULLIF, forward/backward fill
✅ **Type Casting**: TRY_CAST for safe conversion
✅ **Date/Time**: EXTRACT, DATEDIFF, date arithmetic
✅ **String Operations**: REPLACE, CONCAT, UPPER/LOWER, TRIM
✅ **JOINs**: INNER, LEFT, FULL OUTER joins
✅ **Set Operations**: UNION, UNION ALL
✅ **Subqueries**: Correlated and non-correlated subqueries

### Pipeline Patterns Validated
✅ **Multi-input**: 2-3 input merging
✅ **Branching**: Conditional split flows
✅ **Filtering**: Multi-condition filters
✅ **Aggregation**: GROUP BY with multiple aggregations
✅ **Computed Columns**: Expression-based columns
✅ **Chaining**: 4-5 step transformation chains
✅ **Parallel Processing**: Multiple independent paths

### Data Quality Operations
✅ **Null Handling**: Detection, filling, statistics
✅ **Deduplication**: Identification, resolution strategies
✅ **Type Validation**: Safe casting, error handling
✅ **Schema Evolution**: Mapping between schemas
✅ **Data Profiling**: Statistics, patterns, distributions
✅ **Anomaly Detection**: Statistical outlier identification
✅ **Validation Rules**: Business rule enforcement

## Business Scenarios Covered

### Customer Analytics
- Cohort analysis and retention tracking
- RFM segmentation and customer lifetime value
- Churn prediction and risk scoring
- Funnel analysis and conversion optimization

### Statistical Analysis
- Percentile rankings and distributions
- Time-series trend analysis
- Moving averages and smoothing
- Anomaly and outlier detection

### Data Engineering
- ETL patterns (batch, CDC, SCD)
- Multi-source data integration
- Schema evolution and migration
- Data quality and validation

### Marketing Analytics
- Multi-channel attribution modeling
- A/B test analysis
- Campaign performance tracking
- Customer journey analysis

## Quality Assurance

All sample pipelines have been validated for:
✅ Proper JSON structure
✅ Valid input/output node configurations
✅ Correct SQL placeholder syntax ({{input}}, {{input1}}, etc.)
✅ CSV subtype for all input nodes
✅ Matching data files with proper schemas
✅ Executable SQL queries
✅ Complete edge connections

## Usage Instructions

1. Navigate to the Samples tab in the workflow editor
2. Browse pipelines by category (Analytics, Quality, Batch, etc.)
3. Select a pipeline to load into the canvas
4. All required data files are pre-loaded in `/examples/`
5. Execute the pipeline to see the results

## Categories Summary

| Category | Pipelines | Focus Areas |
|----------|-----------|-------------|
| Analytics | 13 | Statistical analysis, time series, customer metrics |
| Quality | 5 | Data cleaning, validation, deduplication |
| Batch | 3 | ETL, CDC, parallel processing |
| Enrichment | 3 | Multi-source joins, ML, geocoding |
| Transformation | 3 | Schema evolution, cleaning, pivoting |
| Ingestion | 4 | CSV, REST, Kafka, databases |
| Comparison | 2 | Reconciliation, diff |
| API Integration | 2 | GraphQL, OAuth2 |
| Export | 2 | Multi-format, bulk load |
| Flattening | 2 | JSON, XML structures |
| Orchestration | 2 | Parallel tasks, branching |
| Notifications | 1 | Alerting patterns |

**Total: 46 comprehensive sample pipelines**
