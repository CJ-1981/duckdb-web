#!/usr/bin/env python3
import json
import os
from pathlib import Path

# Sample data templates for different input types
SAMPLE_DATA = {
    'messy_data.csv': [
        {"id": 1, "name": "John Doe", "email": "john@example.com", "phone": "555-0101", "amount": "150.50", "created_at": "2024-01-15T10:30:00Z"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "phone": "555-0102", "amount": "200.75", "created_at": "2024-01-15T11:45:00Z"},
        {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "phone": "555-0103", "amount": "75.25", "created_at": "2024-01-15T14:20:00Z"}
    ],
    'new_customers.csv': [
        {"customer_id": 1, "email": "customer1@example.com", "phone": "555-0001", "age": 25},
        {"customer_id": 2, "email": "customer2@example.com", "phone": "555-0002", "age": 35},
        {"customer_id": 3, "email": "customer3@example.com", "phone": "", "age": 45}
    ],
    'orders.csv': [
        {"order_id": "ORD-001", "customer_id": "CUST-001", "amount": 150.50, "status": "completed", "created_at": "2024-01-15T10:00:00Z"},
        {"order_id": "ORD-002", "customer_id": "CUST-002", "amount": 299.99, "status": "completed", "created_at": "2024-01-15T11:00:00Z"},
        {"order_id": "ORD-003", "customer_id": "CUST-003", "amount": 89.99, "status": "pending", "created_at": "2024-01-15T12:00:00Z"}
    ],
    'events.csv': [
        {"event_id": 1, "timestamp": "2024-01-15T10:00:00Z", "event_type": "page_view", "value": 0},
        {"event_id": 2, "timestamp": "2024-01-15T10:05:00Z", "event_type": "click", "value": 1},
        {"event_id": 3, "timestamp": "2024-01-15T10:10:00Z", "event_type": "page_view", "value": 0}
    ],
    'funnel_events.csv': [
        {"user_id": "user1", "session_id": "session1", "event_name": "page_view", "timestamp": "2024-01-15T10:00:00Z"},
        {"user_id": "user1", "session_id": "session1", "event_name": "add_to_cart", "timestamp": "2024-01-15T10:05:00Z"},
        {"user_id": "user1", "session_id": "session1", "event_name": "purchase", "timestamp": "2024-01-15T10:15:00Z"}
    ],
    'api_endpoints.csv': [
        {"api_endpoint": "https://jsonplaceholder.typicode.com/posts/1"},
        {"api_endpoint": "https://jsonplaceholder.typicode.com/posts/2"}
    ]
}

def add_sample_data_to_pipeline(file_path):
    """Add sample_data field to input nodes in a pipeline JSON file"""
    try:
        with open(file_path, 'r') as f:
            pipeline = json.load(f)

        modified = False
        for node in pipeline.get('nodes', []):
            if node.get('type') == 'input' and node.get('data', {}).get('config'):
                config = node['data']['config']
                file_path = config.get('file_path', '')

                # Extract filename from path
                filename = file_path.split('/')[-1] if file_path else ''

                if filename in SAMPLE_DATA:
                    config['sample_data'] = SAMPLE_DATA[filename]
                    modified = True
                    print(f"✓ Added sample_data to {file_path}")

        if modified:
            with open(file_path, 'w') as f:
                json.dump(pipeline, f, indent=2)

        return modified
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

# Process all JSON files in examples directory
examples_dir = Path('/Users/chimin/Documents/script/duckdb-web/public/examples')
json_files = list(examples_dir.glob('**/*.json'))

print(f"Found {len(json_files)} sample pipeline files")
print(f"Updating input nodes with inline sample data...\n")

modified_count = 0
for json_file in json_files:
    if add_sample_data_to_pipeline(json_file):
        modified_count += 1

print(f"\n✓ Complete! Updated {modified_count} pipeline files")
