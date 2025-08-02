import os
import streamlit as st
from datetime import timedelta, datetime
import pandas as pd

from basePath import get_base_path_for_time_range
from components.display_location_logs import display_location_logs
from components.select_file import select_file
from components.time_slider import time_slider
from csvLogs import (
    display_csv_log,
    display_download_csv_button,
    get_csv_logs_for_time_range,
)
from geo import interpolate_locations
from utils import (
    convert_location_logs_to_df,
    convert_segment_log_to_df,
    fetch_logs,
    fetch_orientation_logs,
    filter_logs_by_time_range,
)
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

all_location_logs = filter_logs_by_time_range(
    convert_location_logs_to_df(db_path, "raw-location"),
    selected_screen_timestamps,
)

st.subheader("CSV data")

csvLog = get_csv_logs_for_time_range(db_path, selected_screen_timestamps)

display_csv_log(csv_log=csvLog)
display_download_csv_button(csv_log=csvLog)


st.subheader("Location logs")

st.write(
    "With this slider you can analyze only a part of selected route. By default it is the whole route."
)
if all_location_logs.empty:
    st.write("No location logs found for the selected screen.")
else:
    base_path = base_path = get_base_path_for_time_range(
        db_path=db_path, time_range=selected_screen_timestamps
    )
    display_location_logs(
        location_logs=all_location_logs, db_path=db_path, base_path=base_path
    )

st.subheader("Compass logs")

orientation_time = time_slider(
    all_location_logs,
    id="navigation_time_slider_test",
    with_time=True,
    range=False,
    label="Select time to display",
)
orientation_time_range = (orientation_time, orientation_time + timedelta(seconds=10))

orientation_logs = filter_logs_by_time_range(
    fetch_orientation_logs(db_path, "orientation-phone"),
    orientation_time_range,
)

direction_logs = filter_logs_by_time_range(
    fetch_orientation_logs(db_path, "direction-phone"),
    orientation_time_range,
)

track_point_logs = filter_logs_by_time_range(
    convert_location_logs_to_df(db_path, "track-point"),
    (
        orientation_time - timedelta(seconds=60),
        orientation_time + timedelta(seconds=60),
    ),
)

if orientation_logs.empty or direction_logs.empty:
    st.write("No orientation logs found")
else:
    exact_direction_time = direction_logs["timestamp"].iloc[0]
    last_orientation_before_time = filter_logs_by_time_range(
        orientation_logs,
        (exact_direction_time - timedelta(seconds=3), exact_direction_time),
    ).tail(1)
    last_location_before_time = filter_logs_by_time_range(
        all_location_logs,
        (exact_direction_time - timedelta(seconds=60), exact_direction_time),
    ).tail(1)
    last_remaining_segment_before_time = convert_segment_log_to_df(
        filter_logs_by_time_range(
            fetch_logs(db_path, ["remaining-segment"]),
            (exact_direction_time - timedelta(seconds=300), exact_direction_time),
        )
        .tail(1)
        .iloc[0]["value"]
    )
    last_current_segment_before_time = convert_segment_log_to_df(
        filter_logs_by_time_range(
            fetch_logs(db_path, ["current-segment"]),
            (exact_direction_time - timedelta(seconds=300), exact_direction_time),
        )
        .tail(1)
        .iloc[0]["value"]
    )
    last_track_point_before_time = filter_logs_by_time_range(
        track_point_logs,
        (exact_direction_time - timedelta(seconds=300), exact_direction_time),
    ).tail(1)

    col1, col2 = st.columns(2)

    with col1:
        st.text("Phone orientation")

        st.markdown(
            f"""
        <div style="transform: rotate({orientation_logs['value'].iloc[0]}deg); 
                    display: inline-block; 
                    font-size: 60px;">
            ↑
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.text("Presented direction")

        st.markdown(
            f"""
        <div style="width: 150px;height: 300px;border: 1px solid black;border-radius: 10px;display: flex;justify-content: center;align-items: center;transform: rotate({orientation_logs['value'].iloc[0]}deg)">
        <div style="transform: rotate({direction_logs['value'].iloc[0]}deg); 
                    display: inline-block; 
                    margin:0 auto;
                    font-size: 60px;">
            ↑
        </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    last_remaining_segment_before_time = interpolate_locations(
        last_remaining_segment_before_time, 30
    )
    last_current_segment_before_time = interpolate_locations(
        last_current_segment_before_time, 30
    )

    last_track_point_before_time["color"] = "#0f0"
    last_track_point_before_time["size"] = 2
    last_remaining_segment_before_time["color"] = "#00f"
    last_remaining_segment_before_time["size"] = 1
    last_current_segment_before_time["color"] = "#0ff"
    last_current_segment_before_time["size"] = 1
    last_location_before_time["color"] = "#f00"
    last_location_before_time["size"] = 2
    combined_df = pd.concat(
        [
            last_current_segment_before_time,
            last_remaining_segment_before_time,
            last_location_before_time,
            last_track_point_before_time,
        ],
        ignore_index=True,
    )
    st.map(
        combined_df,
        latitude="latitude",
        longitude="longitude",
        color="color",
        zoom=16,
        size="size",
    )
