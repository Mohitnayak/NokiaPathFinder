import os
import streamlit as st
from datetime import timedelta, datetime
import pandas as pd
from streamlit_folium import st_folium
import folium

from gpx import gpx_to_geojson
from utils import convert_location_logs_to_df, fetch_logs
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
        route = (
            row["route"]
            .replace("com.example.path_fainder.screens.", "")
            .replace("/{pathUri}", "")
            .replace("/{withHaptic}", "")
        )
        path = os.path.basename(row["pathUri"]) if row["pathUri"] else ""
        haptic = haptic_visual_map.get(row["withHaptic"], "")
        return (
            f"{row['timestamp'].strftime('%y-%m-%d %H:%M:%S')} {route} {path} {haptic}"
        )

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


def time_slider(dataframe: pd.DataFrame) -> datetime:
    min_time_datetime = dataframe["timestamp"].min().to_pydatetime()
    max_time_datetime = dataframe["timestamp"].max().to_pydatetime()

    selected_date = st.date_input(
        "Select date",
        min_value=min_time_datetime,
        max_value=max_time_datetime,
        value=min_time_datetime,
    )

    data_on_selected_date = dataframe[dataframe["timestamp"].dt.date == selected_date]

    min_time_datetime = data_on_selected_date["timestamp"].min().to_pydatetime()
    max_time_datetime = data_on_selected_date["timestamp"].max().to_pydatetime()

    return st.slider(
        "Select time",
        min_value=min_time_datetime,
        max_value=max_time_datetime,
        step=timedelta(seconds=1),
        value=(min_time_datetime, max_time_datetime),
        format="YY-MM-DD HH:mm:ss",
    )


def select_file(label: str, temp_file_name: str = "", type=""):
    uploaded_file = st.file_uploader(label=label, type=type)
    if temp_file_name:
        if uploaded_file:
            with open(temp_file_name, "wb") as f:
                f.write(uploaded_file.getbuffer())
    return uploaded_file


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


def folium_dataframe_line(df):
    coordinates = list(zip(df["latitude"], df["longitude"]))
    line = folium.PolyLine(
        locations=coordinates,  # List of coordinates (latitude, longitude)
        color="red",  # Color of the line
        weight=4,  # Thickness of the line
    )
    return line


def gpx_line(gpx_path):
    geojson = gpx_to_geojson(gpx_path, color="green")
    return folium.GeoJson(geojson)


def folium_map(elements):
    m = folium.Map(zoom_start=16)
    bounds:list[list[float]] = []
    for element in elements:
        element.add_to(m)
        bounds.append(element.get_bounds())
    computed_bounds = [
        [min(bound[0][0] for bound in bounds), min(bound[0][1] for bound in bounds)],
        [max(bound[1][0] for bound in bounds), max(bound[1][1] for bound in bounds)],
    ]
    m.fit_bounds(computed_bounds)

    return st_folium(m, width=725)


# db_path = "log_database-2.db"
db_path = "temp/db.db"
if not os.path.exists("temp"):
    os.makedirs("temp")

file = select_file("Select database file", db_path, type="db")

if not file:
    st.stop()

st.subheader("Screen selection")

navigation_logs = normalize_logs(fetch_navigation_logs(db_path=db_path))

selected_navigation_time = time_slider(navigation_logs)

selected_screen_timestamps = screen_selector(
    filter_logs_by_time_range(navigation_logs, selected_navigation_time)
)

st.subheader("Location logs")

location_logs = filter_logs_by_time_range(
    normalize_logs(convert_location_logs_to_df(db_path, "location")),
    selected_screen_timestamps,
)
if location_logs.empty:
    st.write("No location logs found for the selected screen.")
else:
    selected_time = time_slider(location_logs)
    filtered_location_logs = filter_logs_by_time_range(location_logs, selected_time)

    base_gpx_path = "temp/path.gpx"
    gpx_base_path = select_file(
        "Select Base GPX path", temp_file_name=base_gpx_path, type="gpx"
    )

    elements = []
    if gpx_base_path:
        elements.append(gpx_line(base_gpx_path))
    elements.append(folium_dataframe_line(filtered_location_logs))
    st_data = folium_map(elements)
