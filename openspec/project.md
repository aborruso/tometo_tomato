# Project Context

## Purpose
tometo_tomato is a Python CLI tool for performing fuzzy joins between two CSV files, designed to handle data with typos, abbreviations, or different formatting. It leverages DuckDB and the rapidfuzz extension to associate similar records across different sources. The tool is particularly useful for data cleaning workflows where exact matches are not possible due to data quality issues.

## Tech Stack
- **Python 3.8+**: Core programming language
- **DuckDB**: In-memory analytical database for fast CSV processing and SQL operations
- **rapidfuzz**: Fuzzy string matching library (with fallback to DuckDB's built-in levenshtein functions)
- **numpy**: Required for DuckDB Python UDFs
- **pytest**: Testing framework
- **setuptools**: Package building and distribution

## Project Conventions

### Code Style
- **Imports**: Standard library imports first, then third-party, then local imports. Use absolute imports within the package.
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants.
- **Docstrings**: Use triple-quoted strings for function/class documentation following Google style.
- **Type hints**: Use typing module for function parameters and return types where beneficial.
- **Line length**: No strict limit, but aim for readability (typically <100 characters).
- **Error handling**: Use logging module for messages, raise exceptions for errors, avoid print statements.
- **SQL**: Use uppercase for SQL keywords, proper indentation for multi-line queries.

### Architecture Patterns
- **CLI-first design**: Pure command-line interface with no GUI components.
- **SQL-centric processing**: Leverages DuckDB for all data operations, treating CSV files as database tables.
- **Preprocessing pipeline**: Data normalization (case, whitespace, latinization) applied before fuzzy matching.
- **Temporary views**: Uses DuckDB temporary views for intermediate processing steps.
- **Fallback mechanisms**: Graceful degradation when rapidfuzz extension unavailable (uses built-in levenshtein).
- **Blocking optimization**: Optional prefix-based blocking to reduce computational complexity on large datasets.

### Testing Strategy
- **Framework**: pytest for all tests.
- **Test types**: Unit tests for core functions, integration tests for end-to-end CLI functionality.
- **Test data**: Temporary CSV files created in test fixtures using tmp_path.
- **Coverage**: Focus on core logic, CLI argument parsing, and output validation.
- **CI/CD**: Automated testing on GitHub Actions for Python 3.11 on Ubuntu.
- **Installation**: Tests run against editable package installation (`pip install -e .`).

### Git Workflow
- **Main branch**: `main` as the primary branch.
- **Commits**: Concise, imperative mood messages. Use present tense ("Add feature" not "Added feature").
- **Pull requests**: Required for all changes, with descriptive titles and summaries.
- **CI triggers**: Only on changes to source code, tests, or configuration files.
- **Versioning**: Uses setuptools_scm for automatic versioning from git tags.
- **Changelog**: LOG.md maintained with date-based entries for significant changes.

## Domain Context
This tool operates in the data engineering and ETL space, specifically for record linkage and data deduplication tasks. Common use cases include:

- Matching customer data across different systems with varying name formats
- Linking geographical data (cities, regions) with spelling variations
- Reconciling financial records with inconsistent formatting
- Entity resolution in master data management

The tool handles common data quality issues: case variations, extra whitespace, accented characters, different encodings, and partial matches.

## Important Constraints
- **Performance**: Must handle large CSV files efficiently using DuckDB's in-memory processing.
- **Memory usage**: DuckDB operations are memory-bound; tool warns on large datasets (>10M combinations).
- **Dependencies**: Minimal dependencies to ensure easy installation; rapidfuzz is optional with fallback.
- **Data integrity**: Preserves original data in outputs while normalizing for matching.
- **Cross-platform**: Must work on Linux, macOS, and Windows (Python + DuckDB compatibility).

## External Dependencies
- **DuckDB**: Core database engine; uses community extensions for rapidfuzz.
- **rapidfuzz**: Fuzzy matching algorithms; falls back to DuckDB built-ins if unavailable.
- **GitHub Actions**: CI/CD pipeline for automated testing.
- **PyPI**: Package distribution (setuptools-based).
