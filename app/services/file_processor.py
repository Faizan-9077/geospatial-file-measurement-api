from pathlib import Path
import tempfile
import zipfile

import geopandas as gpd


REQUIRED_SHAPEFILE_COMPONENTS = {".shp", ".shx", ".dbf", ".prj"}


def _is_safe_zip_member(member_name: str) -> bool:
    """
    Check whether a ZIP member can be safely extracted.

    Rejects absolute paths and paths containing '..' components
    to prevent path traversal outside the extraction directory.
    """

    path = Path(member_name)

    if path.is_absolute():
        return False

    return ".." not in path.parts


def _find_shapefile(extract_dir: Path) -> Path:
    """
    Find the Shapefile (.shp) inside the extracted ZIP.

    A ZIP must contain exactly one Shapefile to avoid ambiguity.
    """

    shapefiles = list(extract_dir.rglob("*.shp"))

    if not shapefiles:
        raise ValueError("ZIP file does not contain a Shapefile (.shp).")

    if len(shapefiles) > 1:
        names = ", ".join(str(path.relative_to(extract_dir)) for path in shapefiles)

        raise ValueError(
            f"ZIP file contains multiple Shapefiles: {names}. "
            "Please provide a ZIP containing exactly one Shapefile."
        )

    return shapefiles[0]


def _validate_shapefile_components(shapefile_path: Path) -> None:
    """
    Validate that the required Shapefile sidecar files exist.

    A Shapefile normally consists of multiple files sharing the
    same filename, such as .shp, .shx, .dbf and .prj.
    """

    missing_components = []

    for extension in REQUIRED_SHAPEFILE_COMPONENTS:
        component = shapefile_path.with_suffix(extension)

        if not component.exists():
            missing_components.append(extension)

    if missing_components:
        missing = ", ".join(sorted(missing_components))

        raise ValueError(
            f"Shapefile is missing required component(s): {missing}."
        )


def _read_shapefile_zip(file_path: Path) -> gpd.GeoDataFrame:
    """
    Safely extract a ZIP archive, validate its Shapefile,
    and return the loaded GeoDataFrame.

    The temporary extraction directory is automatically
    removed after this function finishes.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        extract_dir = Path(temp_dir)

        with zipfile.ZipFile(file_path, "r") as archive:

            for member in archive.infolist():
                if not _is_safe_zip_member(member.filename):
                    raise ValueError(
                        f"Unsafe path detected in ZIP archive: {member.filename}"
                    )

            archive.extractall(extract_dir)

        shapefile_path = _find_shapefile(extract_dir)

        _validate_shapefile_components(shapefile_path)

        return gpd.read_file(shapefile_path)


def read_geospatial_file(file_path: Path) -> gpd.GeoDataFrame:
    """
    Read a supported geospatial file and return its features
    as a GeoDataFrame.
    """

    suffix = file_path.suffix.lower()

    if suffix == ".kml":
        return gpd.read_file(file_path, driver="KML")

    if suffix == ".zip":
        return _read_shapefile_zip(file_path)

    raise ValueError(f"Unsupported file format: {suffix}")