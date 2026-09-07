from fastapi import APIRouter, Depends, File, UploadFile

from app.core.dependencies import get_current_user
from app.schemas.biometric import BiometricUploadResponse
from app.schemas.document import DocumentUploadResponse
from app.schemas.document_result import DocumentResultResponse
from app.schemas.verification import (
    VerificationSessionCreate,
    VerificationSessionResponse,
)
from app.schemas.verification_result import (
    UnifiedVerificationResultResponse,
    VerificationSessionStatusResponse,
)
from app.services.biometric_service import upload_biometric
from app.services.document_processing_service import create_processing_result
from app.services.document_result_service import get_document_result
from app.services.document_service import upload_document
from app.services.verification_result_service import (
    execute_session_verification,
    get_session_final_result,
    get_session_status,
)
from app.services.verification_service import create_verification_session

router = APIRouter(
    prefix="/api/verification",
    tags=["Verification"],
)


@router.post(
    "/sessions",
    response_model=VerificationSessionResponse,
)
async def create_session(
    data: VerificationSessionCreate,
    current_user: dict = Depends(get_current_user),
):
    return await create_verification_session(
        created_by=current_user["user_id"],
        subject_name=data.subject_name,
        document_type=data.document_type,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=VerificationSessionStatusResponse,
)
async def get_session_status_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await get_session_status(
        session_id=session_id,
        requested_by=current_user["user_id"],
    )


@router.post(
    "/sessions/{session_id}/document",
    response_model=DocumentUploadResponse,
)
async def upload_session_document(
    session_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    return await upload_document(
        session_id=session_id,
        uploaded_by=current_user["user_id"],
        file=file,
    )


@router.post(
    "/sessions/{session_id}/biometric",
    response_model=BiometricUploadResponse,
)
async def upload_session_biometric(
    session_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    return await upload_biometric(
        session_id=session_id,
        uploaded_by=current_user["user_id"],
        file=file,
    )


@router.post(
    "/sessions/{session_id}/verify",
    response_model=UnifiedVerificationResultResponse,
)
async def verify_session_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await execute_session_verification(
        session_id=session_id,
        requested_by=current_user["user_id"],
    )


@router.get(
    "/sessions/{session_id}/result",
    response_model=UnifiedVerificationResultResponse,
)
async def get_session_result_endpoint(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await get_session_final_result(
        session_id=session_id,
        requested_by=current_user["user_id"],
    )


@router.get(
    "/documents/{document_id}/result",
    response_model=DocumentResultResponse,
)
async def get_session_document_result(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await get_document_result(
        document_id=document_id,
        requested_by=current_user["user_id"],
    )


@router.post(
    "/documents/{document_id}/process",
    response_model=DocumentResultResponse,
)
async def process_session_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    return await create_processing_result(
        document_id=document_id,
        processed_by=current_user["user_id"],
    )
