from datetime import datetime

from pydantic import BaseModel


class VerificationSessionCreate(BaseModel):
    subject_name: str | None = None
    document_type: str | None = None


class VerificationSessionResponse(BaseModel):
    session_id: str
    created_by: str
    status: str
    subject_name: str | None = None
    document_type: str | None = None
    created_at: datetime
