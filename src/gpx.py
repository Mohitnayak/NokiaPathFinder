from utils import convert_location_logs_to_df
import gpxpy.gpx
import gpxpy


def convert_location_logs_to_gpx(db_path: str, column: str, output_file_path: str):
    df = convert_location_logs_to_df(db_path, column)

    # Create GPX object
    gpx = gpxpy.gpx.GPX()

    # Create a track and segment
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Add points from DataFrame
    for _, row in df.iterrows():
        point = gpxpy.gpx.GPXTrackPoint(
            latitude=row["latitude"], longitude=row["longitude"]
        )
        gpx_segment.points.append(point)

    # Get GPX XML as a string
    gpx_xml = gpx.to_xml()

    # Optional: Save to file
    with open(output_file_path, "w") as f:
        f.write(gpx_xml)


def gpx_to_geojson(gpx_file_path, color="blue"):
    """
    Convert a GPX file to GeoJSON format

    Args:
        gpx_file_path (str): Path to the input GPX file
        output_file_path (str, optional): Path to save the GeoJSON file. If None, returns the GeoJSON dict

    Returns:
        dict: GeoJSON dictionary if no output_file_path is provided
    """
    # Open and parse the GPX file
    try:
        with open(gpx_file_path, "r") as gpx_file:
            gpx = gpxpy.parse(gpx_file)
    except Exception as e:
        raise Exception(f"Error reading GPX file: {str(e)}")

    # Initialize GeoJSON structure
    geojson = {"type": "FeatureCollection", "features": []}

    # Process tracks
    for track in gpx.tracks:
        for segment in track.segments:
            coordinates = []
            times = []
            elevations = []

            for point in segment.points:
                coordinates.append([float(point.longitude), float(point.latitude)])
                times.append(point.time.isoformat() if point.time else None)
                elevations.append(float(point.elevation) if point.elevation else None)

            if coordinates:  # Only add if there are coordinates
                feature = {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coordinates},
                    "properties": {
                        "name": track.name,
                        "times": times if any(times) else None,
                        "elevations": elevations if any(elevations) else None,
                        "type": "track",
                        "color": color,  # Add color to properties
                    },
                }
                geojson["features"].append(feature)

    # Process routes (as LineStrings)
    for route in gpx.routes:
        coordinates = []
        times = []
        elevations = []

        for point in route.points:
            coordinates.append([float(point.longitude), float(point.latitude)])
            times.append(point.time.isoformat() if point.time else None)
            elevations.append(float(point.elevation) if point.elevation else None)

        if coordinates:  # Only add if there are coordinates
            feature = {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "properties": {
                    "name": route.name,
                    "times": times if any(times) else None,
                    "elevations": elevations if any(elevations) else None,
                    "type": "route",
                    "color": color,  # Add color to properties
                },
            }
            geojson["features"].append(feature)

    # Otherwise return the GeoJSON dictionary
    return geojson["features"]


def load_gpx_file(file_path):
    with open(file_path, "r") as f:
        return gpxpy.parse(f)
