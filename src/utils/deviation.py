from datetime import datetime
import pandas as pd

from utils.geo import calculate_distance
from utils.logs import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range


def _clip_interval_to_range(
    start: datetime | None,
    end: datetime | None,
    time_range: tuple[datetime, datetime],
) -> tuple[datetime, datetime]:
    """Clip (start, end) to [time_range[0], time_range[1]] so sum of on/off never exceeds session window."""
    lo, hi = time_range[0], time_range[1]
    s = start if start is not None else lo
    e = end if end is not None else hi
    clip_start = max(s, lo)
    clip_end = min(e, hi)
    return (clip_start, clip_end)


def get_time_on_track(
    db_path: str,
    time_range: tuple[datetime, datetime],
    is_on_track: bool = True,
):
    intervals = get_on_track_intervals(
        db_path, time_range=time_range, is_on_track=is_on_track
    )
    total_s = 0.0
    for start, end in intervals:
        if start is None:
            start = time_range[0]
        if end is None:
            end = time_range[1]
        clip_start, clip_end = _clip_interval_to_range(start, end, time_range)
        total_s += max(0.0, (clip_end - clip_start).total_seconds())
    return total_s


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

    return group_location_data_by_intervals(
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


def group_location_data_by_intervals(
    location_data: pd.DataFrame,
    intervals: list[tuple[datetime, datetime]],
) -> list[pd.DataFrame]:
    """
    Utility that groups location data by intervals.
    """
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
