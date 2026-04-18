"""
Diagnostic test for JSON file loading to verify JSON/JSONL support.
"""

import os
import sys
import tempfile
import traceback

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Check imports
try:
    import pandas as pd
    print(f"✓ pandas version: {pd.__version__}")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")
    sys.exit(1)

print("\n--- Test 1: Create JSON file (array of objects) ---")
data = [
    {'name': 'Alice', 'age': 30, 'city': 'NYC'},
    {'name': 'Bob', 'age': 25, 'city': 'LA'},
    {'name': 'Charlie', 'age': 35, 'city': 'SF'}
]
df = pd.DataFrame(data)

with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    temp_json = f.name
    import json
    json.dump(data, f)
    print(f"✓ Created test JSON file: {temp_json}")

print("\n--- Test 2: Create JSONL file (JSON Lines) ---")
with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    temp_jsonl = f.name
    for row in data:
        f.write(json.dumps(row) + '\n')
    print(f"✓ Created test JSONL file: {temp_jsonl}")

print("\n--- Test 3: pandas.read_json (array format) ---")
try:
    df_read = pd.read_json(temp_json)
    print(f"✓ pandas.read_json succeeded")
    print(f"  Columns: {list(df_read.columns)}")
    print(f"  Rows: {len(df_read)}")
except Exception as e:
    print(f"✗ pandas.read_json failed: {e}")
    traceback.print_exc()

print("\n--- Test 4: pandas.read_json (lines format) ---")
try:
    df_read = pd.read_json(temp_jsonl, lines=True)
    print(f"✓ pandas.read_json with lines=True succeeded")
    print(f"  Columns: {list(df_read.columns)}")
    print(f"  Rows: {len(df_read)}")
except Exception as e:
    print(f"✗ pandas.read_json with lines=True failed: {e}")
    traceback.print_exc()

print("\n--- Test 5: JSONConnector (array) ---")
try:
    from src.core.connectors.json import JSONConnector
    connector = JSONConnector()
    rows = list(connector.read_json(temp_json))
    print(f"✓ JSONConnector.read_json succeeded")
    print(f"  Rows read: {len(rows)}")
    if rows:
        print(f"  First row keys: {list(rows[0].keys())}")
except Exception as e:
    print(f"✗ JSONConnector.read_json failed: {e}")
    traceback.print_exc()

print("\n--- Test 6: JSONConnector (JSONL) ---")
try:
    from src.core.connectors.json import JSONConnector
    connector = JSONConnector()
    rows = list(connector.read_jsonl(temp_jsonl))
    print(f"✓ JSONConnector.read_jsonl succeeded")
    print(f"  Rows read: {len(rows)}")
    if rows:
        print(f"  First row keys: {list(rows[0].keys())}")
except Exception as e:
    print(f"✗ JSONConnector.read_jsonl failed: {e}")
    traceback.print_exc()

print("\n--- Test 7: Processor.load_json (array) ---")
try:
    from src.core.processor import Processor
    processor = Processor()
    df_result = processor.load_json(temp_json, format='json')
    print(f"✓ Processor.load_json (array format) succeeded")
    print(f"  Columns: {list(df_result.columns)}")
    print(f"  Rows: {len(df_result)}")
except Exception as e:
    print(f"✗ Processor.load_json (array format) failed: {e}")
    traceback.print_exc()

print("\n--- Test 8: Processor.load_json (JSONL) ---")
try:
    from src.core.processor import Processor
    processor = Processor()
    df_result = processor.load_json(temp_jsonl, format='jsonl')
    print(f"✓ Processor.load_json (JSONL format) succeeded")
    print(f"  Columns: {list(df_result.columns)}")
    print(f"  Rows: {len(df_result)}")
except Exception as e:
    print(f"✗ Processor.load_json (JSONL format) failed: {e}")
    traceback.print_exc()

print("\n--- Test 9: Nested JSON structure ---")
nested_data = [
    {'name': 'Alice', 'address': {'city': 'NYC', 'zip': '10001'}, 'hobbies': ['reading', 'coding']},
    {'name': 'Bob', 'address': {'city': 'LA', 'zip': '90001'}, 'hobbies': ['gaming']}
]
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    temp_nested = f.name
    json.dump(nested_data, f)
    print(f"✓ Created nested JSON file: {temp_nested}")

print("\n--- Test 10: JSONConnector with nested data ---")
try:
    from src.core.connectors.json import JSONConnector
    connector = JSONConnector()
    rows = list(connector.read_json(temp_nested))
    print(f"✓ JSONConnector with nested data succeeded")
    print(f"  Rows read: {len(rows)}")
    if rows:
        print(f"  Flattened keys: {list(rows[0].keys())}")
except Exception as e:
    print(f"✗ JSONConnector with nested data failed: {e}")
    traceback.print_exc()

# Cleanup
os.unlink(temp_json)
os.unlink(temp_jsonl)
os.unlink(temp_nested)
print("\n✓ Cleaned up test files")

print("\n=== All JSON diagnostic tests completed ===")
