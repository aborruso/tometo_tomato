# PRD: Procedura di Join Flessibile (Fuzzy Join)

## Introduzione

### Contesto

L'integrazione di dati provenienti da fonti diverse presenta spesso una sfida comune: la mancanza di chiavi di join univoche e consistenti. Errori di battitura, abbreviazioni, variazioni nella formattazione o semplici discrepanze (es. "Reggio di Calabria", "Reggio Calabria", "Reggiò Calabria") rendono inefficaci i join SQL standard (`A.key = B.key`).

Questo documento definisce i requisiti per una procedura di "fuzzy join" che permette di collegare record tra due tabelle basandosi sulla somiglianza testuale dei campi, anziché su una corrispondenza esatta.

### Obiettivo

Creare un processo robusto, configurabile e performante per eseguire il join di tabelle tramite *fuzzy string matching*. Il sistema dovrà identificare la migliore corrispondenza possibile per ogni record, gestire in modo trasparente le ambiguità e fornire output chiari e pronti per l'analisi.

## Requisiti Funzionali

### RF1: Logica di Join Basata su Somiglianza

La procedura consente di effettuare un join tra una tabella A (sinistra) e una tabella B (destra) basandosi sulla somiglianza di una o più coppie di colonne testuali.
**Novità:** Se non vengono specificate le colonne da confrontare (`--join-pair`), il sistema utilizza automaticamente tutte le colonne con lo stesso nome presenti in entrambi i file.

### RF2: Calcolo del Punteggio di Somiglianza

Per ogni record della tabella A, il sistema calcola un punteggio di somiglianza (da 0 a 100) con tutti i record della tabella B, usando le funzioni dell'estensione `rapidfuzz` per DuckDB.

### RF3: Selezione della Migliore Corrispondenza (*Best Match*)

- Il sistema identifica come "migliore corrispondenza" il record della tabella B che ottiene il punteggio di somiglianza più alto.
- Un join è valido solo se il punteggio supera una **soglia minima configurabile** (es. `85`). Tutti i match con punteggio inferiore vengono scartati.

### RF4: Supporto per Join Multi-colonna

La procedura supporta il join basato su più coppie di colonne. Se non specificato, usa tutte le colonne comuni.

### RF5: Gestione delle Ambiguità e dei Duplicati

- **Definizione di ambiguità**: Si ha un'ambiguità quando un record della tabella A ottiene lo **stesso punteggio massimo** per più record della tabella B.
- **Gestione**: In caso di ambiguità, il record di A e tutti i record corrispondenti di B vengono esclusi dal risultato finale del join.
- **Output delle ambiguità**: Tutti i record esclusi a causa di ambiguità vengono salvati in un file separato (es. `log_ambigui.csv`) per analisi manuale.

### RF6: Struttura degli Output

La procedura produce due output principali:
1.  **Tabella di Join Pulita**: File con i record che hanno trovato una corrispondenza univoca e superiore alla soglia.
2.  **File di Log delle Ambiguità**: File con i record scartati per le ragioni descritte in RF5.

## Requisiti Non Funzionali

### RNF1: Performance

La procedura è ottimizzata per gestire dataset di grandi dimensioni. L'uso di `WHERE score > soglia` in DuckDB riduce il carico computazionale.

### RNF2: Configurabilità

L'utente può configurare facilmente:
- Percorsi dei file di input.
- Nomi delle colonne da utilizzare per il join (opzionali, se omessi si usano le colonne comuni).
- Soglia di somiglianza (numero da 0 a 100).
- Funzione `rapidfuzz` da utilizzare (es. `rapidfuzz_ratio`, `rapidfuzz_token_sort_ratio`).
- Percorsi dei file di output.

### RNF3: Tracciabilità

Il processo produce un log di esecuzione con statistiche chiave: numero di record in input, join riusciti, casi ambigui.

## Stack Tecnologico

- **Motore di elaborazione**: DuckDB
- **Libreria di Fuzzy Matching**: Estensione `rapidfuzz` per DuckDB
- **Orchestrazione**: Script Shell (CLI monocomando: `tometo_tomato`)

## Caso d'Uso Esemplificativo (Associazione Codici ISTAT)

Questo caso d'uso dimostra l'associazione di codici ISTAT a un'anagrafica non ufficiale, gestendo le imprecisioni nei nomi delle località.

- **Tabella A (`ref.csv` - Fonte ISTAT)**
  Contiene dati ufficiali di comuni italiani.

  | regione    | comune          | codice_comune |
  | :--------- | :-------------- | :------------ |
  | Calabria   | Reggio Calabria | 80065         |
  | Lombardia  | Milano          | 015146        |
  | Piemonte   | Torino          | 001272        |
  | Lazio      | Roma            | 058091        |
  | Campania   | Napoli          | 063049        |

- **Tabella B (`input.csv` - Anagrafica non ufficiale)**
  Contiene dati con possibili errori di battitura.

  | regio     | comu          |
  | :-------- | :------------ |
  | Calabria  | Reggio Calabr |
  | Lombardia | Milano        |
  | Piemonte  | Torinoo       |
  | Lazio     | Rma           |
  | Campania  | Napoli        |

- **Obiettivo**
  Associare il `codice_comune` dalla Tabella A (`ref.csv`) ai record della Tabella B (`input.csv`).

- **Configurazione (Esempio di Chiamata CLI)**
  Il processo viene eseguito tramite il comando CLI monocomando `tometo_tomato`:

  ```bash
  ./tometo_tomato input.csv ref.csv --join-pair regione,regio --join-pair comune,comu --add-field codice_comune --threshold 90 --show-score
  ```

  Oppure, se le colonne da confrontare coincidono nei due file:

  ```bash
  ./tometo_tomato input.csv ref.csv --add-field codice_comune --threshold 90 --show-score
  ```

- **Risultato Atteso**

  Il processo identifica la migliore corrispondenza per ogni riga di `input.csv` in `ref.csv` e associa il `codice_comune` corrispondente.

  Esempio di match atteso:
  - `input.csv` (Reggio Calabr, Calabria) -> `ref.csv` (Reggio Calabria, Calabria) con `codice_comune` 80065.
  - `input.csv` (Torinoo, Piemonte) -> `ref.csv` (Torino, Piemonte) con `codice_comune` 001272.
  - `input.csv` (Rma, Lazio) -> `ref.csv` (Roma, Lazio) con `codice_comune` 058091.

  Il risultato finale è una tabella con le colonne di `input.csv` più il `codice_comune` associato.

