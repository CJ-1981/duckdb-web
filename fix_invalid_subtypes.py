#!/usr/bin/env python3
"""
Fix invalid input subtypes in sample pipelines.
Replaces postgres, kafka, and batch_request (as input) with csv subtype.
"""

import json
from pathlib import Path

def fix_pipeline_file(file_path):
    """Fix invalid subtypes in a pipeline file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        modified = False

        # Fix input nodes
        for node in data.get('nodes', []):
            if node.get('type') == 'input':
                subtype = node.get('data', {}).get('subtype')

                # Replace postgres with csv
                if subtype == 'postgres':
                    node['data']['subtype'] = 'csv'
                    # Remove postgres-specific config, add file_path
                    config = node['data'].get('config', {})
                    if 'connection_string' in config:
                        # Generate a CSV file path based on pipeline name
                        pipeline_name = data.get('name', 'data').replace(' ', '_').lower()
                        csv_file = f"examples/{pipeline_name}.csv"
                        config['file_path'] = csv_file
                        # Keep sample_data but remove postgres-specific fields
                        modified = True
                        print(f"✓ Fixed {file_path.name}: postgres -> csv")

                # Replace kafka with csv
                elif subtype == 'kafka':
                    node['data']['subtype'] = 'csv'
                    config = node['data'].get('config', {})
                    if 'bootstrap_servers' in config:
                        pipeline_name = data.get('name', 'data').replace(' ', '_').lower()
                        csv_file = f"examples/{pipeline_name}.csv"
                        config['file_path'] = csv_file
                        modified = True
                        print(f"✓ Fixed {file_path.name}: kafka -> csv")

                # Replace batch_request (as input) with csv
                elif subtype == 'batch_request':
                    node['data']['subtype'] = 'csv'
                    config = node['data'].get('config', {})
                    if 'url_template' in config:
                        # Extract meaningful name from URL template
                        url_template = config.get('url_template', '')
                        if 'customers' in url_template:
                            config['file_path'] = 'examples/customers.csv'
                        else:
                            pipeline_name = data.get('name', 'api_data').replace(' ', '_').lower()
                            config['file_path'] = f"examples/{pipeline_name}.csv"
                        modified = True
                        print(f"✓ Fixed {file_path.name}: batch_request (input) -> csv")

                # Replace db_read with csv
                elif subtype == 'db_read':
                    node['data']['subtype'] = 'csv'
                    config = node['data'].get('config', {})
                    if 'tableName' in config:
                        table_name = config.get('tableName')
                        config['file_path'] = f'examples/{table_name}.csv'
                    modified = True
                    print(f"✓ Fixed {file_path.name}: db_read -> csv")

        # Fix SQL with hardcoded table references
        for node in data.get('nodes', []):
            if node.get('data', {}).get('subtype') == 'raw_sql':
                sql = node.get('data', {}).get('config', {}).get('sql', '')
                if ' FROM orders ' in sql:
                    sql = sql.replace(' FROM orders ', ' FROM {{input1}} ')
                    node['data']['config']['sql'] = sql
                    modified = True
                    print(f"✓ Fixed {file_path.name}: hardcoded table names -> {{input1}}")
                elif ' FROM api_response ' in sql:
                    sql = sql.replace(' FROM api_response ', ' FROM {{input2}} ')
                    node['data']['config']['sql'] = sql
                    modified = True
                    print(f"✓ Fixed {file_path.name}: hardcoded table names -> {{input2}}")
                elif ' FROM discounts ' in sql:
                    sql = sql.replace(' FROM discounts ', ' FROM {{input3}} ')
                    node['data']['config']['sql'] = sql
                    modified = True
                    print(f"✓ Fixed {file_path.name}: hardcoded table names -> {{input3}}")

        if modified:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True

    except Exception as e:
        print(f"✗ Error fixing {file_path}: {e}")
        return False

def main():
    examples_dir = Path('/Users/chimin/Documents/script/duckdb-web/public/examples')

    # Find problematic pipeline files
    pipeline_files = [
        'ingestion/postgres_export_pipeline.json',
        'ingestion/kafka_stream_pipeline.json',
        'batch/incremental_sync_pipeline.json',
        'comparison/data_reconciliation_pipeline.json',
        'enrichment/multi_source_join_pipeline.json'
    ]

    print(f"Fixing {len(pipeline_files)} pipelines with invalid subtypes...\n")

    fixed_count = 0
    for pipeline_name in pipeline_files:
        file_path = examples_dir / pipeline_name
        if file_path.exists():
            if fix_pipeline_file(file_path):
                fixed_count += 1

    print(f"\n✓ Complete! Fixed {fixed_count} pipeline files")

if __name__ == '__main__':
    main()
