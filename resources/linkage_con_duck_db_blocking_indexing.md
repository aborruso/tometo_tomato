# Record linkage con DuckDB: blocking & indexing

> Obiettivo: collegare nomi di Comuni/Regioni “sporchi” al **codice corretto** (es. codice ISTAT) in modo rapido e ripetibile, limitando i confronti fuzzy ai soli candidati sensati.

---

## Quando servono

- **Blocking**: riduce il numero di confronti creando **mini-insiemi di candidati** (blocchi). Da N×M confronti a tanti join locali più piccoli.
- **Indexing**: accelera filtri e lookup selettivi. In DuckDB: **zonemap** automatiche, **indici ART** espliciti, **Full‑Text Search (FTS)** per ricerche testuali, e **parquet pruning** (min/max, statistiche; opzionalmente Bloom filter se presenti).

**Perché conviene**

- Meno CPU: confronti fuzzy solo tra record plausibili.
- Meno I/O: pruning su Parquet e partizionamento saltano file/row‑group inutili.
- Pipeline più prevedibile: tempi e memoria sotto controllo anche su file grandi.

---

## Ricetta base (toponimi: Comune + Regione)

### 1) Normalizzazione + chiave di blocco

Puliamo e costruiamo una **blocking\_key** semplice ma robusta (prime 3 lettere di comune e regione, in minuscolo; rimozione accentate solo se serve).

> Nota accentate: se non hai una funzione “unaccent”, puoi mappare le vocali più comuni con `replace()`.

```sql
-- INPUT normalizzato
CREATE OR REPLACE TABLE input_stg AS
SELECT
  city,
  region,
  -- normalizzazione semplice (minuscole + mappa accentate italiane più comuni)
  replace(replace(replace(replace(replace(lower(city), 'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS city_n,
  replace(replace(replace(replace(replace(lower(region),'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS region_n,
  substr(lower(city),   1, 3) || '|' || substr(lower(region), 1, 3) AS block_key
FROM read_csv_auto('input.csv');

-- REFERENCE normalizzato
CREATE OR REPLACE TABLE ref_stg AS
SELECT
  city_code,
  city   AS ref_city,
  region AS ref_region,
  replace(replace(replace(replace(replace(lower(city), 'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS ref_city_n,
  replace(replace(replace(replace(replace(lower(region),'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS ref_region_n,
  substr(lower(city),   1, 3) || '|' || substr(lower(region), 1, 3) AS block_key
FROM read_csv_auto('ref_sample.csv');
```

### 2) Join per blocco + distanza + best match

Calcola Levenshtein (o RapidFuzz) **solo dentro lo stesso blocco**; ordina per distanza totale e prendi il primo.

```sql
WITH cand AS (
  SELECT
    i.city, i.region,
    r.ref_city, r.ref_region, r.city_code,
    levenshtein(i.city_n,  r.ref_city_n)  AS d_city,
    levenshtein(i.region_n,r.ref_region_n) AS d_reg
  FROM input_stg i
  JOIN ref_stg  r USING (block_key)
), ranked AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY city, region ORDER BY (d_city + d_reg)) AS rn
  FROM cand
)
SELECT *
FROM ranked
WHERE rn = 1         -- miglior candidato
  AND d_city <= 2    -- soglie da tarare sui tuoi dati
  AND d_reg  <= 1;
```

**Suggerimenti pratici**

- Se i blocchi sono troppo “larghi”, usa 4‑5 lettere o aggiungi un altro indizio (es. provincia).
- Se i blocchi sono troppo “stretti”, perdi recall: allenta a 2‑3 lettere o aggiungi una seconda chiave alternativa (OR logico).

---

## Varianti di blocking

- **Fonetico** (Soundex/Metaphone): utile per “S. Giovanni” \~ “San Giovanni”. Puoi pre‑calcolare fuori DuckDB o con UDF.
- **q‑gram/bigram**: genera n‑grammi e mantieni i candidati con sufficiente sovrapposizione.
- **FTS come pre‑selezione**: estrai i **top‑k** candidati più “testualmente vicini”, poi ricalcoli con Levenshtein/RapidFuzz.

Esempio FTS (indice e query candidati):

```sql
INSTALL fts; LOAD fts;
PRAGMA create_fts_index('ref_stg', 'city_code', 'ref_city', lower=1, strip_accents=0, stopwords='none');

-- top 20 comuni simili a "palermo" (per candidati rapidi)
SELECT ref_city, city_code, score
FROM (
  SELECT r.*, fts_ref_stg.match_bm25(city_code, 'palermo') AS score
  FROM ref_stg r
) s
WHERE score IS NOT NULL
ORDER BY score DESC
LIMIT 20;
```

---

## Indexing in DuckDB (integrazione)

- **Zonemap automatiche**: DuckDB salta data‑chunks se il filtro non può soddisfarsi (min/max). Ordinare/clusterizzare aumenta il pruning.
- **Indici ART**: per lookup selettivi su tabelle DuckDB.
  ```sql
  CREATE INDEX IF NOT EXISTS idx_ref_block ON ref_stg(block_key);
  CREATE INDEX IF NOT EXISTS idx_inp_block ON input_stg(block_key);
  ```
- **Full‑Text Search (FTS)**: ottimo come candidate generator sui nomi.
- **Parquet pruning**: filtri e proiezioni spinti nel reader; con partizioni e statistiche si legge molto meno.
- **Partizionamento “Hive‑style”**: scrivi i reference partizionati per `block_key` e sfrutta il partition pruning.
  ```sql
  COPY ref_stg TO 'ref_part/' (FORMAT PARQUET, PARTITION_BY (block_key));
  -- poi
  SELECT * FROM 'ref_part' WHERE block_key = 'pal|sic';
  ```

> Nota Bloom filter: se i file Parquet includono Bloom filter (dipende da come sono stati scritti), il pruning può migliorare ulteriormente su colonne con alta cardinalità non ordinata.

---

## RapidFuzz (opzionale, spesso più veloce/tollerante)

```sql
INSTALL rapidfuzz FROM community; LOAD rapidfuzz;
SELECT rapidfuzz_ratio(i.city_n, r.ref_city_n) AS sim
FROM input_stg i JOIN ref_stg r USING (block_key);
```

Usalo al posto o insieme a Levenshtein: spesso riduce falsi negativi su nomi con parole invertite/spazi extra.

---

## Pipeline end‑to‑end (compatta)

```sql
-- 1) staging + blocking
CREATE OR REPLACE TABLE input_stg AS
SELECT city, region,
       replace(replace(replace(replace(replace(lower(city), 'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS city_n,
       replace(replace(replace(replace(replace(lower(region),'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS region_n,
       substr(lower(city),1,3) || '|' || substr(lower(region),1,3) AS block_key
FROM read_csv_auto('input.csv');

CREATE OR REPLACE TABLE ref_stg AS
SELECT city_code,
       city   AS ref_city,
       region AS ref_region,
       replace(replace(replace(replace(replace(lower(city), 'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS ref_city_n,
       replace(replace(replace(replace(replace(lower(region),'à','a'),'è','e'),'é','e'),'ì','i'),'ò','o') AS ref_region_n,
       substr(lower(city),1,3) || '|' || substr(lower(region),1,3) AS block_key
FROM read_csv_auto('ref_sample.csv');

-- 2) (opzionale) indici
CREATE INDEX IF NOT EXISTS idx_ref_block ON ref_stg(block_key);

-- 3) matching nel blocco + best match
WITH cand AS (
  SELECT i.city, i.region, r.ref_city, r.ref_region, r.city_code,
         levenshtein(i.city_n, r.ref_city_n)     AS d_city,
         levenshtein(i.region_n, r.ref_region_n) AS d_reg
  FROM input_stg i
  JOIN ref_stg r USING (block_key)
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY city, region ORDER BY (d_city + d_reg)
  ) rn
)
SELECT * FROM ranked
WHERE rn = 1 AND d_city <= 2 AND d_reg <= 1;
```

---

## Tuning & qualità

- **Soglie**: tarale su un campione etichettato (precision/recall). Salva gli “incerti” per revisione manuale.
- **Metriche alternative**: `rapidfuzz_ratio`, `token_sort_ratio`, `damerau_levenshtein` per gestire trasposizioni e parole invertite.
- ``: misura dove spendi tempo/I‑O; valuta partizionamento diverso (es. per provincia o prefisso CAP).
- **Log degli errori tipici**: crea regole ad hoc ("S. → San ", rimozione di parentesi, trattini, apostrofi) in pre‑processing.

---

## Checklist rapida

-

---

## Fonti e link utili

- DuckDB – Create Index: [https://duckdb.org/docs/sql/statements/create\_index](https://duckdb.org/docs/sql/statements/create_index)
- DuckDB – Full‑Text Search: [https://duckdb.org/docs/extensions/full\_text\_search/overview](https://duckdb.org/docs/extensions/full_text_search/overview)
- DuckDB – Parquet & predicate pushdown: [https://duckdb.org/docs/data/parquet/overview](https://duckdb.org/docs/data/parquet/overview)
- DuckDB – Performance tips: [https://duckdb.org/docs/guides/performance/overview](https://duckdb.org/docs/guides/performance/overview)
- RapidFuzz (estensione community per DuckDB): [https://github.com/QueryStringDotOrg/duckdb-rapidfuzz](https://github.com/QueryStringDotOrg/duckdb-rapidfuzz)
- Parquet partitioning (Hive‑style): [https://duckdb.org/docs/data/parquet/writing#partitioned-writes](https://duckdb.org/docs/data/parquet/writing#partitioned-writes)

---

## Livello di confidenza

- Concetti di **blocking/indexing** e pipeline proposta: **alto**.
- Esempi SQL e uso `CREATE INDEX`/FTS/Parquet pruning: **alto** (comportamento atteso in DuckDB recente).
- Funzioni di “unaccent” non standard: **medio** (per questo è mostrata una mappatura `replace()` portabile).
- Supporto Bloom filter su Parquet: **medio** (dipende da come sono stati scritti i file e dalla versione/toolchain).

---

### Prossimi passi

- Misura su un campione reale (200–1.000 righe): scegli **soglie** e definisci la **fascia di revisione**.
- Valuta una seconda **blocking\_key** (es. prefisso CAP o provincia) per aumentare il recall senza esplodere i confronti.
- Se i reference sono grandi, **partiziona** per `block_key` o provincia e conserva in Parquet.

