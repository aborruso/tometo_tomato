# tometo_tomato

**tometo_tomato** è una CLI per eseguire join fuzzy tra due file CSV, anche in presenza di errori di battitura, abbreviazioni o formattazioni diverse. Utilizza DuckDB e l'estensione rapidfuzz per associare record simili tra fonti diverse.

## Caratteristiche
- Join tra due file CSV basato sulla somiglianza testuale
- Supporto multi-colonna (puoi specificare più coppie di colonne oppure usare automaticamente quelle con lo stesso nome)
- Soglia di somiglianza configurabile
- Output separato per match puliti e ambigui
- Log delle statistiche di esecuzione

## Installazione

### Prerequisiti
- [DuckDB](https://duckdb.org/) installato e disponibile nel PATH
- Bash (consigliato su Linux/macOS)

### Installazione rapida
Clona la repository e rendi eseguibile la CLI:

```bash
git clone https://github.com/tuo-utente/tometo_tomato.git
cd tometo_tomato
chmod +x tometo_tomato
```

### Installazione come comando locale
Puoi installare la CLI in `/home/aborruso/bin/` (o in una directory del tuo PATH) in due modi:

**Metodo 1: Copia manuale**
```bash
cp tometo_tomato /home/aborruso/bin/
```
Assicurati che `/home/aborruso/bin/` sia nel tuo PATH:
```bash
export PATH="$HOME/bin:$PATH"
```
Ora puoi lanciare il comando da qualsiasi directory:
```bash
tometo_tomato ...
```

**Metodo 2: Usando Bashly**
Se hai Bashly installato, puoi generare direttamente la CLI nella directory desiderata:

Nota: Bashly non supporta l'opzione --output-dir. Il file viene generato nella directory corrente e va copiato manualmente dove desideri.

```bash
bashly generate
# esempio
cp tometo_tomato /home/username/bin/
```

## Utilizzo

### Esempio base
Supponiamo di avere due file:
- `input.csv` (anagrafica non ufficiale)
- `ref.csv` (fonte ufficiale)

Se le colonne da confrontare hanno lo stesso nome nei due file:

```bash
tometo_tomato input.csv ref.csv --add-field codice_comune --threshold 90 --show-score
```

Se le colonne hanno nomi diversi:

```bash
tometo_tomato input.csv ref.csv \
  --join-pair regione,regio \
  --join-pair comune,comu \
  --add-field codice_comune \
  --threshold 90 \
  --show-score
```

### Parametri principali
- `input.csv` : File CSV da arricchire/correggere
- `ref.csv`   : File CSV di riferimento
- `--join-pair colA,colB` : Coppia di colonne da confrontare (ripetibile)
- `--add-field campo`     : Campo del file di riferimento da aggiungere all'output
- `--threshold N`         : Soglia minima di somiglianza (default: 90)
- `--show-score`          : Mostra il punteggio di somiglianza medio
- `--output-clean`        : File di output per i match puliti
- `--output-ambiguous`    : File di output per i match ambigui

## Output
- Un file CSV con i match puliti (di default: `data/processed/joined_istat_codes.csv`)
- Un file CSV con i match ambigui (di default: `data/processed/ambiguous_istat_matches.csv`)

## Esempio di caso d'uso
Vedi il file [docs/PRD.md](docs/PRD.md) per una descrizione dettagliata e un esempio pratico.

## Note
- Se non specifichi `--join-pair`, verranno usate tutte le colonne con lo stesso nome nei due file.
- Il tool è pensato per essere semplice, robusto e facilmente integrabile in flussi di data cleaning.

---

Per domande, suggerimenti o bug, apri una issue su GitHub!
