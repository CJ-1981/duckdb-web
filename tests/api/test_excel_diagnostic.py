"""
Diagnostic test for Excel file loading to trace openpyxl import issues.
"""

import os
import sys
import tempfile
import traceback

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

# Check openpyxl import
try:
    import openpyxl
    print(f"✓ openpyxl version: {openpyxl.__version__}")
    print(f"✓ openpyxl location: {openpyxl.__file__}")
except ImportError as e:
    print(f"✗ openpyxl import failed: {e}")
    sys.exit(1)

# Check pandas
try:
    import pandas as pd
    print(f"✓ pandas version: {pd.__version__}")
    print(f"✓ pandas location: {pd.__file__}")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")
    sys.exit(1)

# Create a test Excel file
print("\n--- Creating test Excel file ---")
data = {'name': ['Alice', 'Bob'], 'age': [30, 25]}
df = pd.DataFrame(data)

with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
    temp_path = f.name
    df.to_excel(f.name, index=False, engine='openpyxl')
    print(f"✓ Created test file: {temp_path}")

# Try to read with pandas directly
print("\n--- Test 1: pandas.read_excel ---")
try:
    df_read = pd.read_excel(temp_path)
    print(f"✓ pandas.read_excel succeeded")
    print(f"  Columns: {list(df_read.columns)}")
    print(f"  Rows: {len(df_read)}")
except Exception as e:
    print(f"✗ pandas.read_excel failed: {e}")
    traceback.print_exc()

# Try to read with ExcelConnector
print("\n--- Test 2: ExcelConnector ---")
try:
    from src.core.connectors.excel import ExcelConnector
    connector = ExcelConnector()
    rows = list(connector.read_excel(temp_path))
    print(f"✓ ExcelConnector.read_excel succeeded")
    print(f"  Rows read: {len(rows)}")
    if rows:
        print(f"  First row columns: {list(rows[0].keys())}")
except Exception as e:
    print(f"✗ ExcelConnector.read_excel failed: {e}")
    traceback.print_exc()

# Try to read with Processor
print("\n--- Test 3: Processor.load_excel ---")
try:
    from src.core.processor import Processor
    processor = Processor()
    df_result = processor.load_excel(temp_path)
    print(f"✓ Processor.load_excel succeeded")
    print(f"  Columns: {list(df_result.columns)}")
    print(f"  Rows: {len(df_result)}")
except Exception as e:
    print(f"✗ Processor.load_excel failed: {e}")
    traceback.print_exc()

# Cleanup
os.unlink(temp_path)
print(f"\n✓ Cleaned up test file")

print("\n=== All diagnostic tests completed ===")
