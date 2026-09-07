from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.database import database


async def get_document_result(
    document_id: str,
    requested_by: str,
):
    document = await database.documents.find_one(
        {
            "document_id": document_id,
            "uploaded_by": requested_by,
        }
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    result = await database.document_results.find_one(
        {
            "document_id": document_id,
            "session_id": document["session_id"],
        }
    )

    if not result:
        return {
            "document_id": document_id,
            "session_id": document["session_id"],
            "status": "NOT_PROCESSED",
            "extracted_text": None,
            "extracted_name": None,
            "extracted_document_number": None,
            "extracted_document_type": None,
            "date_of_birth": None,
            "date_of_issue": None,
            "date_of_expiry": None,
            "nationality": None,
            "gender": None,
            "address": None,
            "field_confidence": {},
            "ocr_confidence": None,
            "created_at": datetime.now(timezone.utc),
        }

    return result
