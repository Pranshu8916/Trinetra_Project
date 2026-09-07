from typing import Any

from app.providers.base import RiskEngineProvider


class RuleBasedRiskEngineProvider(RiskEngineProvider):
    def calculate_risk(
        self,
        document_analysis: dict[str, Any],
        face_analysis: dict[str, Any],
        face_match: dict[str, Any],
        liveness: dict[str, Any],
        deepfake: dict[str, Any],
        ocr_confidence: float | None = None,
    ) -> dict[str, Any]:
        reasons: list[str] = []
        score: int = 0  # Zero baseline — all risk is additive from signals

        # ── 1. Document Authenticity & Tampering ─────────────────────
        if document_analysis.get("tampering_detected"):
            score += 45
            reasons.append("Document tampering detected")
        elif document_analysis.get("authenticity_score", 1.0) < 0.70:
            score += 25
            reasons.append("Low document authenticity score")

        signals = document_analysis.get("signals", {})
        if not signals.get("required_fields_present", True):
            score += 20
            reasons.append("Required identity fields missing from document")

        # ── 1b. Security Watchlist / Interpol Blacklist Check (Module 2) ───
        doc_no = str(document_analysis.get("document_number") or "").upper()
        name_str = str(document_analysis.get("holder_name") or "").upper()
        blacklisted_entries = {"BLACK_LISTED", "INTERPOL_NOTICE", "SSB_FLAGGED", "WANTED_001"}
        
        is_blacklisted = any(b in doc_no or b in name_str for b in blacklisted_entries)
        watchlist_status = "FLAGGED" if is_blacklisted else "CLEAR"

        if is_blacklisted:
            score += 90
            reasons.append("Subject / Document FLAGGED on SSB & Interpol Security Watchlist")

        # ── 2. Face Presence & Quality ────────────────────────────────
        if not face_analysis.get("face_detected"):
            score += 50
            reasons.append("No face detected in selfie")
        elif face_analysis.get("face_count", 1) > 1:
            score += 30
            reasons.append("Multiple faces detected in biometric image")

        # ── 3. Face Match ─────────────────────────────────────────────
        match_status = face_match.get("match_status")
        similarity = face_match.get("similarity_score", 1.0)
        if match_status == "NOT_MATCHED" or similarity < 0.40:
            # Critical biometric mismatch / blatant impostor attack
            score += 85
            reasons.append("Face mismatch between document photo and selfie (Impostor Alert)")
        elif similarity < 0.60:
            score += 60
            reasons.append("Face mismatch between document photo and selfie")
        elif similarity < 0.75:
            score += 25
            reasons.append("Face similarity below preferred threshold")

        # ── 4. Liveness Check ─────────────────────────────────────────
        if not liveness.get("is_live", True):
            score += 80
            reasons.append("Liveness verification failed (potential spoof)")
        elif liveness.get("liveness_score", 1.0) < 0.70:
            score += 20
            reasons.append("Low liveness confidence score")

        # ── 5. Deepfake / Synthetic Media ────────────────────────────
        if deepfake.get("deepfake_detected"):
            score += 80
            reasons.append("High probability of synthetic/deepfake media")
        elif deepfake.get("deepfake_score", 0.0) > 0.60:
            score += 30
            reasons.append("Elevated synthetic media manipulation score")

        # ── Clamp 0–100 ───────────────────────────────────────────────
        risk_score = max(0, min(100, score))

        # ── Decision Thresholds (contract-aligned) ────────────────────
        # < 40  → "Clean"          — Unlock e-Gate
        # 40-74 → "Suspicious"     — Manual Inspection Alert
        # >= 75 → "Fraud/Impostor" — Gate Lock & Detain
        if risk_score < 40:
            risk_level = "Low"
            decision = "Clean"
        elif risk_score < 75:
            risk_level = "Medium"
            decision = "Suspicious"
        else:
            risk_level = "High"
            decision = "Fraud/Impostor"

        if not reasons:
            reasons = [
                "Document authenticity verified",
                "Face match confirmed",
                "Liveness check passed",
            ]

        is_mock_mode = any(
            [
                document_analysis.get("is_mock", False),
                face_analysis.get("is_mock", False),
                face_match.get("is_mock", False),
                liveness.get("is_mock", False),
            ]
        )

        return {
            "provider": "rule_based_risk_engine",
            "is_mock": is_mock_mode,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "decision": decision,
            "reasons": reasons,
            "watchlist_status": watchlist_status,
        }
