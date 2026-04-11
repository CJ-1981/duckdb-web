# Product Documentation

## Project Name

**DuckDB Workflow Builder** - A visual data analysis platform for building and executing DuckDB workflows through an intuitive drag-and-drop interface.

## Description

The DuckDB Workflow Builder is a full-stack web application that enables users to create complex data processing pipelines visually without writing SQL code. Users can drag and drop nodes onto a canvas to build workflows that connect to multiple data sources, transform data using DuckDB's powerful analytical engine, and generate reports. The platform combines the flexibility of SQL with the ease of visual programming, making data analysis accessible to both technical and non-technical users.

## Target Audience

### Primary Users
- **Data Analysts**: Need to process and analyze data from multiple sources without deep SQL knowledge
- **Business Users**: Require self-service data analysis and reporting capabilities
- **Data Engineers**: Want to quickly prototype and test data transformation pipelines

### Secondary Users
- **Developers**: Building custom data integrations and extending the platform through plugins
- **Researchers**: Processing experimental data with reproducible workflows
- **Consultants**: Delivering data analysis solutions to clients rapidly

## Core Features

### 1. Visual Workflow Builder
- **Drag-and-Drop Interface**: Intuitive canvas for constructing data processing pipelines
- **Node-Based Architecture**: Modular components for data sources, transformations, and outputs
- **Real-Time Validation**: Immediate feedback on workflow structure and connections
- **Keyboard Shortcuts**: Power user commands for efficient workflow construction (⌘/Ctrl key combinations)

### 2. Multi-Source Data Integration
- **Database Connectors**: Native support for DuckDB, PostgreSQL, MySQL
- **File Import**: CSV files with automatic encoding detection (UTF-8, UTF-8-sig, CP949, EUC-KR)
- **Remote Data**: HTTP/HTTPS file downloads with streaming support
- **Schema Inference**: Automatic column type detection and validation

### 3. Real-Time Data Processing
- **DuckDB Engine**: In-memory analytical database for fast query execution
- **Incremental Caching**: Smart node-level caching to avoid redundant computation
- **Streaming Support**: Process large datasets without loading entirely into memory
- **Query Optimization**: Automatic SQL generation with parameterized queries

### 4. AI-Assisted SQL Generation
- **Natural Language to SQL**: Convert plain English descriptions into SQL queries
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Google, Groq, Cerebras
- **Context-Aware**: AI understands data schema and suggests relevant queries
- **Query Validation**: EXPLAIN-based validation to ensure query correctness

### 5. Workflow Persistence
- **Save/Load Workflows**: Store workflow definitions for future use
- **Version Control**: Track changes and revert to previous versions
- **Export/Import**: Share workflows across teams and environments
- **Auto-Save**: Prevent data loss with automatic saving (planned feature)

### 6. Live Data Preview
- **Real-Time Results**: Preview output at any node in the workflow
- **Pagination**: Handle large datasets efficiently with configurable page sizes
- **Data Inspection**: Statistical analysis including column types, null counts, unique values
- **Export Results**: Download processed data as CSV or other formats

### 7. Report Generation
- **PDF Reports**: Generate formatted PDF reports from workflow results
- **Markdown Export**: Create documentation-friendly markdown reports
- **Custom Templates**: Define report layouts and branding
- **Scheduled Reports**: Automate report generation and delivery (planned feature)

## Use Cases

### Data Analysis and Exploration
- Load CSV files from various sources
- Clean and transform data using visual nodes
- Perform aggregations, filtering, and joins
- Visualize results and export insights

### ETL Pipeline Development
- Extract data from databases and APIs
- Transform using DuckDB's analytical functions
- Load results into target systems
- Schedule and monitor pipeline execution

### Business Intelligence
- Connect to production databases
- Build KPI dashboards with custom metrics
- Generate periodic reports automatically
- Share insights with stakeholders

### Data Quality Validation
- Define validation rules for incoming data
- Detect anomalies and missing values
- Create data quality reports
- Alert on quality threshold violations

## Problem Statement

Traditional data analysis requires deep SQL expertise and repetitive coding for even simple transformations. Business users depend on IT teams for routine data tasks, creating bottlenecks. Existing visual tools are either too simple (limited to basic operations) or too complex (require programming knowledge).

## Solution

The DuckDB Workflow Builder bridges this gap by providing:
- **Visual Interface**: No coding required for common operations
- **SQL Power**: Full DuckDB capabilities when needed through AI-assisted SQL builder
- **Extensibility**: Plugin architecture for custom data sources and transformations
- **Performance**: In-memory processing with smart caching for interactive workflows
- **Reproducibility**: Saved workflows ensure consistent, repeatable analysis

## Differentiation

Unlike tools that require extensive SQL knowledge (Mode, Metabase) or limit functionality (Microsoft Power Query), the DuckDB Workflow Builder combines:
- Visual ease-of-use with full SQL power when needed
- Local-first architecture (no cloud dependency) with enterprise deployment options
- Open-source extensibility with professional features
- Focus on analytical workflows rather than just visualization
