"""Authentication dependencies for internal clients (Simaster)."""

from __future__ import annotations

import secrets

from fastapi import Depends, Header, HTTPException

from app.core.config import get_settings, require_simaster_key


def require_simaster_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-KEY"),
) -> None:
    settings = get_settings()
    try:
        expected = require_simaster_key(settings)
    except RuntimeError as e:
        # Misconfiguration: do not silently allow unauthenticated access.
        raise HTTPException(status_code=503, detail=str(e)) from e

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY")

    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=403, detail="Invalid X-API-KEY")


SimasterAuthDep = Depends(require_simaster_api_key)

