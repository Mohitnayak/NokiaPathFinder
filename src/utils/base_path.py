from datetime import datetime
import json
from utils.logs import fetch_logs, filter_logs_by_time_range


class Point:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

    latitude: float
    longitude: float


class BasePath:
    """
    Represents the base GPX path used to navigate the user in the mobile app.

    Attributes:
        points (list[Point]): A list of Point objects representing the path coordinates.
        deviation_zone_radius (float): The radius (in meters) defining the allowed deviation zone from the base path.
    """
    points: list[Point]
    deviation_zone_radius: float

def fetch_base_path_for_time_range(
    db_path: str, time_range: tuple[datetime, datetime]
) -> BasePath:
    """
    Fetches the base path that app was using during the specified time range.
    """
    currentSegmentDf = filter_logs_by_time_range(
        fetch_logs(db_path, ["current-segment"]), time_range
    )
    if currentSegmentDf.empty:
        raise "No route found for this time range. This is most likely a bug in logs."
    if currentSegmentDf.shape[0] > 1:
        raise "More than one route found for this time range. This is most likely a bug in logs."

    # format of currentSegment is {"points": [{"latitude": 0.0, "longitude": 0.0}, ...]}
    currentSegment = json.loads(currentSegmentDf["value"].iloc[0])

    maxDeviationDf = filter_logs_by_time_range(
        fetch_logs(db_path, ["current-max-deviation"]), time_range
    )
    if maxDeviationDf.empty:
        raise "No max deviation found for this time range. This is most likely a bug in logs."
    if maxDeviationDf.shape[0] > 1:
        raise "More than one max deviation found for this time range. This is most likely a bug in logs."

    maxDeviation = float(maxDeviationDf["value"].iloc[0])

    basePath = BasePath()
    basePath.deviation_zone_radius = maxDeviation
    basePath.points = [
        Point(latitude=point["latitude"], longitude=point["longitude"])
        for point in currentSegment["points"]
    ]
    return basePath
