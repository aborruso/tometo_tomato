#!/usr/bin/env python3
import duckdb
import tempfile

def debug_csv_detection():
    """Debug CSV delimiter detection issues"""

    # Test with semicolon delimiter
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('col1;col2;col3\n1;2;3\n')
        csv_path = f.name

    con = duckdb.connect(database=":memory:")

    print("=== Original approach (full query) ===")
    q1 = f"SELECT * FROM read_csv_auto('{csv_path}', header=true, all_varchar=true)"
    res1 = con.execute(q1)
    desc1 = getattr(res1, 'description', None)
    if desc1:
        print(f"Full query columns: {[c[0] for c in desc1]}")

    print("\n=== LIMIT 0 approach ===")
    q2 = f"SELECT * FROM read_csv_auto('{csv_path}', header=true, all_varchar=true) LIMIT 0"
    res2 = con.execute(q2)
    desc2 = getattr(res2, 'description', None)
    if desc2:
        print(f"LIMIT 0 columns: {[c[0] for c in desc2]}")

    print("\n=== Fetch one row to compare ===")
    try:
        row = con.execute(q1).fetchone()
        print(f"First row data: {row}")
    except Exception as e:
        print(f"Error fetching row: {e}")

    import os
    os.unlink(csv_path)

if __name__ == "__main__":
    debug_csv_detection()
