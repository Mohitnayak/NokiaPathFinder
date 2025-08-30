from datetime import datetime
import pandas as pd

from utils.deviation import filter_location_data_by_intervals
from utils.logs import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range


def get_vibration_logs(
    db_path: str, location_column: str, time_range: tuple[datetime, datetime], side: str
) -> list[pd.DataFrame]:
    intervals = get_vibration_intervals(db_path, time_range, side)

    return filter_location_data_by_intervals(
        filter_logs_by_time_range(
            convert_location_logs_to_df(db_path, location_column), time_range
        ),
        intervals,
    )


def get_vibration_intervals(
    db_path: str,
    time_range: tuple[datetime, datetime],
    side: str,  # Left or Right or Both or None
):
    if side != "Both" and side != "Left" and side != "Right" and side != "None":
        raise ValueError("Invalid side value {side}")

    raw_data = filter_logs_by_time_range(
        fetch_logs(db_path, ["vibrator_start", "vibrator_stop"]), time_range
    )
    raw_data = replace_vibrator_stop_with_none(raw_data)

    intervals = []
    start_time = None
    for _, row in raw_data.iterrows():
        if row["value"] == side and start_time is None:
            start_time = row["timestamp"]
        else:
            if start_time is not None:
                intervals.append((start_time, row["timestamp"]))
            elif side == "None":
                intervals.append((None, row["timestamp"]))
            start_time = None
    if start_time is not None:
        intervals.append((start_time, None))

    return intervals


def replace_vibrator_stop_with_none(
    raw_data: pd.DataFrame,
) -> pd.DataFrame:
    mask = raw_data["type"] == "vibrator_stop"
    raw_data.loc[mask, "value"] = "None"
    raw_data.loc[mask, "type"] = "vibrator_start"
    return raw_data
