#!/bin/bash
# Test Runner Script for DuckDB Workflow Builder
# Runs all tests including sample pipeline validation

set -e

echo "=================================="
echo "DuckDB Workflow Builder Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section header
print_section() {
    echo ""
    echo -e "${YELLOW}==================================${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}==================================${NC}"
    echo ""
}

# Function to run tests and report
run_tests() {
    local description=$1
    local command=$2

    echo -e "${GREEN}Running:${NC} $description"
    echo ""

    if eval $command; then
        echo -e "${GREEN}✓ PASSED${NC}: $description"
    else
        echo -e "${RED}✗ FAILED${NC}: $description"
        return 1
    fi
    echo ""
}

# Quick smoke tests (no external dependencies)
print_section "Phase 1: Quick Smoke Tests"
run_tests "Unit tests (fast)" "python3 -m pytest tests/unit/ -v -x -m 'not slow' --tb=short"
run_tests "Sample pipeline structure validation" "python3 -m pytest tests/integration/test_sample_pipelines.py -v --tb=short"

# Integration tests (may require database)
print_section "Phase 2: Integration Tests"
run_tests "Integration tests" "python3 -m pytest tests/integration/ -v -x --tb=short" || true

# Full test suite
print_section "Phase 3: Full Test Suite"
run_tests "All tests with coverage" "python3 -m pytest tests/ -v --cov=src --cov-report=term-missing --tb=short" || true

# Summary
print_section "Test Summary"
echo "Test execution complete!"
echo ""
echo "For detailed coverage report, run:"
echo "  python3 -m pytest tests/ --cov=src --cov-report=html"
echo "  open coverage_html_report/index.html"
echo ""
echo "For detailed test results, check the output above."
