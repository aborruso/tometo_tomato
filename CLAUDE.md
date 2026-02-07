# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

tometo_tomato is a Python CLI tool for fuzzy-joining two CSV files using DuckDB and rapidfuzz. It handles typos, abbreviations, accents, and formatting differences to associate similar records across sources.

## Commands

```bash
# Preferred (uv)
uv sync
uv run pytest -q
uv run tometo_tomato data/input.csv data/ref.csv -j "name,ref_name" --latinize -a city_code -t 85 -s -o tmp/out.csv

# Install (editable, for development)
pip install -e .

# Run tests
pytest -q

# Run tests without installing
PYTHONPATH=$(pwd)/src pytest -q

# Run a single test
pytest tests/test_core.py::test_read_header -v

# Smoke test against sample data
tometo_tomato data/input.csv data/ref.csv -j "name,ref_name" --latinize -a city_code -t 85 -s -o tmp/out.csv

# Run without installing
python3 src/tometo_tomato/tometo_tomato.py data/input.csv data/ref.csv -j "name,ref_name" -o tmp/out.csv
```

## Architecture

Single-module CLI (`src/tometo_tomato/tometo_tomato.py`, ~620 lines) with this flow:

1. **`parse_args()`** - argparse with 30+ flags
2. **`read_header(path)`** - detects CSV columns via DuckDB's `read_csv_auto` with `LIMIT 0`
3. **`build_join_pairs(args)`** - explicit `-j col1,col2` pairs or auto-inference from similar column names
4. **Normalization** - temporary DuckDB views apply case/whitespace/latinize/alphanumeric transformations
5. **`choose_score_expr()`** - builds fuzzy score SQL; prefers rapidfuzz extension, falls back to levenshtein/damerau_levenshtein
6. **SQL generation** - CROSS JOIN (or blocked JOIN with `--block-prefix`) + score calculation
7. **Output** - `COPY (...) TO 'file'` producing clean matches CSV (LEFT JOIN, all input rows) and optional ambiguous matches CSV

Entry point: `tometo_tomato.tometo_tomato:main` (registered in `pyproject.toml`).

## Key Patterns

- **Similarity fallback chain**: rapidfuzz extension → levenshtein → damerau_levenshtein. Preserve this order in `try_load_rapidfuzz()`.
- **SQL construction**: raw DuckDB SQL built as strings. Be careful with quoting/injection when changing column or file path interpolation.
- **LEFT JOIN behavior**: clean output always includes all input rows; unmatched rows have empty reference fields. This is a core contract.
- **Temporary views**: normalization is applied via DuckDB temp views before matching, keeping original data intact in output.
- **`--add-field`**: accepts repeated `-a field` or space-separated lists to add reference columns to output.

## Testing

- Tests in `tests/` use pytest with `tmp_path` for temporary CSV files.
- Tests import `tometo_tomato as tt` — package must be installed or `PYTHONPATH` set.
- CI runs on Python 3.11 (`.github/workflows/ci.yml`).
- After any change to parsing, inference, or SQL generation: add tests and run smoke test against `data/input.csv` + `data/ref.csv`.

## OpenSpec Workflow

For proposals, specs, breaking changes, or architecture shifts, follow the OpenSpec workflow in `openspec/AGENTS.md`. Change proposals go in `openspec/changes/`, specs in `openspec/specs/`.

## Dependencies

- **duckdb** - core SQL engine (required)
- **rapidfuzz** - fuzzy matching (required in pyproject.toml, but code tolerates absence at runtime)
- **numpy** - needed for DuckDB Python UDFs
- **unidecode** - optional, required only when `--latinize` is used
