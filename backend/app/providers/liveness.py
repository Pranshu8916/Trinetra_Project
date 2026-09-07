from pathlib import Path
from typing import Any

from app.providers.base import LivenessProvider
from app.services.ai_biometrics_service import evaluate_liveness, load_image_cv


class MockLivenessProvider(LivenessProvider):
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        return {
            "provider": "mock",
            "is_mock": True,
            "status": "COMPLETED",
            "is_live": True,
            "liveness_score": 0.94,
        }


class RealLivenessProvider(LivenessProvider):
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        path = Path(selfie_image_path)
        if not path.exists():
            raise FileNotFoundError(f"Selfie image not found: {selfie_image_path}")

        img = load_image_cv(path)
        report = evaluate_liveness(img)

        return {
            "provider": "supplied_passive_liveness",
            "is_mock": False,
            "status": "COMPLETED",
            "is_live": report["liveness_passed"],
            "liveness_score": report["liveness_score"],
            "sharpness_score": report["sharpness_score"],
            "saturation_index": report["saturation_index"],
            "anti_spoof_verdict": report["anti_spoof_verdict"],
        }
