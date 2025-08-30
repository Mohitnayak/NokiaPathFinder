import sqlite3
import pandas as pd
from datetime import datetime


def fetch_logs(db_path: str, types: list[str]):
    """
    Fetches logs of specified types from a SQLite database and returns a normalized DataFrame.

    Args:
        db_path (str): Path to the SQLite database file.
        types (list[str]): List of log types to fetch from the database.

    Returns:
        pandas.DataFrame: A normalized DataFrame containing the fetched logs with columns ["timestamp", "type", "value"].

    Notes:
        - Assumes the existence of a 'logs' table with columns 'timestamp', 'type', and 'value'.
        - Relies on a 'normalize_logs' function to process the resulting DataFrame.
    """
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


def normalize_logs(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Converts timestamp columns in the given DataFrame from milliseconds to datetime.

    Parameters:
        dataframe (pd.DataFrame): The input DataFrame containing a 'timestamp' column and optionally a 'next_screen_timestamp' column, both in milliseconds.

    Returns:
        pd.DataFrame: The DataFrame with 'timestamp' (and 'next_screen_timestamp', if present) converted to pandas datetime objects.
    """
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], unit="ms")
    if "next_screen_timestamp" in dataframe.columns:
        dataframe["next_screen_timestamp"] = pd.to_datetime(
            dataframe["next_screen_timestamp"], unit="ms"
        )
    return dataframe


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
