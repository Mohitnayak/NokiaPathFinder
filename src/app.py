import os
import streamlit as st
from datetime import timedelta, datetime
import pandas as pd

from components.display_location_logs import display_location_logs
from components.select_file import select_file
from components.time_slider import time_slider
from utils import convert_location_logs_to_df, filter_logs_by_time_range
from screen import fetch_navigation_logs


def screen_selector(df: pd.DataFrame) -> tuple[datetime, datetime]:
    haptic_visual_map = {
        True: "Haptic",
        1: "Haptic",
        2: "Haptic",
        False: "Visual",
        None: "",
    }

    navigation_screens = df[
        df["route"].str.contains("{withHaptic}") & df["route"].str.contains("{pathUri}")
    ]

    def format_row(row):
        # route = (
        #     row["route"]
        #     .replace("com.example.path_fainder.screens.", "")
        #     .replace("/{pathUri}", "")
        #     .replace("/{withHaptic}", "")
        # )
        path = os.path.basename(row["pathUri"]) if row["pathUri"] else ""
        haptic = haptic_visual_map.get(row["withHaptic"], "")
        return f"{row['timestamp'].strftime('%y-%m-%d %H:%M:%S')} {path} {haptic}"

    formatted_rows = navigation_screens.apply(
        format_row,
        axis=1,
    )

    # Allow the user to select a row
    selected_row = st.selectbox("Select a screen:", formatted_rows)

    # Find the index of the selected row in the DataFrame
    selected_index = formatted_rows[formatted_rows == selected_row].index[0]

    # Get the start and end timestamps for the selected row
    start_timestamp = navigation_screens.loc[selected_index, "timestamp"]
    end_timestamp = navigation_screens.loc[selected_index, "next_screen_timestamp"]

    if end_timestamp is pd.NaT:
        end_timestamp = start_timestamp + timedelta(hours=12)

    return start_timestamp, end_timestamp


def combine_coords(*dfs):
    colors = [
        "#ff0000",
        "#00ff00",
        "#0000ff",
        "#ffff00",
        "#ffa500",
        "#800080",
        "#ffc0cb",
        "#a52a2a",
        "#000000",
    ]
    # Create an empty list to store DataFrames with a color column
    combined_data = []

    # Iterate through each DataFrame
    for idx, df in enumerate(dfs):
        # Add a unique color to each DataFrame (based on the index)
        # You can change the colors here as per your choice
        color = colors[idx % len(colors)]

        # Add the color as a new column to the DataFrame
        df["color"] = color

        # Append the modified DataFrame to the combined data list
        combined_data.append(df)

    # Concatenate all DataFrames in the list into one DataFrame
    combined_df = pd.concat(combined_data, ignore_index=True)

    # Return the combined DataFrame
    return combined_df


st.subheader("Database with logs")
st.write("This is the database exported from the application")
# db_path = "log_database-2.db"
db_path = "temp/db.db"
if not os.path.exists("temp"):
    os.makedirs("temp")

file = select_file("Select database file", db_path, type="db")

if not file:
    st.stop()

st.subheader("Screen selection")
st.write(
    "Select the screen you want to analyze. Pay attention to the track gpx and navigation mode"
)

navigation_logs = fetch_navigation_logs(db_path=db_path)

selected_navigation_time = time_slider(
    navigation_logs, id="navigation_time_slider", with_time=False
)

selected_screen_timestamps = screen_selector(
    filter_logs_by_time_range(navigation_logs, selected_navigation_time)
)

st.subheader("Location logs")

st.write(
    "With this slider you can analyze only a part of selected route. By default it is the whole route."
)
location_logs = filter_logs_by_time_range(
    convert_location_logs_to_df(db_path, "location"),
    selected_screen_timestamps,
)
if location_logs.empty:
    st.write("No location logs found for the selected screen.")
else:
    display_location_logs(location_logs=location_logs, db_path=db_path)
