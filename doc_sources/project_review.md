# Project Review: tometo_tomato

## Overview
- Purpose: Python CLI to fuzzy-join CSVs using DuckDB + rapidfuzz.
- Structure: single entrypoint (`tometo_tomato`), core logic in `src/tometo_tomato/tometo_tomato.py`, tests in `tests/`, Quarto docs in `doc_sources/` → built site in `docs/`.
- Packaging: `pyproject.toml` + `setup.py` with setuptools_scm; CLI entry configured.

## Strengths
- Solid CSV ingestion: uses `read_csv_auto(..., header=true, all_varchar=true)` and a robust header detection with `LIMIT 0` fallback.
- Flexible matching: multi-column joins, optional pair inference, and selective normalization flags (`--raw-case`, `--raw-whitespace`, `--latinize`, `--keep-alphanumeric`).
- Ambiguity handling: clear definition (ties on max avg_score), clean vs ambiguous outputs, helpful warnings.
- Fuzzy fallback: tries rapidfuzz; falls back to `levenshtein`/`damerau_levenshtein` when unavailable.
- Sensible CLI/UX: verbosity controls, overwrite protection via `--force`.
- Tests present: cover headers, pair building, overwrites, whitespace/latinize.

## Key Risks / Issues
- Scalability: `CROSS JOIN` of input × reference in `all_scores` can explode on large datasets despite threshold filtering.
- SQL path quoting: some `read_csv_auto('{args.input_file}')` calls don’t escape single quotes; `read_header()` does but others should too.
- Flags vs docs mismatch: README mentions `--clean-whitespace` but code uses `--raw-whitespace`. `--add-field` help suggests “space separated” but implementation is `append` only.
- Versioning inconsistency: `pyproject.toml` sets a static `version`, while setuptools_scm generates `src/_version.py` (committed). Mixed approaches can drift.
- Test import bug: `tests/test_core.py::test_scorer_option` uses `duckdb` without importing it; test likely skips unintentionally.
- Accent normalization: `strip_accents(...)` used in SQL may depend on DuckDB build/extensions; not explicitly ensured/loaded.
- Output shape: “clean” output includes only join columns from input (not all input columns). May surprise users expecting a full left join; needs docs or an option.

## Recommendations
- Performance/blocking:
  - Add lightweight prefilters (length bands, first-letter match, region/province exact block) before distance computation.
  - Consider per-input top-1 selection without fully materializing `all_scores` (e.g., ORDER BY avg_score DESC LIMIT 1 per block).
- SQL safety:
  - Create a helper to quote file paths (escape single quotes) and reuse it across all `read_csv_auto` calls.
- CLI and docs alignment:
  - Replace `--clean-whitespace` in README with `--raw-whitespace` and clarify defaults.
  - For `--add-field`, either implement parsing of multiple names in a single argument or adjust help to “repeat the flag”.
  - Add an option `--all-input-columns` to include all input columns in the clean output.
  - Validate outputs don’t overwrite input/reference files.
- Packaging/versioning:
  - Adopt setuptools_scm fully: remove static `version` from `pyproject.toml`, mark `dynamic = ["version"]`, and stop committing `src/_version.py`.
  - If `strip_accents` requires an extension (e.g., ICU), `INSTALL/LOAD` it or document the requirement.
- Tests/CI:
  - Fix missing `import duckdb` in `tests/test_core.py`.
  - Add tests for `--infer-pairs` edge thresholds, missing columns, and file paths with quotes/spaces.
  - Add ruff/black (and optionally mypy) to CI; test matrix for Python 3.8–3.12.
- Code hygiene:
  - Remove unused Python UDF for latinize (logic is in SQL).
  - Factor `main()` into smaller functions: building views, scoring expression, clean/ambiguous writers.

## File-Specific Notes
- `src/tometo_tomato/tometo_tomato.py`:
  - Quote `args.input_file`/`args.reference_file` like `read_header()` does.
  - Ensure `strip_accents` availability or provide a fallback/documentation.
  - Consider preserving user column order in `prepare_select_clauses` rather than sorted sets.
- `tests/test_core.py`:
  - Add `import duckdb` at the top to ensure `test_scorer_option` executes as intended.

## Documentation
- Fix README sections: duplicate “Basic example”, flag naming mismatch, and clarify output columns (join-only vs all input; add example and option).
- Add a “Performance Tips” section: blocking strategies, thresholds, and when to use `token_set_ratio`.

## Suggested Next Steps
- Quick fixes: path escaping, README alignment, overwrite safeguards, test import.
- Medium: add `--all-input-columns`, introduce simple blocking/prefilters.
- Long: module refactor (cli/engine/io_utils), richer blocking strategies, benchmarking guidance.

