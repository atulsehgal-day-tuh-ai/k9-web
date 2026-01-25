# src/llm/json_utils.py
from __future__ import annotations

import json
import re
from typing import Dict, Optional, Tuple


def strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_object(text: str) -> Optional[str]:
    """
    Extract the first JSON object substring from model output.
    """
    text = strip_code_fences(text)
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return None


def safe_json_loads(raw: str) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        return json.loads(raw), None
    except Exception as e:
        return None, str(e)
