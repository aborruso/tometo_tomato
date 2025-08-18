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
LEFT_TABLE='data/raw/anagrafica.csv'
RIGHT_TABLE='data/raw/fatture.csv'
OUTPUT_DIR='data/processed'
OUTPUT_CLEAN="$OUTPUT_DIR/joined_clean.csv"
OUTPUT_AMBIGUOUS="$OUTPUT_DIR/joined_ambiguous.csv"
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
    a.id_cliente,
    b.id_fattura,
    (
        rapidfuzz_ratio(a.comune_residenza, b.localita) +
        rapidfuzz_ratio(a.regione, b.regione_fattura)
    ) / 2 AS avg_score
FROM read_csv_auto('$LEFT_TABLE', header=true) AS a
CROSS JOIN read_csv_auto('$RIGHT_TABLE', header=true) AS b;

-- 2. Rank pairs by score for each client and identify top scores with ties
CREATE OR REPLACE TEMP VIEW ranked_scores AS
SELECT
    *,
    DENSE_RANK() OVER(PARTITION BY id_cliente ORDER BY avg_score DESC) as rnk
FROM all_scores
WHERE avg_score >= $THRESHOLD;

-- 3. Identify clients with ambiguous best matches (ties for the top rank)
CREATE OR REPLACE TEMP VIEW ambiguous_clients AS
SELECT id_cliente
FROM ranked_scores
WHERE rnk = 1
GROUP BY id_cliente
HAVING COUNT(*) > 1;

-- 4. Export clean, unambiguous matches (top rank, no ties)
COPY (
    SELECT rs.id_cliente, rs.id_fattura, rs.avg_score
    FROM ranked_scores rs
    LEFT JOIN ambiguous_clients ac ON rs.id_cliente = ac.id_cliente
    WHERE rs.rnk = 1 AND ac.id_cliente IS NULL
) TO '$OUTPUT_CLEAN' (HEADER, DELIMITER ',');

-- 5. Export all potential matches for ambiguous clients
COPY (
    SELECT s.*
    FROM all_scores s
    WHERE s.id_cliente IN (SELECT id_cliente FROM ambiguous_clients)
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
