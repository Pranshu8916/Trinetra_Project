from datetime import datetime

from pydantic import BaseModel


class BiometricUploadResponse(BaseModel):
    biometric_id: str
    session_id: str
    filename: str
    content_type: str
    status: str
    cloudinary_url: str | None = None
    uploaded_at: datetime
