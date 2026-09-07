from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.database import database
from app.services.document_extraction_service import extract_document_fields
from app.services.ocr_service import extract_text


async def create_processing_result(
    document_id: str,
    processed_by: str,
):
    document = await database.documents.find_one(
        {
            "document_id": document_id,
            "uploaded_by": processed_by,
        }
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    existing_result = await database.document_results.find_one(
        {
            "document_id": document_id,
            "session_id": document["session_id"],
        }
    )

    if existing_result:
        return existing_result

    now = datetime.now(timezone.utc)

    try:
        session = await database.verification_sessions.find_one(
            {"session_id": document["session_id"]}
        )
        document_type_hint = (
            session.get("subject", {}).get("document_type") if session else None
        )

        extracted_text = extract_text(
            file_path=document["file_path"],
            content_type=document["content_type"],
        )

        extracted_fields = extract_document_fields(
            raw_text=extracted_text,
            document_type_hint=document_type_hint,
        )

        result = {
            "document_id": document_id,
            "session_id": document["session_id"],
            "status": "COMPLETED",
            "extracted_text": extracted_text,
            "extracted_name": extracted_fields["name"],
            "extracted_document_number": extracted_fields["document_number"],
            "extracted_document_type": extracted_fields["document_type"],
            "date_of_birth": extracted_fields["date_of_birth"],
            "date_of_issue": extracted_fields["date_of_issue"],
            "date_of_expiry": extracted_fields["date_of_expiry"],
            "nationality": extracted_fields["nationality"],
            "gender": extracted_fields["gender"],
            "address": extracted_fields["address"],
            "field_confidence": extracted_fields["field_confidence"],
            "ocr_confidence": extracted_fields["ocr_confidence"],
            "created_at": now,
        }

        await database.document_results.insert_one(result)
        result.pop("_id", None)

        await database.documents.update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "status": "PROCESSED",
                }
            },
        )

        return result

    except Exception as error:
        failed_result = {
            "document_id": document_id,
            "session_id": document["session_id"],
            "status": "FAILED",
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
            "created_at": now,
            "error": str(error),
        }

        await database.document_results.insert_one(failed_result)
        failed_result.pop("_id", None)

        await database.documents.update_one(
            {"document_id": document_id},
            {
                "$set": {
                    "status": "PROCESSING_FAILED",
                }
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document processing failed",
        )
