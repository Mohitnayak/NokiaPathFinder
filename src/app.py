import os
import streamlit as st
from datetime import timedelta, datetime
import pandas as pd

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


def normalize_logs(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], unit="ms")
    if "next_screen_timestamp" in dataframe.columns:
        dataframe["next_screen_timestamp"] = pd.to_datetime(
            dataframe["next_screen_timestamp"], unit="ms"
        )
    return dataframe


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


def filter_logs_by_time_range(
    dataframe: pd.DataFrame, time_range: tuple[datetime, datetime]
) -> pd.DataFrame:
    return dataframe[
        (dataframe["timestamp"] >= time_range[0])
        & (dataframe["timestamp"] <= time_range[1])
    ]


db_path = "log_database-2.db"

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

    st.map(filtered_location_logs, size=1, zoom=16)
