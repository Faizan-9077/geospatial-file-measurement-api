import zipfile
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from app.services.file_processor import read_geospatial_file


def create_test_shapefile(directory: Path) -> Path:
    """
    Create a small valid Polygon Shapefile for testing.
    """

    directory.mkdir(parents=True, exist_ok=True)

    gdf = gpd.GeoDataFrame(
        {
            "name": ["Test Polygon"],
            "category": ["polygon"],
        },
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

    shapefile_path = directory / "test_features.shp"

    gdf.to_file(
        shapefile_path,
        driver="ESRI Shapefile",
    )

    return shapefile_path


def create_zip(zip_path: Path, source_directory: Path) -> None:
    """
    Create a ZIP containing all files from a directory.
    """

    with zipfile.ZipFile(zip_path, "w") as archive:
        for file_path in source_directory.iterdir():
            archive.write(file_path, arcname=file_path.name)


def test_valid_shapefile_zip(tmp_path):
    """
    A valid ZIP containing one complete Shapefile should be
    successfully read.
    """

    shapefile_dir = tmp_path / "shapefile"
    create_test_shapefile(shapefile_dir)

    zip_path = tmp_path / "valid.zip"
    create_zip(zip_path, shapefile_dir)

    gdf = read_geospatial_file(zip_path)

    assert len(gdf) == 1
    assert gdf.crs.to_string() == "EPSG:4326"
    assert gdf.geometry.iloc[0].geom_type == "Polygon"


def test_zip_without_shapefile(tmp_path):
    """
    A ZIP without a .shp file should be rejected.
    """

    zip_path = tmp_path / "invalid.zip"

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("readme.txt", "not a shapefile")

    with pytest.raises(
        ValueError,
        match="ZIP file does not contain a Shapefile",
    ):
        read_geospatial_file(zip_path)


def test_shapefile_missing_component(tmp_path):
    """
    A Shapefile missing a required component should be rejected.
    """

    shapefile_dir = tmp_path / "shapefile"
    create_test_shapefile(shapefile_dir)

    dbf_file = shapefile_dir / "test_features.dbf"
    dbf_file.unlink()

    zip_path = tmp_path / "missing_dbf.zip"
    create_zip(zip_path, shapefile_dir)

    with pytest.raises(
        ValueError,
        match="missing required component",
    ):
        read_geospatial_file(zip_path)


def test_multiple_shapefiles(tmp_path):
    """
    A ZIP containing multiple Shapefiles should be rejected
    instead of arbitrarily selecting one.
    """

    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    create_test_shapefile(first_dir)
    create_test_shapefile(second_dir)


    for file_path in second_dir.iterdir():
        new_name = file_path.name.replace(
            "test_features",
            "second_features",
        )
        file_path.rename(second_dir / new_name)

    zip_path = tmp_path / "multiple.zip"

    with zipfile.ZipFile(zip_path, "w") as archive:

        for file_path in first_dir.iterdir():
            archive.write(
                file_path,
                arcname=file_path.name,
            )

        for file_path in second_dir.iterdir():
            archive.write(
                file_path,
                arcname=file_path.name,
            )

    with pytest.raises(
        ValueError,
        match="multiple Shapefiles",
    ):
        read_geospatial_file(zip_path)


def test_zip_path_traversal(tmp_path):
    """
    ZIP entries containing path traversal should be rejected
    before extraction.
    """

    zip_path = tmp_path / "malicious.zip"

    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(
            "../evil.txt",
            "malicious content",
        )

    with pytest.raises(
        ValueError,
        match="Unsafe path detected",
    ):
        read_geospatial_file(zip_path)