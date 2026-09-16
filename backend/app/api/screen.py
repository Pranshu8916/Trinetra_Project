"""
screen.py — POST /api/v1/screen-document
─────────────────────────────────────────
Single-shot endpoint: accepts a passport scan + live webcam frame,
runs the full 4-module AI screening pipeline, persists the report to
MongoDB, and returns a standardised JSON decision.

Response contract:
{
    "status":         "success",
    "report_id":      "RPT-XXXXXXXX",
    "risk_score":     int (0–100),
    "risk_level":     "Low" | "Medium" | "High",
    "decision":       "Clean" | "Suspicious" | "Fraud/Impostor",
    "action":         str,          # Human-readable gate action
    "reasons":        list[str],
    "extracted_data": {             # OCR identity fields
        "name", "document_number", "document_type",
        "date_of_birth", "date_of_issue", "date_of_expiry",
        "nationality", "gender"
    },
    "ai_confidence":  {             # Per-module confidence scores
        "ocr_confidence", "document_authenticity",
        "face_similarity", "liveness_score", "deepfake_score"
    },
    "is_mock":        bool,
    "screened_at":    ISO-8601 UTC datetime
}
"""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.dependencies import get_current_user_optional
from app.providers import (
    get_deepfake_provider,
    get_document_fraud_provider,
    get_face_analysis_provider,
    get_face_matching_provider,
    get_liveness_provider,
    get_risk_engine_provider,
)
from app.services.ocr_service import extract_text
from app.services.document_extraction_service import extract_document_fields
from app.services.screening_report_service import save_screening_report

router = APIRouter(prefix="/api/v1", tags=["Screening"])

# ── Constants ──────────────────────────────────────────────────────────────────
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp", "application/octet-stream", "blob"}
_ALLOWED_DOC_TYPES   = {"image/jpeg", "image/png", "image/jpg", "image/webp", "application/pdf", "application/octet-stream", "blob"}
_MAX_FILE_BYTES      = 10 * 1024 * 1024  # 10 MB

_DECISION_ACTIONS: dict[str, str] = {
    "Clean":          "e-Gate unlocked — standard entry authorised.",
    "Suspicious":     "Manual inspection required — refer to senior officer.",
    "Fraud/Impostor": "Gate locked — detain subject and escalate immediately.",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _validate_upload(file: UploadFile, contents: bytes, allowed: set[str], label: str) -> None:
    """Raise 400 if the upload fails any basic integrity check."""
    if not contents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"{label} file is empty.")
    if len(contents) > _MAX_FILE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"{label} exceeds the 10 MB size limit.")
    if file.content_type not in allowed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{label} has an unsupported format. Allowed: {', '.join(sorted(allowed))}.",
        )


def _write_temp(contents: bytes, suffix: str) -> Path:
    """Write bytes to a NamedTemporaryFile and return its Path (caller must delete)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        return Path(tmp.name)


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/screen-document")
async def screen_document(
    passport_image: UploadFile = File(..., description="Scanned passport / identity document image (JPEG, PNG, PDF)"),
    live_frame:     UploadFile = File(..., description="Live webcam selfie frame (JPEG or PNG)"),
    current_user:   dict | None = Depends(get_current_user_optional),
) -> dict[str, Any]:
    if not current_user:
        current_user = {"user_id": "usr_officer1_001", "username": "officer1", "role": "operator"}
    """
    **Module orchestration order:**
    1. OCR Extraction        — reads identity fields from the passport image
    2. Document Validation   — MRZ checksums + field consistency + format checks
    3. Tampering Detection   — ELA forensics for compression anomalies / forgery
    4. Face Verification     — matches the document photo against the live frame
    → Risk Score             — weighted rule-based scoring engine (0–100)
    → MongoDB Persist        — saves the full report to `screening_reports`
    """
    # ── 0. Read & Validate Uploads ────────────────────────────────────────────
    passport_bytes = await passport_image.read()
    live_bytes     = await live_frame.read()

    _validate_upload(passport_image, passport_bytes, _ALLOWED_DOC_TYPES, "Passport image")
    _validate_upload(live_frame,     live_bytes,     _ALLOWED_IMAGE_TYPES,  "Live frame")

    # Infer file extension for temp files
    _ext_map = {
        "image/jpeg":       ".jpg",
        "image/jpg":        ".jpg",
        "image/png":        ".png",
        "image/webp":       ".webp",
        "application/pdf":  ".pdf",
    }
    passport_path: Path | None = None
    live_path:     Path | None = None

    try:
        passport_path = _write_temp(passport_bytes, _ext_map.get(passport_image.content_type, ".jpg"))
        live_path     = _write_temp(live_bytes,     _ext_map.get(live_frame.content_type, ".jpg"))

        # ── Module 1: OCR Extraction ──────────────────────────────────────────
        raw_text       = extract_text(str(passport_path), passport_image.content_type)
        extracted      = extract_document_fields(raw_text, document_type_hint="passport")

        extracted_data: dict[str, Any] = {
            "name":            extracted.get("name"),
            "document_number": extracted.get("document_number"),
            "document_type":   extracted.get("document_type"),
            "date_of_birth":   extracted.get("date_of_birth"),
            "date_of_issue":   extracted.get("date_of_issue"),
            "date_of_expiry":  extracted.get("date_of_expiry"),
            "nationality":     extracted.get("nationality"),
            "gender":          extracted.get("gender"),
            "state":           extracted.get("state"),
            "issuing_authority": extracted.get("issuing_authority"),
            "is_valid_checksum": extracted.get("is_valid_checksum", True),
            "visa_number":     extracted.get("visa_number"),
            "visa_type":       extracted.get("visa_type"),
            "stay_duration":   extracted.get("stay_duration"),
            "entry_validity":  extracted.get("entry_validity"),
        }
        ocr_confidence: float = extracted.get("ocr_confidence") or 0.50

        # ── Immediate Criminal Watchlist Check (Module 4) ──────────────────────
        from app.services.watchlist_service import get_watchlist_service
        doc_no = str(extracted.get("document_number") or "")
        name_str = str(extracted.get("name") or "")
        dob = str(extracted.get("date_of_birth") or "")
        nationality = str(extracted.get("nationality") or "")

        watchlist_svc = get_watchlist_service()
        watchlist_check = watchlist_svc.check_subject(
            name=name_str,
            document_number=doc_no,
            birth_date=dob,
            country=nationality,
            raw_text=raw_text,
        )

        if watchlist_check.get("is_flagged"):
            # 🚨 EARLY SHORT-CIRCUIT EXIT: Criminal Flagged on Interpol / SSB Red Notice!
            match_details = watchlist_check.get("match_details") or {}
            entity_name = match_details.get("name", name_str)
            agency = match_details.get("issuing_agency", "SSB / INTERPOL Watchlist")
            charges = match_details.get("charges", "Interpol Red Notice Criminal Flag")

            reason_msg = f"CRITICAL RED NOTICE ALERT: Subject / Document FLAGGED on {agency}: {entity_name}"
            if charges:
                first_charge = str(charges).split("\n")[0][:80]
                reason_msg += f" ({first_charge})"

            risk_score = 100
            risk_level = "High"
            decision = "Fraud/Impostor"
            reasons = [reason_msg]
            watchlist_status = watchlist_check.get("status", "FLAGGED")

            ai_confidence = {
                "ocr_confidence": round(ocr_confidence, 3),
                "document_authenticity": 0.10,
                "face_similarity": 0.0,
                "liveness_score": 0.0,
                "deepfake_score": 0.0,
            }

            report_id, block_hash = await save_screening_report(
                decision=decision,
                risk_score=risk_score,
                risk_level=risk_level,
                reasons=reasons,
                extracted_data=extracted_data,
                ai_confidence=ai_confidence,
                is_mock=False,
                operator_id=current_user.get("user_id"),
            )

            return {
                "status": "success",
                "report_id": report_id,
                "block_hash": block_hash,
                "watchlist_status": watchlist_status,
                "watchlist_details": watchlist_check,
                "risk_score": 100,
                "risk_level": "High",
                "decision": "Fraud/Impostor",
                "action": "Gate locked — detain subject and escalate immediately.",
                "reasons": reasons,
                "extracted_data": extracted_data,
                "ai_confidence": ai_confidence,
                "is_mock": False,
            }

        # ── Module 2 & 3 run in parallel (doc fraud + liveness + deepfake) ───
        # Module 2: Document Validation (MRZ checksums, field consistency, ELA)
        doc_fraud_provider = get_document_fraud_provider()

        # Module 3: Tampering Detection (ELA) — part of doc_fraud for images
        # Module 4a: Face Analysis (presence, count, quality)
        face_provider = get_face_analysis_provider()

        doc_analysis, face_analysis = await asyncio.gather(
            doc_fraud_provider.analyze(
                document_file_path=str(passport_path),
                extracted_data=extracted,
            ),
            face_provider.analyze(face_image_path=str(live_path)),
        )

        # Module 4b: Face Matching (document photo vs live frame)
        face_match_provider = get_face_matching_provider()
        face_match = await face_match_provider.compare(
            document_image_path=str(passport_path),
            selfie_image_path=str(live_path),
        )

        # Module 4c: Liveness + Deepfake (parallel, both use live frame)
        liveness_provider = get_liveness_provider()
        deepfake_provider = get_deepfake_provider()

        liveness, deepfake = await asyncio.gather(
            liveness_provider.analyze(selfie_image_path=str(live_path)),
            deepfake_provider.analyze(selfie_image_path=str(live_path)),
        )

        # ── Risk Scoring ──────────────────────────────────────────────────────
        risk_provider = get_risk_engine_provider()
        risk = risk_provider.calculate_risk(
            document_analysis=doc_analysis,
            face_analysis=face_analysis,
            face_match=face_match,
            liveness=liveness,
            deepfake=deepfake,
            ocr_confidence=ocr_confidence,
        )

        risk_score: int  = risk["risk_score"]
        risk_level: str  = risk["risk_level"]
        decision:   str  = risk["decision"]
        reasons:    list = risk["reasons"]
        is_mock:    bool = risk["is_mock"]
        watchlist:  str  = risk.get("watchlist_status", "CLEAR")
        watchlist_details: dict = risk.get("watchlist_details") or {}

        signals = doc_analysis.get("signals", {})
        exif_info = signals.get("exif_analysis", {})
        stamp_info = signals.get("stamp_analysis", {})

        ai_confidence: dict[str, Any] = {
            "ocr_confidence":        round(ocr_confidence, 3),
            "document_authenticity": doc_analysis.get("authenticity_score"),
            "face_similarity":       face_match.get("similarity_score"),
            "liveness_score":        liveness.get("liveness_score"),
            "deepfake_score":        deepfake.get("deepfake_score"),
            "exif_analysis":         exif_info,
            "stamp_analysis":        stamp_info,
        }

        # ── Persist to MongoDB with Blockchain Cryptographic SHA-256 Hash ───
        report_id, block_hash = await save_screening_report(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            reasons=reasons,
            extracted_data=extracted_data,
            ai_confidence=ai_confidence,
            is_mock=is_mock,
            operator_id=current_user.get("user_id"),
        )

    finally:
        # Always clean up temp files, even on error
        for p in (passport_path, live_path):
            if p and p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    # ── Standardised Response ─────────────────────────────────────────────────
    return {
        "status":           "success",
        "report_id":        report_id,
        "block_hash":       block_hash,
        "watchlist_status": watchlist,
        "watchlist_details": watchlist_details,
        "risk_score":       risk_score,
        "risk_level":       risk_level,
        "decision":         decision,
        "action":           _DECISION_ACTIONS[decision],
        "reasons":          reasons,
        "extracted_data":   extracted_data,
        "ai_confidence":    ai_confidence,
        "is_mock":          is_mock,
        "screened_at":      datetime.now(timezone.utc).isoformat(),
    }
