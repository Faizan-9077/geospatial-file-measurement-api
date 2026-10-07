import geopandas as gpd


def get_measurement_crs(gdf: gpd.GeoDataFrame) -> str:
    """
    Determine an appropriate projected CRS for measurement calculations.

    If the source CRS is already projected, use it directly.
    If the source CRS is geographic, estimate an appropriate UTM CRS
    based on the dataset's location.
    """

    if gdf.crs is None:
        raise ValueError("Input file does not contain a CRS.")

    if gdf.crs.is_projected:
        return gdf.crs.to_string()

    estimated_crs = gdf.estimate_utm_crs()

    if estimated_crs is None:
        raise ValueError(
            "Unable to determine a suitable projected CRS for measurement."
        )

    return estimated_crs.to_string()