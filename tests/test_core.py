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
        "python3", "src/tometo_tomato/tometo_tomato.py",
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

def test_scorer_option(tmp_path):
    """Verify that the --scorer option works and token_set_ratio gives a higher score for specific cases."""
    # Try to install rapidfuzz, skip if it fails (e.g., in CI without network)
    try:
        con = duckdb.connect()
        con.execute("INSTALL rapidfuzz FROM community;")
        con.close()
    except Exception as e:
        pytest.skip(f"Could not install rapidfuzz extension, skipping scorer test. Reason: {e}")

    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_ratio_path = tmp_path / "output_ratio.csv"
    output_token_set_path = tmp_path / "output_token_set.csv"

    # Create test files
    write_csv(input_path, "id,city", ["1,Reggio Calabria"])
    write_csv(ref_path, "id_ref,city_ref", ["101,Reggio di Calabria"])

    # --- Run with default scorer (ratio) ---
    cmd_ratio = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "city,city_ref",
        "-s", # show score
        "-o", str(output_ratio_path)
    ]
    result_ratio = subprocess.run(cmd_ratio, capture_output=True, text=True)
    assert result_ratio.returncode == 0, f"Script failed with ratio scorer: {result_ratio.stderr}"

    # --- Run with token_set_ratio scorer ---
    cmd_token_set = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "city,city_ref",
        "-s", # show score
        "--scorer", "token_set_ratio",
        "-o", str(output_token_set_path)
    ]
    result_token_set = subprocess.run(cmd_token_set, capture_output=True, text=True)
    assert result_token_set.returncode == 0, f"Script failed with token_set_ratio scorer: {result_token_set.stderr}"

    # --- Compare scores ---
    with open(output_ratio_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        header_ratio = lines[0].strip().split(',')
        data_ratio = lines[1].strip().split(',')
        score_ratio = float(data_ratio[header_ratio.index('avg_score')])

    with open(output_token_set_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        header_token_set = lines[0].strip().split(',')
        data_token_set = lines[1].strip().split(',')
        score_token_set = float(data_token_set[header_token_set.index('avg_score')])

    # Assert that token_set_ratio is better and ideally 100
    assert score_token_set > score_ratio
    assert score_token_set == 100.0


def test_clean_whitespace_option(tmp_path):
    """Verify that the --clean-whitespace option removes redundant whitespace before matching."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"
    output_no_clean_path = tmp_path / "output_no_clean.csv"

    # Create test files with redundant whitespace
    with open(input_path, "w", encoding="utf-8") as f:
        f.write("city\n")
        f.write("Rome   City\n")  # Multiple spaces

    with open(ref_path, "w", encoding="utf-8") as f:
        f.write("city\n")
        f.write("  Rome City  \n")  # Leading/trailing and internal spaces

    # Run without --clean-whitespace
    cmd_no_clean = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "city,city",
        "-o", str(output_no_clean_path),
        "-s", "-t", "50"  # Lower threshold to see the difference
    ]
    
    result_no_clean = subprocess.run(cmd_no_clean, capture_output=True, text=True)
    assert result_no_clean.returncode == 0, f"Script failed with error: {result_no_clean.stderr}"

    # Run with --clean-whitespace
    cmd_clean = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "city,city",
        "-o", str(output_path),
        "--clean-whitespace",
        "-s", "-t", "50"  # Lower threshold to see the difference
    ]
    
    result_clean = subprocess.run(cmd_clean, capture_output=True, text=True)
    assert result_clean.returncode == 0, f"Script failed with error: {result_clean.stderr}"

    # Check both output files
    def extract_score(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) < 2:
            return 0.0  # No match found
        data_row = lines[1].strip()
        return float(data_row.split(",")[-1])

    score_no_clean = extract_score(output_no_clean_path)
    score_clean = extract_score(output_path)
    
    # With whitespace cleaning, the score should be higher (closer to 100)
    # because "Rome   City" vs "  Rome City  " becomes "Rome City" vs "Rome City"
    assert score_clean > score_no_clean, f"Clean whitespace should improve score: {score_clean} > {score_no_clean}"
    assert score_clean > 90.0, f"After cleaning, score should be very high: {score_clean}"
