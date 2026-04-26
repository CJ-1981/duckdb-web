#!/usr/bin/env python3
import json
from pathlib import Path

# Generic sample data based on common patterns
GENERIC_SAMPLE_DATA = {
    'products': [
        {"id": 1, "name": "Sample Product 1", "price": 100.00, "category": "electronics"},
        {"id": 2, "name": "Sample Product 2", "price": 50.00, "category": "books"},
        {"id": 3, "name": "Sample Product 3", "price": 75.00, "category": "electronics"}
    ],
    'users': [
        {"user_id": 1, "name": "User 1", "email": "user1@example.com"},
        {"user_id": 2, "name": "User 2", "email": "user2@example.com"},
        {"user_id": 3, "name": "User 3", "email": "user3@example.com"}
    ],
    'orders': [
        {"order_id": "ORD-001", "customer_id": "CUST-001", "amount": 150.00, "status": "completed"},
        {"order_id": "ORD-002", "customer_id": "CUST-002", "amount": 200.00, "status": "pending"}
    ],
    'events': [
        {"event_id": 1, "timestamp": "2024-01-15T10:00:00Z", "type": "click", "value": 1},
        {"event_id": 2, "timestamp": "2024-01-15T10:05:00Z", "type": "view", "value": 0}
    ],
    'data': [
        {"id": 1, "field1": "value1", "field2": 100},
        {"id": 2, "field1": "value2", "field2": 200},
        {"id": 3, "field1": "value3", "field2": 300}
    ],
    'sales': [
        {"date": "2024-01-15", "amount": 1500.00, "region": "North"},
        {"date": "2024-01-16", "amount": 2000.00, "region": "South"}
    ],
    'transactions': [
        {"transaction_id": 1, "from_account": "ACC-001", "to_account": "ACC-002", "amount": 500.00},
        {"transaction_id": 2, "from_account": "ACC-003", "to_account": "ACC-004", "amount": 750.00}
    ],
    'customers': [
        {"customer_id": 1, "name": "Customer 1", "segment": "VIP", "tier": "gold"},
        {"customer_id": 2, "name": "Customer 2", "segment": "Regular", "tier": "silver"}
    ],
    'default': [
        {"id": 1, "value": "sample_value_1"},
        {"id": 2, "value": "sample_value_2"},
        {"id": 3, "value": "sample_value_3"}
    ]
}

def guess_sample_data(file_path, pipeline_name):
    """Guess appropriate sample data based on pipeline name"""
    name_lower = pipeline_name.lower()

    if 'product' in name_lower or 'ecommerce' in name_lower:
        return GENERIC_SAMPLE_DATA['products']
    elif 'user' in name_lower or 'customer' in name_lower or 'profile' in name_lower:
        return GENERIC_SAMPLE_DATA['users']
    elif 'order' in name_lower or 'sales' in name_lower:
        return GENERIC_SAMPLE_DATA['orders']
    elif 'event' in name_lower or 'stream' in name_lower or 'analytics' in name_lower:
        return GENERIC_SAMPLE_DATA['events']
    elif 'transaction' in name_lower:
        return GENERIC_SAMPLE_DATA['transactions']
    elif 'funnel' in name_lower:
        return GENERIC_SAMPLE_DATA['events']
    elif 'ab_test' in name_lower:
        return [{"customer_id": "A", "group": "control", "converted": 1, "revenue": 1000},
                {"customer_id": "B", "group": "variant", "converted": 1, "revenue": 1500}]
    else:
        return GENERIC_SAMPLE_DATA['default']

def add_sample_data_to_pipeline(file_path):
    """Add sample_data field to input nodes in a pipeline JSON file"""
    try:
        with open(file_path, 'r') as f:
            pipeline = json.load(f)

        pipeline_name = pipeline.get('name', '')
        modified = False

        for node in pipeline.get('nodes', []):
            if node.get('type') == 'input' and node.get('data', {}).get('config'):
                config = node['data']['config']

                # If sample_data doesn't exist, add it
                if 'sample_data' not in config:
                    sample_data = guess_sample_data(file_path, pipeline_name)
                    config['sample_data'] = sample_data
                    modified = True
                    print(f"✓ Added sample_data to {file_path.name} ({pipeline_name})")

        if modified:
            with open(file_path, 'w') as f:
                json.dump(pipeline, f, indent=2)
            return True

        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

# Process all JSON files in examples directory
examples_dir = Path('/Users/chimin/Documents/script/duckdb-web/public/examples')
json_files = list(examples_dir.glob('**/*.json'))

print(f"Found {len(json_files)} sample pipeline files")
print(f"Adding inline sample data to input nodes...\n")

modified_count = 0
for json_file in json_files:
    if add_sample_data_to_pipeline(json_file):
        modified_count += 1

print(f"\n✓ Complete! Updated {modified_count} pipeline files with inline sample data")
print(f"\nAll sample pipelines now have inline data and can be executed immediately!")
