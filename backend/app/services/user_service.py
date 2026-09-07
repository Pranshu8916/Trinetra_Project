from uuid import uuid4

from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.database import database


async def create_user(
    username: str,
    password_hash: str,
    role: str,
):
    existing_user = await database.users.find_one({"username": username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user_id = f"TRI-{uuid4().hex[:8].upper()}"

    user = {
        "user_id": user_id,
        "username": username,
        "password_hash": password_hash,
        "role": role,
    }

    try:
        await database.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    return {
        "user_id": user_id,
        "username": username,
        "role": role,
    }
