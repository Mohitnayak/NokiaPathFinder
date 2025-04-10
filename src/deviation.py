from datetime import datetime
import pandas as pd

from screenNavUtils import mapScreenNavValueToArgs
from utils import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range


def get_on_track_logs(
    db_path: str,
    location_column: str,
    time_range: tuple[datetime, datetime],
    is_on_track: bool,
):
    raw_data = filter_logs_by_time_range(
        fetch_logs(db_path, ["is-on-track"]), time_range
    )

    start_value = "true" if is_on_track else "false"
    end_value = "false" if is_on_track else "true"

    intervals = []
    start_time = None
    for _, row in raw_data.iterrows():
        if row["value"] == start_value:
            start_time = row["timestamp"]
        elif row["value"] == end_value:
            if start_time is not None:
                intervals.append((start_time, row["timestamp"]))
            elif len(intervals) == 0:
                intervals.append((None, row["timestamp"]))
            else:
                intervals[-1] = (intervals[-1][0], row["timestamp"])
            start_time = None
    if start_time is not None:
        intervals.append((start_time, None))

    return filter_location_data_by_intervals(
        filter_logs_by_time_range(
            convert_location_logs_to_df(db_path, location_column), time_range
        ),
        intervals,
    )


def filter_location_data_by_intervals(
    location_data: pd.DataFrame,
    intervals: list[tuple[datetime, datetime]],
) -> list[pd.DataFrame]:
    location_data["timestamp"] = pd.to_datetime(location_data["timestamp"])

    segments = []
    for start, end in intervals:
        if start is None and end is None:
            continue
        elif start is None:
            data = location_data[location_data["timestamp"] <= end]
        elif end is None:
            data = location_data[location_data["timestamp"] >= start]
        else:
            data = location_data[
                (location_data["timestamp"] >= start)
                & (location_data["timestamp"] <= end)
            ]
        segments.append(data)

    return segments
