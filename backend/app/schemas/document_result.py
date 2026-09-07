from datetime import datetime

from pydantic import BaseModel, Field


class DocumentResultResponse(BaseModel):
    document_id: str
    session_id: str
    status: str

    extracted_text: str | None = None

    extracted_name: str | None = None
    extracted_document_number: str | None = None
    extracted_document_type: str | None = None
    date_of_birth: str | None = None
    date_of_issue: str | None = None
    date_of_expiry: str | None = None
    nationality: str | None = None
    gender: str | None = None
    address: str | None = None
    field_confidence: dict[str, float] = Field(default_factory=dict)
    ocr_confidence: float | None = None
    created_at: datetime
