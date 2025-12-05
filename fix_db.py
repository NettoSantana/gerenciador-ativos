# fix_db.py
import sqlite3
import os

DB_PATH = os.path.join("instance", "gerenciador_ativos.db")

def main():
    print(f"Conectando ao banco: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE ativos ADD COLUMN horas_offset REAL DEFAULT 0;")
        conn.commit()
        print(">>> Coluna horas_offset criada com sucesso!")
    except Exception as e:
        print(">>> Erro ao criar coluna:", e)

    conn.close()

if __name__ == "__main__":
    main()
