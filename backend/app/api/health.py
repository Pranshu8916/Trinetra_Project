from fastapi import APIRouter

from app.core.database import database

router = APIRouter(
    prefix="/api",
    tags=["Health"],
)


@router.get("/health")
async def health_check():
    try:
        await database.command("ping")

        return {
            "status": "ok",
            "service": "trinetra-backend",
            "database": "connected",
        }
    except Exception as error:
        return {
            "status": "error",
            "service": "trinetra-backend",
            "database": "disconnected",
            "error": str(error),
        }
