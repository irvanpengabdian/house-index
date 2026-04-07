"""Image validation, EXIF stripping, and resize for token/cost control."""

from __future__ import annotations

import io
from typing import Final

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

_ALLOWED_MIME: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)


async def read_and_validate_upload(
    upload: UploadFile,
    *,
    max_bytes: int,
) -> bytes:
    if upload.content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {upload.content_type!r}. Use JPEG, PNG, or WebP.",
        )
    raw = await upload.read()
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Max {max_bytes} bytes.",
        )
    return raw


def strip_exif_resize_to_jpeg(
    image_bytes: bytes,
    *,
    max_side: int,
    jpeg_quality: int,
) -> bytes:
    """Strip metadata by re-encoding; normalize to RGB JPEG for vision API."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            im = ImageOps.exif_transpose(im)
            im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_side:
                scale = max_side / float(max(w, h))
                nw = max(1, int(w * scale))
                nh = max(1, int(h * scale))
                im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            im.save(
                out,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True,
            )
            return out.getvalue()
    except OSError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted image: {e}",
        ) from e
