import pandas as pd
from shapely.geometry import Point, LineString
import pyproj
from shapely.ops import transform
from functools import partial

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
