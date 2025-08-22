# PRD: Flexible Join Procedure (Fuzzy Join)

## Introduction

### Context

Integrating data from different sources often presents a common challenge: the lack of unique and consistent join keys. Typos, abbreviations, formatting variations, or simple discrepancies (e.g., "Reggio di Calabria", "Reggio Calabria", "Reggiò Calabria") render standard SQL joins (`A.key = B.key`) ineffective.

This document defines the requirements for a "fuzzy join" procedure that allows connecting records between two tables based on the textual similarity of fields, rather than an exact match.

### Objective

To create a robust, configurable, and high-performance process for performing table joins via *fuzzy string matching*. The system must identify the best possible match for each record, transparently handle ambiguities, and provide clear, analysis-ready outputs.

## Functional Requirements

### FR1: Similarity-Based Join Logic

The procedure allows performing a join between table A (left) and table B (right) based on the similarity of one or more pairs of text columns.
**New Feature:** If the columns to compare (`--join-pair`) are not specified, the system automatically uses all columns with the same name present in both files.

### Normalization and Raw Comparison

- By default:
  - Column matching is **case insensitive** (comparison ignores upper/lower case).
  - Multiple and leading/trailing whitespaces are **removed** from each field before comparison.
- CLI options:
  - `--raw-case`: enables case sensitive comparison (disables lower-case conversion)
  - `--raw-whitespace`: preserves whitespaces (disables whitespace normalization)
  - `--latinize`: normalizes accented characters and apostrophes, converting non-latin characters to latin and removing special characters (e.g. "Cefalù" and "Cefalu'" both become "Cefalu")
- All options can be combined as needed.

### FR2: Similarity Score Calculation

For each record in table A, the system calculates a similarity score (from 0 to 100) with all records in table B, using the `rapidfuzz` extension functions for DuckDB.

### FR3: Best Match Selection

- The system identifies the "best match" as the record in table B that obtains the highest similarity score.
- A join is valid only if the score exceeds a **configurable minimum threshold** (e.g., `85`). All matches with a lower score are discarded.

### FR4: Multi-column Join Support

The procedure supports joining based on multiple column pairs. If not specified, it uses all common columns.

### FR5: Ambiguity and Duplicate Handling

- **Definition of ambiguity**: Ambiguity occurs when a record in table A obtains the **same maximum score** for multiple records in table B.
- **Handling**: In case of ambiguity, record A and all corresponding records in B are excluded from the final join result.
- **Ambiguity Output**: All records excluded due to ambiguity are saved to a separate file (e.g., `ambiguous_log.csv`) for manual analysis.

### FR6: Output Structure

The procedure produces two main outputs:
1.  **Clean Join Table**: A file with records that found a unique match above the threshold.
2.  **Ambiguity Log File**: A file with records discarded due to the reasons described in FR5.

## Non-Functional Requirements

### NFR1: Performance

The procedure is optimized to handle large datasets. The use of `WHERE score > threshold` in DuckDB reduces computational load.

### NFR2: Configurability

The user can easily configure:
- Input file paths.
- Column names to use for the join (optional; if omitted, common columns are used).
- Similarity threshold (number from 0 to 100).
- `rapidfuzz` function to use (e.g., `rapidfuzz_ratio`, `rapidfuzz_token_sort_ratio`).
- Output file paths.

### NFR3: Traceability

The process produces an execution log with key statistics: number of input records, successful joins, ambiguous cases.

## Technology Stack

- **Processing Engine**: DuckDB
- **Fuzzy Matching Library**: `rapidfuzz` extension for DuckDB
- **Orchestration**: Python script (single-command CLI: `tometo_tomato`)

## Documentation

The project documentation will be published using Quarto, leveraging the project's `docs` folder.

## Example Use Case (ISTAT Code Association)

This use case demonstrates the association of ISTAT codes with an unofficial registry, managing inaccuracies in place names.

**Table A (`ref.csv` - Official ISTAT Source)**
  Contains official data of Italian municipalities.

  | region     | municipality      | municipality_code |
  | :--------- | :--------------- | :---------------- |
  | Calabria   | Reggio Calabria  | 80065             |
  | Lombardy   | Milan            | 015146            |
  | Piedmont   | Turin            | 001272            |
  | Lazio      | Rome             | 058091            |
  | Campania   | Naples           | 063049            |

**Table B (`input.csv` - Unofficial Registry)**
  Contains data with possible typos.

  | region     | municipality      |
  | :--------- | :--------------- |
  | Calabria   | Reggio Calabr    |
  | Lombardy   | Milan            |
  | Piedmont   | Torinoo          |
  | Lazio      | Rma              |
  | Campania   | Naples           |

**Objective**
  Associate the `municipality_code` from Table A (`ref.csv`) with records in Table B (`input.csv`).

**Configuration (CLI Call Example)**
  The process is executed via the single-command CLI `tometo_tomato`:

  ```bash
  tometo_tomato input.csv ref.csv --join-pair region,region --join-pair municipality,municipality --add-field municipality_code --threshold 90 --show-score
  ```

  Or, if the columns to compare coincide in the two files:

  ```bash
  tometo_tomato input.csv ref.csv --add-field municipality_code --threshold 90 --show-score
  ```

  The process identifies the best match for each row in `input.csv` within `ref.csv` and associates the corresponding `municipality_code`.

  Example of expected matches:
  - `input.csv` (Reggio Calabr, Calabria) -> `ref.csv` (Reggio Calabria, Calabria) with `municipality_code` 80065.
  - `input.csv` (Torinoo, Piedmont) -> `ref.csv` (Turin, Piedmont) with `municipality_code` 001272.
  - `input.csv` (Rma, Lazio) -> `ref.csv` (Rome, Lazio) with `municipality_code` 058091.

  The final result is a table with the columns from `input.csv` plus the associated `municipality_code`.
