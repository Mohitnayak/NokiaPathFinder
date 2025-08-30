import streamlit as st

from sections.compass import compass_section
from sections.csv_data import csv_data
from sections.database_selection import select_database
from sections.screen_selection import screen_selector
from utils import (
    convert_location_logs_to_df,
    filter_logs_by_time_range,
)


db_path = select_database()
selected_screen_timestamps = screen_selector(db_path=db_path)

all_location_logs = filter_logs_by_time_range(
    convert_location_logs_to_df(db_path, "raw-location"),
    selected_screen_timestamps,
)

if all_location_logs.empty:
    st.write("No location logs found for the selected screen.")
    st.stop()

csv_data(db_path=db_path, selected_screen_timestamps=selected_screen_timestamps)

compass_section(db_path=db_path, all_location_logs=all_location_logs)
