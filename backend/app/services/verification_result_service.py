from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.database import database
from app.providers import (
    get_deepfake_provider,
    get_document_fraud_provider,
    get_face_analysis_provider,
    get_face_matching_provider,
    get_liveness_provider,
    get_risk_engine_provider,
)


def _calculate_progress(session: dict[str, Any]) -> tuple[int, str]:
    curr_status = session.get("status", "CREATED")
    if curr_status == "CREATED":
        return 10, "AWAITING_DOCUMENT"
    elif curr_status == "IN_PROGRESS" or curr_status == "DOCUMENT_UPLOADED":
        return 30, "AWAITING_BIOMETRIC"
    elif curr_status == "BIOMETRIC_UPLOADED":
        return 60, "READY_FOR_VERIFICATION"
    elif curr_status == "PROCESSING":
        return 80, "RUNNING_AI_CHECKS"
    elif curr_status == "COMPLETED":
        return 100, "VERIFICATION_COMPLETE"
    elif curr_status == "FAILED":
        return 100, "VERIFICATION_FAILED"
    return 20, "IN_PROGRESS"


async def get_session_status(session_id: str, requested_by: str) -> dict[str, Any]:
    session = await database.verification_sessions.find_one(
        {
            "session_id": session_id,
            "created_by": requested_by,
        }
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification session not found",
        )

    progress, current_step = _calculate_progress(session)

    return {
        "session_id": session["session_id"],
        "status": session.get("status", "CREATED"),
        "progress": progress,
        "current_step": current_step,
        "subject_name": session.get("subject", {}).get("name"),
        "document_type": session.get("subject", {}).get("document_type"),
        "created_at": session["created_at"],
        "updated_at": session.get("updated_at", session["created_at"]),
    }


async def execute_session_verification(
    session_id: str,
    requested_by: str,
) -> dict[str, Any]:
    session = await database.verification_sessions.find_one(
        {
            "session_id": session_id,
            "created_by": requested_by,
        }
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification session not found",
        )

    # Check for existing unified result (idempotency)
    existing_result = await database.verification_results.find_one(
        {"session_id": session_id}
    )
    if existing_result:
        existing_result.pop("_id", None)
        return existing_result

    # Retrieve document and biometric records
    document = await database.documents.find_one(
        {"session_id": session_id, "uploaded_by": requested_by}
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be uploaded before running verification",
        )

    # Ensure document is processed (or process it now)
    doc_result = await database.document_results.find_one(
        {"document_id": document["document_id"]}
    )
    if not doc_result or doc_result.get("status") != "COMPLETED":
        # Auto-process if not yet processed
        from app.services.document_processing_service import create_processing_result
        doc_result = await create_processing_result(
            document_id=document["document_id"],
            processed_by=requested_by,
        )

    biometric = await database.biometric_results.find_one(
        {"session_id": session_id, "uploaded_by": requested_by}
    )
    if not biometric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Biometric selfie must be uploaded before running verification",
        )

    now = datetime.now(timezone.utc)

    # Transition session to PROCESSING
    await database.verification_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"status": "PROCESSING", "updated_at": now}},
    )

    # 1. Document Fraud Analysis Provider
    doc_fraud_provider = get_document_fraud_provider()
    doc_analysis = await doc_fraud_provider.analyze(
        document_file_path=document["file_path"],
        extracted_data=doc_result,
    )

    # 2. Face Analysis Provider
    face_provider = get_face_analysis_provider()
    face_analysis = await face_provider.analyze(
        face_image_path=biometric["file_path"]
    )

    # 3. Face Matching Provider
    face_match_provider = get_face_matching_provider()
    face_match = await face_match_provider.compare(
        document_image_path=document["file_path"],
        selfie_image_path=biometric["file_path"],
    )

    # 4. Liveness Provider
    liveness_provider = get_liveness_provider()
    liveness = await liveness_provider.analyze(
        selfie_image_path=biometric["file_path"]
    )

    # 5. Deepfake Detection Provider
    deepfake_provider = get_deepfake_provider()
    deepfake = await deepfake_provider.analyze(
        selfie_image_path=biometric["file_path"]
    )

    # 6. Risk Engine Provider
    risk_provider = get_risk_engine_provider()
    risk = risk_provider.calculate_risk(
        document_analysis=doc_analysis,
        face_analysis=face_analysis,
        face_match=face_match,
        liveness=liveness,
        deepfake=deepfake,
        ocr_confidence=doc_result.get("ocr_confidence"),
    )

    unified_result = {
        "session_id": session_id,
        "status": "COMPLETED",
        "identity": {
            "name": doc_result.get("extracted_name"),
            "document_number": doc_result.get("extracted_document_number"),
            "document_type": doc_result.get("extracted_document_type"),
            "date_of_birth": doc_result.get("date_of_birth"),
            "nationality": doc_result.get("nationality"),
            "gender": doc_result.get("gender"),
            "address": doc_result.get("address"),
        },
        "document": {
            "processed": True,
            "provider": doc_analysis.get("provider"),
            "authenticity_score": doc_analysis.get("authenticity_score"),
            "tampering_detected": doc_analysis.get("tampering_detected", False),
            "is_mock": doc_analysis.get("is_mock", True),
            "signals": doc_analysis.get("signals", {}),
        },
        "biometric": {
            "provider": face_analysis.get("provider"),
            "face_detected": face_analysis.get("face_detected", True),
            "face_count": face_analysis.get("face_count", 1),
            "quality_score": face_analysis.get("quality_score"),
            "is_mock": face_analysis.get("is_mock", True),
        },
        "face_match": {
            "provider": face_match.get("provider"),
            "match_status": face_match.get("match_status", "MATCHED"),
            "similarity_score": face_match.get("similarity_score"),
            "is_mock": face_match.get("is_mock", True),
        },
        "liveness": {
            "provider": liveness.get("provider"),
            "is_live": liveness.get("is_live", True),
            "liveness_score": liveness.get("liveness_score"),
            "is_mock": liveness.get("is_mock", True),
        },
        "deepfake": {
            "provider": deepfake.get("provider"),
            "deepfake_detected": deepfake.get("deepfake_detected", False),
            "deepfake_score": deepfake.get("deepfake_score"),
            "is_mock": deepfake.get("is_mock", True),
        },
        "risk": {
            "provider": risk.get("provider"),
            "risk_score": risk.get("risk_score"),
            "risk_level": risk.get("risk_level"),
            "decision": risk.get("decision"),
            "reasons": risk.get("reasons", []),
            "is_mock": risk.get("is_mock", True),
        },
        "created_at": now,
    }

    await database.verification_results.insert_one(unified_result)
    unified_result.pop("_id", None)

    # Transition session to COMPLETED
    await database.verification_sessions.update_one(
        {"session_id": session_id},
        {"$set": {"status": "COMPLETED", "updated_at": now}},
    )

    return unified_result


async def get_session_final_result(
    session_id: str,
    requested_by: str,
) -> dict[str, Any]:
    session = await database.verification_sessions.find_one(
        {
            "session_id": session_id,
            "created_by": requested_by,
        }
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification session not found",
        )

    result = await database.verification_results.find_one({"session_id": session_id})
    if not result:
        # Check if ready to execute or still in progress
        document = await database.documents.find_one(
            {"session_id": session_id, "uploaded_by": requested_by}
        )
        biometric = await database.biometric_results.find_one(
            {"session_id": session_id, "uploaded_by": requested_by}
        )

        if document and biometric:
            # Automatically execute verification and return result
            return await execute_session_verification(session_id, requested_by)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification result not ready. Upload document and biometric first.",
        )

    result.pop("_id", None)
    return result
