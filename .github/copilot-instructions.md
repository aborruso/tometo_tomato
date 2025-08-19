<!-- Copilot instructions for contributors and automated coding agents -->
# tometo_tomato — Copilot instructions

This file gives focused, actionable guidance for AI coding agents working on the
tometo_tomato repository. Keep it short and concrete. Reference the project files
mentioned below when making code changes.

- Entry points
  - CLI: `tometo_tomato` installed via `setup.py` -> `tometo_tomato:main` (module in `src/`).
  - Direct runner: `python3 src/tometo_tomato.py` (script implements the core logic).

- Big picture
  - Purpose: fuzzy-joining two CSVs using DuckDB and (optionally) the `rapidfuzz` extension.
  - Flow: parse CLI args -> infer or accept explicit join pairs -> build DuckDB SQL -> compute per-pair similarity -> average score -> produce `--output-clean` and optional `--output-ambiguous` CSVs.
  - Key files: `README.md`, `src/README.md`, `src/tometo_tomato.py`, `setup.py`.

- Important patterns & conventions (do not change without tests)
  - Header parsing in `read_header` is intentionally naive (split on comma) to match existing behaviour; preserve this unless you add tests and update callers.
  - Similarity: prefers `rapidfuzz` extension; falls back to `levenshtein` or `damerau_levenshtein` when `rapidfuzz` unavailable. Keep the same ordering/logic when modifying `try_load_rapidfuzz` or the score expressions.
  - SQL construction: code builds raw DuckDB SQL and writes CSVs using `COPY (...) TO 'file'`. Be careful with quoting and injection when changing how columns or file paths are interpolated.
  - CLI flags: multiple `--join-pair` and `--add-field` are accepted; `--add-field` supports repeated entries or space-separated lists.

- Developer workflows / commands
  - Install (dev): pip install .  (or use the project's `uv` wrapper if available).
  - Run locally without install: `python3 src/tometo_tomato.py <input.csv> <ref.csv> [flags]`.
  - Tests: none exist. Add unit tests when changing parsing, inference, or SQL generation.

- Integration & external dependencies
  - DuckDB is required at runtime; the code uses `duckdb.connect(':memory:')` and `read_csv_auto`.
  - `rapidfuzz` is an optional extension loaded via DuckDB's `INSTALL rapidfuzz; LOAD rapidfuzz;` call; the package is listed in `setup.py` but code tolerates absence at runtime.

- Quick implementation contract (when editing core logic)
  - Inputs: two CSV paths, join pairs or infer flag, threshold, optional add-fields.
  - Outputs: `--output-clean` (required) CSV, optional `--output-ambiguous` CSV.
  - Error modes: exit with non-zero when no join pairs found or when no fuzzy function exists in DuckDB.

- Examples to reference
  - `python3 src/tometo_tomato.py data/raw/input.csv data/raw/ref.csv -i -a codice_comune -t 85 -s -o out.csv`
  - In `README.md` examples for `tometo_tomato` CLI.

- When making changes
  - Preserve existing command-line behavior unless explicitly updating the CLI contract in `README.md` and `setup.py` entry points.
  - Add unit tests for header parsing, `build_join_pairs` inference, and SQL-generation snippets.
  - If editing SQL assembly, run a local smoke test against `data/raw/input.csv` and `data/raw/ref.csv` (or the sample files in `data/raw/`) to confirm outputs.

If anything here is unclear or you need an example test harness, ask and I will add a tiny test script and CI notes.

- CI / repo policies
  - A minimal GitHub Actions workflow is provided at `.github/workflows/ci.yml` (runs pytest on push/PR to `main`).
  - Add tests under `tests/` for any change to parsing, inference or SQL generation. Keep tests small and deterministic (use temporary files via pytest `tmp_path`).
  - Prefer non-destructive smoke tests: use `data/raw/` sample CSVs when validating SQL output locally.

- Running tests locally
  - The test suite imports the package `tometo_tomato`. Either install the package in editable mode or set PYTHONPATH:

    - Install editable (recommended):

      ```bash
      pip install -e .
      pytest -q
      ```

    - Or run without installing (quick):

      ```bash
      PYTHONPATH=$(pwd)/src pytest -q
      ```

