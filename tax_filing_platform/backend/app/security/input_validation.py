from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import Settings


def validate_upload_metadata(file: UploadFile, size_bytes: int, settings: Settings) -> None:
    if size_bytes <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty upload")
    if size_bytes > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="upload too large")
    if file.content_type not in settings.allowed_upload_mime_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="file type not allowed")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".txt"}:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="file extension not allowed")
