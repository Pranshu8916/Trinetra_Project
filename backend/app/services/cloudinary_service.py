import os
from typing import Any

import cloudinary
import cloudinary.uploader

from app.core.config import settings

_configured = False


def init_cloudinary():
    global _configured
    if _configured:
        return True

    if settings.cloudinary_url:
        cloudinary.config(cloudinary_url=settings.cloudinary_url)
        _configured = True
        return True

    if (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        _configured = True
        return True

    return False


def is_cloudinary_configured() -> bool:
    return init_cloudinary()


def upload_to_cloudinary(
    file_path: str,
    folder: str = "trinetra/documents",
    public_id: str | None = None,
    resource_type: str = "auto",
) -> dict[str, Any] | None:
    if not is_cloudinary_configured():
        return None

    options: dict[str, Any] = {
        "folder": folder,
        "resource_type": resource_type,
    }
    if public_id:
        options["public_id"] = public_id

    result = cloudinary.uploader.upload(file_path, **options)
    return {
        "secure_url": result.get("secure_url"),
        "public_id": result.get("public_id"),
        "format": result.get("format"),
        "bytes": result.get("bytes"),
        "resource_type": result.get("resource_type"),
    }
