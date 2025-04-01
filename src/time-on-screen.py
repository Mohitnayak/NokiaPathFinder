import pandas as pd
import json

from utils import fetch_logs


def fetch_navigation_logs(db_path):
    raw_data = fetch_logs(db_path, ["navigation"])
    print("Fetching and processing logs...")

    df = raw_data.apply(process_row, axis=1)
    df.columns = ["timestamp", "route", "pathUri", "withHaptic"]
    return df


def process_row(row):
    try:
        json_data = json.loads(row["value"])  # Parse JSON
        route = json_data.get("route")
        args_raw = json_data.get("args")
        args = json.loads(args_raw) if args_raw else None
        pathUri = None
        withHaptic = None
        if args and isinstance(args, dict):
            mMap = args.get("mMap")
            if mMap:
                pathUri = mMap.get("pathUri")
                withHaptic = mMap.get("withHaptic")
        return pd.Series([row["timestamp"], route, pathUri, withHaptic])
    except (json.JSONDecodeError, TypeError):
        return pd.Series([row["timestamp"], None, None, None])


def calculate_time_on_screen(df_old):
    df = df_old.copy()
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    # Sort by timestamp
    df = df.sort_values(by="timestamp")
    # Calculate time differences
    df["time_on_screen"] = df["timestamp"].diff().dt.total_seconds().fillna(0)
    return df


# Example usage
db_path = "log_database.db"  # Update with your actual database path
df = fetch_navigation_logs(db_path)
df = calculate_time_on_screen(df)
time_on_screen = df.groupby(["route"])["time_on_screen"].sum().reset_index()
print(df)

print(time_on_screen)
