import json
import os
from components.time_slider import time_slider
import streamlit as st
import pandas as pd
from datetime import timedelta, datetime

from utils import fetch_logs, filter_logs_by_time_range

haptic_visual_map = {
    True: "Haptic",
    1: "Haptic",
    2: "Haptic",
    False: "Visual",
    None: "",
}


def screen_selector(db_path: str) -> tuple[datetime, datetime]:
    st.subheader("Screen selection")
    st.write(
        "Select the screen you want to analyze. Pay attention to the track gpx and navigation mode"
    )

    navigation_logs = fetch_navigation_logs(db_path=db_path)

    selected_navigation_time = time_slider(
        navigation_logs, id="navigation_time_slider", with_time=False
    )

    df = filter_logs_by_time_range(navigation_logs, selected_navigation_time)

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
        path = os.path.basename(row["pathUri"]) if row["pathUri"] else ""  # noqa: F821
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


def fetch_navigation_logs(db_path):
    raw_data = fetch_logs(db_path, ["navigation"])
    print("Fetching and processing logs...")

    df = raw_data.apply(process_row, axis=1)
    df.columns = ["timestamp", "route", "pathUri", "withHaptic"]
    df["next_screen_timestamp"] = df["timestamp"].shift(-1)
    return df


def process_row(row):
    data = mapScreenNavValueToArgs(row["value"])
    return pd.Series(
        [row["timestamp"], data["route"], data["pathUri"], data["withHaptic"]]
    )


def calculate_time_on_screen(df_old):
    df = df_old.copy()
    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    # Sort by timestamp
    df = df.sort_values(by="timestamp")
    # Calculate time differences
    df["time_on_screen"] = df["timestamp"].diff().dt.total_seconds().fillna(0)
    return df


def mapScreenNavValueToArgs(value: str):
    try:
        json_data = json.loads(value)  # Parse JSON
        route = json_data.get("route")
        args_raw = json_data.get("args")
        args = json.loads(args_raw) if args_raw else None
        pathUri = None
        withHaptic = None
        if args and isinstance(args, dict):
            mMap = args.get("mMap")
            if mMap:
                pathUri = mMap.get("pathUri")
                withHaptic = mMap.get("withHaptic")
        return {
            "route": route,
            "pathUri": pathUri,
            "withHaptic": withHaptic,
            "args": args,
        }
    except (json.JSONDecodeError, TypeError):
        return None
