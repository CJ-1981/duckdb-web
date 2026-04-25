# Sample Workflow Pipelines

This directory contains sample workflow pipelines that demonstrate the batch request functionality and other workflow features.

## Available Pipelines

### 1. User Profile Enrichment Pipeline (`sample_user_enrichment_pipeline.json`)

**Description**: Basic batch request example that fetches user profiles from JSONPlaceholder API.

**Features Demonstrated**:
- CSV input with user IDs
- Single variable URL substitution: `{user_id}`
- Parallel API requests (5 concurrent)
- Response field extraction with SQL
- Output filtering (keep only successful responses)

**Input File**: `users_input.csv`

**Expected Output**: Enriched user profiles with names, emails, companies, and websites.

---

### 2. E-Commerce Product Scraper (`ecommerce_product_pipeline.json`)

**Description**: Advanced product scraping with multi-variable substitution, filtering, and analytics.

**Features Demonstrated**:
- Multi-variable URL substitution: `{product_id}`, `{region}`, `{variant_type}`
- Complex output filtering (price > 10, rating > 3)
- Field selection and transformation
- Computed fields (price with tax calculation)
- Category-based aggregation
- High-value product filtering

**Input File**: `products_input.csv`

**Expected Output**: Product analytics with category statistics and filtered high-value items.

---

### 3. Social Media Analytics Pipeline (`social_media_pipeline.json`)

**Description**: Complex pipeline demonstrating multi-variable substitution in URLs, query parameters, and headers.

**Features Demonstrated**:
- Multi-variable URL with query params: `{post_id}`, `{comment_type}`, `{limit}`
- Custom header substitution: `{request_id}`, `{tenant_id}`
- Array unnesting (flattening comments)
- Multiple filtering stages
- Aggregation and sorting
- Top N limiting

**Input File**: `social_posts_input.csv`

**Expected Output**: Top 10 most commented posts with analytics.

---

## How to Use These Pipelines

### Option 1: Import via Canvas UI

1. Navigate to the workflow canvas in your browser
2. Click the "Import" or "Load Workflow" button
3. Select one of the JSON pipeline files from this directory
4. The canvas will render the workflow with all nodes and edges

### Option 2: Manual Node Configuration

1. Create a new workflow in the canvas
2. Add nodes manually following the structure in the JSON files
3. Configure each node with the specified parameters
4. Connect nodes with edges

### Option 3: API Usage

```python
import requests

# Load pipeline
with open('sample_user_enrichment_pipeline.json', 'r') as f:
    pipeline = json.load(f)

# Submit for execution
response = requests.post(
    'http://localhost:8000/api/v1/workflows/execute',
    json=pipeline,
    headers={'Content-Type': 'application/json'}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Row count: {result.get('row_count')}")
```

---

## Pipeline Structure Reference

### Node Types

**Input Nodes**:
- `csv`: Load CSV file
- `parquet`: Load Parquet file
- `json`: Load JSON file
- `remote_file`: Load from URL (httpfs)
- `rest_api`: REST API ingestion
- `web_scraper`: HTML scraping

**Transform Nodes**:
- `batch_request`: Parallel web scraping with variable substitution
- `filter`: Filter rows based on conditions
- `select`: Select specific columns
- `aggregate`: Group and aggregate
- `sort`: Sort rows
- `limit`: Limit row count
- `computed`: Add calculated columns
- `raw_sql`: Execute custom SQL
- `combine`: Join/union datasets

**Output Nodes**:
- `db_write`: Save to database table
- `export`: Export to file

### Edge Connections

Edges connect nodes and define data flow:
- `source`: Source node ID
- `target`: Target node ID
- `sourceHandle`: Output position ("right", "bottom")
- `targetHandle`: Input position ("left", "top")

---

## Batch Request Configuration

### URL Template Substitution

Use `{variable_name}` placeholders that will be replaced with values from your input data:

```json
{
  "url_template": "https://api.example.com/{tenant}/users/{user_id}/posts/{post_id}?type={category}"
}
```

**Supported Variables**:
- Path parameters: `/{user_id}/`
- Query parameters: `?type={category}&sort={order}`
- Header values: `"X-Tenant-ID": "{tenant_id}"`

### Authentication

```json
{
  "auth_type": "bearer",
  "token": "your_bearer_token",
  "refresh_token": "your_refresh_token",
  "token_endpoint": "https://auth.example.com/oauth/refresh"
}
```

**Supported Auth Types**:
- `bearer`: Bearer token authentication
- `api_key`: API key in header
- `basic`: Basic authentication

### Performance Tuning

```json
{
  "concurrency": 50,
  "rate_limit": {
    "requests_per_second": 100,
    "burst": 10
  },
  "timeout": 30,
  "retry_policy": {
    "max_retries": 3,
    "base_delay": 1.0,
    "max_delay": 60.0
  }
}
```

**Performance Guidelines**:
- `concurrency`: 10-100 (default: 50)
- `rate_limit`: Match API limits
- `timeout`: 10-120 seconds (default: 30)
- `max_retries`: 1-5 (default: 3)

### Output Filtering

```json
{
  "output_filter": {
    "mode": "include",
    "conditions": [
      {
        "field": "response.status",
        "operator": "==",
        "value": 200
      },
      {
        "field": "response.data.price",
        "operator": ">",
        "value": 100
      }
    ]
  }
}
```

**Filter Modes**:
- `include`: Keep rows that match ALL conditions (AND logic)
- `exclude`: Remove rows that match ANY condition (OR logic)

**Supported Operators**:
- Comparison: `==`, `!=`, `>`, `<`, `>=`, `<=`
- Membership: `in`, `not_in`
- String: `contains`, `not_contains`
- Regex: `matches`, `not_matches`
- Null checks: `is_null`, `is_not_null`
- Key existence: `has_key`

---

## Error Handling

The batch request system includes comprehensive error handling:

### Automatic Retry
- Transient errors: Network blips, rate limits (429)
- Server errors: 500, 502, 503, 504
- Exponential backoff with jitter

### Dead Letter Queue
Failed requests are exported to `dead_letter_queue_<timestamp>.json` with:
- Error details and classification
- Original input data
- Retry eligibility flag

### Error Categories
- `transient`: Retryable network issues
- `recoverable`: Token expiry, auth failures
- `permanent`: 404, malformed requests
- `catastrophic`: No network, invalid config

---

## Tips for Production Use

1. **Start Small**: Test with 10-100 requests before scaling to 10k+
2. **Monitor Rate Limits**: Check API documentation for rate limits
3. **Use Filters**: Apply output filters early to reduce data volume
4. **Set Timeouts**: Adjust `timeout` based on API response times
5. **Check Dead Letter Queue**: Review failed requests and adjust filters
6. **Token Refresh**: Use refresh tokens for long-running workflows
7. **Progress Tracking**: Use `progress_callback` for long-running jobs

---

## Troubleshooting

### Common Issues

**Circuit Breaker Opens**:
- Symptom: Requests stop after several failures
- Cause: API endpoint is returning consistent errors
- Solution: Check API status, fix authentication, or wait for circuit breaker timeout (60s)

**High Memory Usage**:
- Symptom: Memory grows with large result sets
- Solution: Use `limit` nodes to restrict output size, add filters early

**Slow Execution**:
- Symptom: Pipeline takes too long
- Solution: Increase `concurrency`, adjust `rate_limit`, or reduce `timeout`

**Token Expiry**:
- Symptom: 401 errors after some time
- Solution: Configure `refresh_token` and `token_endpoint` for auto-refresh

---

## Additional Resources

- Workflow API Documentation: `/docs/api/workflows.md`
- Batch Request Implementation: `src/workflow/batch_executor.py`
- Output Filter Implementation: `src/workflow/output_filter.py`
- Integration Tests: `tests/integration/test_workflow_execution.py`
