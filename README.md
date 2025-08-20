# tometo_tomato

**tometo_tomato** is a Python CLI tool for performing fuzzy joins between two CSV files, even in the presence of typos, abbreviations, or different formatting. It leverages DuckDB and the rapidfuzz extension to associate similar records across different sources.

## Features
- Join between two CSV files based on textual similarity
- Multi-column support (you can specify multiple column pairs or automatically use those with the same name)
- Configurable similarity threshold
- Separate output for clean and ambiguous matches
- Execution statistics logging

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

## Usage

### Basic example
Suppose we have two files:
- `input.csv` (unofficial registry)
- `ref.csv` (official source)


### Basic example
If the columns to compare have the same name in both files:

```bash
tometo_tomato input.csv ref.csv --add-field codice_comune --threshold 90 --show-score --output-clean output.csv
```

If the columns have different names:

```bash
tometo_tomato input.csv ref.csv \
  --join-pair regione,regio \
  --join-pair comune,comu \
  --add-field codice_comune \
  --threshold 90 \
  --show-score \
  --output-clean output.csv
```

### Handling Field Names with Spaces

If your column names in the CSV files contain spaces, you must enclose the arguments for `--join-pair` (`-j`) and `--add-field` (`-a`) in quotes. This ensures that the shell treats them as a single argument.

**Example:**

Suppose your files have columns named `"Input City"` and `"Reference City"`, and you want to add a field named `"Special Code"`.

```bash
tometo_tomato "input data.csv" "reference data.csv" \
  --join-pair "Input City,Reference City" \
  --add-field "Special Code" \
  --output-clean "clean output.csv"
```

### Cleaning Whitespace for Better Matching

If your data contains inconsistent whitespace (multiple spaces, leading/trailing spaces), use `--clean-whitespace` to normalize spacing before fuzzy matching:

```bash
tometo_tomato input.csv ref.csv \
  --join-pair city,city_name \
  --clean-whitespace \
  --threshold 90 \
  --output-clean output.csv
```

This is especially useful when dealing with data that has formatting inconsistencies like `"Rome  City"` vs `" Rome City "`.

### Main parameters
- `input.csv` : CSV file to enrich/correct
- `ref.csv`   : Reference CSV file
- `--join-pair colA,colB` : Pair of columns to compare (repeatable)

- `--add-field field`     : Field from the reference file to add to the output
- `--threshold N`         : Minimum similarity threshold (default: 90)
- `--show-score`          : Show average similarity score
- `--output-clean`        : Output file for clean matches (mandatory)
- `--output-ambiguous`    : Output file for ambiguous matches (optional)
- `--scorer ALGO`         : Fuzzy matching algorithm (`ratio` or `token_set_ratio`). Default: `ratio`.
- `--clean-whitespace`    : Remove redundant whitespace from columns before fuzzy matching

## Logic and Behavior
- Fuzzy comparison is always case-insensitive (LOWER).
- The join is a LEFT JOIN: all input file records are always present in the clean output.
- The clean output file contains only the best match for each input row (if it exceeds the threshold).
- You can add extra fields from the reference file using `--add-field`.
- If you specify `--output-ambiguous`, an ambiguous records file is generated (for multiple matches with the same highest score).
- If no ambiguous records are found, a message "No ambiguous records found." is displayed.
- If ambiguous records are found, a warning message is displayed, indicating the file to check.
- The `--clean-whitespace` option applies whitespace normalization to join columns before fuzzy matching, removing leading/trailing spaces and replacing multiple consecutive spaces with single spaces.

## Output
- A CSV file with clean matches (name and path always specified with `--output-clean`).
- A CSV file with ambiguous matches (only if you specify `--output-ambiguous`).

## Use case example
See the file [docs/PRD.md](docs/PRD.md) for a detailed description and practical example.

## Notes
- The `--scorer token_set_ratio` is recommended for cases where names have different word counts (e.g., "Reggio Calabria" vs. "Reggio di Calabria").
- If you don't specify `--join-pair`, all columns with the same name in both files will be used.
- Use `--clean-whitespace` when your data contains inconsistent spacing (e.g., "Rome  City" vs " Rome City ") to improve matching accuracy.
- The tool is designed to be simple, robust, and easily integrable into data cleaning workflows.

## Development

### Running tests

To run the test suite locally, you need to set the `PYTHONPATH` to use the local source code:

```bash
# Run all tests
PYTHONPATH=$(pwd)/src pytest -v

# Run specific test files
PYTHONPATH=$(pwd)/src pytest tests/test_read_header.py -v
```

Alternatively, you can install the package in editable mode:

```bash
pip install -e .
pytest -v
```

---

For questions, suggestions, or bugs, open an issue on GitHub!
