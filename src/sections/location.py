from datetime import datetime
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from utils.base_path import BasePath
from components.time_slider import time_slider
from utils.deviation import get_on_track_distance, get_on_track_logs, get_time_on_track
from utils.geojson import convert_base_path_to_geojson
from utils.haptic import get_vibration_logs
from utils.logs import convert_location_logs_to_df, filter_logs_by_time_range

from utils.base_path import get_base_path_for_time_range


def location_section(
    db_path: str,
    selected_screen_timestamps: tuple[datetime, datetime],
    location_logs: pd.DataFrame,
):
    st.subheader("Location logs")

    st.write(
        "With this slider you can analyze only a part of selected route. By default it is the whole route."
    )

    base_path = base_path = get_base_path_for_time_range(
        db_path=db_path, time_range=selected_screen_timestamps
    )

    selected_time = time_slider(
        location_logs, id="location_time_slider", with_date=False
    )

    on_track_logs = get_on_track_logs(
        db_path,
        location_column="raw-location",
        is_on_track=True,
        time_range=selected_time,
    )
    off_track_logs = get_on_track_logs(
        db_path,
        location_column="raw-location",
        is_on_track=False,
        time_range=selected_time,
    )
    filtered_location_logs = filter_logs_by_time_range(location_logs, selected_time)
    raw_filtered_location_logs = filter_logs_by_time_range(
        convert_location_logs_to_df(db_path, "raw-location"), selected_time
    )
    side_logs = {}
    for side in ["Left", "Right", "Both", "None"]:
        side_logs[side] = get_vibration_logs(
            db_path, location_column="location", time_range=selected_time, side=side
        )

    st.write(f"Time on track: {get_time_on_track(db_path, selected_time)}s")
    st.write(
        f"Distance on track: {get_on_track_distance(db_path, location_column='location', time_range=selected_time, is_on_track=True)}m"
    )

    st.write(
        f"Time off track: {get_time_on_track(db_path, selected_time, is_on_track=False)}s"
    )
    st.write(
        f"Distance off track: {get_on_track_distance(db_path, location_column='location', time_range=selected_time, is_on_track=False)}m"
    )

    st.write("You can also add the recorded GPX file to compare it with user's route.")
    st.markdown(
        """
    <span style="color:red">⬤</span> User's route (Fused location)  \n
    <span style="color:orange">⬤</span> User's route (GPS only location)  \n
    <span style="color:blue">⬤</span> Base Track  \n
    <span style="color:green">⬤</span> Locations where user was on track  \n
    <span style="color:purple">⬤</span> Locations where user was off track 
    """,
        unsafe_allow_html=True,
    )
    elements = []
    haptic_elements = []
    if base_path:
        elements.append(base_path_line(base_path))
        haptic_elements.append(base_path_line(base_path))

    elements += map(
        lambda row: folium_dataframe_line(row, color="green", weight=16, opacity=0.5),
        on_track_logs,
    )
    elements += map(
        lambda row: folium_dataframe_line(row, color="purple", weight=16, opacity=0.5),
        off_track_logs,
    )

    elements.append(folium_dataframe_line(filtered_location_logs))
    elements.append(
        folium_dataframe_line(raw_filtered_location_logs, color="orange", weight=4)
    )
    haptic_elements.append(folium_dataframe_line(filtered_location_logs))

    folium_map(elements)

    st.header("Locations of haptic feedback")
    sides = ["Left", "Right", "Both", "None"]
    side = st.selectbox("Select a side of haptic feedback:", sides)

    haptic_elements += map(
        lambda row: folium_dataframe_line(row, color="green", weight=16, opacity=0.5),
        side_logs[side],
    )
    folium_map(haptic_elements)


def folium_dataframe_line(df, color="red", weight=4, opacity=1.0):
    coordinates = list(zip(df["latitude"], df["longitude"]))
    line = folium.PolyLine(
        locations=coordinates,  # List of coordinates (latitude, longitude)
        color=color,
        weight=weight,
        opacity=opacity,
    )
    return line


def folium_map(elements):
    m = folium.Map(zoom_start=16)
    bounds: list[list[float]] = []
    for element in elements:
        element.add_to(m)
        bounds.append(element.get_bounds())
    computed_bounds = [
        [min(bound[0][0] for bound in bounds), min(bound[0][1] for bound in bounds)],
        [max(bound[1][0] for bound in bounds), max(bound[1][1] for bound in bounds)],
    ]
    m.fit_bounds(computed_bounds)

    return st_folium(m, width=725)


def base_path_line(base_path: BasePath):
    geojson = convert_base_path_to_geojson(base_path, color="blue")
    return folium.GeoJson(geojson)
