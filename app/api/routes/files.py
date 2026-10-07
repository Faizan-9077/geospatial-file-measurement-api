from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.file_processor import read_geospatial_file


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

        gdf = read_geospatial_file(saved_file)

        return {
            "id": file_id,
            "filename": file.filename,
            "feature_count": len(gdf),
            "crs": str(gdf.crs) if gdf.crs else None,
            "geometry_types": gdf.geometry.geom_type.unique().tolist(),
            "message": "File processed successfully."
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to process geospatial file: {str(exc)}"
        )

    finally:
        if saved_file.exists():
            saved_file.unlink()