import sqlite3
import pandas as pd


def fetch_logs(db_path: str, types: list[str]):
    # Connect to the SQLite database
    print(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to select logs of type 'navigation'
    placeholders = ",".join("?" * len(types))  # Creates placeholders like ?,?,?
    query = f"SELECT timestamp, type, value FROM logs WHERE type IN ({placeholders})"
    print(f"Executing query: {query} with types: {types}")
    cursor.execute(query, types)

    data = []

    print("Fetching and processing logs...")
    for row in cursor.fetchall():
        timestamp, type, value = row
        data.append((timestamp, type, value))

    # Close connection
    conn.close()

    print(f"Fetched {len(data)} valid navigation logs.")
    # Create DataFrame
    df = pd.DataFrame(data, columns=["timestamp", "type", "value"])
    return df
