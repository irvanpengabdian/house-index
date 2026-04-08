"""Environment-driven settings (no secrets in code)."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator


class Settings(BaseModel):
    openai_api_key: str = Field(default="", description="OpenAI API key from OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o")
    simaster_api_key: str = Field(
        default="",
        description="Internal API key for Simaster clients (SIMASTER_API_KEY)",
    )
    request_timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0)
    max_image_bytes: int = Field(default=10 * 1024 * 1024)
    max_image_side: int = Field(default=2048, ge=512, le=4096)
    jpeg_quality: int = Field(default=85, ge=60, le=95)
    min_images_per_request: int = Field(default=1, ge=1, le=20)
    max_images_per_request: int = Field(default=5, ge=1, le=20)
    system_prompt_file: str = Field(
        default="config/system_prompt.txt",
        description="Path to system prompt text file (relative to repo root or absolute)",
    )
    max_decoded_pixels: int = Field(
        default=40_000_000,
        ge=1_000_000,
        le=200_000_000,
        description="Reject decoded images exceeding width*height (decompression bomb mitigation)",
    )
    rate_limit_analyze_per_minute: int = Field(
        default=60,
        ge=0,
        le=10_000,
        description="Max /api/v1/analyze calls per minute per X-API-KEY hash + IP; 0 disables",
    )
    docs_enabled: bool = Field(
        default=True,
        description="Expose /docs and /redoc (disable in production)",
    )

    @model_validator(mode="after")
    def check_image_limits(self) -> Settings:
        if self.min_images_per_request > self.max_images_per_request:
            raise ValueError(
                "min_images_per_request must be <= max_images_per_request"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    model_raw = os.getenv("OPENAI_MODEL", "gpt-4o").strip()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=model_raw or "gpt-4o",
        simaster_api_key=os.getenv("SIMASTER_API_KEY", "").strip(),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        max_image_bytes=int(os.getenv("MAX_IMAGE_BYTES", str(10 * 1024 * 1024))),
        max_image_side=int(os.getenv("MAX_IMAGE_SIDE", "2048")),
        jpeg_quality=int(os.getenv("JPEG_QUALITY", "85")),
        min_images_per_request=int(os.getenv("MIN_IMAGES_PER_REQUEST", "1")),
        max_images_per_request=int(os.getenv("MAX_IMAGES_PER_REQUEST", "5")),
        system_prompt_file=(
            os.getenv("SYSTEM_PROMPT_FILE", "config/system_prompt.txt").strip()
            or "config/system_prompt.txt"
        ),
        max_decoded_pixels=int(os.getenv("MAX_DECODED_PIXELS", "40000000")),
        rate_limit_analyze_per_minute=int(
            os.getenv("RATE_LIMIT_ANALYZE_PER_MINUTE", "60")
        ),
        docs_enabled=os.getenv("DOCS_ENABLED", "true").strip().lower()
        not in ("0", "false", "no", "off"),
    )


def require_openai_key(settings: Settings) -> str:
    if not settings.openai_api_key:
        msg = "OPENAI_API_KEY is not set. Configure .env before calling analyze."
        raise RuntimeError(msg)
    return settings.openai_api_key


def require_simaster_key(settings: Settings) -> str:
    if not settings.simaster_api_key:
        msg = "SIMASTER_API_KEY is not set. Configure .env before exposing the API."
        raise RuntimeError(msg)
    return settings.simaster_api_key
