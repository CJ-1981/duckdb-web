# Project Structure Documentation

## Recommended Directory Structure

```
duckdb-data-processor/
├── src/                                    # Source code directory
│   ├── __init__.py                        # Package initialization
│   ├── main.py                            # Main entry point
│   ├── cli/                               # Command-line interface module
│   │   ├── __init__.py
│   │   ├── app.py                         # CLI application logic
│   │   ├── commands/                      # Individual CLI commands
│   │   │   ├── __init__.py
│   │   │   ├── interactive.py            # Interactive mode
│   │   │   ├── batch.py                  # Batch processing
│   │   │   ├── query.py                  # Query execution
│   │   │   └── config.py                 # Configuration management
│   ├── core/                              # Core functionality
│   │   ├── __init__.py
│   │   ├── processor.py                   # Main processing logic
│   │   ├── duckdb/                        # DuckDB-specific functionality
│   │   │   ├── __init__.py
│   │   │   ├── connector.py              # DuckDB connection management
│   │   │   ├── queries.py                # Query utilities
│   │   │   └── types.py                  # DuckDB type mappings
│   │   ├── config/                        # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── parsers.py                # Configuration file parsers
│   │   │   ├── validator.py               # Configuration validation
│   │   │   └── defaults.py               # Default configurations
│   │   ├── io/                            # Input/output operations
│   │   │   ├── __init__.py
│   │   │   ├── csv.py                     # CSV file handling
│   │   │   ├── streams.py                # Stream processing
│   │   │   └── formatters.py             # Output formatting
│   │   └── utils/                         # Utility functions
│   │       ├── __init__.py
│   │       ├── logger.py                  # Logging utilities
│   │       ├── validators.py              # Data validation
│   │       └── helpers.py                # General helpers
│   └── plugins/                           # Plugin system
│       ├── __init__.py
│       ├── registry.py                   # Plugin registry
│       ├── base.py                        # Base plugin classes
│       └── processors/                    # Custom processor plugins
├── tests/                                 # Test files
│   ├── __init__.py                        # Test package initialization
│   ├── unit/                              # Unit tests
│   │   ├── __init__.py
│   │   ├── test_cli.py                    # CLI interface tests
│   │   ├── test_processor.py             # Core processor tests
│   │   ├── test_duckdb.py                 # DuckDB functionality tests
│   │   ├── test_config.py                 # Configuration tests
│   │   └── test_io.py                    # Input/output tests
│   ├── integration/                       # Integration tests
│   │   ├── __init__.py
│   │   ├── test_pipeline.py              # Pipeline integration tests
│   │   ├── test_csv_processing.py         # CSV processing integration
│   │   └── test_configuration.py          # Configuration integration
│   ├── fixtures/                          # Test data and fixtures
│   │   ├── sample_data/                  # Sample CSV files
│   │   ├── configs/                      # Test configuration files
│   │   └── expected_outputs/             # Expected output samples
│   └── conftest.py                        # Test configuration and fixtures
├── docs/                                  # Documentation files
│   ├── source/                           # Source documentation
│   │   ├── getting-started.md           # Getting started guide
│   │   ├── user-guide.md                 # User documentation
│   │   ├── api-reference.md              # API documentation
│   │   ├── configuration.md              # Configuration reference
│   │   └── examples/                     # Usage examples
│   │       ├── basic-usage.md
│   │       ├── advanced-queries.md
│   │       ├── pipeline-examples.md
│   │       └── configuration-examples.md
│   ├── _static/                          # Static assets
│   └── _build/                           # Generated documentation
├── .moai/                                # MoAI project configuration
│   ├── project/                          # Project documentation
│   │   ├── product.md                    # Product documentation (this file)
│   │   ├── structure.md                  # Project structure documentation
│   │   └── tech.md                      # Technical documentation
│   ├── specs/                           # Project specifications
│   ├── config/                          # MoAI configuration
│   │   ├── sections/
│   │   │   ├── user.yaml                 # User configuration
│   │   │   ├── language.yaml            # Language settings
│   │   │   └── quality.yaml             # Quality standards
│   │   └── workflow.yaml                # Workflow configuration
│   └── rules/                           # Project rules and standards
│       ├── moai/
│       │   ├── core/
│       │   ├── development/
│       │   └── workflow/
├── config/                              # Configuration templates
│   ├── default.yaml                     # Default configuration
│   ├── development.yaml                 # Development environment config
│   ├── production.yaml                  # Production environment config
│   └── examples/                        # Configuration examples
│       ├── analytics-config.yaml
│       ├── batch-config.yaml
│       └── interactive-config.yaml
├── scripts/                             # Utility scripts
│   ├── install.sh                      # Installation script
│   ├── build.sh                        # Build script
│   ├── test.sh                         # Test runner script
│   ├── lint.sh                         # Code linting script
│   └── deploy.sh                       # Deployment script
├── examples/                            # Usage examples
│   ├── basic/                          # Basic usage examples
│   │   ├── simple-query.py
│   │   └── csv-filtering.py
│   ├── advanced/                       # Advanced usage examples
│   │   ├── custom-aggregations.py
│   │   └── complex-pipelines.py
│   └── real-world/                     # Real-world use cases
│       ├── financial-analysis.py
│       ├── sales-reporting.py
│       └── data-quality-checks.py
├── .github/                            # GitHub Actions workflows
│   └── workflows/
│       ├── ci.yml                     # Continuous integration
│       └── release.yml                # Release management
├── .gitignore                          # Git ignore patterns
├── pyproject.toml                      # Python project configuration
├── requirements/                       # Dependency files
│   ├── base.txt                       # Core dependencies
│   ├── dev.txt                        # Development dependencies
│   ├── test.txt                       # Testing dependencies
│   └── docs.txt                       # Documentation dependencies
├── README.md                          # Project README
├── CHANGELOG.md                       # Change log
├── LICENSE                           # License file
└── MANIFEST.in                       # Package manifest
```

## Directory Purpose

### Source Code Structure (`src/`)

The `src/` directory contains all the main source code for the project, organized by functional areas:

- **`main.py`**: Entry point for the application, handles argument parsing and initial setup
- **`cli/`**: Command-line interface components, including the main app logic and individual commands
- **`core/`**: Core functionality including DuckDB integration, configuration management, and I/O operations
- **`plugins/`**: Plugin system for extending functionality with custom processors and formatters

### Testing Structure (`tests/`)

The `tests/` directory is organized to ensure comprehensive test coverage:

- **`unit/`**: Unit tests for individual components and classes
- **`integration/`**: Integration tests for components working together
- **`fixtures/`**: Test data, configuration files, and expected outputs

### Documentation Structure (`docs/`)

The `docs/` directory contains comprehensive documentation:

- **`source/`**: Source documentation files that can be built into various formats
- **`examples/`**: Practical usage examples and tutorials
- **`_static/`**: Static assets like images and diagrams

### Configuration Structure (`config/`)

The `config/` directory provides configuration templates:

- **Environment-specific configs**: Different configurations for development, testing, and production
- **Examples**: Sample configurations demonstrating different use cases

### Scripts (`scripts/`)

Utility scripts for common tasks:

- **Installation and build**: Scripts for setting up and building the project
- **Testing and linting**: Automated quality assurance scripts
- **Deployment**: Scripts for deploying the application

## Key File Locations

### Entry Points
- **Main Entry Point**: `src/main.py` - Application entry point
- **CLI Application**: `src/cli/app.py` - Command-line interface logic
- **Interactive Mode**: `src/cli/commands/interactive.py` - Interactive terminal interface

### Configuration Files
- **Default Configuration**: `config/default.yaml` - Base configuration template
- **Project Configuration**: `.moai/config/sections/user.yaml` - MoAI project settings
- **Quality Standards**: `.moai/config/sections/quality.yaml` - Code quality requirements

### Test Files
- **Unit Tests**: `tests/unit/` - Individual component tests
- **Integration Tests**: `tests/integration/` - Cross-component integration tests
- **Test Data**: `tests/fixtures/` - Sample data and test fixtures

### Documentation Files
- **Product Documentation**: `.moai/project/product.md` - Product overview and features
- **Structure Documentation**: `.moai/project/structure.md` - Project architecture
- **Technical Documentation**: `.moai/project/tech.md` - Technology stack and standards

## Module Organization

### Core Processing Flow

1. **Entry Point**: `main.py` parses command-line arguments and initializes the application
2. **CLI Interface**: `cli/app.py` routes commands to appropriate handlers
3. **Core Processor**: `core/processor.py` coordinates the main processing workflow
4. **DuckDB Integration**: `core/duckdb/` handles database connections and query execution
5. **Configuration**: `core/config/` manages loading and validating configuration
6. **Input/Output**: `core/io/` handles CSV file operations and output formatting

### Plugin Architecture

- **Plugin Registry**: `plugins/registry.py` manages available plugins
- **Base Plugins**: `plugins/base.py` defines plugin interfaces and base classes
- **Custom Processors**: `plugins/processors/` contains custom data processing plugins

### Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **Fixtures**: Provide reusable test data and expected results
- **Configuration**: Test configuration loading and validation

### Documentation Structure

- **Getting Started**: Basic usage and setup instructions
- **User Guide**: Comprehensive documentation for end users
- **API Reference**: Detailed documentation for developers
- **Examples**: Practical use cases and implementation examples

---

*This documentation is part of the DuckDB CSV Processor project. For more information, see the complete project documentation in `.moai/project/`.*