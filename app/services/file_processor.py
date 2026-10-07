from pathlib import Path

import geopandas as gpd


def read_geospatial_file(file_path: Path) -> gpd.GeoDataFrame:
    """
    Read a supported geospatial file and return its features
    as a GeoDataFrame.
    """

    suffix = file_path.suffix.lower()

    if suffix == ".kml":
        return gpd.read_file(file_path, driver="KML")

    if suffix == ".zip":
        return gpd.read_file(file_path)

    raise ValueError(f"Unsupported file format: {suffix}")