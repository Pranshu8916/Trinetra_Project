from pathlib import Path
from typing import Any

from app.providers.base import FaceMatchingProvider
from app.services.ai_biometrics_service import compare_faces


class MockFaceMatchingProvider(FaceMatchingProvider):
    async def compare(
        self,
        document_image_path: str,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        doc_path = Path(document_image_path)
        selfie_path = Path(selfie_image_path)

        if doc_path.exists() and selfie_path.exists():
            try:
                res = compare_faces(doc_path, selfie_path)
                return {
                    "provider": "real_biometric_face_matching",
                    "is_mock": False,
                    "match_status": "MATCHED" if res["verified"] else "NOT_MATCHED",
                    "similarity_score": res["similarity_score"],
                    "raw_cosine_similarity": res["raw_cosine_similarity"],
                    "confidence_level": "HIGH",
                    "biometric_verdict": res["match_verdict"],
                }
            except Exception:
                pass

        return {
            "provider": "mock_impostor_alert",
            "is_mock": True,
            "match_status": "NOT_MATCHED",
            "similarity_score": 0.25,
            "confidence_level": "HIGH",
            "biometric_verdict": "IMPOSTOR_ALERT_MISMATCH",
        }


class RealFaceMatchingProvider(FaceMatchingProvider):
    async def compare(
        self,
        document_image_path: str,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        doc_path = Path(document_image_path)
        selfie_path = Path(selfie_image_path)

        if not doc_path.exists():
            raise FileNotFoundError(f"Document image not found: {document_image_path}")
        if not selfie_path.exists():
            raise FileNotFoundError(f"Selfie image not found: {selfie_image_path}")

        result = compare_faces(doc_path, selfie_path)
        similarity = result["similarity_score"]

        # Map to standard Trinetra status vocabulary: MATCHED, NOT_MATCHED, MANUAL_REVIEW
        if result["verified"] or similarity >= 0.75:
            match_status = "MATCHED"
            confidence = "HIGH"
        elif similarity < 0.50:
            match_status = "NOT_MATCHED"
            confidence = "HIGH"
        else:
            match_status = "MANUAL_REVIEW"
            confidence = "MEDIUM"

        return {
            "provider": "supplied_joint_color_structure",
            "is_mock": False,
            "match_status": match_status,
            "similarity_score": similarity,
            "raw_cosine_similarity": result["raw_cosine_similarity"],
            "confidence_level": confidence,
            "biometric_verdict": result["match_verdict"],
        }
