from datetime import datetime
import json

import pandas as pd

from basePath import get_base_path_for_time_range
from geo_utils import compute_average_speed_m_s
from utils import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range
import streamlit as st


class CSVLog:
    is_haptic = False
    average_speed_m_s = 0
    average_distance_from_route_m = 0
    task_completion_time_s = 0
    deviation_zone_radius = 0

    def to_dataframe(self) -> pd.DataFrame:
        column_suffix = " haptic" if self.is_haptic else " visual"
        data = {
            f"Average Speed (m/s){column_suffix}": [self.average_speed_m_s],
            f"Avg Distance from Route (m){column_suffix}": [
                self.average_distance_from_route_m
            ],
            f"Task Completion Time (s){column_suffix}": [self.task_completion_time_s],
            # "Deviation Zone Radius": [self.deviation_zone_radius],
        }
        return pd.DataFrame(data)


def get_csv_logs_for_time_range(
    db_path: str, time_range: tuple[datetime, datetime]
) -> CSVLog:
    # dataframe with columns: timestamp, value: json {type, withHaptic}
    navigation_df = filter_logs_by_time_range(
        fetch_logs(db_path, ["navigation-started"]), time_range
    )
    if navigation_df.empty:
        raise ValueError(
            "No navigation logs found for the selected time range. This is most likely a bug in logs."
        )
    if navigation_df.shape[0] > 1:
        raise ValueError(
            "More than one navigation log found for the selected time range. This is most likely a bug in logs."
        )
    is_haptic = json.loads(navigation_df["value"].iloc[0])["withHaptic"]
    # location logs in format: dataframe with columns: timestamp, latitude, longitude
    location_logs_df = filter_logs_by_time_range(
        convert_location_logs_to_df(db_path, "location"), time_range
    )
    base_path = get_base_path_for_time_range(db_path, time_range)
    distance_from_track_df = filter_logs_by_time_range(
        fetch_logs(db_path, ["distance-from-track"]), time_range
    )
    distance_from_track_df["value"] = pd.to_numeric(
        distance_from_track_df["value"], errors="coerce"
    )
    csvLog = CSVLog()
    csvLog.deviation_zone_radius = base_path.deviation_zone_radius
    csvLog.task_completion_time_s = (time_range[1] - time_range[0]).total_seconds()
    csvLog.average_speed_m_s = compute_average_speed_m_s(location_logs_df)
    csvLog.average_distance_from_route_m = distance_from_track_df["value"].mean()
    csvLog.is_haptic = is_haptic

    return csvLog


def display_csv_log(csv_log: CSVLog):
    df = csv_log.to_dataframe()

    st.dataframe(df, use_container_width=True)


def display_download_csv_button(csv_log: CSVLog):
    df = csv_log.to_dataframe()
    csv = df.to_csv(index=False).encode("utf-8")
    name_suffix = "haptic" if csv_log.is_haptic else "visual"
    st.download_button("Download as CSV", csv, f"log_{name_suffix}.csv", "text/csv")
