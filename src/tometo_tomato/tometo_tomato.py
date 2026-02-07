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


def check_file_overwrite(file_path: str, force: bool = False) -> bool:
    """Check if a file exists and prompt user for overwrite confirmation if needed.

    Args:
        file_path: Path to the file to check
        force: If True, skip the prompt and return True

    Returns:
        True if we should proceed with writing/overwriting the file, False otherwise
    """
    if not os.path.exists(file_path):
        return True

    if force:
        return True

    # File exists and we're not forcing - prompt user
    try:
        response = input(f"File '{file_path}' already exists. Overwrite? [Y/n]: ").strip().lower()
        if response == '' or response == 'y' or response == 'yes':
            return True
        else:
            return False
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environments or user interruption
        print("\nOperation cancelled.")
        return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fuzzy join utility using DuckDB",
        epilog=(
            "Example:\n"
            "  tometo_tomato input.csv ref.csv -j \"col1,col_ref1\" -j \"col2,col_ref2\" -a \"field_to_add1\" -a \"field_to_add2\" -o \"output_clean.csv\"\n"
            "  tometo_tomato input.csv ref.csv -j \"name,ref_name\" --keep-alphanumeric -o clean_output.csv\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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
    parser.add_argument("--latinize", action="store_true", help="Normalize/latinize accented and special characters before matching")
    parser.add_argument("--keep-alphanumeric", "-k", action="store_true", help="Keep only alphanumeric characters and spaces in join columns (removes punctuation and special characters)")
    parser.add_argument(
        "--block-prefix",
        type=int,
        default=0,
        help=(
            "Enable blocking by joining only records that share the same key built "
            "from the first N characters of each cleaned join column, concatenated with '|' (N = block-prefix)."
        ),
    )
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity (e.g., -v, -vv)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress all output except errors")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing output files without prompting")
    return parser.parse_args()

def read_header(path: str) -> List[str]:
    # Use DuckDB SQL engine as primary source of truth for header detection
    con = duckdb.connect(database=":memory:")
    safe_path = path.replace("'", "''")

    # Use the same query from test_csv_reading.py that works correctly
    q = f"SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true)"
    res = con.execute(q)

    desc = getattr(res, 'description', None)
    if desc:
        return [c[0] for c in desc]
    # If DuckDB doesn't populate description, try with LIMIT 0 which always forces description population
    try:
        q_limit = f"SELECT * FROM read_csv_auto('{safe_path}', header=true, all_varchar=true) LIMIT 0"
        res_limit = con.execute(q_limit)
        desc_limit = getattr(res_limit, 'description', None)
        if desc_limit:
            return [c[0] for c in desc_limit]
        else:
            raise Exception("Could not determine column names from CSV file")
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


def choose_score_expr(
    using_rapidfuzz: bool,
    join_pairs: List[str],
    scorer: str,
    args: "argparse.Namespace",
    preprocessed: bool = False,
) -> str:
    import re

    # Fast-path: columns have already been normalised into *_clean aliases.
    # Build the score expression by simply referencing those aliases so the
    # CROSS JOIN only runs the distance function.
    if preprocessed:
        exprs: List[str] = []

        if using_rapidfuzz:
            score_func = 'rapidfuzz_token_set_ratio' if scorer == 'token_set_ratio' else 'rapidfuzz_ratio'
            for pair in join_pairs:
                inp_col, ref_col = [c.strip().replace('"', '').replace("'", "") for c in pair.split(",")]
                exprs.append(f"{score_func}(ref.\"{ref_col}_clean\", inp.\"{inp_col}_clean\")")
        else:
            if scorer != 'ratio':
                logging.error(f"The '{scorer}' scorer requires the rapidfuzz extension, which could not be loaded.")
                sys.exit(1)
            for pair in join_pairs:
                inp_col, ref_col = [c.strip().replace('"', '').replace("'", "") for c in pair.split(",")]
                exprs.append(
                    f"(1.0 - CAST(levenshtein(ref.\"{ref_col}_clean\", inp.\"{inp_col}_clean\") AS DOUBLE) "
                    f"/ NULLIF(GREATEST(LENGTH(ref.\"{ref_col}_clean\"), LENGTH(inp.\"{inp_col}_clean\")),0)) * 100"
                )
        return " + ".join(exprs)
    # ...resto della funzione...
        expr = base_expr
        if not args.raw_whitespace:
            expr = f"trim(regexp_replace({expr}, '\\s+', ' ', 'g'))"
        if args.latinize:
            expr = f"strip_accents({expr})"
        return expr

    exprs = []

    # Determine if case sensitive (raw) or not
    raw_case = getattr(args, "raw_case", False)

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

            inp_expr = clean_column_expr("inp", inp, args)
            ref_expr = clean_column_expr("ref", ref, args)

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

            inp_expr = clean_column_expr("inp", inp, args)
            ref_expr = clean_column_expr("ref", ref, args)

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

    # Verify that join pair columns exist in the actual datasets
    input_cols = read_header(args.input_file)
    ref_cols = read_header(args.reference_file)

    for pair in join_pairs:
        inp_col, ref_col = [c.strip().replace('"', '').replace("'", "") for c in pair.split(",")]
        if inp_col not in input_cols:
            logging.error(f"Column '{inp_col}' not found in input file. Available columns: {', '.join(input_cols)}")
            sys.exit(1)
        if ref_col not in ref_cols:
            logging.error(f"Column '{ref_col}' not found in reference file. Available columns: {', '.join(ref_cols)}")
            sys.exit(1)



    # prepare select clauses
    add_fields = []
    if args.add_field:
        # The `action='append'` in argparse creates a list of all given fields.
        add_fields = [a.strip() for a in args.add_field]

    select_clean_cols, select_ambiguous_cols, selected_input_cols_list = prepare_select_clauses(join_pairs, add_fields, args.show_score)

    # For ambiguous output, use actual column names from the datasets
    # Get all columns from input that are used in joins (using real column names)
    actual_input_cols_used = []
    for pair in join_pairs:
        inp_col = pair.split(",")[0].strip().replace('"', '').replace("'", "")
        actual_input_cols_used.append(inp_col)
    actual_input_cols_used = list(set(actual_input_cols_used))  # Remove duplicates

    # Build ambiguous output column list with actual column names
    ambiguous_cols_list = []
    # Input columns used in joins (prefix with inp.)
    for col in actual_input_cols_used:
        ambiguous_cols_list.append(f'inp."{col}"')
    # Reference columns used in joins (prefix with s.)
    for pair in join_pairs:
        ref_col = pair.split(",")[1].strip().replace('"', '').replace("'", "")
        ambiguous_cols_list.append(f's."{ref_col}"')
    # Additional fields (prefix with s.)
    if add_fields:
        for f in add_fields:
            ambiguous_cols_list.append(f's."{f}"')
    if args.show_score:
        ambiguous_cols_list.append('s.avg_score')
    select_ambiguous_cols_fixed = ', '.join(ambiguous_cols_list)

    con = duckdb.connect(database=":memory:")

    # Register UDF for latinization if needed
    if args.latinize:
        def latinize_udf(text):
            if text is None:
                return None
            # Use the DuckDB strip_accents() function
            # If called as Python UDF, it calls the SQL function
            # But here, for efficiency, the Python UDF calls the DuckDB function via SQL
            # or, if DuckDB supports it directly, it can be used in SQL
            # Here the Python UDF is a pass-through, the logic is in SQL with strip_accents()
            return text  # No modification, the logic is in SQL with strip_accents()
        try:
            con.create_function("latinize_udf", latinize_udf, ['VARCHAR'], 'VARCHAR')
        except Exception as e:
            err_msg = str(e)
            if 'numpy' in err_msg.lower() or 'numpy' in getattr(e, 'args', ('',))[0].lower():
                logging.error("Registering latinize_udf failed: DuckDB requires numpy to register Python UDFs. Install numpy and retry.")
            else:
                logging.error(f"Failed to register latinize_udf: {e}")
            sys.exit(1)

    # Check dataset size and warn if --latinize might be slow
    if args.latinize:
        # Quick row count estimate
        try:
            input_count_res = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{args.input_file}', header=true, all_varchar=true)")
            input_count = input_count_res.fetchone()[0]

            ref_count_res = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{args.reference_file}', header=true, all_varchar=true)")
            ref_count = ref_count_res.fetchone()[0]

            total_combinations = input_count * ref_count

            if total_combinations > 10_000_000:  # 10 million combinations
                logging.warning(f"Large dataset detected ({input_count:,} × {ref_count:,} = {total_combinations:,} combinations)")
                logging.warning("--latinize option may cause significant performance impact on large datasets.")
                logging.warning("Consider using smaller samples or removing --latinize for better performance.")

        except Exception as e:
            logging.debug(f"Could not estimate dataset size: {e}")

    using_rapidfuzz = try_load_rapidfuzz(con)
    if using_rapidfuzz:
        score_expr_base = choose_score_expr(True, join_pairs, args.scorer, args, True)
    else:
        try:
            con.execute("SELECT levenshtein('a','b')")
            score_expr_base = choose_score_expr(False, join_pairs, args.scorer, args, True)
        except Exception:
            try:
                con.execute("SELECT damerau_levenshtein('a','b')")
                exprs = []
                for pair in join_pairs:
                    inp_col, ref_col = [c.strip().replace('"', '').replace("'", "") for c in pair.split(",")]
                    inp_expr = f'inp."{inp_col}_clean"'
                    ref_expr = f'ref."{ref_col}_clean"'
                    exprs.append(
                        f"(1.0 - CAST(damerau_levenshtein({ref_expr}, {inp_expr}) AS DOUBLE) "
                        f"/ NULLIF(GREATEST(LENGTH({ref_expr}), LENGTH({inp_expr})),0)) * 100"
                    )
                score_expr_base = " + ".join(exprs)
            except Exception:
                logging.error("No fuzzy function available in DuckDB (rapidfuzz, levenshtein or damerau_levenshtein). Install the rapidfuzz extension or use a DuckDB version that includes levenshtein.")
                sys.exit(1)

    # avg_score = (score_expr_base) / num_pairs
    num_pairs = len(join_pairs)
    avg_score_expr = f"({score_expr_base}) / {num_pairs}"

    # ------------------------------------------------------------------
    # Pre-process the join columns once so the CROSS JOIN only executes
    # the distance function, not the expensive cleaning logic.
    # ------------------------------------------------------------------
    def _build_clean_expr(table_alias: str, column: str) -> str:
        expr = f'{table_alias}."{column}"'
        if not args.raw_whitespace:
            expr = f"trim(regexp_replace({expr}, '\\s+', ' ', 'g'))"
        if args.latinize:
            expr = f"strip_accents({expr})"
        if args.keep_alphanumeric:
            expr = f"regexp_replace({expr}, '[^a-zA-Z0-9 ]', '', 'g')"
        if not args.raw_case:
            expr = f"lower({expr})"
        return expr

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

    input_clean_cols_sql = []
    ref_clean_cols_sql = []
    inp_clean_col_names = []
    for pair in join_pairs:
        inp_col, ref_col = [c.strip().replace('"', '').replace("'", "") for c in pair.split(",")]
        input_clean_cols_sql.append(f"{_build_clean_expr('inp', inp_col)} AS \"{inp_col}_clean\"")
        ref_clean_cols_sql.append(f"{_build_clean_expr('ref', ref_col)} AS \"{ref_col}_clean\"")
        inp_clean_col_names.append(f'"{inp_col}_clean"')

    con.execute(f"""
        CREATE TEMP VIEW input_preproc AS
        SELECT inp.input_id, {', '.join(input_clean_cols_sql)}
        {',' if args.block_prefix and args.block_prefix > 0 else ''}
        {(" || '|' || ".join([f"substr(" + _build_clean_expr('inp', pair.split(',')[0].strip().replace('"','').replace("'",'')) + f", 1, {args.block_prefix})" for pair in join_pairs])) + " AS block_key" if args.block_prefix and args.block_prefix > 0 else ''}
        FROM input_with_id inp;
    """)

    con.execute(f"""
        CREATE TEMP VIEW ref_preproc AS
        SELECT ref.*, {', '.join(ref_clean_cols_sql)}
        {',' if args.block_prefix and args.block_prefix > 0 else ''}
        {(" || '|' || ".join([f"substr(" + _build_clean_expr('ref', pair.split(',')[1].strip().replace('"','').replace("'",'')) + f", 1, {args.block_prefix})" for pair in join_pairs])) + " AS block_key" if args.block_prefix and args.block_prefix > 0 else ''}
        FROM read_csv_auto('{args.reference_file}', header=true, all_varchar=true) AS ref;
    """)

    # ------------------------------------------------------------------
    # DISTINCT optimization: deduplicate input join keys before the
    # expensive CROSS JOIN so fuzzy matching runs only on unique combos.
    # ------------------------------------------------------------------
    clean_cols_csv = ', '.join(inp_clean_col_names)
    block_key_col = ', block_key' if args.block_prefix and args.block_prefix > 0 else ''

    con.execute(f"""
        CREATE TEMP VIEW input_keys AS
        SELECT ROW_NUMBER() OVER () AS key_id, t.*
        FROM (
            SELECT DISTINCT {clean_cols_csv}{block_key_col}
            FROM input_preproc
        ) t;
    """)

    join_on_clauses = ' AND '.join(
        [f'ip.{col} IS NOT DISTINCT FROM ik.{col}' for col in inp_clean_col_names]
    )
    if args.block_prefix and args.block_prefix > 0:
        join_on_clauses += ' AND ip.block_key IS NOT DISTINCT FROM ik.block_key'

    con.execute(f"""
        CREATE TEMP VIEW input_key_map AS
        SELECT ip.input_id, ik.key_id
        FROM input_preproc ip
        JOIN input_keys ik ON {join_on_clauses};
    """)

    if args.block_prefix and args.block_prefix > 0:
        con.execute(f"""
            CREATE TEMP VIEW key_scores AS
            SELECT inp.key_id, ref.*, {avg_score_expr} AS avg_score
            FROM ref_preproc AS ref
            JOIN input_keys AS inp
              ON ref.block_key = inp.block_key;
        """)
    else:
        con.execute(f"""
            CREATE TEMP VIEW key_scores AS
            SELECT inp.key_id, ref.*, {avg_score_expr} AS avg_score
            FROM ref_preproc AS ref
            CROSS JOIN input_keys AS inp;
        """)

    con.execute(f"""
        CREATE TEMP VIEW all_scores AS
        SELECT ikm.input_id, ks.* EXCLUDE (key_id)
        FROM input_key_map ikm
        JOIN key_scores ks ON ikm.key_id = ks.key_id;
    """)

    con.execute(f"""
        CREATE TEMP VIEW best_matches AS
        SELECT *, ROW_NUMBER() OVER(PARTITION BY input_id ORDER BY avg_score DESC, input_id ASC) as rnk
        FROM all_scores
        WHERE avg_score >= {args.threshold};
    """)

    # Build DuckDB SQL for clean output (LEFT JOIN behavior - include ALL input records)
    sql_clean = f"""
COPY (
    WITH max_scores AS (
        SELECT input_id, MAX(avg_score) as max_score
        FROM all_scores
        WHERE avg_score >= {args.threshold}
        GROUP BY input_id
    ),
    ambiguous_inputs AS (
        SELECT ms.input_id
        FROM max_scores ms
        JOIN all_scores s ON ms.input_id = s.input_id AND ms.max_score = s.avg_score
        GROUP BY ms.input_id
        HAVING COUNT(*) > 1
    ),
    clean_best_matches AS (
        SELECT * FROM best_matches
        WHERE rnk = 1
        AND input_id NOT IN (SELECT input_id FROM ambiguous_inputs)
    )
    SELECT DISTINCT {select_clean_cols}
    FROM input_with_id inp
    LEFT JOIN clean_best_matches bst ON inp.input_id = bst.input_id
) TO '{args.output_clean}' (HEADER, DELIMITER ',');
"""

    # Check for file overwrite before writing clean output
    if not check_file_overwrite(args.output_clean, args.force):
        logging.error("Operation cancelled: will not overwrite existing file.")
        sys.exit(1)

    con.execute(sql_clean)

    # Check for ambiguous records before creating the ambiguous file
    ambiguous_count_result = con.execute(f"""
        WITH max_scores AS (
            SELECT input_id, MAX(avg_score) as max_score
            FROM all_scores
            WHERE avg_score >= {args.threshold}
            GROUP BY input_id
        ),
        ambiguous_inputs AS (
            SELECT ms.input_id
            FROM max_scores ms
            JOIN all_scores s ON ms.input_id = s.input_id AND ms.max_score = s.avg_score
            GROUP BY ms.input_id
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) FROM ambiguous_inputs
    """)
    ambiguous_count = ambiguous_count_result.fetchone()[0]

    if args.output_ambiguous and ambiguous_count > 0:
        # Only check for file overwrite if there are actually ambiguous records
        if not check_file_overwrite(args.output_ambiguous, args.force):
            logging.error("Operation cancelled: will not overwrite existing ambiguous file.")
            sys.exit(1)

        # Build DuckDB SQL for ambiguous output
        sql_amb = f"""
COPY (
    WITH max_scores AS (
        SELECT input_id, MAX(avg_score) as max_score
        FROM all_scores
        WHERE avg_score >= {args.threshold}
        GROUP BY input_id
    ),
    ambiguous_inputs AS (
        SELECT ms.input_id
        FROM max_scores ms
        JOIN all_scores s ON ms.input_id = s.input_id AND ms.max_score = s.avg_score
        GROUP BY ms.input_id
        HAVING COUNT(*) > 1
    )
    SELECT DISTINCT {select_ambiguous_cols_fixed}
    FROM all_scores s
    JOIN input_with_id inp ON s.input_id = inp.input_id
    WHERE s.input_id IN (SELECT input_id FROM ambiguous_inputs)
       AND s.avg_score >= {args.threshold}
) TO '{args.output_ambiguous}' (HEADER, DELIMITER ',');
"""

        con.execute(sql_amb)
        logging.warning(f"Ambiguous records found! Check file: {args.output_ambiguous}")
    elif args.output_ambiguous and ambiguous_count == 0:
        # Don't create ambiguous file if no ambiguous records exist
        logging.info("No ambiguous records found.")
    elif ambiguous_count > 0:
        # Warn about ambiguous records even when no output file is specified
        logging.warning(f"Ambiguous records found! Use --output-ambiguous filename.csv to see which records are ambiguous")

    logging.info("Fuzzy join complete.")
    logging.info(f"- Clean matches saved to: {args.output_clean}")
    if args.output_ambiguous and ambiguous_count > 0:
        logging.info(f"- Ambiguous matches saved to: {args.output_ambiguous}")


if __name__ == '__main__':
    main()
