"""
Export each SQLite database in all_participants_db to a CSV file in all_participant_csv.
Same columns and data: id, timestamp, type, value.
"""
import os
import sqlite3
import pandas as pd

DB_DIR = "all_participants_db"
CSV_DIR = "all_participant_csv"

os.makedirs(CSV_DIR, exist_ok=True)

db_files = [f for f in os.listdir(DB_DIR) if f.endswith(".db")]
for db_name in sorted(db_files):
    db_path = os.path.join(DB_DIR, db_name)
    csv_name = db_name.replace(".db", ".csv")
    csv_path = os.path.join(CSV_DIR, csv_name)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT id, timestamp, type, value FROM logs ORDER BY id", conn)
    conn.close()
    df.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Exported {db_name} -> {csv_name} ({len(df)} rows)")

print(f"\nDone. {len(db_files)} CSV files in {CSV_DIR}/")
