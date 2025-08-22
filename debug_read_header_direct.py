#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tometo_tomato as tt
import tempfile

def test_direct():
    """Test the actual read_header function directly"""

    # Test semicolon
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('col1;col2;col3\n1;2;3\n')
        csv_path = f.name

    try:
        result = tt.read_header(csv_path)
        print(f"Semicolon test result: {result}")
    except Exception as e:
        print(f"Semicolon test error: {e}")
    finally:
        os.unlink(csv_path)

    # Test tab
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('x\ty\tz\n1\t2\t3\n')
        csv_path = f.name

    try:
        result = tt.read_header(csv_path)
        print(f"Tab test result: {result}")
    except Exception as e:
        print(f"Tab test error: {e}")
    finally:
        os.unlink(csv_path)

if __name__ == "__main__":
    test_direct()
