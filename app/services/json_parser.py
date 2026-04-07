"""Extract a single JSON object from model text (handles ```json fences)."""

from __future__ import annotations

import json
import re
from typing import Any


_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse first JSON object from model output."""
    s = text.strip()
    m = _JSON_FENCE.search(s)
    if m:
        s = m.group(1).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    chunk = s[start : end + 1]
    return json.loads(chunk)
