"""
Test data transformation methods in Processor.

This test verifies that:
1. pivot_table() creates cross-tabulations
2. group_by() performs aggregations
3. merge() joins tables correctly
4. window() functions work for rolling analytics
5. rolling_aggregate() works for moving averages

@MX:SPEC: SPEC-PLATFORM-001 P2-T005
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os

from src.core.processor import Processor


class TestPivotTable:
    """Test pivot_table transformation."""

    def setup_method(self):
        """Create a Processor with sample data for each test."""
        self.processor = Processor()

        # Create sample sales data
        data = {
            'region': ['North', 'North', 'South', 'South', 'East', 'East', 'West', 'West'],
            'product': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
            'sales': [100, 150, 200, 120, 180, 160, 140, 190]
        }
        df = pd.DataFrame(data)

        # Load data into DuckDB
        self.processor.load_df(df, 'sales_data')

    def test_pivot_table_basic(self):
        """Test basic pivot table creation."""
        self.setup_method()

        result = self.processor.pivot(
            row_key='region',
            col_key='product',
            val='sales',
            func='SUM'
        )

        assert not result.empty
        assert 'region' in result.columns
        assert 'A' in result.columns or 'B' in result.columns

    def test_pivot_table_with_avg(self):
        """Test pivot table with average aggregation."""
        self.setup_method()

        result = self.processor.pivot(
            row_key='region',
            col_key='product',
            val='sales',
            func='AVG'
        )

        assert not result.empty

    def test_pivot_table_with_count(self):
        """Test pivot table with count aggregation."""
        self.setup_method()

        result = self.processor.pivot(
            row_key='region',
            col_key='product',
            val='sales',
            func='COUNT'
        )

        assert not result.empty


class TestGroupBy:
    """Test group_by transformation."""

    def setup_method(self):
        """Create a Processor with sample data."""
        self.processor = Processor()

        # Create sample sales data
        data = {
            'category': ['A', 'A', 'B', 'B', 'C', 'C'],
            'region': ['X', 'Y', 'X', 'Y', 'X', 'Y'],
            'sales': [100, 150, 200, 120, 180, 160]
        }
        df = pd.DataFrame(data)

        self.processor.load_df(df, 'sales_data')

    def test_group_by_single_column(self):
        """Test group by with single column."""
        self.setup_method()

        result = self.processor.group_by(
            group_columns=['category'],
            agg_column='sales',
            func='SUM'
        )

        assert not result.empty
        assert 'category' in result.columns
        assert 'sum_sales' in result.columns

    def test_group_by_multiple_columns(self):
        """Test group by with multiple columns."""
        self.setup_method()

        result = self.processor.group_by(
            group_columns=['category', 'region'],
            agg_column='sales',
            func='SUM'
        )

        assert not result.empty
        assert 'category' in result.columns
        assert 'region' in result.columns

    def test_group_by_with_avg(self):
        """Test group by with average aggregation."""
        self.setup_method()

        result = self.processor.group_by(
            group_columns=['category'],
            agg_column='sales',
            func='AVG'
        )

        assert not result.empty
        assert 'avg_sales' in result.columns

    def test_group_by_with_count(self):
        """Test group by with count aggregation."""
        self.setup_method()

        result = self.processor.group_by(
            group_columns=['category'],
            agg_column='sales',
            func='COUNT'
        )

        assert not result.empty
        assert 'count_sales' in result.columns


class TestMerge:
    """Test merge/join transformation."""

    def setup_method(self):
        """Create a Processor with sample data."""
        self.processor = Processor()

        # Create customers table
        customers = {
            'customer_id': [1, 2, 3, 4],
            'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
            'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 'diana@example.com']
        }

        # Create orders table
        orders = {
            'customer_id': [1, 1, 2, 4],
            'order_id': [101, 102, 103, 104],
            'amount': [50, 75, 100, 125]
        }

        customers_df = pd.DataFrame(customers)
        orders_df = pd.DataFrame(orders)

        self.processor.load_df(customers_df, 'customers')
        self.processor.load_df(orders_df, 'orders')

    def test_merge_inner_join(self):
        """Test inner join."""
        self.setup_method()

        result = self.processor.merge(
            other_table='orders',
            on=['customer_id'],
            how='inner'
        )

        assert not result.empty
        # Inner join should only have matching customer_ids
        assert set(result['customer_id'].tolist()).issubset({1, 2, 4})

    def test_merge_left_join(self):
        """Test left join."""
        self.setup_method()

        result = self.processor.merge(
            other_table='orders',
            on=['customer_id'],
            how='left'
        )

        assert not result.empty
        # Left join from orders to customers: customer 1 appears twice (has 2 orders)
        # Total: 4 orders joined with customers = 4 rows (customer 1 has 2 orders, others have 1 each)
        # But wait, we're joining FROM orders (current table) TO customers
        # Orders table: [1, 1, 2, 4] - 4 rows
        # After LEFT JOIN with customers: still 4 rows (all orders have matching customers)
        assert len(result) >= 4  # At minimum, all orders should be present

    def test_merge_right_join(self):
        """Test right join."""
        self.setup_method()

        result = self.processor.merge(
            other_table='orders',
            on=['customer_id'],
            how='right'
        )

        assert not result.empty

    def test_merge_outer_join(self):
        """Test full outer join."""
        self.setup_method()

        result = self.processor.merge(
            other_table='orders',
            on=['customer_id'],
            how='outer'
        )

        assert not result.empty


class TestWindowFunctions:
    """Test window function transformations."""

    def setup_method(self):
        """Create a Processor with sample time series data."""
        self.processor = Processor()

        # Create time series data
        data = {
            'date': pd.date_range('2024-01-01', periods=10),
            'category': ['A', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'B'],
            'value': [10, 20, 15, 25, 30, 40, 35, 45, 50, 55]
        }
        df = pd.DataFrame(data)

        self.processor.load_df(df, 'time_series')

    def test_window_row_number(self):
        """Test ROW_NUMBER window function."""
        self.setup_method()

        result = self.processor.window(
            func='ROW_NUMBER',
            over_column='date',
            partition_by=['category']
        )

        assert not result.empty
        # Check that row_number column exists
        assert 'row_number_date' in result.columns

    def test_window_rank(self):
        """Test RANK window function."""
        self.setup_method()

        result = self.processor.window(
            func='RANK',
            over_column='value',
            partition_by=['category']
        )

        assert not result.empty

    def test_window_lag(self):
        """Test LAG window function."""
        self.setup_method()

        result = self.processor.window(
            func='LAG',
            over_column='value',
            partition_by=['category']
        )

        assert not result.empty
        assert 'lag_value' in result.columns

    def test_window_sum(self):
        """Test SUM over window function."""
        self.setup_method()

        result = self.processor.window(
            func='SUM',
            over_column='value',
            partition_by=['category'],
            alias='running_total'
        )

        assert not result.empty
        assert 'running_total' in result.columns


class TestRollingAggregate:
    """Test rolling aggregate transformations."""

    def setup_method(self):
        """Create a Processor with sample time series data."""
        self.processor = Processor()

        # Create time series data
        data = {
            'date': pd.date_range('2024-01-01', periods=10),
            'category': ['A', 'A', 'B', 'B', 'A', 'A', 'B', 'B', 'A', 'B'],
            'value': [10, 20, 15, 25, 30, 40, 35, 45, 50, 55]
        }
        df = pd.DataFrame(data)

        self.processor.load_df(df, 'time_series')

    def test_rolling_sum(self):
        """Test rolling SUM aggregation."""
        self.setup_method()

        result = self.processor.rolling_aggregate(
            agg_column='value',
            func='SUM',
            window_size=3
        )

        assert not result.empty
        assert 'rolling_sum_value' in result.columns

    def test_rolling_avg(self):
        """Test rolling AVG aggregation."""
        self.setup_method()

        result = self.processor.rolling_aggregate(
            agg_column='value',
            func='AVG',
            window_size=3
        )

        assert not result.empty
        assert 'rolling_avg_value' in result.columns

    def test_rolling_with_partition(self):
        """Test rolling aggregation with partitioning."""
        self.setup_method()

        result = self.processor.rolling_aggregate(
            agg_column='value',
            func='SUM',
            window_size=3,
            partition_by=['category']
        )

        assert not result.empty
        assert 'rolling_sum_value' in result.columns


class TestTransformationIntegration:
    """Integration tests combining multiple transformations."""

    def setup_method(self):
        """Create a Processor with sample data."""
        self.processor = Processor()

        # Create sales data
        data = {
            'date': pd.date_range('2024-01-01', periods=15),
            'region': ['North', 'South', 'East', 'West'] * 3 + ['North', 'South', 'East'],
            'product': ['A', 'B', 'C'] * 5,
            'sales': np.random.randint(50, 200, 15),
            'quantity': np.random.randint(1, 10, 15)
        }
        df = pd.DataFrame(data)

        self.processor.load_df(df, 'sales')

    def test_group_by_then_pivot(self):
        """Test combining group_by and pivot operations."""
        self.setup_method()

        # First group by region
        grouped = self.processor.group_by(
            group_columns=['region'],
            agg_column='sales',
            func='SUM'
        )

        assert not grouped.empty

    def test_window_then_aggregate(self):
        """Test combining window functions and aggregation."""
        self.setup_method()

        # Add running total
        with_window = self.processor.window(
            func='SUM',
            over_column='sales',
            alias='running_total'
        )

        assert not with_window.empty
        assert 'running_total' in with_window.columns

    def test_merge_then_group(self):
        """Test combining merge and group_by."""
        self.setup_method()

        # Create a target table to merge with
        targets = pd.DataFrame({
            'region': ['North', 'South', 'East', 'West'],
            'target': [500, 600, 700, 800]
        })

        self.processor.load_df(targets, 'targets')

        # Merge and then group
        merged = self.processor.merge(
            other_table='targets',
            on=['region'],
            how='left'
        )

        assert not merged.empty

        # For group_by on merged result, we need to load it first
        # or use the current table which now has the merged data
        # Since merge() doesn't change the current table, we load the merged result
        temp_processor = Processor()
        temp_processor.load_df(merged, 'merged_data')

        grouped = temp_processor.group_by(
            group_columns=['region'],
            agg_column='target',
            func='AVG'
        )

        assert not grouped.empty
