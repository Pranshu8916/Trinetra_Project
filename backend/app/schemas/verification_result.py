from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VerificationSessionStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: int
    current_step: str
    subject_name: str | None = None
    document_type: str | None = None
    created_at: datetime
    updated_at: datetime


class UnifiedIdentityResult(BaseModel):
    name: str | None = None
    document_number: str | None = None
    document_type: str | None = None
    date_of_birth: str | None = None
    nationality: str | None = None
    gender: str | None = None
    address: str | None = None


class UnifiedDocumentResult(BaseModel):
    processed: bool
    provider: str | None = None
    authenticity_score: float | None = None
    tampering_detected: bool = False
    is_mock: bool = True
    signals: dict[str, Any] = Field(default_factory=dict)


class UnifiedBiometricResult(BaseModel):
    provider: str | None = None
    face_detected: bool
    face_count: int
    quality_score: float | None = None
    is_mock: bool = True


class UnifiedFaceMatchResult(BaseModel):
    provider: str | None = None
    match_status: str
    similarity_score: float | None = None
    is_mock: bool = True


class UnifiedLivenessResult(BaseModel):
    provider: str | None = None
    is_live: bool
    liveness_score: float | None = None
    is_mock: bool = True


class UnifiedDeepfakeResult(BaseModel):
    provider: str | None = None
    deepfake_detected: bool
    deepfake_score: float | None = None
    is_mock: bool = True


class UnifiedRiskResult(BaseModel):
    provider: str | None = None
    risk_score: int
    risk_level: str
    decision: str
    reasons: list[str] = Field(default_factory=list)
    is_mock: bool = True


class UnifiedVerificationResultResponse(BaseModel):
    session_id: str
    status: str
    identity: UnifiedIdentityResult
    document: UnifiedDocumentResult
    biometric: UnifiedBiometricResult
    face_match: UnifiedFaceMatchResult
    liveness: UnifiedLivenessResult
    deepfake: UnifiedDeepfakeResult
    risk: UnifiedRiskResult
    created_at: datetime
