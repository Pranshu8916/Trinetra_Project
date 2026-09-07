from fastapi import APIRouter

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    return await authenticate_user(
        username=credentials.username,
        password=credentials.password,
    )
