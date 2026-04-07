"""OpenAI GPT-4o vision call."""

from __future__ import annotations

import base64
import logging

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

from app.core.config import Settings

logger = logging.getLogger(__name__)


def _user_message_text(num_images: int) -> str:
    if num_images <= 1:
        return (
            "Analisis foto rumah berikut dan kembalikan SATU objek JSON sesuai instruksi sistem."
        )
    return (
        f"Berikut ada {num_images} foto dari satu rumah yang sama. "
        "Gabungkan informasi dari semua foto menjadi SATU objek JSON sesuai instruksi sistem."
    )


async def analyze_images_b64_jpeg(
    *,
    settings: Settings,
    jpeg_bytes_list: list[bytes],
    system_prompt: str,
) -> str:
    """Send one or more JPEG images in a single user message; return assistant text."""
    if not jpeg_bytes_list:
        raise ValueError("jpeg_bytes_list must not be empty")

    key = settings.openai_api_key
    content: list[dict[str, object]] = [
        {"type": "text", "text": _user_message_text(len(jpeg_bytes_list))},
    ]
    for jpeg_bytes in jpeg_bytes_list:
        b64 = base64.standard_b64encode(jpeg_bytes).decode("ascii")
        data_url = f"data:image/jpeg;base64,{b64}"
        content.append(
            {"type": "image_url", "image_url": {"url": data_url, "detail": "auto"}},
        )

    client = AsyncOpenAI(
        api_key=key,
        timeout=settings.request_timeout_seconds,
        max_retries=1,
    )

    try:
        completion = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
    except APITimeoutError as e:
        logger.warning("OpenAI request timed out: %s", e)
        raise
    except APIStatusError as e:
        # Contains HTTP status + provider error payload (safe to log server-side).
        logger.warning("OpenAI status error %s: %s", getattr(e, "status_code", None), e)
        raise
    except APIConnectionError as e:
        logger.warning("OpenAI connection error: %s", e)
        raise
    except RateLimitError as e:
        logger.warning("OpenAI rate limit: %s", e)
        raise

    choice = completion.choices[0]
    text = choice.message.content
    if not text:
        raise ValueError("Empty completion content from model")
    return text


async def analyze_image_b64_jpeg(
    *,
    settings: Settings,
    jpeg_bytes: bytes,
    system_prompt: str,
) -> str:
    """Send one image (JPEG bytes) to chat completions; return assistant message text."""
    return await analyze_images_b64_jpeg(
        settings=settings,
        jpeg_bytes_list=[jpeg_bytes],
        system_prompt=system_prompt,
    )
