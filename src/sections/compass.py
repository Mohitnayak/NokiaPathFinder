import pandas as pd
import streamlit as st
from datetime import timedelta

from geo import interpolate_locations
from components.time_slider import time_slider
from utils import (
    fetch_logs,
    convert_location_logs_to_df,
    convert_segment_log_to_df,
    filter_logs_by_time_range,
)


def compass_section(db_path: str, all_location_logs: pd.DataFrame):
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


def fetch_orientation_logs(db_path: str, column: str):
    df = fetch_logs(db_path, [column])
    # convert value to number
    df["value"] = df["value"].astype(float)
    # combine logs from one second and average it
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["timestamp"] = df["timestamp"].dt.floor("1S")

    result = df.groupby(df["timestamp"])["value"].first().reset_index()
    return result
