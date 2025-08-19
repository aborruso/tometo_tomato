import os
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
