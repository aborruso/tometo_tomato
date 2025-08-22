#!/usr/bin/env python3
"""Test script to verify if pandas is actually needed in read_header()"""

import duckdb
import tempfile
import os

def test_duckdb_column_info():
    """Test different ways to get column names from DuckDB without pandas"""

    # Create a test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('col1,col2,col3\n1,2,3\n')
        csv_path = f.name

    try:
        con = duckdb.connect(database=":memory:")
        safe_path = csv_path.replace("'", "''")

        # Test 1: description attribute (current primary method)
        print("=== Test 1: description attribute ===")
        q = f"SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true)"
        res = con.execute(q)
        desc = getattr(res, 'description', None)
        if desc:
            cols_from_desc = [c[0] for c in desc]
            print(f"Columns from description: {cols_from_desc}")
        else:
            print("Description is None")

        # Test 2: fetchdf() method (current fallback)
        print("\n=== Test 2: fetchdf() method ===")
        try:
            df = res.fetchdf()
            cols_from_fetchdf = list(df.columns)
            print(f"Columns from fetchdf(): {cols_from_fetchdf}")
            print(f"DataFrame type: {type(df)}")
        except Exception as e:
            print(f"fetchdf() failed: {e}")

        # Test 3: fetchall() method with LIMIT 0 (alternative approach)
        print("\n=== Test 3: fetchall() with LIMIT 0 ===")
        try:
            q_limit = f"SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true) LIMIT 0"
            res2 = con.execute(q_limit)
            desc2 = getattr(res2, 'description', None)
            if desc2:
                cols_from_limit = [c[0] for c in desc2]
                print(f"Columns from LIMIT 0 description: {cols_from_limit}")
            else:
                print("LIMIT 0 description is None")
        except Exception as e:
            print(f"LIMIT 0 approach failed: {e}")

        # Test 4: Information schema approach
        print("\n=== Test 4: Using SQL schema info ===")
        try:
            # First read the CSV into a temporary table
            con.execute(f"CREATE TEMP TABLE temp_csv AS SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true)")

            # Query column information
            cols_info = con.execute("PRAGMA table_info('temp_csv')").fetchall()
            cols_from_pragma = [row[1] for row in cols_info]  # column name is at index 1
            print(f"Columns from PRAGMA table_info: {cols_from_pragma}")
        except Exception as e:
            print(f"PRAGMA approach failed: {e}")

        # Test 5: DESCRIBE approach
        print("\n=== Test 5: DESCRIBE approach ===")
        try:
            describe_result = con.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true) LIMIT 0").fetchall()
            cols_from_describe = [row[0] for row in describe_result]  # column name should be first column
            print(f"Columns from DESCRIBE: {cols_from_describe}")
        except Exception as e:
            print(f"DESCRIBE approach failed: {e}")

        con.close()

    finally:
        # Clean up
        os.unlink(csv_path)

if __name__ == "__main__":
    test_duckdb_column_info()
