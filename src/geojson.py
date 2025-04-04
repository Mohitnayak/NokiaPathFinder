import json
import pandas as pd
import urllib.parse
import webbrowser
from typing import Callable


def convert_to_geojson_line(df: pd.DataFrame, color: str = "blue") -> dict[str, any]:
    line_coords = df[["longitude", "latitude"]].values.tolist()

    line_feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": line_coords},
        "properties": {
            "name": "My Path",
            "stroke": color,
            "stroke-width": 2,
            "stroke-opacity": 1,
        },
    }

    return line_feature


def convert_to_geojson_points(
    df: pd.DataFrame,
    color: Callable[[pd.Series], str] = lambda: "blue",
    info_columns: list[str] = [],
) -> list[dict[str, any]]:
    features = []
    for _, row in df.iterrows():
        point_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]],
            },
            "properties": {
                "marker-color": color(row),
                "marker-size": "medium",
                "marker-symbol": "",
                **{col: row[col] for col in info_columns},
            },
        }
        features.append(point_feature)
    return features


def combine_geojson_features(
    geojson1: list[dict[str, any]], geojson2: list[dict[str, any]]
) -> dict[str, any]:
    combined_features = geojson1 + geojson2
    return {"type": "FeatureCollection", "features": combined_features}


def stringify_geojson(geojson: dict[str, any]) -> str:
    return json.dumps(geojson, indent=2)


def visualize_geojson_io(geojson_str: str):
    encoded_geojson = urllib.parse.quote(geojson_str)
    url = f"https://geojson.io/#data=data:application/json,{encoded_geojson}"
    webbrowser.open(url, new=0, autoraise=True)
