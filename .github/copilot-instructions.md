# tometo_tomato Development Instructions

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Project Overview

**tometo_tomato** is a Python CLI tool for performing fuzzy joins between two CSV files, handling typos, abbreviations, and formatting variations. It leverages DuckDB and the rapidfuzz extension to associate similar records across different sources.

## Working Effectively

### Quick Start (Tested Commands)
```bash
# Clone and setup (for first-time users)
git clone https://github.com/aborruso/tometo_tomato.git
cd tometo_tomato

# Install dependencies - NEVER CANCEL: May take 60+ seconds due to network timeouts
pip install duckdb rapidfuzz --timeout=120

# Run CLI directly (bypasses network-dependent pyproject.toml build)
PYTHONPATH=~/.local/lib/python3.12/site-packages python3 src/tometo_tomato.py data/raw/input.csv data/raw/ref.csv --join-pair regio,regione --join-pair comu,comune --add-field codice_comune --threshold 90 --show-score --output-clean output.csv

# Optional: Install as package (requires internet access, may timeout)
pip install . --timeout=300
```

### Build and Installation
- **Primary method**: Use CLI directly with `PYTHONPATH` (reliable, 1 second execution)
- **Alternative**: `pip install .` - NEVER CANCEL: Takes 60+ seconds, may timeout due to pyproject.toml network dependencies
- **Dependencies**: Python 3.8+, duckdb, rapidfuzz
- **Installation time**: Direct CLI: <1 second, Package install: 60+ seconds (network dependent)

### Bash CLI Generation (Optional)
```bash
# Install Ruby and Bashly - NEVER CANCEL: Takes 30+ seconds
gem install --user-install bashly
export PATH="$PATH:~/.local/share/gem/ruby/3.2.0/bin"

# Generate bash script - Takes <1 second
bashly generate

# Note: Bash CLI requires DuckDB CLI binary
wget https://github.com/duckdb/duckdb/releases/download/v1.3.2/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
sudo mv duckdb /usr/local/bin/
```

## Validation

### ALWAYS run these complete end-to-end scenarios after making changes:

#### Scenario 1: Explicit Column Mapping (Recommended)
```bash
PYTHONPATH=~/.local/lib/python3.12/site-packages python3 src/tometo_tomato.py data/raw/input.csv data/raw/ref.csv --join-pair regio,regione --join-pair comu,comune --add-field codice_comune --threshold 90 --show-score --output-clean test_output.csv
```
**Expected**: Creates CSV with fuzzy matches, ~1 second execution time

#### Scenario 2: Auto-Detection (Only works with identical column names)
```bash
PYTHONPATH=~/.local/lib/python3.12/site-packages python3 src/tometo_tomato.py input_same_cols.csv ref_same_cols.csv --add-field extra_field --threshold 80 --output-clean auto_output.csv
```
**Expected**: Auto-detects common columns if names match exactly

#### Scenario 3: Help and Version
```bash
python3 src/tometo_tomato.py --help
./tometo_tomato --help  # If bash CLI is generated
```

### Critical Testing Notes
- **ALWAYS test with sample data in `data/raw/`** before validating changes
- **Auto-detection requires EXACT column name matches** - different names will cause "No join pair found" error
- **Threshold behavior**: Low thresholds (70-80) may produce empty results if data is too dissimilar
- **Network dependencies**: rapidfuzz extension may be unavailable offline - Python CLI handles this gracefully, Bash CLI will fail

## Common Tasks

### Repository Structure
```
.
├── README.md                    # User documentation and examples
├── setup.py                     # Package configuration
├── pyproject.toml              # Build system (network dependent)
├── src/
│   ├── tometo_tomato.py        # Main Python CLI implementation
│   ├── bashly.yml              # Bash CLI configuration
│   └── root_command.sh         # Bash CLI implementation
├── data/
│   └── raw/                    # Sample data for testing
│       ├── input.csv           # Test input file
│       └── ref.csv             # Test reference file
├── docs/
│   └── PRD.md                  # Detailed requirements and use cases
└── .gemini/
    └── GEMINI.md               # Project context for AI agents
```

### Key Files to Check When Making Changes
- **Always test**: `src/tometo_tomato.py` after changing core logic
- **Always validate**: Sample data workflow after changing join algorithms
- **Always regenerate**: Bash CLI with `bashly generate` after changing `src/bashly.yml`
- **Always update**: `docs/PRD.md` if changing user-facing behavior

### Dependency Management
- **DuckDB Python**: Always available after `pip install duckdb`
- **rapidfuzz Python**: Always available after `pip install rapidfuzz`  
- **DuckDB CLI**: Download manually from GitHub releases (required for Bash CLI)
- **rapidfuzz extension**: Community extension, may fail offline (gracefully handled in Python CLI)

### Performance Expectations
- **Python CLI execution**: <1 second for sample data
- **Package installation**: 60+ seconds (network timeouts common)
- **Bash CLI generation**: <1 second
- **Dependency installation**: 30-120 seconds

### Error Patterns to Expect
- `No join pair found. Exiting.` - Column names don't match exactly (use explicit --join-pair)
- `pip subprocess did not run successfully` - Network timeout during package install (use direct CLI method)
- `duckdb: command not found` - Bash CLI requires DuckDB binary installation
- `rapidfuzz extension not found` - Network restriction (Python CLI will fallback gracefully)

### Limitations and Workarounds
- **Offline development**: Use `PYTHONPATH` approach, avoid `pip install .`
- **Bash CLI limitations**: Requires internet for rapidfuzz extension, use Python CLI instead
- **Column name sensitivity**: Auto-detection requires exact matches, prefer explicit mapping
- **Network timeouts**: Set pip timeout to 300+ seconds for reliable installs

## Environment Requirements
- Python 3.8+ (tested with 3.12)
- pip or equivalent package manager
- Internet access for dependency installation (optional for direct CLI usage)
- Ruby 3.2+ and gem (optional, for Bash CLI generation)