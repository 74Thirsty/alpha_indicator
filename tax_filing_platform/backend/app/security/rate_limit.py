from __future__ import annotations

from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request, status

_hits: dict[str, list[float]] = defaultdict(list)


def simple_rate_limit(request: Request, *, limit: int = 120, window_seconds: int = 60) -> None:
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    _hits[key] = [ts for ts in _hits[key] if now - ts <= window_seconds]
    if len(_hits[key]) >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate limit exceeded")
    _hits[key].append(now)
