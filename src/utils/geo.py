import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString
import pyproj
from shapely.ops import transform
from functools import partial
from geopy.distance import geodesic

projection = partial(
    pyproj.transform,
    pyproj.Proj("epsg:4326"),  # From: WGS84
    pyproj.Proj("epsg:3857"),  # To: Web Mercator
)

reverse_projection = partial(
    pyproj.transform, pyproj.Proj("epsg:3857"), pyproj.Proj("epsg:4326")
)


def closest_point_on_track(
    position_lat: float, position_lon: float, track_df: pd.DataFrame
) -> tuple[float, float]:
    your_lat = position_lat
    your_lon = position_lon
    your_point = Point(your_lon, your_lat)  # Shapely uses (lon, lat)

    # 2. Track as DataFrame (lat, lon)
    track_line = convert_track_to_line(track_df)

    # 4. Project geometries
    track_line_proj = transform(projection, track_line)
    your_point_proj = transform(projection, your_point)

    # 5. Compute closest point on projected line
    projected_distance = track_line_proj.project(your_point_proj)
    closest_point_proj = track_line_proj.interpolate(projected_distance)

    # 6. Convert closest point back to lat/lon
    closest_point_latlon = transform(reverse_projection, closest_point_proj)
    return closest_point_latlon.y, closest_point_latlon.x


def get_point_d_ahead(
    position_lat: float,
    position_lon: float,
    track_df: pd.DataFrame,
    distance_ahead: float,
) -> tuple[float, float]:
    """
    Get the point on the track that is a certain distance ahead of the current position.
    """
    closest_lat, closest_lon = closest_point_on_track(
        position_lat, position_lon, track_df
    )
    track_line = convert_track_to_line(track_df)
    track_line_proj = transform(projection, track_line)
    your_point_proj = transform(projection, Point(closest_lon, closest_lat))

    # Distance along the line to your current point
    current_distance = track_line_proj.project(your_point_proj)

    # Add distance ahead
    target_distance = current_distance + distance_ahead

    # Make sure you don't exceed the total length of the track
    target_distance = min(target_distance, track_line_proj.length)

    # Get the new point ahead
    point_ahead_proj = track_line_proj.interpolate(target_distance)

    # Convert back to lat/lon if needed
    point_ahead_latlon = transform(reverse_projection, point_ahead_proj)

    return point_ahead_latlon.y, point_ahead_latlon.x


def convert_track_to_line(track_df: pd.DataFrame) -> LineString:
    """
    Convert a DataFrame of track points into a Shapely LineString.
    """
    points = [
        Point(lon, lat) for lon, lat in zip(track_df["longitude"], track_df["latitude"])
    ]
    return LineString(points)


def interpolate_locations(df: pd.DataFrame, num_points=20) -> pd.DataFrame:
    """
    Interpolates `num_points` points between each consecutive pair of coordinates in the DataFrame.

    Parameters:
    - df: A pandas DataFrame with 'latitude' and 'longitude' columns.
    - num_points: Number of interpolated points between each pair (default is 20).

    Returns:
    - A new DataFrame with interpolated latitude and longitude points.
    """
    interpolated_data = []

    for i in range(len(df) - 1):
        start = df.iloc[i]
        end = df.iloc[i + 1]

        # Create arrays of interpolated latitudes and longitudes
        latitudes = np.linspace(
            start["latitude"], end["latitude"], num_points + 2
        )  # +2 to include start and end
        longitudes = np.linspace(start["longitude"], end["longitude"], num_points + 2)

        for lat, lon in zip(latitudes, longitudes):
            interpolated_data.append({"latitude": lat, "longitude": lon})

    # Convert to DataFrame
    return pd.DataFrame(interpolated_data)


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


# Speed bounds (m/s) for segment to count as "movement". Below min = stationary (excluded). Above max = noise/jump (excluded).
MIN_SEGMENT_SPEED_M_S = 0.3   # ~1 km/h; below this = standing still, not counted in completion time
MAX_SEGMENT_SPEED_M_S = 2.5   # ~9 km/h fast walk; above = GPS noise or non-walking, excluded so average reflects walking only


def _plausible_segment_totals(df: pd.DataFrame) -> tuple[float, float]:
    """
    Sum distance (m) and time (s) over segments with MIN <= speed <= MAX.
    Stationary and GPS jumps are excluded so completion time = time actually moving.
    """
    timestamps = df["timestamp"].tolist()
    coords = df[["latitude", "longitude"]].values.tolist()
    total_distance = 0.0
    total_time_s = 0.0
    for i in range(1, len(coords)):
        seg_dist_m = geodesic(coords[i - 1], coords[i]).meters
        seg_dt_s = (timestamps[i] - timestamps[i - 1]).total_seconds()
        if seg_dt_s <= 0:
            continue
        seg_speed = seg_dist_m / seg_dt_s
        if MIN_SEGMENT_SPEED_M_S <= seg_speed <= MAX_SEGMENT_SPEED_M_S:
            total_distance += seg_dist_m
            total_time_s += seg_dt_s
    return total_distance, total_time_s


def compute_average_speed_m_s(df: pd.DataFrame) -> float:
    """
    Average speed over plausible segments only (excludes GPS jumps).
    """
    total_distance, total_time_s = _plausible_segment_totals(df)
    return total_distance / total_time_s if total_time_s > 0 else 0.0


def compute_movement_time_s(df: pd.DataFrame) -> float:
    """
    Total time (s) spent in plausible movement (segments with speed <= MAX_SEGMENT_SPEED_M_S).
    Use this as completion time so it reflects actual movement duration, not full log span.
    """
    _, total_time_s = _plausible_segment_totals(df)
    return total_time_s
