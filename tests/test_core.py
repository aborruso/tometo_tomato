import os
import subprocess
from types import SimpleNamespace

import pytest

import tometo_tomato as tt


def write_csv(path, header, rows=None):
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        if rows:
            for r in rows:
                f.write(r + "\n")


def test_read_header(tmp_path):
    p = tmp_path / "a.csv"
    write_csv(p, 'col1,col2,col3', ['1,2,3'])
    hdr = tt.read_header(str(p))
    assert hdr == ['col1', 'col2', 'col3']


def test_build_join_pairs_with_explicit_pair(tmp_path):
    inp = tmp_path / "inp.csv"
    ref = tmp_path / "ref.csv"
    write_csv(inp, 'a,b')
    write_csv(ref, 'x,y')
    args = SimpleNamespace(join_pair=['a,x'], infer_pairs=False, input_file=str(inp), reference_file=str(ref), infer_threshold=0.7)
    pairs = tt.build_join_pairs(args)
    assert pairs == ['a,x']


def test_build_join_pairs_infer(tmp_path):
    inp = tmp_path / "inp2.csv"
    ref = tmp_path / "ref2.csv"
    # similar names: regio <-> regione, comu <-> comune
    write_csv(inp, 'regio,comu,other')
    write_csv(ref, 'regione,comune,other_ref')
    args = SimpleNamespace(join_pair=None, infer_pairs=True, input_file=str(inp), reference_file=str(ref), infer_threshold=0.6)
    pairs = tt.build_join_pairs(args)
    # Expect at least one inferred pair
    assert any(',' in p for p in pairs)


def test_add_field_with_spaces(tmp_path):
    """Verify that --add-field works with column names containing spaces."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"

    # Create test files
    with open(input_path, "w", encoding="utf-8") as f:
        f.write("id,city\n")
        f.write("1,rome\n")
        f.write("2,milan\n")

    with open(ref_path, "w", encoding="utf-8") as f:
        f.write('"City Name","Special ID"\n')
        f.write('"Rome","ID-ROME-123"\n')
        f.write('"Milan","ID-MILAN-456"\n')

    # Run the main script as a subprocess
    cmd = [
        "python3", "src/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "city,City Name",
        "-a", "Special ID",
        "-o", str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

    # Check the output file
    with open(output_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    assert len(lines) == 3 # Header + 2 data rows
    header = lines[0].strip()
    assert header == "city,ref_City Name,Special ID"
    
    # Check content - order might vary
    rows = {lines[1].strip(), lines[2].strip()}
    assert "rome,Rome,ID-ROME-123" in rows
    assert "milan,Milan,ID-MILAN-456" in rows