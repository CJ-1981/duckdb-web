# DuckDB Workflow Builder - User Guide

## File Upload Support

The platform supports multiple file formats for data import:

### Supported File Formats

| Format | Extensions | Max Size | Features |
|--------|-----------|----------|----------|
| **CSV** | .csv | 1GB | Encoding detection, custom delimiters |
| **Excel** | .xlsx, .xls | 1GB | Multiple sheets, header row selection |
| **JSON** | .json, .jsonl | 1GB | Nested structures, JSONL format |
| **Parquet** | .parquet | 1GB | Compression detection, column pruning |

### CSV Upload

**Features:**
- Automatic encoding detection (UTF-8, UTF-8-sig, CP949, EUC-KR)
- Custom delimiter support (comma, tab, pipe, semicolon)
- Header detection and validation
- Missing value handling (NULL, empty, NA, NaN)

**Usage:**
1. Click "Upload Data" or drag a CSV file onto the canvas
2. Select the file from your system
3. The system automatically detects encoding and schema
4. Data is loaded into a new input node

### Excel Upload

**Features:**
- Support for .xlsx and .xls formats
- Multiple sheet selection
- Custom header row configuration
- Data type preservation

**Usage:**
1. Select an Excel file (.xlsx or .xls)
2. Choose the sheet to import (first sheet by default)
3. Specify which row contains headers (row 0 by default)
4. Data is loaded with proper type inference

### JSON Upload

**Features:**
- JSON array format
- JSONL (JSON Lines) format
- Nested structure handling
- Unicode and special character support

**JSON Array Format:**
```json
[
  {"id": 1, "name": "Alice", "value": 100},
  {"id": 2, "name": "Bob", "value": 200}
]
```

**JSONL Format (one JSON per line):**
```json
{"id": 1, "name": "Alice", "value": 100}
{"id": 2, "name": "Bob", "value": 200}
{"id": 3, "name": "Charlie", "value": 300}
```

### Parquet Upload

**Features:**
- Automatic compression detection
- Support for snappy, gzip, brotli, lz4, zstd
- Column pruning (select specific columns)
- Efficient for large datasets

**Supported Compression:**
- Snappy (.snappy.parquet)
- Gzip (.gz.parquet)
- Brotli (.br.parquet)
- LZ4 (.lz4.parquet)
- Zstandard (.zst.parquet)
- Uncompressed (.parquet)

## Data Transformations

### Group By (Aggregation)

Aggregate data across groups using various functions.

**Available Functions:**
- `SUM` - Sum of values
- `AVG` - Average value
- `MIN` - Minimum value
- `MAX` - Maximum value
- `COUNT` - Count of values

**SQL Example:**
```sql
SELECT category, SUM(sales) as sum_sales
FROM data
GROUP BY category
```

**Processor Usage:**
```python
processor.group_by(
    group_columns=['category', 'region'],
    agg_column='sales',
    func='SUM'
)
```

### Join (Merge)

Combine data from multiple tables using various join types.

**Join Types:**
- `INNER` - Only matching rows
- `LEFT` - All rows from left table, matches from right
- `RIGHT` - All rows from right table, matches from left
- `OUTER` - All rows from both tables
- `CROSS` - Cartesian product

**SQL Example:**
```sql
SELECT *
FROM customers t1
INNER JOIN orders t2
ON t1.customer_id = t2.customer_id
```

**Processor Usage:**
```python
processor.merge(
    other_table='orders',
    on=['customer_id'],
    how='inner'
)
```

### Window Functions

Perform calculations across related rows.

**Available Functions:**
- `ROW_NUMBER` - Sequential row numbers
- `RANK` - Ranking with ties
- `DENSE_RANK` - Dense ranking
- `LAG` - Value from previous row
- `LEAD` - Value from next row
- `SUM`, `AVG`, `MIN`, `MAX` - Running aggregates

**SQL Example:**
```sql
SELECT *,
       ROW_NUMBER() OVER (PARTITION BY category ORDER BY date) as row_num
FROM data
```

**Processor Usage:**
```python
processor.window(
    func='ROW_NUMBER',
    over_column='date',
    partition_by=['category']
)
```

**Running Total Example:**
```python
processor.window(
    func='SUM',
    over_column='sales',
    partition_by=['region'],
    alias='running_total'
)
```

### Rolling Aggregates

Calculate moving averages and sums over a window of rows.

**Available Functions:**
- `SUM` - Rolling sum
- `AVG` - Rolling average (moving average)
- `MIN` - Rolling minimum
- `MAX` - Rolling maximum

**Processor Usage:**
```python
# 3-period moving average
processor.rolling_aggregate(
    agg_column='value',
    func='AVG',
    window_size=3
)

# Rolling sum by category
processor.rolling_aggregate(
    agg_column='sales',
    func='SUM',
    window_size=7,
    partition_by=['product_category']
)
```

### Pivot Tables

Create cross-tabulation views of your data.

**SQL Example:**
```sql
SELECT region,
       SUM(CASE WHEN product='A' THEN sales ELSE 0 END) as A,
       SUM(CASE WHEN product='B' THEN sales ELSE 0 END) as B
FROM data
GROUP BY region
```

## API Data Loading

Load data directly from REST API endpoints.

### Authentication Methods

**Bearer Token:**
```python
processor.load_api(
    'https://api.example.com/users',
    auth_type='bearer',
    token='your_token_here'
)
```

**API Key:**
```python
processor.load_api(
    'https://api.example.com/data',
    auth_type='api_key',
    api_key='your_api_key',
    api_key_header='X-API-Key'  # Custom header name
)
```

**Basic Authentication:**
```python
processor.load_api(
    'https://api.example.com/secure',
    auth_type='basic',
    username='user@example.com',
    password='password123'
)
```

### Pagination

**Offset-based Pagination:**
```python
processor.load_api(
    'https://api.example.com/items',
    pagination='offset',
    max_pages=5
)
```

### Custom Headers

```python
processor.load_api(
    'https://api.example.com/data',
    headers={
        'User-Agent': 'MyApp/1.0',
        'Accept': 'application/json'
    }
)
```

### Data Path Extraction

For APIs that return nested structures:

```python
processor.load_api(
    'https://api.example.com/data',
    data_path='response.data.items'  # Extract nested array
)
```

### Query Parameters

```python
processor.load_api(
    'https://api.example.com/search',
    params={'query': 'python', 'limit': 100}
)
```

## Complete Workflow Example

Here's a complete example workflow:

1. **Upload Excel file** with sales data
2. **Upload Parquet file** with customer data
3. **Join** the tables on customer_id
4. **Group by** region to calculate total sales
5. **Apply window function** to rank regions by sales
6. **Calculate** 7-day rolling average
7. **Export** results as CSV

**Result:** A comprehensive sales analysis dashboard combining multiple data sources with advanced analytics.

## Tips and Best Practices

### File Upload
- Use CSV for small datasets with simple structure
- Use Excel when you need to preserve formatting or multiple sheets
- Use JSON for nested or hierarchical data
- Use Parquet for large datasets or when performance is critical

### Data Transformations
- Use group_by for categorical aggregation
- Use merge when you need to combine related datasets
- Use window functions for time-series analysis
- Use rolling_aggregates for moving averages and trends

### API Loading
- Always check API authentication requirements
- Use pagination for large datasets
- Implement retry logic for unreliable APIs
- Cache API responses when possible

### Performance
- Parquet files are fastest for large datasets
- Use column pruning to only load needed columns
- Apply filters early in the workflow
- Use streaming for files larger than 100MB

## Error Handling

### Common Issues

**"File format not supported"**
- Check that the file extension matches the format
- Verify the file is not corrupted

**"Encoding error"**
- Try saving the CSV with UTF-8 encoding
- Use a text editor to convert the file encoding

**"API authentication failed"**
- Verify your API token/key is valid
- Check that auth_type matches the API requirements

**"Memory limit exceeded"**
- Use Parquet format for better compression
- Apply filters to reduce data size
- Use streaming mode for large files

## Support

For issues or questions:
1. Check the test files for usage examples
2. Review the API documentation
3. Check the GitHub issues for similar problems
