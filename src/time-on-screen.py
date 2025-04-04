import pandas as pd

from utils import fetch_logs
from screenNavUtils import mapScreenNavValueToArgs


def fetch_navigation_logs(db_path):
    raw_data = fetch_logs(db_path, ["navigation"])
    print("Fetching and processing logs...")

    df = raw_data.apply(process_row, axis=1)
    df.columns = ["timestamp", "route", "pathUri", "withHaptic"]
    return df


def process_row(row):
    data = mapScreenNavValueToArgs(row["value"])
    return pd.Series(
        [row["timestamp"], data["route"], data["pathUri"], data["withHaptic"]]
    )


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
