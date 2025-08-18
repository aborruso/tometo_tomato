# This file is located at 'src/fuzzy_join_command.sh'.
# It contains the implementation for the 'fuzzy-join-cli fuzzy-join' command.
# The code you write here will be wrapped by a function named 'fuzzy_join_cli_fuzzy_join_command()'.
# Feel free to edit this file; your changes will persist when regenerating.

# Access arguments and flags
local INPUT_FILE="${args[input_file]}"
local REFERENCE_FILE="${args[reference_file]}"
local THRESHOLD="${args[--threshold]}"
local OUTPUT_CLEAN="${args[--output-clean]}"
local OUTPUT_AMBIGUOUS="${args[--output-ambiguous]}"
local SHOW_SCORE="${args[--show-score]}" # Non-empty if the flag is present

# Build the dynamic join columns part of the SQL query
local JOIN_PAIRS_SQL=""
local FIRST_PAIR=true
# Bashly passes repeatable flags as a space-delimited string.
# We need to parse it into an array.
eval "local join_pairs_array=(${args[--join-pair]})"

# Loop through each pair string
for pair_string in "${join_pairs_array[@]}"; do
    # Split the string by comma
    IFS=',' read -r REF_COL INPUT_COL <<< "$pair_string"

    if [ "$FIRST_PAIR" = true ]; then
        JOIN_PAIRS_SQL+="rapidfuzz_ratio(a.$REF_COL, b.$INPUT_COL)"
        FIRST_PAIR=false
    else
        JOIN_PAIRS_SQL+=" +
        rapidfuzz_ratio(a.$REF_COL, b.$INPUT_COL)"
    fi
done

# Build the dynamic SELECT clause for the clean output
local SELECT_CLEAN_COLS="rs.regio, rs.comu" # Base columns from input.csv
local SELECT_AMBIGUOUS_COLS="s.regio, s.comu" # Base columns from input.csv

# Add fields from reference file if specified
eval "local add_fields_array=(${args[--add-field]})"
for field in "${add_fields_array[@]}"; do
    SELECT_CLEAN_COLS+=", rs.$field"
    SELECT_AMBIGUOUS_COLS+=", s.$field"
done

# Add avg_score if --show-score flag is present
if [[ -n "$SHOW_SCORE" ]]; then
    SELECT_CLEAN_COLS+=", rs.avg_score"
    SELECT_AMBIGUOUS_COLS+=", s.avg_score"
fi


# --- Execution ---
echo "🚀 Starting fuzzy join process..."

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_CLEAN")" # Use dirname to get the directory path

# Execute the DuckDB query using a heredoc for clarity
duckdb <<EOF

INSTALL rapidfuzz FROM community;
LOAD rapidfuzz;

-- 1. Calculate scores for all possible pairs
CREATE OR REPLACE TEMP VIEW all_scores AS
SELECT
    a.*, -- Select all columns from reference table
    b.*, -- Select all columns from input table
    (
        $JOIN_PAIRS_SQL
    ) / ${#join_pairs_array[@]} AS avg_score -- Divide by number of pairs
FROM read_csv_auto('$REFERENCE_FILE', header=true) AS a
CROSS JOIN read_csv_auto('$INPUT_FILE', header=true) AS b;

-- 2. Rank pairs by score for each input record and identify top scores with ties
CREATE OR REPLACE TEMP VIEW ranked_scores AS
SELECT
    *,
    DENSE_RANK() OVER(PARTITION BY regio, comu ORDER BY avg_score DESC) as rnk -- Partition by input.csv unique identifier
FROM all_scores
WHERE avg_score >= $THRESHOLD;

-- 3. Identify input records with ambiguous best matches (ties for the top rank)
CREATE OR REPLACE TEMP VIEW ambiguous_inputs AS
SELECT regio, comu
FROM ranked_scores
WHERE rnk = 1
GROUP BY regio, comu
HAVING COUNT(*) > 1;

-- 4. Export clean, unambiguous matches (top rank, no ties)
COPY (
    SELECT
        $SELECT_CLEAN_COLS
    FROM ranked_scores rs
    LEFT JOIN ambiguous_inputs ai ON rs.comu = ai.comu AND rs.regio = ai.regio
    WHERE rs.rnk = 1 AND ai.comu IS NULL
) TO '$OUTPUT_CLEAN' (HEADER, DELIMITER ',');

-- 5. Export all potential matches for ambiguous input records
COPY (
    SELECT $SELECT_AMBIGUOUS_COLS
    FROM all_scores s
    WHERE (s.comu, s.regio) IN (SELECT comu, regio FROM ambiguous_inputs)
) TO '$OUTPUT_AMBIGUOUS' (HEADER, DELIMITER ',');

EOF

# Check if the ambiguous file is empty (only header) and delete it
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
