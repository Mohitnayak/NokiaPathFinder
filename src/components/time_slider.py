from datetime import datetime, timedelta
import pandas as pd
import streamlit as st


def time_slider(
    dataframe: pd.DataFrame,
    id: str,
    with_time: bool = True,
    with_date: bool = True,
    range: bool = True,
    label: str = "Select time",
) -> tuple[datetime, datetime] | datetime:
    min_time_datetime = dataframe["timestamp"].min().to_pydatetime()
    max_time_datetime = dataframe["timestamp"].max().to_pydatetime()

    if with_date:
        if min_time_datetime.date() == max_time_datetime.date():
            selected_date = min_time_datetime.date()
        else:
            selected_date = st.date_input(
                "Select date",
                min_value=min_time_datetime,
                max_value=max_time_datetime,
                value=max_time_datetime,
                key=id,
            )

        data_on_selected_date = dataframe[
            dataframe["timestamp"].dt.date == selected_date
        ]

        min_time_datetime = data_on_selected_date["timestamp"].min().to_pydatetime()
        max_time_datetime = data_on_selected_date["timestamp"].max().to_pydatetime()
        if not with_time:
            return (
                datetime.combine(selected_date, datetime.min.time()),
                datetime.combine(selected_date, datetime.max.time()),
            )

    if with_time:
        value = (min_time_datetime, max_time_datetime) if range else min_time_datetime
        return st.slider(
            label,
            key=id,
            min_value=min_time_datetime,
            max_value=max_time_datetime,
            step=timedelta(seconds=1),
            value=value,
            format="YY-MM-DD HH:mm:ss",
        )
