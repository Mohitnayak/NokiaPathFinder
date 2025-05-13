import folium
import pandas as pd
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium


from components.select_file import select_file
from components.time_slider import time_slider
from deviation import get_on_track_distance, get_on_track_logs, get_time_on_track
from gpx import gpx_to_geojson
from utils import filter_logs_by_time_range


def display_location_logs(location_logs: pd.DataFrame, db_path: str):
    selected_time = time_slider(
        location_logs, id="location_time_slider", with_date=False
    )

    on_track_logs = get_on_track_logs(
        db_path, location_column="location", is_on_track=True, time_range=selected_time
    )
    off_track_logs = get_on_track_logs(
        db_path, location_column="location", is_on_track=False, time_range=selected_time
    )
    filtered_location_logs = filter_logs_by_time_range(location_logs, selected_time)

    base_gpx_path = "temp/path.gpx"
    st.write("You can also add the recorded GPX file to compare it with user's route.")
    gpx_base_path = select_file(
        "Select Base GPX path", temp_file_name=base_gpx_path, type="gpx"
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
    <span style="color:red">⬤</span> User's route  \n
    <span style="color:blue">⬤</span> Base Track  \n
    <span style="color:green">⬤</span> Locations where user was on track  \n
    <span style="color:purple">⬤</span> Locations where user was off track 
    """,
        unsafe_allow_html=True,
    )
    elements = []
    if gpx_base_path:
        elements.append(gpx_line(base_gpx_path))
    elements += map(
        lambda row: folium_dataframe_line(row, color="green", weight=16, opacity=0.5),
        on_track_logs,
    )
    elements += map(
        lambda row: folium_dataframe_line(row, color="purple", weight=16, opacity=0.5),
        off_track_logs,
    )
    elements.append(folium_dataframe_line(filtered_location_logs))
    st_data = folium_map(elements)


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


def gpx_line(gpx_path):
    geojson = gpx_to_geojson(gpx_path, color="green")
    return folium.GeoJson(geojson)
