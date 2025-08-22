#!/usr/bin/env python3
"""Fuzzy join utility using DuckDB.

This mirrors the behavior of `root_command.sh` but implemented in Python.
It attempts to install/load the `rapidfuzz` extension in DuckDB; if unavailable,
it falls back to built-in `levenshtein`/`damerau_levenshtein` functions.

Usage example:
  python3 src/fuzzy_join.py input.csv ref.csv --threshold 85 --add-field codice_comune --show-score
"""
import os
import sys

# Add src directory to Python path to allow importing _version.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

try:
    from _version import version as __version__
except ImportError:
    __version__ = "unknown"


import argparse
import logging
try:
    import duckdb
except Exception as e:
    logging.error("Error: duckdb Python package is required but not installed. Install via 'pip install duckdb'")
    raise
from typing import List


def parse_args():
    parser = argparse.ArgumentParser(description="Fuzzy join utility using DuckDB")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    parser.add_argument("input_file")
    parser.add_argument("reference_file")
    parser.add_argument("--threshold", "-t", type=float, default=85.0)
    parser.add_argument("--infer-pairs", "-i", action="store_true", help="Infer join pairs from similar column names")
    parser.add_argument("--infer-threshold", "-I", type=float, default=0.7, help="Threshold (0-1) for header name similarity when inferring pairs")
    parser.add_argument("--output-clean", "-o", default="clean_matches.csv")
    parser.add_argument("--output-ambiguous", "-u", default=None)
    parser.add_argument("--join-pair", "-j", action="append", help="Pair in the form input_col,ref_col. Can be repeated.")
    parser.add_argument("--add-field", "-a", action="append", help="Fields from reference to add to output (space separated or repeated)")
    parser.add_argument("--show-score", "-s", action="store_true", help="Include avg_score in outputs")
    parser.add_argument("--scorer", choices=['ratio', 'token_set_ratio'], default='ratio', help="Fuzzy matching algorithm to use.")
    parser.add_argument("--raw-whitespace", action="store_true", help="Disable whitespace normalization (no trimming or space reduction)")
    parser.add_argument("--raw-case", action="store_true", help="Enable case sensitive comparison (do not convert to lower-case)")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity (e.g., -v, -vv)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress all output except errors")
    return parser.parse_args()

def read_header(path: str) -> List[str]:
    # Use DuckDB SQL engine as primary source of truth for header detection
    con = duckdb.connect(database=":memory:")
    safe_path = path.replace("'", "''")

    # Usa la stessa query di test_csv_reading.py che funziona correttamente
    q = f"SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true)"
    res = con.execute(q)

    desc = getattr(res, 'description', None)
    if desc:
        return [c[0] for c in desc]
    # Se DuckDB non popola description, provo a fetchdf (comportamento identico a test_csv_reading.py)
    try:
        df = res.fetchdf()
        return list(df.columns)
    except Exception as e:
        logging.error(f"DuckDB could not determine header columns for file: {path}. Error: {e}")
        raise


def build_join_pairs(args) -> List[str]:
    if args.join_pair:
        pairs = []
        for p in args.join_pair:
            pairs.append(p.strip())
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


def prepare_select_clauses(join_pairs: List[str], add_fields: List[str], show_score: bool):
    # Extract unique input columns from join_pairs
    selected_input_cols = set()
    selected_ref_cols = set()
    for pair in join_pairs:
        inp_col = pair.split(",")[0].strip().replace('"', '').replace("'", "")
        ref_col = pair.split(",")[1].strip().replace('"', '').replace("'", "")
        selected_input_cols.add(inp_col)
        selected_ref_cols.add(ref_col)

    # Convert sets to lists to maintain order (optional, but good practice)
    selected_input_cols_list = sorted(list(selected_input_cols))
    selected_ref_cols_list = sorted(list(selected_ref_cols))

    input_cols_select = ", ".join([f"inp.\"{c}\"" for c in selected_input_cols_list])
    input_cols_noprefix = ", ".join([f"\"{c}\"" for c in selected_input_cols_list])

    # Always include reference join fields with ref_ prefix
    for ref_col in selected_ref_cols_list:
        input_cols_select += f", bst.\"{ref_col}\" AS \"ref_{ref_col}\""
        input_cols_noprefix += f", \"ref_{ref_col}\""

    # Add any additional fields specified with --add-field
    if add_fields:
        for f in add_fields:
            input_cols_select += f", bst.\"{f}\""
            input_cols_noprefix += f", \"{f}\""

    if show_score:
        input_cols_select += ", bst.avg_score"
        input_cols_noprefix += ", avg_score"
    return input_cols_select, input_cols_noprefix, selected_input_cols_list


def try_load_rapidfuzz(con: duckdb.DuckDBPyConnection) -> bool:
    try:
        con.execute("INSTALL rapidfuzz FROM community;")
        con.execute("LOAD rapidfuzz;")
        return True
    except Exception:
        return False


def choose_score_expr(using_rapidfuzz: bool, join_pairs: List[str], scorer: str, clean_whitespace: bool = False) -> str:
    def clean_column_expr(table_alias: str, column: str) -> str:
        """Generate column expression with default whitespace cleaning unless --raw-whitespace is set."""
        base_expr = f'{table_alias}."{column}"'
        # Determina se usare la normalizzazione degli spazi
        raw_whitespace = getattr(sys.modules['__main__'], 'args', None)
        if raw_whitespace is None:
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'args' in frame.f_locals:
                    raw_whitespace = frame.f_locals['args']
                    break
                frame = frame.f_back
        raw_whitespace_flag = getattr(raw_whitespace, 'raw_whitespace', False)
        if not raw_whitespace_flag:
            # Default: trim + riduci tutti i gruppi di spazi (spazi/tab) a uno solo
            # DuckDB supporta \s per whitespace, quindi sostituisco tutti i gruppi di whitespace
            return f"trim(regexp_replace({base_expr}, '\\s+', ' ', 'g'))"
        return base_expr

    exprs = []

    # Determine if case sensitive (raw) or not
    case_sensitive = getattr(sys.modules['__main__'], 'args', None)
    if case_sensitive is None:
        # fallback: try to get from caller
        import inspect
        frame = inspect.currentframe()
        while frame:
            if 'args' in frame.f_locals:
                case_sensitive = frame.f_locals['args']
                break
            frame = frame.f_back
    raw_case = getattr(case_sensitive, 'raw_case', False)

    def maybe_lower(expr):
        return expr if raw_case else f"LOWER({expr})"

    if using_rapidfuzz:
        # Select the function name based on the scorer argument
        if scorer == 'token_set_ratio':
            score_func = 'rapidfuzz_token_set_ratio'
        else: # default to 'ratio'
            score_func = 'rapidfuzz_ratio'

        for pair in join_pairs:
            inp, ref = pair.split(",")
            inp = inp.replace('"', '').replace("'", '').strip()
            ref = ref.replace('"', '').replace("'", '').strip()

            inp_expr = clean_column_expr("inp", inp)
            ref_expr = clean_column_expr("ref", ref)

            exprs.append(f"{score_func}({maybe_lower(ref_expr)}, {maybe_lower(inp_expr)})")
    else:
        # Fallback logic without rapidfuzz
        if scorer != 'ratio':
            logging.error(f"The '{scorer}' scorer requires the rapidfuzz extension, which could not be loaded.")
            sys.exit(1)

        for pair in join_pairs:
            inp, ref = pair.split(",")
            inp = inp.replace('"', '').replace("'", '').strip()
            ref = ref.replace('"', '').replace("'", '').strip()

            inp_expr = clean_column_expr("inp", inp)
            ref_expr = clean_column_expr("ref", ref)

            # we will build an expression that computes: (1 - levenshtein/NULLIF(GREATEST(LENGTH(a), LENGTH(b)),0)) * 100
            expr = (
                f"(1.0 - CAST(levenshtein({maybe_lower(ref_expr)}, {maybe_lower(inp_expr)}) AS DOUBLE) / NULLIF(GREATEST(LENGTH({maybe_lower(ref_expr)}), LENGTH({maybe_lower(inp_expr)})),0)) * 100"
            )
            exprs.append(expr)

    # average
    return " + ".join(exprs)


def main():
    args = parse_args()

    # Configure logging
    if args.quiet:
        logging.basicConfig(level=logging.CRITICAL, format='%(levelname)s: %(message)s')
    elif args.verbose == 1:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    elif args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    if '--help' in sys.argv or '-h' in sys.argv:
        logging.info("\nExample:")
        logging.info("  tometo_tomato input.csv ref.csv -j \"col1,col_ref1\" -j \"col2,col_ref2\" -a \"field_to_add1\" -a \"field_to_add2\" -o \"output_clean.csv\"")
        logging.info("") # Add an empty line for better formatting


    # Build join pairs
    join_pairs = build_join_pairs(args)
    if not join_pairs:
        logging.error("No join pair found. Exiting.")
        sys.exit(1)



    # prepare select clauses
    add_fields = []
    if args.add_field:
        # The `action='append'` in argparse creates a list of all given fields.
        add_fields = [a.strip() for a in args.add_field]

    select_clean_cols, select_ambiguous_cols, selected_input_cols_list = prepare_select_clauses(join_pairs, add_fields, args.show_score)

    con = duckdb.connect(database=":memory:")
    using_rapidfuzz = try_load_rapidfuzz(con)
    # Passa il flag raw_whitespace alla funzione di scoring
    if using_rapidfuzz:
        score_expr_base = choose_score_expr(True, join_pairs, args.scorer, args.raw_whitespace)
    else:
        try:
            con.execute("SELECT levenshtein('a','b')")
            score_expr_base = choose_score_expr(False, join_pairs, args.scorer, args.raw_whitespace)
        except Exception:
            try:
                con.execute("SELECT damerau_levenshtein('a','b')")
                exprs = []
                def clean_column_expr_damerau(table_alias: str, column: str) -> str:
                    base_expr = f'{table_alias}."{column}"'
                    if not args.raw_whitespace:
                        return f"trim(regexp_replace({base_expr}, ' {{2,}}', ' ', 'g'))"
                    return base_expr
                for pair in join_pairs:
                    inp, ref = pair.split(",")
                    inp = inp.replace('"', '').replace("'", '').strip()
                    ref = ref.replace('"', '').replace("'", '').strip()
                    inp_expr = clean_column_expr_damerau("inp", inp)
                    ref_expr = clean_column_expr_damerau("ref", ref)
                    expr = (
                        "(1.0 - CAST(damerau_levenshtein(LOWER({ref_expr}), LOWER({inp_expr})) AS DOUBLE) / NULLIF(GREATEST(LENGTH(LOWER({ref_expr})), LENGTH(LOWER({inp_expr}))),0)) * 100"
                    ).format(ref_expr=ref_expr, inp_expr=inp_expr)
                    exprs.append(expr)
                score_expr_base = " + ".join(exprs)
            except Exception:
                logging.error("No fuzzy function available in DuckDB (rapidfuzz, levenshtein or damerau_levenshtein). Install the rapidfuzz extension or use a DuckDB version that includes levenshtein.")
                sys.exit(1)

    # avg_score = (score_expr_base) / num_pairs
    num_pairs = len(join_pairs)
    avg_score_expr = f"({score_expr_base}) / {num_pairs}"

    # Create temporary views for common CTEs
    # Extract unique input columns from join_pairs for SQL selection
    input_join_cols_for_sql = set()
    for pair in join_pairs:
        inp_col = pair.split(",")[0].strip().replace('"', '').replace("'", "")
        input_join_cols_for_sql.add(f'"{inp_col}"')
    input_join_cols_for_sql_list = sorted(list(input_join_cols_for_sql))
    input_cols_for_cte = ", ".join(input_join_cols_for_sql_list)

    # Build WHERE clause to filter out empty rows based on join columns
    where_clause_parts = []
    for col in input_join_cols_for_sql_list:
        where_clause_parts.append(f"{col} IS NOT NULL AND {col} != ''")
    where_clause = " AND ".join(where_clause_parts)
    if where_clause:
        where_clause = f"WHERE {where_clause}"

    con.execute(f"""
        CREATE TEMP VIEW input_with_id AS
        SELECT ROW_NUMBER() OVER () AS input_id, {input_cols_for_cte}
        FROM read_csv_auto('{args.input_file}', header=true, all_varchar=true)
        {where_clause};
    """)

    con.execute(f"""
        CREATE TEMP VIEW all_scores AS
        SELECT inp.input_id, ref.*, {avg_score_expr} AS avg_score
        FROM read_csv_auto('{args.reference_file}', header=true, all_varchar=true) AS ref
        CROSS JOIN input_with_id AS inp;
    """)

    con.execute(f"""
        CREATE TEMP VIEW best_matches AS
        SELECT *, ROW_NUMBER() OVER(PARTITION BY input_id ORDER BY avg_score DESC, input_id ASC) as rnk
        FROM all_scores
        WHERE avg_score >= {args.threshold};
    """)

    # Build DuckDB SQL for clean output
    sql_clean = f"""
COPY (
    SELECT DISTINCT {select_clean_cols}
    FROM input_with_id inp
    LEFT JOIN (SELECT * FROM best_matches WHERE rnk = 1) bst ON inp.input_id = bst.input_id
) TO '{args.output_clean}' (HEADER, DELIMITER ',');
"""

    con.execute(sql_clean)

    if args.output_ambiguous:
        # Build DuckDB SQL for ambiguous output
        sql_amb = f"""
COPY (
    WITH ambiguous_inputs AS (
        SELECT input_id FROM best_matches WHERE rnk = 1 GROUP BY input_id HAVING COUNT(*) > 1
    )
    SELECT DISTINCT {select_ambiguous_cols}
    FROM all_scores s
    WHERE s.input_id IN (SELECT input_id FROM ambiguous_inputs)
) TO '{args.output_ambiguous}' (HEADER, DELIMITER ',');
"""

        con.execute(sql_amb)

        ambiguous_file_saved = False
        # post-process ambiguous file: delete if only header
        if os.path.exists(args.output_ambiguous):
            with open(args.output_ambiguous, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) <= 1:
                logging.info("No ambiguous records found.")
            else:
                ambiguous_file_saved = True
                logging.warning(f"Ambiguous records found! Check file: {args.output_ambiguous}")

    logging.info("Fuzzy join complete.")
    logging.info(f"- Clean matches saved to: {args.output_clean}")
    if args.output_ambiguous and ambiguous_file_saved:
        logging.info(f"- Ambiguous matches saved to: {args.output_ambiguous}")


if __name__ == '__main__':
    main()
