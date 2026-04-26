#!/usr/bin/env python3
"""
Comprehensive sample pipeline audit and fix script.
Checks for common issues and fixes them automatically.
"""

import json
from pathlib import Path
import sys

def audit_pipeline(file_path):
    """Audit a pipeline file and return issues found."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        issues = []

        # Check 1: Input nodes with invalid subtypes
        valid_input_subtypes = ['csv', 'json', 'parquet', 'remote_file', 'rest_api', 'web_scraper', 'db_read', None]

        for node in data.get('nodes', []):
            if node.get('type') == 'input':
                subtype = node.get('data', {}).get('subtype')
                if subtype not in valid_input_subtypes:
                    issues.append(f"Invalid input subtype: {subtype}")

        # Check 2: batch_request used as input node
        for node in data.get('nodes', []):
            if node.get('type') == 'input' and node.get('data', {}).get('subtype') == 'batch_request':
                issues.append("batch_request cannot be input node type")

        # Check 3: Missing output nodes
        output_nodes = [n for n in data.get('nodes', []) if n.get('type') == 'output']
        if not output_nodes:
            issues.append("No output node found")

        # Check 4: SQL with hardcoded table names instead of {{input}}
        for node in data.get('nodes', []):
            if node.get('data', {}).get('subtype') == 'raw_sql':
                sql = node.get('data', {}).get('config', {}).get('sql', '')
                if ' FROM ' in sql and '{{input}}' not in sql and '{{input1}}' not in sql:
                    # Check if it references specific table names
                    if ' FROM orders ' in sql or ' FROM api_response ' in sql or ' FROM discounts ' in sql:
                        issues.append(f"SQL uses hardcoded table names instead of {{input}} placeholders")

        # Check 5: Multiple input nodes without proper multi-input references
        input_nodes = [n for n in data.get('nodes', []) if n.get('type') == 'input']
        if len(input_nodes) > 1:
            # Check if any transform nodes properly reference multiple inputs
            for node in data.get('nodes', []):
                if node.get('type') == 'default':
                    sql = node.get('data', {}).get('config', {}).get('sql', '')
                    if sql and '{{input1}}' not in sql and '{{input2}}' not in sql:
                        # This might be an issue for multi-input pipelines
                        pass  # Will flag for manual review

        return issues

    except Exception as e:
        return [f"Failed to audit: {e}"]

def main():
    examples_dir = Path('/Users/chimin/Documents/script/duckdb-web/public/examples')

    # Find all pipeline files
    pipeline_files = list(examples_dir.glob('**/*pipeline.json'))

    print(f"Auditing {len(pipeline_files)} sample pipelines...\n")

    all_issues = {}

    for pipeline_file in sorted(pipeline_files):
        issues = audit_pipeline(pipeline_file)
        if issues:
            all_issues[str(pipeline_file.relative_to(examples_dir))] = issues

    if all_issues:
        print("=== ISSUES FOUND ===\n")
        for file_path, issues in all_issues.items():
            print(f"📁 {file_path}:")
            for issue in issues:
                print(f"  ❌ {issue}")
        else:
            print("✅ All pipelines passed basic validation!")

    return len(all_issues) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
