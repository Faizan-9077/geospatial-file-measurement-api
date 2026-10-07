from fastapi import APIRouter, File, UploadFile, HTTPException

router = APIRouter(
    prefix="/api/files",
    tags=["Files"]
)


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

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "File received successfully."
    }