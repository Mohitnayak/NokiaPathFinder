import streamlit as st

from sections.compass import compass_section
from sections.csv_data import csv_data
from sections.database_selection import select_database_section
from sections.location import location_section
from sections.screen_selection import screen_selection_section
from utils.logs import (
    convert_location_logs_to_df,
    filter_logs_by_time_range,
)


def get_location_logs_for_screen(db_path: str, time_range):
    """Use raw-location for the screen; if none in range, use fused location (e.g. 12:43 run)."""
    raw = filter_logs_by_time_range(
        convert_location_logs_to_df(db_path, "raw-location"),
        time_range,
    )
    if not raw.empty:
        return raw
    fused = filter_logs_by_time_range(
        convert_location_logs_to_df(db_path, "location"),
        time_range,
    )
    return fused


db_path = select_database_section()
selected_screen_timestamps = screen_selection_section(db_path=db_path)

all_location_logs = get_location_logs_for_screen(db_path, selected_screen_timestamps)

if all_location_logs.empty:
    st.write("No location logs found for the selected screen.")
    st.stop()

csv_data(db_path=db_path, selected_screen_timestamps=selected_screen_timestamps)

location_section(
    db_path=db_path,
    selected_screen_timestamps=selected_screen_timestamps,
    location_logs=all_location_logs,
)

compass_section(db_path=db_path, all_location_logs=all_location_logs)
