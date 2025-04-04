from gpx import convert_location_logs_to_gpx, gpx_to_geojson
from utils import convert_location_logs_to_df, fetch_logs
from geojson import (
    convert_to_geojson_line,
    combine_geojson_features,
    convert_to_geojson_points,
    stringify_geojson,
    visualize_geojson_io,
)
import pandas as pd
import json


def convert_is_on_track_logs_to_df(db_path: str) -> pd.DataFrame:
    df = fetch_logs(db_path, ["location", "is-on-track"])
    result_df = pd.DataFrame(
        columns=["timestamp", "type", "latitude", "longitude", "is-on-track"]
    )
    last_location = None

    # Iterate through the DataFrame
    for _, row in df.iterrows():
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


convert_location_logs_to_gpx("log_database-a.db", "location", "out/output.gpx")
convert_location_logs_to_gpx(
    "log_database-a.db", "snapped-location", "out/snapped-output.gpx"
)

path1 = gpx_to_geojson("pynykin-1-dev.gpx", color="green")
path2 = gpx_to_geojson("pynykin-2-dev.gpx", color="black")

locations = convert_to_geojson_line(
    convert_location_logs_to_df("log_database-a.db", "location")
)
snappedLocations = convert_to_geojson_line(
    convert_location_logs_to_df("log_database-a.db", "snapped-location"), color="orange"
)
isOnTrack = convert_to_geojson_points(
    convert_is_on_track_logs_to_df("log_database-a.db"),
    color=lambda row: "green" if row["is-on-track"] else "red",
    info_columns=["is-on-track"],
)
visualize_geojson_io(
    stringify_geojson(
        combine_geojson_features(
            path1, path2, [locations], [snappedLocations], isOnTrack
        )
    )
)
