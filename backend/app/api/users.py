from fastapi import APIRouter

from app.core.security import hash_password
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.post("", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate):
    password_hash = hash_password(user.password)

    return await create_user(
        username=user.username,
        password_hash=password_hash,
        role=user.role,
    )
