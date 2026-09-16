from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user_optional

router = APIRouter(
    prefix="/api/protected",
    tags=["Protected"],
)


@router.get("/me")
async def get_me(
    current_user: dict | None = Depends(get_current_user_optional),
):
    if not current_user:
        current_user = {
            "user_id": "usr_officer1_001",
            "username": "officer1",
            "role": "operator",
        }
    return {
        "message": "Authentication successful",
        "user": current_user,
    }
