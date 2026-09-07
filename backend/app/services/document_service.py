from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import filetype
from fastapi import HTTPException, UploadFile, status

from app.core.database import database

STORAGE_DIR = Path("storage/documents")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

ALLOWED_FILE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
}


async def upload_document(
    session_id: str,
    uploaded_by: str,
    file: UploadFile,
):
    session = await database.verification_sessions.find_one(
        {
            "session_id": session_id,
            "created_by": uploaded_by,
        }
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification session not found",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10 MB limit",
        )

    detected_type = filetype.guess(contents)

    if detected_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine the actual file type",
        )

    detected_mime = detected_type.mime

    if detected_mime not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is not supported",
        )

    if detected_mime != file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match declared file type",
        )

    document_id = f"DOC-{uuid4().hex[:8].upper()}"
    extension = ALLOWED_CONTENT_TYPES[file.content_type]
    filename = f"{document_id}{extension}"
    file_path = STORAGE_DIR / filename

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(contents)

    from app.services.cloudinary_service import upload_to_cloudinary
    cloud_result = upload_to_cloudinary(
        file_path=str(file_path),
        folder="trinetra/documents",
        public_id=document_id,
        resource_type="auto",
    )
    cloudinary_url = cloud_result.get("secure_url") if cloud_result else None
    cloudinary_public_id = cloud_result.get("public_id") if cloud_result else None

    now = datetime.now(timezone.utc)

    document = {
        "document_id": document_id,
        "session_id": session_id,
        "uploaded_by": uploaded_by,
        "original_filename": file.filename,
        "stored_filename": filename,
        "content_type": file.content_type,
        "detected_type": detected_mime,
        "file_path": str(file_path),
        "cloudinary_url": cloudinary_url,
        "cloudinary_public_id": cloudinary_public_id,
        "status": "UPLOADED",
        "uploaded_at": now,
    }

    await database.documents.insert_one(document)

    await database.verification_sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "document_result_id": document_id,
                "status": "IN_PROGRESS",
                "updated_at": now,
            }
        },
    )

    return {
        "document_id": document_id,
        "session_id": session_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "UPLOADED",
        "cloudinary_url": cloudinary_url,
        "uploaded_at": now,
    }
