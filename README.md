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
- `input.csv` : File CSV da arricchire/correggere
- `ref.csv`   : File CSV di riferimento
- `--join-pair colA,colB` : Coppia di colonne da confrontare (ripetibile)
- `--add-field campo`     : Campo del file di riferimento da aggiungere all'output
- `--threshold N`         : Soglia minima di somiglianza (default: 90)
- `--show-score`          : Mostra il punteggio di somiglianza medio
- `--output-clean`        : File di output per i match puliti (obbligatorio)
- `--output-ambiguous`    : File di output per i match ambigui (facoltativo)

## Logica e comportamento
- Il confronto fuzzy avviene sempre su valori convertiti in minuscolo (case-insensitive).
- Il join è di tipo LEFT JOIN: tutti i record del file di input sono sempre presenti nell'output pulito.
- Il file pulito contiene solo il miglior match per ogni riga di input (se supera la soglia).
- Puoi aggiungere campi extra dal file di riferimento con `--add-field`.
- Se specifichi `--output-ambiguous`, viene generato anche un file con i record ambigui (più match con lo stesso punteggio massimo).
- Se non ci sono record ambigui, il file viene cancellato e la shell ti avvisa.
- Se ci sono record ambigui, la shell ti avvisa e ti indica il file da controllare.

## Output
- Un file CSV con i match puliti (nome e path sempre da specificare con `--output-clean`)
- Un file CSV con i match ambigui (solo se specifichi `--output-ambiguous`)

## Esempio di caso d'uso
Vedi il file [docs/PRD.md](docs/PRD.md) per una descrizione dettagliata e un esempio pratico.

## Note
- Se non specifichi `--join-pair`, verranno usate tutte le colonne con lo stesso nome nei due file.
- Il tool è pensato per essere semplice, robusto e facilmente integrabile in flussi di data cleaning.

---

Per domande, suggerimenti o bug, apri una issue su GitHub!
