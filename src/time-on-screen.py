import sqlite3
import pandas as pd
import json


def fetch_navigation_logs(db_path):
    # Connect to the SQLite database
    print(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to select logs of type 'navigation'
    query = "SELECT timestamp, value FROM logs WHERE type = 'navigation'"
    print(f"Executing query: {query}")
    cursor.execute(query)

    data = []

    print("Fetching and processing logs...")
    for row in cursor.fetchall():
        timestamp, value = row
        try:
            json_data = json.loads(value)  # Parse JSON
            route = json_data.get("route")  # Extract 'route' key if exists
            args_raw = json_data.get("args")
            args = json.loads(args_raw)
            pathUri = None
            withHaptic = None
            if args and type(args) == dict:
                mMap = args.get("mMap")
                if mMap:
                    pathUri = mMap.get("pathUri")
                    withHaptic = mMap.get("withHaptic")

            data.append((timestamp, route, pathUri, withHaptic))
        except json.JSONDecodeError:
            continue  # Skip invalid JSON

    # Close connection
    conn.close()

    print(f"Fetched {len(data)} valid navigation logs.")
    # Create DataFrame
    df = pd.DataFrame(data, columns=["timestamp", "route", "pathUri", "withHaptic"])
    return df


# Example usage
db_path = "log_database.db"  # Update with your actual database path
df = fetch_navigation_logs(db_path)
print(df)
