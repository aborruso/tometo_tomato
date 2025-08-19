#!/usr/bin/env python3
"""Minimal DuckDB example: write a semicolon-delimited CSV and read it with DuckDB."""
import duckdb
from pathlib import Path

p = Path('tmp_csvs/hello_semi.csv')
# Ensure tmp_csvs exists
p.parent.mkdir(parents=True, exist_ok=True)

# Write a semicolon-delimited CSV with 4 rows and 2 columns
p.write_text('colA;colB\n1;one\n2;two\n3;three\n4;four\n', encoding='utf-8')
print('Wrote', p)

# Read it via SQL (read_csv_auto) to leverage DuckDB's autodetection
con = duckdb.connect()
q = f"SELECT * FROM read_csv_auto('{str(p)}', header=true, all_varchar=true);"
print('Running query:', q)
res = con.execute(q)
print(res.fetchall())
print('Column names:', [c[0] for c in res.description])
