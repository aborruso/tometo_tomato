## Why
The tool currently fails with internal DuckDB errors when processing CSV files with non-UTF-8 encoding, as seen in the debug/duckdb_bug_report.md. Adding an upfront encoding check prevents these errors and provides clear feedback to users.

## What Changes
- Add encoding validation for input CSV files before processing
- Block execution if files are not UTF-8 encoded
- Provide clear error message indicating the encoding issue

## Impact
- Affected specs: csv-processing (new capability for file validation)
- Affected code: Main CLI script to add validation before DuckDB operations
- No breaking changes to existing API