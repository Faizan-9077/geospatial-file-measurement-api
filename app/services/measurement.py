import geopandas as gpd
from app.services.serialization import make_json_safe

def calculate_measurements(
    gdf: gpd.GeoDataFrame,
    measurement_crs: str,
) -> list[dict]:

    projected_gdf = gdf.to_crs(measurement_crs)

    measurements = []

    original_crs = str(gdf.crs) if gdf.crs else None

    for index, row in gdf.iterrows():

        geometry = row.geometry
        geometry_type = geometry.geom_type

        projected_geometry = projected_gdf.loc[index].geometry

        properties = {
            key: make_json_safe(value)
            for key, value in row.items()
            if key != "geometry"
        }

        result = {
            "feature_id": make_json_safe(index),
            "geometry_type": geometry_type,
            "geometry": geometry.__geo_interface__,
            "crs": original_crs,
            "properties": properties,
            "measurement": None,
            "unit": None,
        }

        if geometry_type in {"Polygon", "MultiPolygon"}:
            result["measurement"] = projected_geometry.area
            result["unit"] = "square_meters"

        elif geometry_type in {"LineString", "MultiLineString"}:
            result["measurement"] = projected_geometry.length
            result["unit"] = "meters"

        measurements.append(result)

    return measurements