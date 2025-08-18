# PRD: Procedura di Join Flessibile (Fuzzy Join)

## 1. Introduzione

### Contesto

L'integrazione di dati provenienti da fonti diverse presenta spesso una sfida comune: la mancanza di chiavi di join univoche e consistenti. Errori di battitura, abbreviazioni, variazioni nella formattazione o semplici discrepanze (es. "Reggio di Calabria", "Reggio Calabria", "Reggiò Calabria") rendono inefficaci i join SQL standard (`A.key = B.key`).

Questo documento definisce i requisiti per una procedura di "fuzzy join" che permette di collegare record tra due tabelle basandosi sulla somiglianza testuale dei campi, anziché su una corrispondenza esatta.

### Obiettivo

Creare un processo robusto, configurabile e performante per eseguire il join di tabelle tramite *fuzzy string matching*. Il sistema dovrà identificare la migliore corrispondenza possibile per ogni record, gestire in modo trasparente le ambiguità e fornire output chiari e pronti per l'analisi.

## 2. Requisiti Funzionali

### RF1: Logica di Join Basata su Somiglianza

La procedura deve consentire di effettuare un join tra una tabella A (sinistra) e una tabella B (destra) basandosi sulla somiglianza di una o più coppie di colonne testuali.

### RF2: Calcolo del Punteggio di Somiglianza

Per ogni record della tabella A, il sistema deve calcolare un punteggio di somiglianza (da 0 a 100) con tutti i record della tabella B. Questo calcolo verrà eseguito utilizzando le funzioni messe a disposizione dall'estensione `rapidfuzz` per DuckDB.

### RF3: Selezione della Migliore Corrispondenza (*Best Match*)

- Il sistema deve identificare come "migliore corrispondenza" il record della tabella B che ottiene il punteggio di somiglianza più alto.
- Un join verrà considerato valido solo se il punteggio di somiglianza supera una **soglia minima configurabile** (es. `85`). Tutti i match con punteggio inferiore verranno scartati.

### RF4: Supporto per Join Multi-colonna

La procedura deve supportare il join basato su più coppie di colonne. In questo scenario, per ogni record di A, verrà calcolato il punteggio di somiglianza per ogni coppia di colonne con i record di B. La coppia di colonne che produce il punteggio più alto determinerà il *best match*.

### RF5: Gestione delle Ambiguità e dei Duplicati

- **Definizione di ambiguità**: Si ha un'ambiguità quando un record della tabella A ottiene lo **stesso punteggio massimo** per più record della tabella B.
- **Gestione**: In caso di ambiguità, il record di A e tutti i record corrispondenti di B verranno esclusi dal risultato finale del join.
- **Output delle ambiguità**: Tutti i record esclusi a causa di ambiguità verranno salvati in un file separato (es. `log_ambigui.csv`) per consentire un'analisi manuale.

### RF6: Struttura degli Output

La procedura dovrà produrre due output principali:

1.  **Tabella di Join Pulita**: Un file contenente i record che hanno trovato una corrispondenza univoca e superiore alla soglia.
2.  **File di Log delle Ambiguità**: Un file contenente i record scartati per le ragioni descritte in RF5.

## 3. Requisiti Non Funzionali

### RNF1: Performance

La procedura deve essere ottimizzata per gestire dataset di grandi dimensioni. L'uso di `WHERE score > soglia` durante l'elaborazione in DuckDB è fondamentale per ridurre il carico computazionale.

### RNF2: Configurabilità

L'utente deve poter configurare facilmente i seguenti parametri:

- Percorsi dei file di input.
- Nomi delle colonne da utilizzare per il join.
- Soglia di somiglianza (numero da 0 a 100).
- Funzione `rapidfuzz` da utilizzare (es. `rapidfuzz_ratio`, `rapidfuzz_token_sort_ratio`).
- Percorsi dei file di output.

### RNF3: Tracciabilità

Il processo deve produrre un log di esecuzione che riporti le statistiche chiave, come il numero di record in input, il numero di join riusciti e il numero di casi ambigui riscontrati.

## 4. Stack Tecnologico

- **Motore di elaborazione**: DuckDB
- **Libreria di Fuzzy Matching**: Estensione `rapidfuzz` per DuckDB
- **Orchestrazione**: Script Python o Shell per automatizzare il flusso.

## 5. Caso d'Uso Esemplificativo (Associazione Codici ISTAT)

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
  Il processo verrà eseguito tramite il comando CLI `fuzzy-join-cli fuzzy-join` con i seguenti parametri:

  ```bash
  ./fuzzy-cli fuzzy-join \
    input.csv \
    ref.csv \
    --join-pair regione regio \
    --join-pair comune comu \
    --add-field codice_comune \
    --threshold 90 \
    --show-score
  ```

- **Risultato Atteso**

  Il processo identificherà la migliore corrispondenza per ogni riga di `input.csv` in `ref.csv` e assocerà il `codice_comune` corrispondente.

  Esempio di match atteso:
  - `input.csv` (Reggio Calabr, Calabria) -> `ref.csv` (Reggio Calabria, Calabria) con `codice_comune` 80065.
  - `input.csv` (Torinoo, Piemonte) -> `ref.csv` (Torino, Piemonte) con `codice_comune` 001272.
  - `input.csv` (Rma, Lazio) -> `ref.csv` (Roma, Lazio) con `codice_comune` 058091.

  Il risultato finale sarà una tabella con le colonne di `input.csv` più il `codice_comune` associato.

