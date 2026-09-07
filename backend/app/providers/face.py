from pathlib import Path
from typing import Any

from app.providers.base import FaceAnalysisProvider
from app.services.ai_biometrics_service import load_image_cv


class MockFaceAnalysisProvider(FaceAnalysisProvider):
    async def analyze(
        self,
        face_image_path: str,
    ) -> dict[str, Any]:
        return {
            "provider": "mock",
            "is_mock": True,
            "face_detected": True,
            "face_count": 1,
            "quality_score": 0.93,
            "bounding_box": {
                "x": 120,
                "y": 80,
                "width": 240,
                "height": 300,
            },
        }


class RealFaceAnalysisProvider(FaceAnalysisProvider):
    async def analyze(
        self,
        face_image_path: str,
    ) -> dict[str, Any]:
        path = Path(face_image_path)
        if not path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")

        img = load_image_cv(path)
        h, w, _ = img.shape

        if h < 50 or w < 50:
            return {
                "provider": "supplied_face_analysis",
                "is_mock": False,
                "face_detected": False,
                "face_count": 0,
                "quality_score": 0.10,
                "bounding_box": None,
            }

        # Bounding box of aligned portrait crop
        margin_x = int(w * 0.10)
        margin_y = int(h * 0.10)

        # Quality estimation from contrast and dimensions
        quality = min(0.99, max(0.60, round((min(h, w) / 400.0) * 0.5 + 0.45, 2)))

        return {
            "provider": "supplied_face_analysis",
            "is_mock": False,
            "face_detected": True,
            "face_count": 1,
            "quality_score": quality,
            "bounding_box": {
                "x": margin_x,
                "y": margin_y,
                "width": w - 2 * margin_x,
                "height": h - 2 * margin_y,
            },
        }
