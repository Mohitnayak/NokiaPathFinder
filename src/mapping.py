from utils import fetch_logs
from geojson import (
    convert_to_geojson_line,
    combine_geojson_features,
    convert_to_geojson_points,
    stringify_geojson,
    visualize_geojson_io,
)
import gpxpy
import gpxpy.gpx
import pandas as pd
import json


def convert_is_on_track_logs_to_df(db_path: str) -> pd.DataFrame:
    df = fetch_logs(db_path, ["location", "is-on-track"])
    result_df = pd.DataFrame(
        columns=["timestamp", "type", "latitude", "longitude", "is-on-track"]
    )
    last_location = None

    # Iterate through the DataFrame
    for index, row in df.iterrows():
        if row["type"] == "location":
            # Update last known location
            last_location = json.loads(row["value"])
        elif row["type"] == "is-on-track" and last_location is not None:
            new_row = {
                "timestamp": row["timestamp"],
                "type": "is-on-track",
                "latitude": last_location["latitude"],
                "longitude": last_location["longitude"],
                "is-on-track": True if row["value"] == "true" else False,
            }
            result_df = pd.concat(
                [result_df, pd.DataFrame([new_row])], ignore_index=True
            )

    return result_df


def convert_location_logs_to_df(db_path: str, column: str) -> pd.DataFrame:
    df = fetch_logs(db_path, [column])

    df["latitude"] = (
        df["value"].str.extract(r"\"latitude\":\s*([\d\.\-]+)").astype(float)
    )
    df["longitude"] = (
        df["value"].str.extract(r"\"longitude\":\s*([\d\.\-]+)").astype(float)
    )

    return df


# convert_location_logs_to_gpx("log_database-1.db", "location", "output.gpx")
# convert_location_logs_to_gpx("log_database-1.db", "snapped-location", "snapped-output.gpx")

geojson = convert_to_geojson_line(
    convert_location_logs_to_df("log_database-1.db", "location")
)
isOnTrack = convert_to_geojson_points(
    convert_is_on_track_logs_to_df("log_database-1.db"),
    color=lambda row: "green" if row["is-on-track"] else "red",
    info_columns=["is-on-track"],
)
visualize_geojson_io(stringify_geojson(combine_geojson_features([geojson], isOnTrack)))
