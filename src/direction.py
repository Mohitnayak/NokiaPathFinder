from utils import fetch_logs
import pandas as pd
import json


def convert_direction_logs_to_df(db_path: str) -> pd.DataFrame:
    df = fetch_logs(db_path, ["location", "bearing", "direction-chest"])
    result_df = pd.DataFrame(
        columns=[
            "timestamp",
            "type",
            "latitude",
            "longitude",
            "bearing",
            "direction-chest",
        ]
    )
    last_location = None
    last_bearing = None

    # Iterate through the DataFrame
    for _, row in df.iterrows():
        if row["type"] == "location":
            # Update last known location
            last_location = json.loads(row["value"])
        elif row["type"] == "bearing":
            # Update last known bearing
            last_bearing = row["value"]
        elif (
            row["type"] == "direction-chest"
            and last_location is not None
            and last_bearing is not None
        ):
            new_row = {
                "timestamp": row["timestamp"],
                "type": "direction-chest",
                "latitude": last_location["latitude"],
                "longitude": last_location["longitude"],
                "bearing": last_bearing,
                "direction-chest": row["value"],
            }
            result_df = pd.concat(
                [result_df, pd.DataFrame([new_row])], ignore_index=True
            )

    return result_df


df = convert_direction_logs_to_df("log_database-a.db")
print(df)
df.to_json("direction.json", orient="records")
