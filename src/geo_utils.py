from geopy.distance import geodesic
import pandas as pd

from basePath import BasePath


def calculate_distance(df: pd.DataFrame) -> float:
    """
    Calculate total geodesic distance (in meters) between points in a DataFrame.

    Assumes DataFrame has columns: ['lat', 'lon'] or ['latitude', 'longitude'].

    Parameters:
    df (pd.DataFrame): A DataFrame containing latitude and longitude columns.

    Returns:
    float: Total distance in meters.
    """
    total_distance = 0.0

    # Handle different column name possibilities
    if "lat" in df.columns and "lon" in df.columns:
        coords = list(zip(df["lat"], df["lon"]))
    elif "latitude" in df.columns and "longitude" in df.columns:
        coords = list(zip(df["latitude"], df["longitude"]))
    else:
        raise ValueError(
            "DataFrame must contain 'lat' and 'lon' or 'latitude' and 'longitude' columns."
        )

    for i in range(len(coords) - 1):
        total_distance += geodesic(coords[i], coords[i + 1]).meters

    return total_distance


def compute_average_speed_m_s(df: pd.DataFrame) -> float:
    total_distance = 0.0
    timestamps = df["timestamp"].tolist()
    coords = df[["latitude", "longitude"]].values.tolist()

    for i in range(1, len(coords)):
        total_distance += geodesic(coords[i - 1], coords[i]).meters

    total_time_s = (timestamps[-1] - timestamps[0]).total_seconds()
    return total_distance / total_time_s if total_time_s > 0 else 0
