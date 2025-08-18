# Access arguments and flags
INPUT_FILE="${args[input_file]}"
REFERENCE_FILE="${args[reference_file]}"
THRESHOLD="${args[--threshold]}"
OUTPUT_CLEAN="${args[--output-clean]}"
OUTPUT_AMBIGUOUS="${args[--output-ambiguous]}"
SHOW_SCORE="${args[--show-score]}"

# Get join pairs from flag (space separated)
JOIN_PAIRS_RAW="${args[--join-pair]}"

# If join pairs not specified, use common columns
if [[ -z "$JOIN_PAIRS_RAW" ]]; then
	# Read headers from both files
	IFS=',' read -r -a input_cols < <(head -n 1 "$INPUT_FILE")
	IFS=',' read -r -a ref_cols < <(head -n 1 "$REFERENCE_FILE")
	# Find common columns
	join_pairs=()
	for col in "${input_cols[@]}"; do
		for refcol in "${ref_cols[@]}"; do
			if [[ "$col" == "$refcol" ]]; then
				join_pairs+=("$col,$col")
			fi
		done
	done
else
	# Parse join pairs from flag
	IFS=' ' read -r -a join_pairs <<< "$JOIN_PAIRS_RAW"
fi

# Build SQL for DuckDB
JOIN_PAIRS_SQL=""
FIRST_PAIR=true
for pair_string in "${join_pairs[@]}"; do
	IFS=',' read -r REF_COL INPUT_COL <<< "$pair_string"
	if [ "$FIRST_PAIR" = true ]; then
		JOIN_PAIRS_SQL+="rapidfuzz_ratio(a.$REF_COL, b.$INPUT_COL)"
		FIRST_PAIR=false
	else
		JOIN_PAIRS_SQL+=" + rapidfuzz_ratio(a.$REF_COL, b.$INPUT_COL)"
	fi
done

# Build SELECT clause
SELECT_CLEAN_COLS="b.*"
SELECT_AMBIGUOUS_COLS="b.*"
if [[ -n "${args[--add-field]}" ]]; then
	IFS=' ' read -r -a add_fields <<< "${args[--add-field]}"
	for field in "${add_fields[@]}"; do
		SELECT_CLEAN_COLS+=", a.$field"
		SELECT_AMBIGUOUS_COLS+=", a.$field"
	done
fi
if [[ -n "$SHOW_SCORE" ]]; then
	SELECT_CLEAN_COLS+=", avg_score"
	SELECT_AMBIGUOUS_COLS+=", avg_score"
fi

echo "🚀 Starting fuzzy join process..."
mkdir -p "$(dirname "$OUTPUT_CLEAN")"
duckdb <<EOF
INSTALL rapidfuzz FROM community;
LOAD rapidfuzz;
CREATE OR REPLACE TEMP VIEW all_scores AS
SELECT a.*, b.*, ($JOIN_PAIRS_SQL) / ${#join_pairs[@]} AS avg_score
FROM read_csv_auto('$REFERENCE_FILE', header=true) AS a
CROSS JOIN read_csv_auto('$INPUT_FILE', header=true) AS b;
CREATE OR REPLACE TEMP VIEW ranked_scores AS
SELECT *, DENSE_RANK() OVER(PARTITION BY b.* ORDER BY avg_score DESC) as rnk
FROM all_scores
WHERE avg_score >= $THRESHOLD;
CREATE OR REPLACE TEMP VIEW ambiguous_inputs AS
SELECT b.* FROM ranked_scores WHERE rnk = 1 GROUP BY b.* HAVING COUNT(*) > 1;
COPY (
	SELECT $SELECT_CLEAN_COLS
	FROM ranked_scores rs
	LEFT JOIN ambiguous_inputs ai ON rs.rowid = ai.rowid
	WHERE rs.rnk = 1 AND ai.rowid IS NULL
) TO '$OUTPUT_CLEAN' (HEADER, DELIMITER ',');
COPY (
	SELECT $SELECT_AMBIGUOUS_COLS
	FROM all_scores s
	WHERE s.rowid IN (SELECT rowid FROM ambiguous_inputs)
) TO '$OUTPUT_AMBIGUOUS' (HEADER, DELIMITER ',');
EOF
if [ -f "$OUTPUT_AMBIGUOUS" ]; then
	LINE_COUNT=$(wc -l < "$OUTPUT_AMBIGUOUS")
	if [ "$LINE_COUNT" -eq 1 ]; then
		rm "$OUTPUT_AMBIGUOUS"
		echo "🗑️ Deleted empty ambiguous matches file: $OUTPUT_AMBIGUOUS"
	fi
fi
echo "✅ Fuzzy join complete."
echo "- Clean matches saved to: $OUTPUT_CLEAN"
echo "- Ambiguous matches saved to: $OUTPUT_AMBIGUOUS"
