#!/bin/bash

# -----------------------------------------------------------------------------
# fuzzy_join.sh
#
# Description:
#   Performs a fuzzy join between two CSV files based on the average similarity
#   of two pairs of columns. It separates clean, one-to-one matches from
#   ambiguous matches.
#
# Usage:
#   ./scripts/fuzzy_join.sh
#
# -----------------------------------------------------------------------------

# --- Configuration ---
LEFT_TABLE='data/raw/ref.csv'
RIGHT_TABLE='data/raw/input.csv'
OUTPUT_DIR='data/processed'
OUTPUT_CLEAN="$OUTPUT_DIR/joined_istat_codes.csv" # Changed output name
OUTPUT_AMBIGUOUS="$OUTPUT_DIR/ambiguous_istat_matches.csv" # Changed output name
THRESHOLD=90

# --- Execution ---
echo "🚀 Starting fuzzy join process..."

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Execute the DuckDB query using a heredoc for clarity
duckdb <<EOF

INSTALL rapidfuzz FROM community;
LOAD rapidfuzz;

-- 1. Calculate scores for all possible pairs
CREATE OR REPLACE TEMP VIEW all_scores AS
SELECT
    a.regione, # Keep original columns from ref.csv
    a.comune,
    a.codice_comune,
    b.regio, # Keep original columns from input.csv
    b.comu,
    (
        rapidfuzz_ratio(a.regione, b.regio) +
        rapidfuzz_ratio(a.comune, b.comu)
    ) / 2 AS avg_score
FROM read_csv_auto('$LEFT_TABLE', header=true) AS a
CROSS JOIN read_csv_auto('$RIGHT_TABLE', header=true) AS b;

-- 2. Rank pairs by score for each input record and identify top scores with ties
CREATE OR REPLACE TEMP VIEW ranked_scores AS
SELECT
    *,
    DENSE_RANK() OVER(PARTITION BY comu, regio ORDER BY avg_score DESC) as rnk # Partition by input.csv unique identifier
FROM all_scores
WHERE avg_score >= $THRESHOLD;

-- 3. Identify input records with ambiguous best matches (ties for the top rank)
CREATE OR REPLACE TEMP VIEW ambiguous_inputs AS
SELECT comu, regio
FROM ranked_scores
WHERE rnk = 1
GROUP BY comu, regio
HAVING COUNT(*) > 1;

-- 4. Export clean, unambiguous matches (top rank, no ties)
COPY (
    SELECT
        rs.regio,
        rs.comu,
        rs.codice_comune,
        rs.avg_score
    FROM ranked_scores rs
    LEFT JOIN ambiguous_inputs ai ON rs.comu = ai.comu AND rs.regio = ai.regio
    WHERE rs.rnk = 1 AND ai.comu IS NULL
) TO '$OUTPUT_CLEAN' (HEADER, DELIMITER ',');

-- 5. Export all potential matches for ambiguous input records
COPY (
    SELECT s.*
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