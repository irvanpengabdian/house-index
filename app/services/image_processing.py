"""Image validation, EXIF stripping, and resize for token/cost control."""

from __future__ import annotations

import io
from typing import Final

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

_ALLOWED_MIME: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)


def _detect_format_from_magic(data: bytes) -> str | None:
    """Return canonical MIME if magic bytes match JPEG/PNG/WebP."""
    if len(data) < 12:
        return None
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


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
    magic_mime = _detect_format_from_magic(raw)
    if magic_mime is None:
        raise HTTPException(
            status_code=415,
            detail="File content is not a valid JPEG, PNG, or WebP image.",
        )
    if magic_mime != upload.content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type does not match file content (signature mismatch).",
        )
    return raw


def strip_exif_resize_to_jpeg(
    image_bytes: bytes,
    *,
    max_side: int,
    jpeg_quality: int,
    max_decoded_pixels: int,
) -> bytes:
    """Strip metadata by re-encoding; normalize to RGB JPEG for vision API."""
    old_limit = Image.MAX_IMAGE_PIXELS
    try:
        Image.MAX_IMAGE_PIXELS = max_decoded_pixels
        with Image.open(io.BytesIO(image_bytes)) as im:
            im.load()
            w, h = im.size
            if w * h > max_decoded_pixels:
                raise HTTPException(
                    status_code=413,
                    detail="Image has too many pixels (possible decompression bomb).",
                )
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
    except HTTPException:
        raise
    except Image.DecompressionBombError as e:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds maximum allowed pixel count.",
        ) from e
    except OSError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or corrupted image: {e}",
        ) from e
    finally:
        Image.MAX_IMAGE_PIXELS = old_limit
