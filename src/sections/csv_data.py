import streamlit as st
from datetime import datetime
import json

import pandas as pd

from utils.base_path import fetch_base_path_for_time_range
from utils.geo import compute_average_speed_m_s, compute_movement_time_s
from utils.logs import convert_location_logs_to_df, fetch_logs, filter_logs_by_time_range


def csv_data(db_path: str, selected_screen_timestamps: tuple[datetime, datetime]):
    st.subheader("CSV data")

    csvLog = get_csv_logs_for_time_range(db_path, selected_screen_timestamps)

    df = csvLog.to_dataframe()

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    name_suffix = "haptic" if csvLog.is_haptic else "visual"
    st.download_button("Download as CSV", csv, f"log_{name_suffix}.csv", "text/csv")


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
    # If extended range includes multiple runs, use the one at run start (earliest in range)
    navigation_df = navigation_df.sort_values("timestamp").reset_index(drop=True)
    nav_row = navigation_df.iloc[0]
    is_haptic = json.loads(nav_row["value"])["withHaptic"]
    # location logs in format: dataframe with columns: timestamp, latitude, longitude
    location_logs_df = filter_logs_by_time_range(
        convert_location_logs_to_df(db_path, "location"), time_range
    )
    base_path = fetch_base_path_for_time_range(db_path, time_range)
    distance_from_track_df = filter_logs_by_time_range(
        fetch_logs(db_path, ["distance-from-track"]), time_range
    )
    distance_from_track_df["value"] = pd.to_numeric(
        distance_from_track_df["value"], errors="coerce"
    )
    csvLog = CSVLog()
    csvLog.deviation_zone_radius = base_path.deviation_zone_radius
    # Task completion time = time moving (plausible segments only), same as summary "Completion time"
    if len(location_logs_df) > 1:
        csvLog.task_completion_time_s = round(
            compute_movement_time_s(location_logs_df), 1
        )
        csvLog.average_speed_m_s = round(
            compute_average_speed_m_s(location_logs_df), 2
        )
    else:
        csvLog.task_completion_time_s = 0.0
        csvLog.average_speed_m_s = 0.0
    avg_dist = distance_from_track_df["value"].mean()
    csvLog.average_distance_from_route_m = (
        round(avg_dist, 2) if pd.notna(avg_dist) else 0.0
    )
    csvLog.is_haptic = is_haptic

    return csvLog
    
