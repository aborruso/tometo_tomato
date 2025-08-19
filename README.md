# tometo_tomato

**tometo_tomato** è uno strumento CLI Python per eseguire join fuzzy tra due file CSV, anche in presenza di errori di battitura, abbreviazioni o formattazioni diverse. Utilizza DuckDB e l'estensione rapidfuzz per associare record simili tra diverse fonti.

## Caratteristiche
- Join tra due file CSV basato sulla somiglianza testuale
- Supporto multi-colonna (puoi specificare più coppie di colonne oppure usare automaticamente quelle con lo stesso nome)
- Soglia di somiglianza configurabile
- Output separato per match puliti e ambigui
- Log delle statistiche di esecuzione

## Installazione

### Prerequisiti
- Python 3.8 o superiore
- `pip` o `uv` (consigliato)

### Installazione dal codice sorgente
1. Clona il repository:
   ```bash
   git clone https://github.com/aborruso/tometo_tomato.git
   cd tometo_tomato
   ```
2. Installa il pacchetto:
   Usando `uv` (consigliato):
   ```bash
   uv pip install .
   # Oppure, per uno strumento CLI isolato:
   uv tool install .
   ```
   Usando `pip`:
   ```bash
   pip install .
   ```

Dopo l'installazione, il comando `tometo_tomato` sarà disponibile nel tuo terminale.

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

### Gestione dei nomi di campo con spazi

Se i nomi delle colonne nei file CSV contengono spazi, devi racchiudere gli argomenti per `--join-pair` (`-j`) e `--add-field` (`-a`) tra virgolette. Questo garantisce che la shell li tratti come un singolo argomento.

**Esempio:**

Supponiamo che i tuoi file abbiano colonne chiamate `"Input City"` e `"Reference City"`, e tu voglia aggiungere un campo chiamato `"Special Code"`.

```bash
tometo_tomato "input data.csv" "reference data.csv" \
  --join-pair "Input City,Reference City" \
  --add-field "Special Code" \
  --output-clean "clean output.csv"
```

### Parametri principali
- `input.csv` : File CSV da arricchire/correggere
- `ref.csv`   : File CSV di riferimento
- `--join-pair colA,colB` : Coppia di colonne da confrontare (ripetibile)

- `--add-field field`     : Campo dal file di riferimento da aggiungere all'output
- `--threshold N`         : Soglia minima di somiglianza (default: 90)
- `--show-score`          : Mostra il punteggio medio di somiglianza
- `--output-clean`        : File di output per i match puliti (obbligatorio)
- `--output-ambiguous`    : File di output per i match ambigui (opzionale)
- `--scorer ALGO`         : Algoritmo di matching fuzzy (`ratio` o `token_set_ratio`). Default: `ratio`.

## Logica e Comportamento
- Il confronto fuzzy è sempre case-insensitive (LOWER).
- Il join è un LEFT JOIN: tutti i record del file di input sono sempre presenti nell'output pulito.
- Il file di output pulito contiene solo la migliore corrispondenza per ogni riga di input (se supera la soglia).
- Puoi aggiungere campi extra dal file di riferimento usando `--add-field`.
- Se specifichi `--output-ambiguous`, viene generato un file di record ambigui (per corrispondenze multiple con lo stesso punteggio più alto).
- Se non vengono trovati record ambigui, viene visualizzato il messaggio "Nessun record ambiguo trovato.".
- Se vengono trovati record ambigui, viene visualizzato un messaggio di avviso che indica il file da controllare.

## Output
- Un file CSV con i match puliti (nome e percorso sempre specificati con `--output-clean`).
- Un file CSV con i match ambigui (solo se specifichi `--output-ambiguous`).

## Esempio di caso d'uso
Vedi il file [docs/PRD.md](docs/PRD.md) per una descrizione dettagliata e un esempio pratico.

## Note
- Il `--scorer token_set_ratio` è consigliato per i casi in cui i nomi hanno conteggi di parole diversi (ad esempio, "Reggio Calabria" vs. "Reggio di Calabria").
- Se non specifichi `--join-pair`, verranno utilizzate tutte le colonne con lo stesso nome in entrambi i file.
- Lo strumento è progettato per essere semplice, robusto e facilmente integrabile nei flussi di lavoro di pulizia dei dati.

---

Per domande, suggerimenti o bug, apri un issue su GitHub!
