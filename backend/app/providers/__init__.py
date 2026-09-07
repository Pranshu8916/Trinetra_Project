from app.core.config import settings
from app.providers.deepfake import (
    MockDeepfakeDetectionProvider,
    RealDeepfakeDetectionProvider,
)
from app.providers.document_fraud import (
    MockDocumentFraudProvider,
    RealDocumentFraudProvider,
)
from app.providers.face import (
    MockFaceAnalysisProvider,
    RealFaceAnalysisProvider,
)
from app.providers.face_matching import (
    MockFaceMatchingProvider,
    RealFaceMatchingProvider,
)
from app.providers.liveness import (
    MockLivenessProvider,
    RealLivenessProvider,
)
from app.providers.risk import RuleBasedRiskEngineProvider


def get_document_fraud_provider():
    if not settings.use_mock_mode:
        return RealDocumentFraudProvider()
    return MockDocumentFraudProvider()


def get_face_analysis_provider():
    if not settings.use_mock_mode:
        return RealFaceAnalysisProvider()
    return MockFaceAnalysisProvider()


def get_face_matching_provider():
    if not settings.use_mock_mode:
        return RealFaceMatchingProvider()
    return MockFaceMatchingProvider()


def get_liveness_provider():
    if not settings.use_mock_mode:
        return RealLivenessProvider()
    return MockLivenessProvider()


def get_deepfake_provider():
    if not settings.use_mock_mode:
        return RealDeepfakeDetectionProvider()
    return MockDeepfakeDetectionProvider()


def get_risk_engine_provider():
    return RuleBasedRiskEngineProvider()
