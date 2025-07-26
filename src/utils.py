import sqlite3
import pandas as pd
from datetime import datetime
import json


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


def fetch_orientation_logs(db_path: str, column: str):
    df = fetch_logs(db_path, [column])
    # convert value to number
    df["value"] = df["value"].astype(float)
    # combine logs from one second and average it
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["timestamp"] = df["timestamp"].dt.floor("1S")

    result = df.groupby(df["timestamp"])["value"].first().reset_index()
    return result


def convert_location_logs_to_df(db_path: str, column: str) -> pd.DataFrame:
    df = fetch_logs(db_path, [column])

    df["latitude"] = (
        df["value"].str.extract(r"\"latitude\":\s*([\d\.\-]+)").astype(float)
    )
    df["longitude"] = (
        df["value"].str.extract(r"\"longitude\":\s*([\d\.\-]+)").astype(float)
    )

    return df


def convert_segment_log_to_df(value: str) -> pd.DataFrame:
    # Assuming value is a JSON string with "latitude" and "longitude" keys
    #     {
    #   "points":
    #     [
    #       { "latitude": 61.454442, "longitude": 23.844628 },
    #       { "latitude": 61.454435, "longitude": 23.844597 },
    #       { "latitude": 61.454345, "longitude": 23.844226 },
    #       { "latitude": 61.454269, "longitude": 23.843925 },
    #       { "latitude": 61.454421, "longitude": 23.843762 },
    #       { "latitude": 61.454605, "longitude": 23.843571 },
    #       { "latitude": 61.454621, "longitude": 23.843555 },
    #       { "latitude": 61.45456662371037, "longitude": 23.843247526770075 },
    #       { "latitude": 61.454566, "longitude": 23.843247 },
    #       { "latitude": 61.454566, "longitude": 23.843244 },
    #       { "latitude": 61.454632, "longitude": 23.843176 },
    #       { "latitude": 61.454448, "longitude": 23.842328 },
    #       { "latitude": 61.454431, "longitude": 23.842293 },
    #       { "latitude": 61.454404, "longitude": 23.842279 },
    #       { "latitude": 61.45438, "longitude": 23.842214 },
    #       { "latitude": 61.454297, "longitude": 23.841847 },
    #       { "latitude": 61.454239, "longitude": 23.841773 },
    #       { "latitude": 61.454164, "longitude": 23.841819 },
    #       { "latitude": 61.453939, "longitude": 23.842057 },
    #     ],
    # }
    try:
        data = json.loads(value)
        points = data.get("points", [])
        if not points:
            print("No points found in the segment log.")
            return pd.DataFrame()
        df = pd.DataFrame(points)
        df["latitude"] = df["latitude"].astype(float)
        df["longitude"] = df["longitude"].astype(float)
        return df
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {value}")
        return pd.DataFrame()


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
