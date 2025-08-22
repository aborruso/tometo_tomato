# LOG

## 2025-08-22

- Added `--raw-case` flag to allow case-sensitive fuzzy matching (preserve original case during comparisons). (closes #26)
- Implemented `--raw-whitespace` to disable default whitespace normalization; default behavior trims and collapses repeated spaces for more robust matching. (closes #27)
- Implemented `--latinize` option using `unidecode` (registered as a DuckDB UDF) so accented and special characters are normalized for scoring while preserving original characters in outputs.
- Unified example input files under `data/` (`data/input.csv` and `data/ref.csv`) with comprehensive test cases for case, whitespace, and accent normalization.
- Updated README and Copilot instructions to document normalization flags and example usage.
- Added unit tests for whitespace normalization and latinization; updated existing tests to match new flags and behavior.
- Updated `.gitignore` to exclude common virtual environment directories (e.g. `.venv/`) and cleaned temporary sample CSVs from the repo.
- General cleanup and refactoring of SQL and UDF registration logic to apply normalization only during scoring.

## 2025-08-20

- Ottimizzato il trigger del workflow di CI per l'attivazione solo su modifiche a file di codice, test o configurazione.
- Created basic Quarto documentation configuration.

## 2025-08-19

- Aggiunto il parametro `--scorer` per selezionare l'algoritmo di matching (`ratio` o `token_set_ratio`).
- Aggiornato README.md con esempi per nomi di campo con spazi.
- Corretto un bug nella selezione delle colonne in `tometo_tomato.py` che causava la duplicazione delle colonne di input quando i nomi coincidevano con quelli del file di riferimento (issue #11).
- Resolved Issue #7: Changed default output logic.
- Resolved Issue #8: Verified handling of field names with spaces.
- Resolved Issue #9: Implemented generation of ambiguous matches file only when explicitly requested.
- Resolved Issue #10: Translated all stdout messages to English.
- Migrated the fuzzy join script from bash to Python CLI.
- Improved output logic for clean and ambiguous matches.
- Configured package installation with `setup.py` and `pyproject.toml`.
- Added test files for field names with spaces.
- Updated `.gitignore` to exclude build artifacts and processed/interim data.

## 2025-08-18

- Created the Python version of the fuzzy join script (`src/fuzzy_join.py`).
- Updated README and PRD with details on CLI installation and usage.
- Added `tometo_tomato` script for fuzzy joining CSV files.
- Implemented the fuzzy join process with dynamic column selection and output management.
- Refactored the CLI with `bashly`.
- Updated the script for the ISTAT/unofficial data example.
- Updated the PRD with the ISTAT/unofficial data example.
- Created the initial script for fuzzy join.
- Created `GEMINI.md` for project context.
- Added the Product Requirements Document for fuzzy join.
- Complete refactoring of the Bash script logic:
  - Fuzzy comparison always case-insensitive (LOWER).
  - LEFT JOIN: all input records are always present in the output.
  - Clean and ambiguous output parameters managed as requested.
  - Ambiguous output generated only if requested, with clear messages in shell.
  - If no ambiguous records, the file is deleted and the shell notifies.
  - Updated README with current logic, parameters, and behavior.
  - Tested the CLI with various output and ambiguity scenarios.
