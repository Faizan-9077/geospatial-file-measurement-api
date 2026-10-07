import geopandas as gpd


def calculate_measurements(
    gdf: gpd.GeoDataFrame,
    measurement_crs: str,
) -> list[dict]:

    projected_gdf = gdf.to_crs(measurement_crs)

    measurements = []

    for index, row in projected_gdf.iterrows():

        geometry = row.geometry
        geometry_type = geometry.geom_type

        result = {
            "feature_id": index,
            "geometry_type": geometry_type,
            "measurement": None,
            "unit": None,
        }

        if geometry_type == "Polygon":
            result["measurement"] = geometry.area
            result["unit"] = "square_meters"

        elif geometry_type == "MultiPolygon":
            result["measurement"] = geometry.area
            result["unit"] = "square_meters"

        elif geometry_type == "LineString":
            result["measurement"] = geometry.length
            result["unit"] = "meters"

        elif geometry_type == "MultiLineString":
            result["measurement"] = geometry.length
            result["unit"] = "meters"

        measurements.append(result)

    return measurements