#!/usr/bin/env python3
"""
Test Data Generator for DuckDB Web Platform E2E Tests

Generates various CSV files with different characteristics for comprehensive testing.
Run this script before executing E2E tests to ensure test data is available.
"""

import csv
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
TEST_DATA_DIR = Path("tests/e2e/test_data")
SEED = 42

# Set random seed for reproducibility
random.seed(SEED)


def create_directory():
    """Create test data directory if it doesn't exist."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created test data directory: {TEST_DATA_DIR}")


def generate_sales_csv(rows=1000, filename='sales.csv'):
    """
    Generate sales data with various characteristics.

    Columns: id, product, category, quantity, price, date
    """
    filepath = TEST_DATA_DIR / filename
    products = ['Widget A', 'Gadget B', 'Tool C', 'Device D', 'Instrument E']
    categories = ['Electronics', 'Office', 'Hardware', 'Software', 'Accessories']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'product', 'category', 'quantity', 'price', 'date'])

        base_date = datetime(2024, 1, 1)
        for i in range(1, rows + 1):
            writer.writerow([
                i,
                random.choice(products),
                random.choice(categories),
                random.randint(1, 100),
                round(random.uniform(10, 500), 2),
                (base_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            ])

    print(f"✓ Generated {filename}: {rows} rows")
    return filepath


def generate_customers_csv(rows=500, filename='customers.csv'):
    """
    Generate customer data.

    Columns: customer_id, name, email, country, registration_date
    """
    filepath = TEST_DATA_DIR / filename
    first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank']
    last_names = ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller']
    countries = ['USA', 'UK', 'Canada', 'Germany', 'France', 'Australia', 'Japan', 'Brazil']
    domains = ['example.com', 'test.co.uk', 'demo.ca', 'sample.org', 'temp.net']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['customer_id', 'name', 'email', 'country', 'registration_date'])

        base_date = datetime(2023, 1, 1)
        for i in range(1, rows + 1):
            first = random.choice(first_names)
            last = random.choice(last_names)
            email = f"{first.lower()}.{last.lower()}{i}@{random.choice(domains)}"

            writer.writerow([
                i,
                f"{first} {last}",
                email,
                random.choice(countries),
                (base_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d')
            ])

    print(f"✓ Generated {filename}: {rows} rows")
    return filepath


def generate_orders_csv(rows=2000, filename='orders.csv'):
    """
    Generate order data.

    Columns: order_id, customer_id, product_id, quantity, total, status
    """
    filepath = TEST_DATA_DIR / filename
    statuses = ['completed', 'pending', 'shipped', 'cancelled', 'refunded']

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'customer_id', 'product_id', 'quantity', 'total', 'status'])

        for i in range(1, rows + 1):
            quantity = random.randint(1, 10)
            price = round(random.uniform(10, 500), 2)

            writer.writerow([
                1000 + i,
                random.randint(1, 500),
                f"P{random.randint(1, 100):03d}",
                quantity,
                round(quantity * price, 2),
                random.choice(statuses)
            ])

    print(f"✓ Generated {filename}: {rows} rows")
    return filepath


def generate_edge_cases_csv(rows=100, filename='edge_cases.csv'):
    """
    Generate edge case data with special characters, nulls, etc.

    Columns: id, name, value, date, description
    """
    filepath = TEST_DATA_DIR / filename

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'value', 'date', 'description'])

        # Normal row
        writer.writerow([1, 'Normal Row', '100', '2024-01-01', 'Standard entry'])

        # Null values in multiple columns
        writer.writerow([2, '', '', '', 'Null values in multiple columns'])

        # Special characters and quotes
        writer.writerow([3, 'Special "Chars"', '50.5', '2024-01-03', 'Quoted, comma, text'])

        # UTF-8 characters
        writer.writerow([4, 'Émojis ñoño Ð', '25', '2024-01-04', 'UTF-8 characters'])

        # Leading/trailing spaces
        writer.writerow([5, '  Spaces  ', '  150  ', ' 2024-01-05 ', 'Leading/trailing spaces'])

        # Generate more rows
        base_date = datetime(2024, 1, 6)
        for i in range(6, rows + 1):
            # Mix of normal and edge cases
            if i % 10 == 0:
                writer.writerow([i, '', str(random.randint(1, 1000)), '', 'Null name'])
            elif i % 7 == 0:
                writer.writerow([i, f'Row {i} with, commas', str(random.randint(1, 1000)),
                               (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                               'Description with, commas, inside'])
            else:
                writer.writerow([i, f'Test User {i}', str(random.randint(1, 1000)),
                               (base_date + timedelta(days=i)).strftime('%Y-%m-%d'),
                               f'Test description {i}'])

    print(f"✓ Generated {filename}: {rows} rows")
    return filepath


def generate_empty_csv(filename='empty.csv'):
    """Generate an empty CSV file with headers only."""
    filepath = TEST_DATA_DIR / filename

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'value'])

    print(f"✓ Generated {filename}: 0 data rows (headers only)")
    return filepath


def generate_no_header_csv(filename='no_header.csv'):
    """Generate CSV without header row."""
    filepath = TEST_DATA_DIR / filename

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([1, 'Alice', '100'])
        writer.writerow([2, 'Bob', '200'])
        writer.writerow([3, 'Charlie', '150'])

    print(f"✓ Generated {filename}: 3 rows, no header")
    return filepath


def generate_quarterly_csv(filename_prefix='sales_q'):
    """Generate quarterly sales files for union/combine tests."""
    quarters = [
        (1, '2024-01-01', 90),
        (2, '2024-04-01', 91),
        (3, '2024-07-01', 92)
    ]

    for q_num, start_date, days in quarters:
        filename = f'{filename_prefix}{q_num}.csv'
        filepath = TEST_DATA_DIR / filename

        products = ['Widget A', 'Gadget B', 'Tool C']
        categories = ['Electronics', 'Office', 'Hardware']

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'product', 'category', 'quantity', 'price', 'date'])

            base_date = datetime.strptime(start_date, '%Y-%m-%d')
            for i in range(100):
                writer.writerow([
                    i + 1,
                    random.choice(products),
                    random.choice(categories),
                    random.randint(1, 50),
                    round(random.uniform(10, 500), 2),
                    (base_date + timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d')
                ])

        print(f"✓ Generated {filename}: 100 rows (Q{q_num} {start_date[:4]})")


def generate_customer_segments(filename_a='customers_a.csv', filename_b='customers_b.csv'):
    """Generate two customer datasets for join tests with no overlap."""
    # First set: IDs 1-100
    filepath_a = TEST_DATA_DIR / filename_a
    with open(filepath_a, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'email'])
        for i in range(1, 101):
            writer.writerow([i, f'Customer A{i}', f'customer{i}@domain-a.com'])
    print(f"✓ Generated {filename_a}: 100 rows (IDs 1-100)")

    # Second set: IDs 200-300 (no overlap)
    filepath_b = TEST_DATA_DIR / filename_b
    with open(filepath_b, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'email'])
        for i in range(200, 301):
            writer.writerow([i, f'Customer B{i}', f'customer{i}@domain-b.com'])
    print(f"✓ Generated {filename_b}: 100 rows (IDs 200-300, no overlap with A)")


def generate_all():
    """Generate all test data files."""
    print("\n🔧 Generating E2E test data...\n")
    create_directory()

    # Standard datasets
    generate_sales_csv(1000, 'sales.csv')
    generate_customers_csv(500, 'customers.csv')
    generate_orders_csv(2000, 'orders.csv')
    generate_edge_cases_csv(100, 'edge_cases.csv')

    # Special cases
    generate_empty_csv('empty.csv')
    generate_no_header_csv('no_header.csv')

    # For combine/union tests
    generate_quarterly_csv('sales_q')

    # For join tests
    generate_customer_segments('customers_a.csv', 'customers_b.csv')

    # Large dataset for performance tests
    print("\n⚠️  Large dataset generation skipped (100K rows)")
    print("   Run with --large flag to generate large_sales.csv")

    print(f"\n✅ Test data generation complete!")
    print(f"📁 Location: {TEST_DATA_DIR.absolute()}")
    print(f"📊 Total files generated: {len(list(TEST_DATA_DIR.glob('*.csv')))}")


def generate_large():
    """Generate large datasets for performance testing."""
    print("\n🔧 Generating large datasets for performance tests...\n")
    create_directory()
    generate_sales_csv(100000, 'large_sales.csv')
    print(f"\n✅ Large dataset generation complete!")


if __name__ == '__main__':
    import sys

    if '--large' in sys.argv:
        generate_large()
    else:
        generate_all()
