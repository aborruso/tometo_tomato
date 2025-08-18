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
	# Rimuovo virgolette, backslash e spazi
	REF_COL="${REF_COL//\"/}"
	REF_COL="${REF_COL//\'/}"
	REF_COL="${REF_COL//\\/}"
	REF_COL="${REF_COL// /}"
	INPUT_COL="${INPUT_COL//\"/}"
	INPUT_COL="${INPUT_COL//\'/}"
	INPUT_COL="${INPUT_COL//\\/}"
	INPUT_COL="${INPUT_COL// /}"
	if [ "$FIRST_PAIR" = true ]; then
		JOIN_PAIRS_SQL+="rapidfuzz_ratio(LOWER(ref.$REF_COL), LOWER(inp.$INPUT_COL))"
		FIRST_PAIR=false
	else
		JOIN_PAIRS_SQL+=" + rapidfuzz_ratio(LOWER(ref.$REF_COL), LOWER(inp.$INPUT_COL))"
	fi
done

# Build SELECT clause for LEFT JOIN
INPUT_HEADER=$(head -n 1 "$INPUT_FILE")
IFS=',' read -r -a input_cols <<< "$INPUT_HEADER"
INPUT_COLS_LIST=""
INPUT_COLS_LIST_NOPREFIX=""
INPUT_COLS_SELECT=""
for col in "${input_cols[@]}"; do
	col_clean="${col//\"/}"
	col_clean="${col_clean// /}"
	if [[ -z "$INPUT_COLS_LIST" ]]; then
		INPUT_COLS_LIST="b.$col_clean"
		INPUT_COLS_LIST_NOPREFIX="$col_clean"
		INPUT_COLS_SELECT="inp.$col_clean"
	else
		INPUT_COLS_LIST+=" , b.$col_clean"
		INPUT_COLS_LIST_NOPREFIX+=" , $col_clean"
		INPUT_COLS_SELECT+=" , inp.$col_clean"
	fi
done
SELECT_CLEAN_COLS="$INPUT_COLS_SELECT"
SELECT_AMBIGUOUS_COLS="$INPUT_COLS_LIST_NOPREFIX"
# Aggiungi sempre il codice_comune_alfanumerico dal file di riferimento
SELECT_CLEAN_COLS+=", bst.codice_comune_alfanumerico"
if [[ -n "${args[--add-field]}" ]]; then
	IFS=' ' read -r -a add_fields <<< "${args[--add-field]}"
	for field in "${add_fields[@]}"; do
		SELECT_CLEAN_COLS+=", bst.$field"
		SELECT_AMBIGUOUS_COLS+=", a.$field"
	done
fi
if [[ -n "$SHOW_SCORE" ]]; then
	SELECT_CLEAN_COLS+=", bst.avg_score"
	SELECT_AMBIGUOUS_COLS+=", avg_score"
fi

echo "🚀 Starting fuzzy join process..."
mkdir -p "$(dirname "$OUTPUT_CLEAN")"
duckdb <<EOF
INSTALL rapidfuzz FROM community;
LOAD rapidfuzz;
-- Script per LEFT JOIN che mantiene tutti i record del file di input
COPY (
	WITH input_with_id AS (
		SELECT ROW_NUMBER() OVER () AS input_id, *
		FROM read_csv_auto('$INPUT_FILE', header=true)
	),
	-- Calcoliamo tutti i punteggi per ogni combinazione
	all_scores AS (
		SELECT inp.input_id, inp.*, ref.*, ($JOIN_PAIRS_SQL) / ${#join_pairs[@]} AS avg_score
		FROM read_csv_auto('$REFERENCE_FILE', header=true) AS ref
		CROSS JOIN input_with_id AS inp
	),
	-- Per ogni record di input, troviamo il miglior match che supera la soglia
	best_matches AS (
		SELECT *, ROW_NUMBER() OVER(PARTITION BY input_id ORDER BY avg_score DESC) as rn
		FROM all_scores
		WHERE avg_score >= $THRESHOLD
	)
	-- LEFT JOIN: tutti i record di input + il miglior match se esiste
	SELECT $SELECT_CLEAN_COLS
	FROM input_with_id inp
	LEFT JOIN (SELECT * FROM best_matches WHERE rn = 1) bst ON inp.input_id = bst.input_id
) TO '$OUTPUT_CLEAN' (HEADER, DELIMITER ',');
EOF

# Genera l'output ambiguo solo se il parametro è valorizzato
if [[ -n "$OUTPUT_AMBIGUOUS" ]]; then
duckdb <<EOF
INSTALL rapidfuzz FROM community;
LOAD rapidfuzz;
COPY (
	WITH input_with_id AS (
		SELECT ROW_NUMBER() OVER () AS input_id, *
		FROM read_csv_auto('$INPUT_FILE', header=true)
	),
	all_scores AS (
		SELECT inp.input_id, inp.*, ref.*, ($JOIN_PAIRS_SQL) / ${#join_pairs[@]} AS avg_score
		FROM read_csv_auto('$REFERENCE_FILE', header=true) AS ref
		CROSS JOIN input_with_id AS inp
	),
	best_matches AS (
		SELECT *, ROW_NUMBER() OVER(PARTITION BY input_id ORDER BY avg_score DESC) as rn
		FROM all_scores
		WHERE avg_score >= $THRESHOLD
	),
	ambiguous_inputs AS (
		SELECT input_id FROM best_matches WHERE rn = 1 GROUP BY input_id HAVING COUNT(*) > 1
	)
	SELECT $SELECT_AMBIGUOUS_COLS
	FROM all_scores s
	WHERE s.input_id IN (SELECT input_id FROM ambiguous_inputs)
) TO '$OUTPUT_AMBIGUOUS' (HEADER, DELIMITER ',');
EOF
	if [ -f "$OUTPUT_AMBIGUOUS" ]; then
		LINE_COUNT=$(wc -l < "$OUTPUT_AMBIGUOUS")
		if [ "$LINE_COUNT" -eq 1 ]; then
			rm "$OUTPUT_AMBIGUOUS"
			echo "ℹ️ Nessun record ambiguo trovato. Il file $OUTPUT_AMBIGUOUS è stato cancellato."
		else
			echo "⚠️ Sono stati trovati record ambigui! Controlla il file: $OUTPUT_AMBIGUOUS"
		fi
	fi
fi
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
