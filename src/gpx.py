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
