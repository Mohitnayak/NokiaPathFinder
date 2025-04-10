import streamlit as st
from datetime import timedelta, datetime
import pandas as pd

from utils import convert_location_logs_to_df, fetch_logs

logs = fetch_logs("log_database-2.db", ["location"])


def normalize_logs(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"], unit="ms")
    return dataframe


def time_slider(dataframe: pd.DataFrame) -> datetime:
    min_time_datetime = dataframe["timestamp"].min().to_pydatetime()
    max_time_datetime = dataframe["timestamp"].max().to_pydatetime()

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


location_logs = normalize_logs(
    convert_location_logs_to_df("log_database-2.db", "location")
)
selected_time = time_slider(location_logs)
filtered_location_logs = filter_logs_by_time_range(location_logs, selected_time)

st.map(filtered_location_logs, size=1)
