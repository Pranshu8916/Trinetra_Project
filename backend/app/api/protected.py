from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/api/protected",
    tags=["Protected"],
)


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    return {
        "message": "Authentication successful",
        "user": current_user,
    }
