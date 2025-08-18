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

## 5. Caso d'Uso Esemplificativo

- **Tabella A (`anagrafica.csv`)**

| id_cliente | comune_residenza      |
| :--------- | :-------------------- |
| 1          | 'Reggio di Calabria'  |
| 2          | 'Milano'              |

- **Tabella B (`fatture.csv`)**

| id_fattura | localita        | importo |
| :--------- | :-------------- | :------ |
| 101        | 'Reggio Calabria' | 500     |
| 102        | 'Reggiò Calabria' | 600     |
| 103        | 'Milano'          | 700     |

- **Configurazione**
  - Join tra `comune_residenza` e `localita`.
  - Soglia: `90`.
  - Funzione: `rapidfuzz_token_sort_ratio`.

- **Risultato Atteso**
  - `rapidfuzz_token_sort_ratio('Reggio di Calabria', 'Reggio Calabria')` -> `~96`
  - `rapidfuzz_token_sort_ratio('Reggio di Calabria', 'Reggiò Calabria')` -> `~93`
  - Il record `1` di A matcha con `101` di B (punteggio più alto).
  - Il record `2` di A matcha con `103` di B (punteggio `100`).
  - **Output Pulito**: Join tra `(1, 101)` e `(2, 103)`.
  - **Output Ambigui**: Vuoto.
