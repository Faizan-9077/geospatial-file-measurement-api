import geopandas as gpd
import pytest
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Point, Polygon

from app.services.crs import get_measurement_crs
from app.services.measurement import calculate_measurements


def test_polygon_area_uses_projected_crs():
    gdf = gpd.GeoDataFrame(
        {"name": ["Test Polygon"]},
        geometry=[
            Polygon([
                (77.5900, 12.9700),
                (77.6000, 12.9700),
                (77.6000, 12.9800),
                (77.5900, 12.9800),
                (77.5900, 12.9700),
            ])
        ],
        crs="EPSG:4326",
    )

    measurement_crs = get_measurement_crs(gdf)

    assert measurement_crs == "EPSG:32643"

    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["geometry_type"] == "Polygon"
    assert results[0]["measurement"] > 0
    assert results[0]["unit"] == "square_meters"
    assert results[0]["crs"] == "EPSG:4326"


def test_multipolygon_area():
    polygon_1 = Polygon([
        (77.5900, 12.9700),
        (77.5950, 12.9700),
        (77.5950, 12.9750),
        (77.5900, 12.9750),
        (77.5900, 12.9700),
    ])

    polygon_2 = Polygon([
        (77.6000, 12.9700),
        (77.6050, 12.9700),
        (77.6050, 12.9750),
        (77.6000, 12.9750),
        (77.6000, 12.9700),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["MultiPolygon"]},
        geometry=[MultiPolygon([polygon_1, polygon_2])],
        crs="EPSG:4326",
    )

    measurement_crs = get_measurement_crs(gdf)
    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["geometry_type"] == "MultiPolygon"
    assert results[0]["measurement"] > 0
    assert results[0]["unit"] == "square_meters"


def test_linestring_length():
    gdf = gpd.GeoDataFrame(
        {"name": ["Test Line"]},
        geometry=[
            LineString([
                (77.5900, 12.9700),
                (77.6000, 12.9800),
            ])
        ],
        crs="EPSG:4326",
    )

    measurement_crs = get_measurement_crs(gdf)
    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["geometry_type"] == "LineString"
    assert results[0]["measurement"] > 0
    assert results[0]["unit"] == "meters"


def test_multilinestring_length():
    line_1 = LineString([
        (77.5900, 12.9700),
        (77.6000, 12.9800),
    ])

    line_2 = LineString([
        (77.6100, 12.9700),
        (77.6200, 12.9800),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["MultiLine"]},
        geometry=[MultiLineString([line_1, line_2])],
        crs="EPSG:4326",
    )

    measurement_crs = get_measurement_crs(gdf)
    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["geometry_type"] == "MultiLineString"
    assert results[0]["measurement"] > 0
    assert results[0]["unit"] == "meters"


def test_point_has_no_measurement():
    gdf = gpd.GeoDataFrame(
        {"name": ["Test Point"]},
        geometry=[Point(77.5946, 12.9716)],
        crs="EPSG:4326",
    )

    measurement_crs = get_measurement_crs(gdf)
    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["geometry_type"] == "Point"
    assert results[0]["measurement"] is None
    assert results[0]["unit"] is None


def test_projected_crs_is_used_directly():
    gdf = gpd.GeoDataFrame(
        {"name": ["Projected Polygon"]},
        geometry=[
            Polygon([
                (500000, 1400000),
                (500100, 1400000),
                (500100, 1400100),
                (500000, 1400100),
                (500000, 1400000),
            ])
        ],
        crs="EPSG:32643",
    )

    measurement_crs = get_measurement_crs(gdf)

    assert measurement_crs == "EPSG:32643"

    results = calculate_measurements(gdf, measurement_crs)

    assert results[0]["measurement"] == pytest.approx(10000)
    assert results[0]["unit"] == "square_meters"


def test_missing_crs_is_rejected():
    gdf = gpd.GeoDataFrame(
        {"name": ["No CRS"]},
        geometry=[
            Polygon([
                (0, 0),
                (1, 0),
                (1, 1),
                (0, 1),
                (0, 0),
            ])
        ],
    )

    with pytest.raises(
        ValueError,
        match="Input file does not contain a CRS",
    ):
        get_measurement_crs(gdf)