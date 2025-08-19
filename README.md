# tometo_tomato

**tometo_tomato** is a Python CLI tool for performing fuzzy joins between two CSV files, even in the presence of typos, abbreviations, or different formatting. It leverages DuckDB and the rapidfuzz extension to associate similar records across different sources.

## Caratteristiche
- Join tra due file CSV basato sulla somiglianza testuale
- Supporto multi-colonna (puoi specificare più coppie di colonne oppure usare automaticamente quelle con lo stesso nome)
- Soglia di somiglianza configurabile
- Output separato per match puliti e ambigui
- Log delle statistiche di esecuzione

## Installation

### Prerequisites
- Python 3.8 or higher
- `pip` or `uv` (recommended)

### Install from source
1. Clone the repository:
   ```bash
   git clone https://github.com/aborruso/tometo_tomato.git
   cd tometo_tomato
   ```
2. Install the package:
   Using `uv` (recommended):
   ```bash
   uv pip install .
   # Or, for an isolated CLI tool:
   uv tool install .
   ```
   Using `pip`:
   ```bash
   pip install .
   ```

After installation, the `tometo_tomato` command will be available in your terminal.

## Utilizzo

### Esempio base
Supponiamo di avere due file:
- `input.csv` (anagrafica non ufficiale)
- `ref.csv` (fonte ufficiale)


### Esempio base
Se le colonne da confrontare hanno lo stesso nome nei due file:

```bash
tometo_tomato input.csv ref.csv --add-field codice_comune --threshold 90 --show-score --output-clean output.csv
```

Se le colonne hanno nomi diversi:

```bash
tometo_tomato input.csv ref.csv \
  --join-pair regione,regio \
  --join-pair comune,comu \
  --add-field codice_comune \
  --threshold 90 \
  --show-score \
  --output-clean output.csv
```

### Parametri principali
- `input.csv` : CSV file to enrich/correct
- `ref.csv`   : Reference CSV file
- `--join-pair colA,colB` : Pair of columns to compare (repeatable)
- `--add-field field`     : Field from the reference file to add to the output
- `--threshold N`         : Minimum similarity threshold (default: 90)
- `--show-score`          : Show average similarity score
- `--output-clean`        : Output file for clean matches (mandatory)
- `--output-ambiguous`    : Output file for ambiguous matches (optional)

## Logic and Behavior
- Fuzzy comparison is always case-insensitive (LOWER).
- The join is a LEFT JOIN: all input file records are always present in the clean output.
- The clean output file contains only the best match for each input row (if it exceeds the threshold).
- You can add extra fields from the reference file using `--add-field`.
- If you specify `--output-ambiguous`, an ambiguous records file is generated (for multiple matches with the same highest score).
- If no ambiguous records are found, a message "No ambiguous records found." is displayed.
- If ambiguous records are found, a warning message is displayed, indicating the file to check.

## Output
- A CSV file with clean matches (name and path always specified with `--output-clean`).
- A CSV file with ambiguous matches (only if you specify `--output-ambiguous`).

## Esempio di caso d'uso
Vedi il file [docs/PRD.md](docs/PRD.md) per una descrizione dettagliata e un esempio pratico.

## Notes
- If you don't specify `--join-pair`, all columns with the same name in both files will be used.
- The tool is designed to be simple, robust, and easily integrable into data cleaning workflows.

---

For questions, suggestions, or bugs, open an issue on GitHub!
