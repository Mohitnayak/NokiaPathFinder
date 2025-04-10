import sqlite3
import pandas as pd
from datetime import datetime


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
    return normalize_logs(df)


def convert_location_logs_to_df(db_path: str, column: str) -> pd.DataFrame:
    df = fetch_logs(db_path, [column])

    df["latitude"] = (
        df["value"].str.extract(r"\"latitude\":\s*([\d\.\-]+)").astype(float)
    )
    df["longitude"] = (
        df["value"].str.extract(r"\"longitude\":\s*([\d\.\-]+)").astype(float)
    )

    return df


def filter_logs_by_time_range(
    dataframe: pd.DataFrame, time_range: tuple[datetime, datetime]
) -> pd.DataFrame:
    return dataframe[
        (dataframe["timestamp"] >= time_range[0])
        & (dataframe["timestamp"] <= time_range[1])
    ]


def normalize_logs(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], unit="ms")
    if "next_screen_timestamp" in dataframe.columns:
        dataframe["next_screen_timestamp"] = pd.to_datetime(
            dataframe["next_screen_timestamp"], unit="ms"
        )
    return dataframe
