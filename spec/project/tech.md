# Technical Documentation

## Python Version Recommendation

### Recommended Version: Python 3.13+

The DuckDB CSV Processor requires **Python 3.13 or higher** to ensure compatibility with modern Python features, security updates, and performance optimizations. This version aligns with MoAI's Python development standards and provides access to the latest language improvements.

### Version Rationale

- **Modern Python Features**: Access to pattern matching, type parameter generics, and other Python 3.13+ features
- **Performance Improvements**: Better performance in string processing, async operations, and memory management
- **Security Updates**: Latest security patches and vulnerability fixes
- **Tooling Compatibility**: Optimal compatibility with modern development tools and libraries
- **Future-Proofing**: Long-term support and compatibility with upcoming Python versions

### Python Environment Setup

```bash
# Create virtual environment with Python 3.13+
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.13.0 or higher
```

## Key Dependencies

### Core Dependencies

#### DuckDB
- **Purpose**: High-performance in-memory analytical database
- **Version**: `duckdb >= 0.9.0`
- **Importance**: Core functionality for CSV processing and SQL operations
- **Installation**: `pip install duckdb`

#### CLI Framework (Click or Typer)
- **Click**: `click >= 8.0.0`
  - Traditional CLI framework with decorators and command groups
  - Mature ecosystem and extensive documentation
  - Better for complex CLI applications with subcommands

- **Typer**: `typer >= 0.9.0`
  - Modern alternative built on Click with improved type hints
  - Better integration with Pydantic for data validation
  - More concise syntax and better IDE support

**Recommendation**: Use **Typer** for better type safety and modern Python integration.

#### Output Formatting (Rich)
- **Rich**: `rich >= 13.0.0`
- **Purpose**: Enhanced terminal output with tables, colors, and progress bars
- **Importation**: Provides beautiful console rendering, markdown support, and progress indicators
- **Installation**: `pip install rich`

### Package Management

#### UV (Recommended)
- **Purpose**: High-performance Python package manager and build tool
- **Advantages**:
  - 10-100x faster than pip and pip-tools
  - Automatic virtual environment management
  - Direct dependency resolution
  - Integrated build and dependency management

**Setup**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
uv init duckdb-processor
uv add duckdb typer rich pydantic
uv add --dev pytest mypy ruff black pre-commit
```

#### Poetry (Alternative)
- **Purpose**: Traditional Python package and dependency management
- **Setup**:
  ```bash
  pip install poetry
  poetry new duckdb-processor
  poetry add duckdb typer rich pydantic
  poetry add --dev pytest mypy ruff black pre-commit
  ```

## Linting and Formatting Tools

### Ruff (Recommended)
- **Purpose**: Extremely fast Python linter and code formatter
- **Configuration**: `pyproject.toml`
- **Installation**: `uv add ruff` or `poetry add ruff`

**pyproject.toml configuration**:
```toml
[tool.ruff]
line-length = 88
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Black
- **Purpose**: Opinionated code formatter
- **Configuration**: `pyproject.toml`
- **Installation**: `uv add black` or `poetry add black`

**pyproject.toml configuration**:
```toml
[tool.black]
line-length = 88
target-version = ["py313"]
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### MyPy
- **Purpose**: Static type checker
- **Configuration**: `pyproject.toml`
- **Installation**: `uv add mypy` or `poetry add mypy`

**pyproject.toml configuration**:
```toml
[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

### Pre-commit Hooks
- **Purpose**: Automated code quality checks
- **Installation**: `uv add pre-commit` or `poetry add pre-commit`

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
```

## Development Environment Requirements

### System Requirements
- **Operating System**: Linux, macOS, or Windows 10/11
- **Python**: 3.13.0 or higher
- **Memory**: Minimum 512MB RAM, 2GB+ recommended for large datasets
- **Storage**: 100MB for installation, plus space for data files

### Virtual Environment Setup
```bash
# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync  # or poetry install
```

### IDE Configuration

#### VS Code
**.vscode/settings.json**:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.ruff": true,
        "source.organizeImports.ruff": true
    }
}
```

### Development Tools
- **Git**: Version control
- **GitHub CLI**: For GitHub integration
- **Make**: Alternative to shell scripts (optional)
- **tmux**: For terminal multiplexing (recommended for development)

## Build and Deployment Configuration

### Build Configuration

#### pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "duckdb-data-processor"
version = "0.1.0"
description = "DuckDB-based CSV data processor with flexible parsing capabilities"
authors = [
    {name = "CJ-1981", email = "cj1981@example.com"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.13"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Data Scientists",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Database",
    "Topic :: Scientific/Engineering :: Information Analysis",
]

dependencies = [
    "duckdb>=0.9.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "tomli>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "pre-commit>=3.0.0",
    "types-PyYAML>=6.0.0",
]

[project.scripts]
duckdb-processor = "duckdb_data_processor.main:app"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "pre-commit>=3.0.0",
    "types-PyYAML>=6.0.0",
]
```

### Deployment Configuration

#### Docker Support
**Dockerfile**:
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY src/ ./src/
COPY config/ ./config/

ENTRYPOINT ["uv", "run", "duckdb-processor"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  duckdb-processor:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app/src
```

#### CI/CD Pipeline
**.github/workflows/ci.yml**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
        with:
          version: "latest"
      - run: uv sync --frozen
      - run: uv run pytest --cov=src --cov-report=xml
      - run: uv run mypy src/
      - run: uv run ruff check src/
      - run: uv run ruff format --check src/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
        with:
          version: "latest"
      - run: uv sync --frozen --no-dev
      - run: uv build
```

## Testing Framework

### pytest Configuration
**pyproject.toml**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=85",
    "-v"
]
```

### Test Requirements
- **Coverage**: 85%+ test coverage required
- **Table-driven tests**: For comprehensive test coverage
- **Integration tests**: For cross-component functionality
- **Characterization tests**: For legacy code behavior preservation

### Test Running
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/unit/test_processor.py

# Run tests with verbose output
uv run pytest -v
```

## Type Hints and Async/Await Considerations

### Type Hints
- **Full Type Coverage**: All functions and classes should have complete type hints
- **Pydantic Models**: For configuration and data validation
- **Union Types**: For handling multiple possible types
- **Optional Types**: For nullable values

### Async/Await Considerations
- **DuckDB Operations**: Most DuckDB operations are synchronous, but async I/O operations may benefit from async/await
- **File Operations**: Use async file operations for large file processing
- **CLI Interface**: Typer supports both sync and async command handlers
- **Concurrent Processing**: Consider concurrent processing for batch operations

**Example Async Implementation**:
```python
import asyncio
from typing import List
from duckdb import DuckDBPyConnection

async def process_files_concurrently(
    file_paths: List[str],
    db_connection: DuckDBPyConnection
) -> None:
    """Process multiple files concurrently."""
    tasks = [
        process_single_file(file_path, db_connection)
        for file_path in file_paths
    ]
    await asyncio.gather(*tasks)
```

## MoAI Python Rules Integration

### Configuration Integration
The project integrates with MoAI's Python rules through the `.moai/config/sections/` directory:

- **User Configuration**: `.moai/config/sections/user.yaml`
- **Language Configuration**: `.moai/config/sections/language.yaml`
- **Quality Standards**: `.moai/config/sections/quality.yaml`

### Development Workflow
1. **Planning Phase**: Use `/moai plan` to create specifications
2. **Development Phase**: Use `/moai run` to implement features with DDD approach
3. **Documentation Phase**: Use `/moai sync` to generate documentation
4. **Quality Assurance**: Ensure TRUST 5 framework compliance

### Code Quality Requirements
- **Tested**: 85%+ coverage with pytest
- **Readable**: Clear naming and comprehensive type hints
- **Unified**: Consistent formatting with ruff and black
- **Secured**: Input validation and secure data handling
- **Trackable**: Conventional commits and clear documentation

---

*This documentation is part of the DuckDB CSV Processor project. For more information, see the complete project documentation in `.moai/project/`.*