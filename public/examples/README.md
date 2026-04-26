# Sample Pipelines

This directory contains sample DAG engineering pipelines demonstrating various data engineering use cases.

## Sample Data Files

The following CSV files contain sample input data for running the pipelines:

| File | Description | Used By |
|------|-------------|---------|
| `products_input.csv` | Product catalog with IDs, names, prices | E-Commerce Product Scraper |
| `social_posts_input.csv` | Social media post parameters | Social Media Analytics |
| `users_input.csv` | User IDs for enrichment | User Profile Enrichment |
| `messy_data.csv` | Data with quality issues | Data Cleaning Pipeline |
| `orders.csv` | Order transactions | Time-Series Rollup, Incremental Sync |
| `events.csv` | Event stream data | Time-Series Rollup |
| `new_customers.csv` | Customer data with validation issues | Data Validation Pipeline |
| `funnel_events.csv` | User session events | Funnel Analysis |
| `ab_test_events.csv` | A/B test results | A/B Test Analysis |
| `api_endpoints.csv` | API URLs to fetch | REST API with Pagination |
| `sales_data.csv` | Sales transactions | Multi-Format Export |
| `transactions_long.csv` | Transaction records | PIVOT Table Generator |
| `task_config.csv` | Task configurations | Dynamic Parallel Tasks |
| `catalog.csv` | Product catalog data | XML Hierarchical Flattening |

## How to Use

1. Click **Open Pipeline** in the toolbar
2. Switch to the **Sample Pipelines** tab
3. Browse categories and expand to see samples
4. Click on any sample pipeline to load it
5. Click the **Execute (Play)** button to run with sample data

## Pipeline Categories

### 📥 Data Ingestion
Import data from various sources (CSV, databases, APIs, Kafka)

### 🔄 Data Transformation
Clean, transform, and evolve data schemas

### 🎯 Data Enrichment
Add value through joins, geocoding, ML inference

### ✅ Data Quality
Validate, profile, and ensure data integrity

### 📊 Analytics & Reporting
Aggregate time-series data, analyze funnels, A/B testing

### ⚡ Batch Processing
ETL patterns, SCD Type 2, incremental sync, parallel processing

### 🔗 API Integration
OAuth2 authentication, GraphQL queries

### 💾 Data Export
Multi-format exports, bulk database loading

### 🔔 Notifications
Alert on pipeline failures with retry logic

### 🎮 Orchestration
Conditional branching, dynamic parallel tasks

### 🔄 Data Comparison
Reconcile data sources, detect changes with CDC

### 📋 Flattening
Convert nested JSON/XML to tabular format

## Sample Pipeline Structure

Each sample pipeline is a JSON file containing:
- `name`: Pipeline title
- `description`: What the pipeline does
- `nodes`: List of processing nodes (input, transform, output)
- `edges`: Connections between nodes

Sample data files are referenced in node configurations using paths like `examples/filename.csv`.
