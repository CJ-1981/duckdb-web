# CSV Connector Usage Guide

## Quick Start

### Basic Usage

```python
from src.core.connectors.csv import CSVConnector
from src.core.database import DatabaseConnection

# Create connector with default settings
connector = CSVConnector()

# Import CSV into DuckDB
db = DatabaseConnection('data.duckdb')
connector.import_to_duckdb('data.csv', db, 'my_table')

# Query the imported data
result = db.execute("SELECT * FROM my_table LIMIT 10")
print(result)
```

## Advanced Usage

### Custom Delimiter

```python
# Pipe-delimited CSV
connector = CSVConnector(delimiter='|')
connector.import_to_duckdb('data.txt', db, 'my_table')
```

### No Header Row

```python
# CSV without header (columns named col_0, col_1, etc.)
connector = CSVConnector(has_header=False)
connector.import_to_duckdb('data.csv', db, 'my_table')
```

### Custom Encoding

```python
# Latin-1 encoded CSV
connector = CSVConnector(encoding='latin-1')
connector.import_to_duckdb('data.csv', db, 'my_table')
```

### Large File Streaming

```python
# Files > 100MB automatically use streaming
connector = CSVConnector(
    streaming_threshold=50 * 1024 * 1024,  # 50MB threshold
    chunk_size=5000  # Smaller chunks
)

# Track progress
def progress_callback(progress):
    print(f"Progress: {progress['rows_processed']}/{progress['total_rows']} "
          f"({progress['percentage']:.1f}%)")

connector.import_to_duckdb(
    'large_file.csv',
    db,
    'my_table',
    progress_callback=progress_callback
)
```

## Configuration Integration

### From YAML Configuration

```yaml
# config.yaml
connectors:
  csv:
    delimiter: ','
    has_header: true
    encoding: 'utf-8'
    streaming_threshold: 104857600  # 100MB
    chunk_size: 10000
```

```python
from src.core.config.loader import Config

config = Config('config.yaml').load()
connector = CSVConnector.from_config(config)
```

## CSV Reading

### Read CSV File

```python
connector = CSVConnector()

# Read all rows
rows = list(connector.read_csv('data.csv'))
for row in rows:
    print(row)

# Stream large files in chunks
for chunk in connector.stream_csv('large_file.csv'):
    print(f"Processing chunk of {len(chunk)} rows")
    for row in chunk:
        process(row)
```

## Schema Inference

### Get CSV Schema

```python
connector = CSVConnector()

# Infer schema before importing
schema = connector.infer_schema('data.csv')
print(schema)
# Output: {'id': 'INTEGER', 'name': 'VARCHAR', 'amount': 'FLOAT', ...}
```

### Get File Statistics

```python
stats = connector.get_statistics('data.csv')
print(f"Rows: {stats['row_count']}")
print(f"Columns: {stats['column_count']}")
print(f"Size: {stats['file_size_mb']:.2f} MB")
```

## Missing Value Handling

The CSV connector automatically handles these missing value representations:
- Empty strings: `''`
- NULL variations: `'NULL'`, `'null'`, `'None'`, `'none'`
- NA variations: `'NA'`, `'N/A'`, `'na'`
- NaN variations: `'NaN'`, `'nan'`

All missing values are converted to `None` for DuckDB.

### Example

```python
# CSV with missing values
csv_data = '''id,name,value
1,Alice,100
2,Bob,
3,Charlie,NA
4,,300
'''

connector = CSVConnector()
connector.import_to_duckdb('data.csv', db, 'my_table')

# Query shows NULL for missing values
result = db.execute("SELECT * FROM my_table WHERE name IS NULL")
# Returns: [{'id': 4, 'name': None, 'value': '300'}]
```

## Type Inference

The connector automatically infers DuckDB data types:

| Pattern | Inferred Type |
|---------|--------------|
| `1`, `2`, `100` | INTEGER |
| `1.5`, `2.75`, `3.99` | FLOAT |
| `true`, `false`, `TRUE`, `FALSE` | BOOLEAN |
| `2023-01-15`, `2023-02-20` | DATE |
| Any other text | VARCHAR |

### Custom Type Handling

```python
# Import with automatic type inference
connector.import_to_duckdb('data.csv', db, 'my_table')

# Check inferred schema
schema = db.execute("DESCRIBE my_table")
for row in schema:
    print(f"{row['column_name']}: {row['column_type']}")
```

## Error Handling

### File Validation

```python
connector = CSVConnector()

try:
    connector.validate_csv_path('data.csv')
    print("CSV is valid")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Invalid CSV: {e}")
```

### Import Error Handling

```python
from src.core.database.exceptions import QueryExecutionError

try:
    connector.import_to_duckdb('data.csv', db, 'my_table')
except QueryExecutionError as e:
    print(f"Import failed: {e}")
except FileNotFoundError:
    print("CSV file not found")
```

## Performance Tips

### For Large Files

1. **Use appropriate streaming threshold**:
   ```python
   # Default: 100MB
   connector = CSVConnector(streaming_threshold=50 * 1024 * 1024)
   ```

2. **Adjust chunk size**:
   ```python
   # Smaller chunks = lower memory usage
   connector = CSVConnector(chunk_size=5000)
   ```

3. **Monitor progress**:
   ```python
   def progress_callback(progress):
       print(f"{progress['percentage']:.1f}% complete")

   connector.import_to_duckdb(
       'large_file.csv',
       db,
       'my_table',
       progress_callback=progress_callback
   )
   ```

### For Many Small Files

```python
# Reuse connector instance
connector = CSVConnector()

for file_path in csv_files:
    table_name = Path(file_path).stem
    connector.import_to_duckdb(file_path, db, table_name)
```

## Integration Examples

### With Configuration System

```python
from src.core.config.loader import Config
from src.core.connectors.csv import CSVConnector
from src.core.database import DatabaseConnection

# Load configuration
config = Config('config.yaml').load()

# Create components
db = DatabaseConnection.from_config(config)
connector = CSVConnector.from_config(config)

# Import data
connector.import_to_duckdb('data.csv', db, 'my_table')
```

### With Plugin System

```python
from src.core.connectors import get_connector

# Get connector class from registry
CSVConnector = get_connector('csv')

# Create and use connector
connector = CSVConnector(delimiter='|')
connector.import_to_duckdb('data.txt', db, 'my_table')
```

## Best Practices

1. **Always validate CSV files** before importing:
   ```python
   connector.validate_csv_path('data.csv')
   ```

2. **Check schema** before importing large files:
   ```python
   schema = connector.infer_schema('data.csv')
   print(schema)
   ```

3. **Use streaming** for files > 100MB (automatic)
4. **Handle missing values** explicitly in queries:
   ```python
   db.execute("SELECT * FROM table WHERE col IS NOT NULL")
   ```
5. **Close database connections** when done:
   ```python
   db.close()
   ```

## Troubleshooting

### Common Issues

**Issue**: "Empty CSV file" error
- **Solution**: Check file has data and correct path

**Issue**: "Conversion Error" during import
- **Solution**: Check for inconsistent data types in columns

**Issue**: Poor performance on large files
- **Solution**: Reduce `chunk_size` or lower `streaming_threshold`

**Issue**: Special characters not displayed correctly
- **Solution**: Specify correct encoding: `CSVConnector(encoding='latin-1')`

## API Reference

See implementation docstrings for complete API:
- `CSVConnector.__init__()` - Initialize connector
- `CSVConnector.read_csv()` - Read CSV file
- `CSVConnector.stream_csv()` - Stream CSV in chunks
- `CSVConnector.import_to_duckdb()` - Import to DuckDB
- `CSVConnector.infer_schema()` - Infer column types
- `CSVConnector.get_statistics()` - Get file statistics
- `CSVConnector.validate_csv_path()` - Validate CSV file

---

For more information, see:
- Implementation Summary: `P1-T004_IMPLEMENTATION_SUMMARY.md`
- Unit Tests: `tests/unit/test_csv_connector.py`
- Integration Tests: `tests/integration/test_csv_processing.py`
