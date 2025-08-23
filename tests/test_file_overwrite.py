import os
import subprocess
import pytest


def write_csv(path, header, rows=None):
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        if rows:
            for r in rows:
                f.write(r + "\n")


def test_force_flag_bypasses_overwrite_prompt(tmp_path):
    """Test that the --force flag bypasses file overwrite prompts."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"

    # Create test input files
    write_csv(input_path, "name", ["Mario Rossi"])
    write_csv(ref_path, "name", ["Mario Rossi"])
    
    # Create existing output file
    output_path.write_text("existing content")
    
    # Run with --force flag - should not prompt
    cmd = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "name,name",
        "-o", str(output_path),
        "--force"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # File should be overwritten
    content = output_path.read_text()
    assert "existing content" not in content
    assert "name,ref_name" in content


def test_short_force_flag_bypasses_overwrite_prompt(tmp_path):
    """Test that the -f flag (short version) bypasses file overwrite prompts."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"

    # Create test input files
    write_csv(input_path, "name", ["Mario Rossi"])
    write_csv(ref_path, "name", ["Mario Rossi"])
    
    # Create existing output file
    output_path.write_text("existing content")
    
    # Run with -f flag - should not prompt
    cmd = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "name,name",
        "-o", str(output_path),
        "-f"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # File should be overwritten
    content = output_path.read_text()
    assert "existing content" not in content
    assert "name,ref_name" in content


def test_nonexistent_file_does_not_prompt(tmp_path):
    """Test that non-existent files don't trigger prompts."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"

    # Create test input files
    write_csv(input_path, "name", ["Mario Rossi"])
    write_csv(ref_path, "name", ["Mario Rossi"])
    
    # Don't create output file - should not prompt
    cmd = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "name,name",
        "-o", str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # File should be created
    assert output_path.exists()
    content = output_path.read_text()
    assert "name,ref_name" in content


def test_overwrite_prompt_with_no_response_cancels(tmp_path):
    """Test that answering 'no' to overwrite prompt cancels operation."""
    input_path = tmp_path / "input.csv"
    ref_path = tmp_path / "ref.csv"
    output_path = tmp_path / "output.csv"

    # Create test input files
    write_csv(input_path, "name", ["Mario Rossi"])
    write_csv(ref_path, "name", ["Mario Rossi"])
    
    # Create existing output file
    original_content = "existing content"
    output_path.write_text(original_content)
    
    # Run and simulate 'no' response
    cmd = [
        "python3", "src/tometo_tomato/tometo_tomato.py",
        str(input_path), str(ref_path),
        "-j", "name,name",
        "-o", str(output_path)
    ]
    result = subprocess.run(cmd, input="n\n", capture_output=True, text=True)
    assert result.returncode == 1, "Script should exit with error code 1"
    assert "Operation cancelled" in result.stderr
    
    # Original file should be unchanged
    content = output_path.read_text()
    assert content == original_content