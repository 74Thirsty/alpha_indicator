from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from ..config import get_settings


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "role": role, "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp())}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
