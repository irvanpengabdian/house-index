"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI

from app.api.v1.analyze import router as analyze_router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

_settings = get_settings()
_docs = "/docs" if _settings.docs_enabled else None
_redoc = "/redoc" if _settings.docs_enabled else None

app = FastAPI(
    title="House Indexing AI Gateway",
    description="Middleware API untuk analisis indeks rumah (Simaster UGM).",
    version="0.1.0",
    docs_url=_docs,
    redoc_url=_redoc,
)

app.include_router(analyze_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
