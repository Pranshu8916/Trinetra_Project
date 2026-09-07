from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.providers.base import DeepfakeDetectionProvider
from app.services.ai_biometrics_service import load_image_cv


class MockDeepfakeDetectionProvider(DeepfakeDetectionProvider):
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        return {
            "provider": "mock",
            "is_mock": True,
            "deepfake_detected": False,
            "deepfake_score": 0.08,
            "manipulation_confidence": 0.05,
        }


class RealDeepfakeDetectionProvider(DeepfakeDetectionProvider):
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        path = Path(selfie_image_path)
        if not path.exists():
            raise FileNotFoundError(f"Selfie image not found: {selfie_image_path}")

        img = load_image_cv(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # High-frequency anomaly analysis (detects GAN blur / blending boundaries)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = float(laplacian.var())

        # Synthetic media typically lacks natural camera sensor noise or has localized boundary blur
        is_synthetic = variance < 5.0
        score = min(0.95, max(0.05, round(0.10 if not is_synthetic else 0.85, 2)))

        return {
            "provider": "supplied_frequency_analysis",
            "is_mock": False,
            "deepfake_detected": is_synthetic,
            "deepfake_score": score,
            "manipulation_confidence": score,
        }
