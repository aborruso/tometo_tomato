#!/usr/bin/env python3
"""Fuzzy join utility using DuckDB.

This mirrors the behavior of `root_command.sh` but implemented in Python.
It attempts to install/load the `rapidfuzz` extension in DuckDB; if unavailable,
it falls back to built-in `levenshtein`/`damerau_levenshtein` functions.

Usage example:
  python3 src/fuzzy_join.py input.csv ref.csv --threshold 85 --add-field codice_comune --show-score
"""
import argparse
import duckdb
import os
import sys
from typing import List


def parse_args():
    parser = argparse.ArgumentParser(description="Fuzzy join using DuckDB")
    parser.add_argument("input_file")
    parser.add_argument("reference_file")
    parser.add_argument("--threshold", "-t", type=float, default=85.0)
    parser.add_argument("--infer-pairs", "-i", action="store_true", help="Infer join pairs from similar column names")
    parser.add_argument("--infer-threshold", "-I", type=float, default=0.7, help="Threshold (0-1) for header name similarity when inferring pairs")
    parser.add_argument("--output-clean", "-o", default="clean_matches.csv")
    parser.add_argument("--output-ambiguous", "-u", default="ambiguous_matches.csv")
    parser.add_argument("--join-pair", "-j", action="append", help="Pair in the form input_col,ref_col. Can be repeated.")
    parser.add_argument("--add-field", "-a", action="append", help="Fields from reference to add to output (space separated or repeated)")
    parser.add_argument("--show-score", "-s", action="store_true", help="Include avg_score in outputs")
    return parser.parse_args()


def read_header(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        first = f.readline().strip()
    # naive split on comma; keep compatibility with existing script which does same
    return [c.strip().strip('"') for c in first.split(",")]


def build_join_pairs(args) -> List[str]:
    if args.join_pair:
        pairs = []
        for p in args.join_pair:
            # allow multiple space-separated pairs in same arg
            for part in p.split():
                pairs.append(part.strip())
        return pairs
    # otherwise infer common columns
    input_cols = read_header(args.input_file)
    ref_cols = read_header(args.reference_file)
    pairs = []
    # exact matches first
    for col in input_cols:
        if col in ref_cols:
            pairs.append(f"{col},{col}")
    # if infer-pairs requested, try fuzzy match on header names
    if args.infer_pairs:
        from difflib import SequenceMatcher

        for inp in input_cols:
            best = None
            best_score = 0.0
            for ref in ref_cols:
                if f"{inp},{ref}" in pairs or f"{ref},{inp}" in pairs:
                    continue
                score = SequenceMatcher(None, inp.lower(), ref.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best = ref
            if best and best_score >= args.infer_threshold:
                pairs.append(f"{inp},{best}")
    return pairs


def prepare_select_clauses(input_cols: List[str], add_fields: List[str], show_score: bool):
    # SELECT lists similar to shell script
    input_cols_select = ", ".join([f"inp.\"{c}\"" for c in input_cols])
    input_cols_noprefix = ", ".join([f"\"{c}\"" for c in input_cols])
    if add_fields:
        for f in add_fields:
            input_cols_select += f", bst.\"{f}\""
            input_cols_noprefix += f", \"{f}\""
    if show_score:
        input_cols_select += ", bst.avg_score"
        input_cols_noprefix += ", avg_score"
    return input_cols_select, input_cols_noprefix


def try_load_rapidfuzz(con: duckdb.DuckDBPyConnection) -> bool:
    try:
        con.execute("INSTALL rapidfuzz FROM community;")
        con.execute("LOAD rapidfuzz;")
        return True
    except Exception:
        return False


def choose_score_expr(using_rapidfuzz: bool, join_pairs: List[str]) -> str:
    exprs = []
    for pair in join_pairs:
        inp, ref = pair.split(",")
        inp = inp.replace('"', '').replace("'", "").strip()
        ref = ref.replace('"', '').replace("'", "").strip()
        if using_rapidfuzz:
            exprs.append(f"rapidfuzz_ratio(LOWER(ref.\"{ref}\"), LOWER(inp.\"{inp}\"))")
        else:
            # fallback: use levenshtein normalized to 0-100 by similarity = (1 - dist/max_len)*100
            # use greatest length between strings to normalize; in DuckDB SQL we'll compute it
            # we will build an expression that computes: (1 - levenshtein/NULLIF(GREATEST(LENGTH(a), LENGTH(b)),0)) * 100
            expr = (
                "(1.0 - CAST(levenshtein(LOWER(ref.\"{ref}\"), LOWER(inp.\"{inp}\")) AS DOUBLE) / NULLIF(GREATEST(LENGTH(LOWER(ref.\"{ref}\")), LENGTH(LOWER(inp.\"{inp}\"))),0)) * 100"
            ).format(ref=ref, inp=inp)
            exprs.append(expr)
    # average
    return " + ".join(exprs)


def main():
    args = parse_args()

    # Build join pairs
    join_pairs = build_join_pairs(args)
    if not join_pairs:
        print("Nessuna join pair trovata. Esco.")
        sys.exit(1)

    # read input header cols
    input_header = read_header(args.input_file)
    input_cols = input_header

    

    # prepare select clauses
    add_fields = []
    if args.add_field:
        # allow repeated --add-field or space separated inside
        for a in args.add_field:
            for part in a.split():
                add_fields.append(part.strip())

    select_clean_cols, select_ambiguous_cols = prepare_select_clauses(input_cols, add_fields, args.show_score)

    con = duckdb.connect(database=":memory:")
    using_rapidfuzz = try_load_rapidfuzz(con)
    if using_rapidfuzz:
        score_expr_base = choose_score_expr(True, join_pairs)
    else:
        # check for levenshtein/damerau availability by trying a trivial query
        try:
            con.execute("SELECT levenshtein('a','b')")
            score_expr_base = choose_score_expr(False, join_pairs)
        except Exception:
            # try damerau_levenshtein
            try:
                con.execute("SELECT damerau_levenshtein('a','b')")
                # replace levenshtein with damerau_levenshtein in expressions
                exprs = []
                for pair in join_pairs:
                    inp, ref = pair.split(",")
                    inp = inp.replace('"', '').replace("'", "").strip()
                    ref = ref.replace('"', '').replace("'", "").strip()
                    expr = (
                        "(1.0 - CAST(damerau_levenshtein(LOWER(ref.\"{ref}\"), LOWER(inp.\"{inp}\")) AS DOUBLE) / NULLIF(GREATEST(LENGTH(LOWER(ref.\"{ref}\")), LENGTH(LOWER(inp.\"{inp}\"))),0)) * 100"
                    ).format(ref=ref, inp=inp)
                    exprs.append(expr)
                score_expr_base = " + ".join(exprs)
            except Exception:
                print("Nessuna funzione di fuzzy disponibile in DuckDB (rapidfuzz, levenshtein o damerau_levenshtein). Installare l'estensione rapidfuzz o usare una versione di DuckDB che include levenshtein.")
                sys.exit(1)

    # avg_score = (score_expr_base) / num_pairs
    num_pairs = len(join_pairs)
    avg_score_expr = f"({score_expr_base}) / {num_pairs}"

    # Create temporary views for common CTEs
    con.execute(f"""
        CREATE TEMP VIEW input_with_id AS
        SELECT ROW_NUMBER() OVER () AS input_id, *
        FROM read_csv_auto('{args.input_file}', header=true, all_varchar=true);
    """)

    con.execute(f"""
        CREATE TEMP VIEW all_scores AS
        SELECT inp.input_id, inp.*, ref.*, {avg_score_expr} AS avg_score
        FROM read_csv_auto('{args.reference_file}', header=true, all_varchar=true) AS ref
        CROSS JOIN input_with_id AS inp;
    """)

    con.execute(f"""
        CREATE TEMP VIEW best_matches AS
        SELECT *, RANK() OVER(PARTITION BY input_id ORDER BY avg_score DESC) as rnk
        FROM all_scores
        WHERE avg_score >= {args.threshold};
    """)

    # Build DuckDB SQL for clean output
    sql_clean = f"""
COPY (
    SELECT {select_clean_cols}
    FROM input_with_id inp
    LEFT JOIN (SELECT * FROM best_matches WHERE rnk = 1) bst ON inp.input_id = bst.input_id
) TO '{args.output_clean}' (HEADER, DELIMITER ',');
"""

    con.execute(sql_clean)

    # Build DuckDB SQL for ambiguous output
    sql_amb = f"""
COPY (
    WITH ambiguous_inputs AS (
        SELECT input_id FROM best_matches WHERE rnk = 1 GROUP BY input_id HAVING COUNT(*) > 1
    )
    SELECT {select_ambiguous_cols}
    FROM all_scores s
    WHERE s.input_id IN (SELECT input_id FROM ambiguous_inputs)
) TO '{args.output_ambiguous}' (HEADER, DELIMITER ',');
"""

    con.execute(sql_amb)

    # post-process ambiguous file: delete if only header
    if os.path.exists(args.output_ambiguous):
        with open(args.output_ambiguous, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1:
            os.remove(args.output_ambiguous)
            print(f"ℹ️ Nessun record ambiguo trovato. Il file {args.output_ambiguous} è stato cancellato.")
        else:
            print(f"⚠️ Sono stati trovati record ambigui! Controlla il file: {args.output_ambiguous}")

    print("✅ Fuzzy join complete.")
    print(f"- Clean matches saved to: {args.output_clean}")
    print(f"- Ambiguous matches saved to: {args.output_ambiguous}")


if __name__ == '__main__':
    main()
