## 2025-08-18

- Creata la versione Python dello script di fuzzy join (`src/fuzzy_join.py`).
- Aggiornati README e PRD con dettagli su installazione e utilizzo della CLI.
- Aggiunto script `tometo_tomato` per join fuzzy tra file CSV.
- Implementato il processo di fuzzy join con selezione dinamica delle colonne e gestione dell'output.
- Refactoring della CLI con `bashly`.
- Aggiornato lo script per l'esempio dei dati ISTAT/non ufficiali.
- Aggiornato il PRD con l'esempio dei dati ISTAT/non ufficiali.
- Creato lo script iniziale per il fuzzy join.
- Creato `GEMINI.md` per il contesto del progetto.
- Aggiunto il Product Requirements Document per il fuzzy join.
- Refactoring completo della logica dello script Bash:
	- Confronto fuzzy sempre case-insensitive (LOWER).
	- LEFT JOIN: tutti i record di input sono sempre presenti nell'output.
	- Parametri di output pulito e ambiguo gestiti come richiesto.
	- Output ambiguo generato solo se richiesto, con messaggi chiari in shell.
	- Se non ci sono record ambigui, il file viene cancellato e la shell avvisa.
	- Aggiornato README con la logica attuale, parametri e comportamento.
	- Testata la CLI con vari scenari di output e ambiguità.

## 2025-08-19

- Resolved Issue #7: Changed default output logic.
- Resolved Issue #8: Verified handling of field names with spaces.
- Resolved Issue #9: Implemented generation of ambiguous matches file only when explicitly requested.
- Resolved Issue #10: Translated all stdout messages to English.
- Migrated the fuzzy join script from bash to Python CLI.
- Improved output logic for clean and ambiguous matches.
- Configured package installation with `setup.py` and `pyproject.toml`.
- Added test files for field names with spaces.
- Updated `.gitignore` to exclude build artifacts and processed/interim data.