# Base Provider Interfaces
from typing import Any


class DocumentFraudProvider:
    async def analyze(
        self,
        document_file_path: str,
        extracted_data: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


class FaceAnalysisProvider:
    async def analyze(
        self,
        face_image_path: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class FaceMatchingProvider:
    async def compare(
        self,
        document_image_path: str,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class LivenessProvider:
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class DeepfakeDetectionProvider:
    async def analyze(
        self,
        selfie_image_path: str,
    ) -> dict[str, Any]:
        raise NotImplementedError


class RiskEngineProvider:
    def calculate_risk(
        self,
        document_analysis: dict[str, Any],
        face_analysis: dict[str, Any],
        face_match: dict[str, Any],
        liveness: dict[str, Any],
        deepfake: dict[str, Any],
        ocr_confidence: float | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError
