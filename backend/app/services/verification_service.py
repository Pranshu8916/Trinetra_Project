from datetime import datetime, timezone
from uuid import uuid4

from app.core.database import database


async def create_verification_session(
    created_by: str,
    subject_name: str | None,
    document_type: str | None,
):
    now = datetime.now(timezone.utc)

    session = {
        "session_id": f"VER-{uuid4().hex[:8].upper()}",
        "created_by": created_by,
        "status": "CREATED",
        "subject": {
            "name": subject_name,
            "document_type": document_type,
        },
        "document_result_id": None,
        "biometric_result_id": None,
        "risk_assessment_id": None,
        "created_at": now,
        "updated_at": now,
    }

    await database.verification_sessions.insert_one(session)

    return {
        "session_id": session["session_id"],
        "created_by": session["created_by"],
        "status": session["status"],
        "subject_name": subject_name,
        "document_type": document_type,
        "created_at": now,
    }
