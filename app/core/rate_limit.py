"""Simple in-memory sliding-window rate limiter (per API key hash + client IP)."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.core.config import get_settings

_lock = threading.Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _allow(key: str, *, max_events: int, window_seconds: float) -> bool:
    if max_events <= 0:
        return True
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and q[0] < now - window_seconds:
            q.popleft()
        if len(q) >= max_events:
            return False
        q.append(now)
        return True


def _client_ip(request: Request) -> str:
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _rate_limit_key(request: Request) -> str:
    raw_key = request.headers.get("X-API-KEY", "") or ""
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
    return f"{digest}:{_client_ip(request)}"


async def rate_limit_analyze(request: Request) -> None:
    cfg = get_settings()
    limit = cfg.rate_limit_analyze_per_minute
    if limit <= 0:
        return
    if not _allow(
        _rate_limit_key(request),
        max_events=limit,
        window_seconds=60.0,
    ):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Try again later.",
        )
