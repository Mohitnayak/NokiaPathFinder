from datetime import datetime
import pandas as pd

from geo_utils import calculate_distance
from utils import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range


def get_time_on_track(
    db_path: str,
    time_range: tuple[datetime, datetime],
    is_on_track: bool = True,
):
    intervals = get_on_track_intervals(
        db_path, time_range=time_range, is_on_track=is_on_track
    )
    for i, interval in enumerate(intervals):
        if interval[0] is not None and interval[1] is not None:
            continue
        start = interval[0]
        end = interval[1]
        if start is None:
            start = time_range[0]
        if end is None:
            end = time_range[1]
        intervals[i] = (start, end)

    return sum((interval[1] - interval[0]).total_seconds() for interval in intervals)


def get_on_track_distance(
    db_path: str,
    location_column: str,
    time_range: tuple[datetime, datetime],
    is_on_track: bool = True,
):
    on_track_logs = get_on_track_logs(
        db_path,
        location_column=location_column,
        is_on_track=is_on_track,
        time_range=time_range,
    )
    return sum(map(calculate_distance, on_track_logs))


def get_on_track_logs(
    db_path: str,
    location_column: str,
    time_range: tuple[datetime, datetime],
    is_on_track: bool,
) -> list[pd.DataFrame]:
    intervals = get_on_track_intervals(db_path, time_range, is_on_track)

    return filter_location_data_by_intervals(
        filter_logs_by_time_range(
            convert_location_logs_to_df(db_path, location_column), time_range
        ),
        intervals,
    )


def get_on_track_intervals(
    db_path: str,
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
    return intervals


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
        if len(data) > 0:
            segments.append(data)

    return segments
