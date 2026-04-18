#!/bin/bash

# Verify Excel support setup for DuckDB Data Processor

echo "=== Verifying Excel Support Setup ==="
echo ""

# 1. Check if we're using the venv
echo "1. Checking Python environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    PYTHON_EXE=".venv/bin/python"
    echo "   ✓ Virtual environment found"
else
    PYTHON_EXE="python"
    echo "   ⚠ No virtual environment found, using system Python"
fi

# 2. Check Python version
PYTHON_VERSION=$($PYTHON_EXE --version 2>&1)
echo "   Python version: $PYTHON_VERSION"

# 3. Check openpyxl
echo ""
echo "2. Checking openpyxl..."
$PYTHON_EXE -c "import openpyxl; print(f'   ✓ openpyxl {openpyxl.__version__} installed')" 2>&1 || {
    echo "   ✗ openpyxl NOT installed"
    echo "   Installing openpyxl..."
    $PYTHON_EXE -m pip install openpyxl
}

# 4. Check pandas
echo ""
echo "3. Checking pandas..."
$PYTHON_EXE -c "import pandas; print(f'   ✓ pandas {pandas.__version__} installed')" 2>&1 || {
    echo "   ✗ pandas NOT installed"
}

# 5. Check uvicorn
echo ""
echo "4. Checking uvicorn..."
$PYTHON_EXE -m uvicorn --version 2>&1 | head -1 || {
    echo "   ✗ uvicorn NOT installed in venv"
    echo "   Installing uvicorn..."
    $PYTHON_EXE -m pip install uvicorn
}

# 6. Test Excel file reading
echo ""
echo "5. Testing Excel file reading..."
TEST_OUTPUT=$($PYTHON_EXE -c "
import tempfile
import pandas as pd
import os

data = {'name': ['Alice', 'Bob'], 'age': [30, 25]}
df = pd.DataFrame(data)

with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
    temp_path = f.name
    df.to_excel(f.name, index=False)

df_read = pd.read_excel(temp_path)
os.unlink(temp_path)
print('✓ Excel file read test passed')
" 2>&1)

echo "   $TEST_OUTPUT"

# 7. Test Processor
echo ""
echo "6. Testing Processor.load_excel..."
TEST_OUTPUT=$($PYTHON_EXE -c "
import sys
sys.path.insert(0, '/Users/chimin/Documents/script/duckdb-web')
from src.core.processor import Processor
import tempfile
import pandas as pd
import os

data = {'name': ['Alice', 'Bob'], 'age': [30, 25]}
df = pd.DataFrame(data)

with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as f:
    temp_path = f.name
    df.to_excel(f.name, index=False)

processor = Processor()
df_result = processor.load_excel(temp_path)
os.unlink(temp_path)
print(f'✓ Processor.load_excel test passed ({len(df_result)} rows, {len(df_result.columns)} columns)')
" 2>&1)

echo "   $TEST_OUTPUT"

echo ""
echo "=== Verification Complete ==="
echo ""
echo "If all tests passed, Excel support is working correctly."
echo "Start the server with: ./run.sh"
