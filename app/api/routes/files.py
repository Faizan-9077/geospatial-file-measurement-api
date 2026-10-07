from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.crs import get_measurement_crs
from app.services.file_processor import read_geospatial_file
from app.services.storage import save_file_record, get_file_record

from app.services.measurement import calculate_measurements

router = APIRouter(
    prefix="/api/files",
    tags=["Files"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    allowed_extensions = {".kml", ".zip"}

    filename = file.filename.lower()

    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Only .kml and .zip files are supported."
        )

    file_id = str(uuid4())
    extension = Path(filename).suffix

    saved_file = UPLOAD_DIR / f"{file_id}{extension}"

    try:
        contents = await file.read()
        saved_file.write_bytes(contents)

        # Read geospatial data
        gdf = read_geospatial_file(saved_file)

        # Determine CRS used for measurements
        measurement_crs = get_measurement_crs(gdf)

        measurements = calculate_measurements(
            gdf,
            measurement_crs
        )

        record = {
            "id": file_id,
            "filename": file.filename,
            "feature_count": len(gdf),
            "crs": str(gdf.crs) if gdf.crs else None,
            "measurement_crs": measurement_crs,
            "geometry_types": gdf.geometry.geom_type.unique().tolist(),
            "status": "COMPLETED",
            "measurements": measurements
        }

        save_file_record(file_id, record)

        return record

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to process geospatial file: {str(exc)}"
        )

    finally:
        if saved_file.exists():
            saved_file.unlink()


@router.get("/{file_id}")
def get_file(file_id: str):

    from app.services.storage import get_file_record

    record = get_file_record(file_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    return record 


@router.get("/{file_id}/measurements")
def get_measurements(file_id: str):

    record = get_file_record(file_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    return {
        "file_id": file_id,
        "filename": record["filename"],
        "measurement_crs": record["measurement_crs"],
        "feature_count": record["feature_count"],
        "measurements": record["measurements"]
    }