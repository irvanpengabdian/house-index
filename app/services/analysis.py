"""Orchestrate validation → preprocess → vision → parse → Pydantic."""

from __future__ import annotations

import logging

from fastapi import HTTPException, UploadFile
from openai import APITimeoutError, APIStatusError, RateLimitError

from app.core.config import Settings, get_settings, require_openai_key
from app.models.house_index import HouseIndexAnalysis
from app.services.image_processing import read_and_validate_upload, strip_exif_resize_to_jpeg
from app.services.json_parser import extract_json_object
from app.services.openai_vision import analyze_images_b64_jpeg
from app.services.prompts import get_system_prompt

logger = logging.getLogger(__name__)


async def analyze_house_photos(
    *,
    student_id: str,
    files: list[UploadFile],
    settings: Settings | None = None,
) -> HouseIndexAnalysis:
    cfg = settings or get_settings()

    sid = student_id.strip()
    if not sid:
        raise HTTPException(status_code=400, detail="student_id is required")

    n = len(files)
    if n < cfg.min_images_per_request:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Minimal {cfg.min_images_per_request} foto diperlukan; "
                f"diterima {n}."
            ),
        )
    if n > cfg.max_images_per_request:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Maksimal {cfg.max_images_per_request} foto per permintaan; "
                f"diterima {n}."
            ),
        )

    try:
        require_openai_key(cfg)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    jpegs: list[bytes] = []
    for upload in files:
        raw = await read_and_validate_upload(upload, max_bytes=cfg.max_image_bytes)
        jpeg = strip_exif_resize_to_jpeg(
            raw,
            max_side=cfg.max_image_side,
            jpeg_quality=cfg.jpeg_quality,
        )
        jpegs.append(jpeg)

    try:
        text = await analyze_images_b64_jpeg(
            settings=cfg,
            jpeg_bytes_list=jpegs,
            system_prompt=get_system_prompt(cfg),
        )
    except APITimeoutError as e:
        logger.warning("OpenAI timeout: %s", e)
        raise HTTPException(
            status_code=504,
            detail="AI service timed out. Retry later.",
        ) from e
    except RateLimitError as e:
        logger.warning("OpenAI rate limit: %s", e)
        raise HTTPException(
            status_code=429,
            detail="AI service rate limited. Retry later.",
        ) from e
    except APIStatusError as e:
        # Surface a concise reason for debugging integration (no secrets).
        status = int(getattr(e, "status_code", 502) or 502)
        msg = str(e)
        logger.warning("OpenAI APIStatusError status=%s msg=%s", status, msg)
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {msg}",
        ) from e
    except Exception as e:
        err = str(e).lower()
        if "timeout" in err or "timed out" in err:
            raise HTTPException(
                status_code=504,
                detail="AI service timed out. Retry later.",
            ) from e
        logger.exception("OpenAI vision call failed")
        raise HTTPException(
            status_code=502,
            detail="AI service error. Please retry.",
        ) from e

    try:
        data = extract_json_object(text)
    except (ValueError, TypeError) as e:
        logger.warning("Failed to parse JSON from model: %s", text[:500])
        raise HTTPException(
            status_code=502,
            detail="Invalid analysis response from model.",
        ) from e

    data["student_id"] = sid
    if data.get("materials") is None:
        data["materials"] = {}
    if data.get("wealth_proxies") is None:
        data["wealth_proxies"] = {}
    try:
        return HouseIndexAnalysis.model_validate(data)
    except Exception as e:
        logger.warning("Pydantic validation failed: %s data=%s", e, data)
        raise HTTPException(
            status_code=502,
            detail="Analysis response did not match expected schema.",
        ) from e
