import duckdb
import os

def create_and_read_csv(filename, content): # Rimosso 'delimiter'
    """Crea un file CSV temporaneo e lo legge con DuckDB, stampando lo schema e i dati."""
    print(f"\n--- Test per {filename} ---")
    file_path = os.path.join(os.getcwd(), filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"File '{filename}' creato con successo.")

    try:
        con = duckdb.connect(database=":memory:")
        
        # Query senza specificare il delimitatore
        query = f"SELECT * FROM read_csv_auto('{file_path}', header=true, all_varchar=true)"
        
        print(f"Esecuzione query: {query}")
        
        # Esegui la query e stampa lo schema
        res = con.execute(query)
        
        # Stampa lo schema (nomi e tipi di colonna)
        print("\nSchema rilevato:")
        for col in res.description:
            print(f"- {col[0]} ({col[1]})")
        
        # Stampa i primi 5 record
        print("\nPrimi 5 record:")
        print(res.fetchdf())

    except Exception as e:
        print(f"Errore durante la lettura di '{filename}': {e}")
    finally:
        # Pulisci il file temporaneo
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File '{filename}' rimosso.")

# --- Esempi di utilizzo ---

# 1. CSV con virgola (default)
create_and_read_csv(
    "comma_test.csv",
    "id,name,value\n1,Apple,100\n2,Banana,200\n3,Orange,150"
)

# 2. CSV con punto e virgola (auto-rilevamento)
create_and_read_csv(
    "semicolon_test.csv",
    "id;name;value\n1;Apple;100\n2;Banana;200\n3;Orange;150"
)

# 3. CSV con tab (auto-rilevamento)
create_and_read_csv(
    "tab_test.csv",
    "id\tname\tvalue\n1\tApple\t100\n2\tBanana\t200\n3\tOrange\t150"
)

# 4. CSV con punto e virgola e campi quotati contenenti virgole (auto-rilevamento)
create_and_read_csv(
    "quoted_semicolon_test.csv",
    '"ID";"Product, Name";"Price"\n1;"Apple, Red";1.20\n2;"Banana, Yellow";0.75'
)