Title: Use DuckDB to detect CSV headers instead of naive comma split

Description
-----------
The current implementation of `read_header` in `src/tometo_tomato.py` naively reads the first line and splits on comma. This fails for many valid CSV files that use different delimiters (semicolon, tab) or have quoted fields containing commas.

Proposal
--------
- Use DuckDB's `read_csv_auto()` to read just the header/schema (for example with `SELECT * FROM read_csv_auto(file, header=true) LIMIT 0`) to obtain column names. DuckDB's CSV auto-detection is robust and already used for data loading.
- Provide a small, safe Python fallback using `csv.Sniffer` when DuckDB cannot be used (e.g. older DuckDB versions or missing Python bindings).

Motivation
----------
Using DuckDB for header detection keeps behavior consistent between header inference and actual CSV parsing performed later with `read_csv_auto`. It avoids mismatches between the header parsing logic and DuckDB's CSV loader.

Suggested change
----------------
Replace the `read_header` function with an implementation that:
1. Opens an in-memory DuckDB connection.
2. Uses `read_csv_auto('{path}', header=true, all_varchar=true)` and executes `SELECT * FROM read_csv_auto(... ) LIMIT 0` to get the column names from the returned cursor description or via `fetchdf()`.
3. On failure, fallback to `csv.Sniffer` as a best-effort.

Please refer to `src/tometo_tomato.py` for the current implementation.
