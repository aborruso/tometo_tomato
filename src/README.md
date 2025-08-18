# fuzzy_join.py

Script Python che replica la logica di `root_command.sh` usando DuckDB.

Esempio di esecuzione:

```bash
python3 src/fuzzy_join.py data/raw/input.csv data/raw/ref.csv --join-pair regio,regione --join-pair comu,comune --add-field codice_comune --threshold 90 --show-score --output-clean out.csv --output-ambiguous ambigui.csv
```

Comportamento:
- Prova a caricare l'estensione `rapidfuzz` in DuckDB; se non disponibile, usa `levenshtein` o `damerau_levenshtein` per calcolare una similarità normalizzata.
- Produce due file: uno con i match puliti (`--output-clean`) e uno con i record ambigui (`--output-ambiguous`).

Opzione utile: inferenza automatica delle coppie
- Usa `--infer-pairs` per tentare di abbinare automaticamente colonne con nomi simili (es. `regio` -> `regione`).
- È possibile regolare la soglia di similarità dei nomi con `--infer-threshold` (valore tra 0 e 1, default 0.7).

Esempio con inferenza automatica:

```bash
python3 src/fuzzy_join.py data/raw/input.csv data/raw/ref.csv --infer-pairs --add-field codice_comune --threshold 85 --show-score --output-clean out.csv
```

Esempio (short flags):

```bash
python3 src/fuzzy_join.py data/raw/input.csv data/raw/ref.csv -i -a codice_comune -t 85 -s -o out_short.csv
```

Future tasks
- Normalizzare meglio le intestazioni prima della inferenza (rimozione accenti, stopwords, tokenization e lowercasing) per migliorare i match tra nomi colonna dissimili.
- Aggiungere logging statistico (conteggio record input, matched, unmatched, ambiguous) e output di diagnostica.
- Aggiungere test unitari per le funzioni di parsing header, inferenza delle coppie e costruzione SQL.
