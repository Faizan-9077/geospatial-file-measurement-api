import zipfile

import geopandas as gpd
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from app.main import app


client = TestClient(app)


def create_test_shapefile(directory):
    """
    Create a small valid Shapefile for API testing.
    """

    directory.mkdir(parents=True, exist_ok=True)

    gdf = gpd.GeoDataFrame(
        {
            "name": ["API Test Polygon"],
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

    shapefile_path = directory / "api_test.shp"

    gdf.to_file(
        shapefile_path,
        driver="ESRI Shapefile",
    )


def create_shapefile_zip(zip_path, shapefile_directory):
    """
    Create a ZIP containing all Shapefile components.
    """

    with zipfile.ZipFile(zip_path, "w") as archive:
        for file_path in shapefile_directory.iterdir():
            archive.write(
                file_path,
                arcname=file_path.name,
            )


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Geospatial File Measurement API is running"
    )


def test_upload_kml():
    with open("sample_data/test.kml", "rb") as file:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "test.kml",
                    file,
                    "application/vnd.google-earth.kml+xml",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "test.kml"
    assert data["feature_count"] == 3
    assert data["crs"] == "EPSG:4326"
    assert data["measurement_crs"] == "EPSG:32643"
    assert data["status"] == "COMPLETED"


def test_upload_shapefile_zip(tmp_path):
    shapefile_directory = tmp_path / "shapefile"

    create_test_shapefile(shapefile_directory)

    zip_path = tmp_path / "api_test.zip"

    create_shapefile_zip(
        zip_path,
        shapefile_directory,
    )

    with open(zip_path, "rb") as file:
        response = client.post(
            "/api/files/",
            files={
                "file": (
                    "api_test.zip",
                    file,
                    "application/zip",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "api_test.zip"
    assert data["feature_count"] == 1
    assert data["crs"] == "EPSG:4326"
    assert data["measurement_crs"] == "EPSG:32643"
    assert data["geometry_types"] == ["Polygon"]
    assert data["status"] == "COMPLETED"


def test_get_file_and_measurements(tmp_path):
    shapefile_directory = tmp_path / "shapefile"

    create_test_shapefile(shapefile_directory)

    zip_path = tmp_path / "api_test.zip"

    create_shapefile_zip(
        zip_path,
        shapefile_directory,
    )

    with open(zip_path, "rb") as file:
        upload_response = client.post(
            "/api/files/",
            files={
                "file": (
                    "api_test.zip",
                    file,
                    "application/zip",
                )
            },
        )

    assert upload_response.status_code == 200

    uploaded_data = upload_response.json()
    file_id = uploaded_data["id"]

    file_response = client.get(
        f"/api/files/{file_id}"
    )

    assert file_response.status_code == 200
    assert file_response.json()["id"] == file_id

    measurement_response = client.get(
        f"/api/files/{file_id}/measurements"
    )

    assert measurement_response.status_code == 200

    measurement_data = measurement_response.json()

    assert measurement_data["file_id"] == file_id
    assert measurement_data["feature_count"] == 1
    assert len(measurement_data["measurements"]) == 1
    assert measurement_data["measurements"][0]["measurement"] > 0
    assert (
        measurement_data["measurements"][0]["unit"]
        == "square_meters"
    )


def test_file_not_found():
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(
        f"/api/files/{fake_id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."


def test_measurements_file_not_found():
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(
        f"/api/files/{fake_id}/measurements"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found."