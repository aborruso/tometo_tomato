import os
import duckdb
import tometo_tomato as tt


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def test_read_header_comma(tmp_path):
    p = tmp_path / 'comma.csv'
    write_file(p, 'a,b,c\n1,2,3\n')
    assert tt.read_header(str(p)) == ['a', 'b', 'c']


def test_read_header_semicolon(tmp_path):
    p = tmp_path / 'semi.csv'
    write_file(p, 'col1;col2;col3\n1;2;3\n')
    hdr = tt.read_header(str(p))
    assert hdr == ['col1', 'col2', 'col3']


def test_read_header_tab(tmp_path):
    p = tmp_path / 'tab.csv'
    write_file(p, 'x\ty\tz\n1\t2\t3\n')
    hdr = tt.read_header(str(p))
    assert hdr == ['x', 'y', 'z']


def test_read_header_quoted_with_comma(tmp_path):
    p = tmp_path / 'quoted.csv'
    # header fields quoted and one contains a comma
    # Use semicolon as the file delimiter; header contains a comma inside quoted field
    write_file(p, '"Name";"Address, Line";Age\n"Bob";"Somewhere, 12";30\n')
    hdr = tt.read_header(str(p))
    assert hdr == ['Name', 'Address, Line', 'Age']
