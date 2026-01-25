from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """
    Settings for the K9 API service.

    Notes:
    - K9 LLM credentials/provider are configured via `k9_core/src/llm/config.py` (env prefix: K9_).
    - This config is only for the API runtime concerns.
    """

    # Where is the copied K9 core folder relative to this backend?
    # Default assumes repo layout:
    #   k9_web/
    #     k9_backend/app/...
    #     k9_core/...
    # From `k9_backend/app/` to `k9_core/` in the default repo layout
    k9_core_dir: str = Field(default="../../k9_core", description="Path to k9_core directory")

    # API server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # CORS (comma-separated list)
    allowed_origins: str = Field(default="*", description="CORS origins, comma-separated or '*'")

    model_config = {
        "env_prefix": "K9API_",
        "case_sensitive": False,
    }


def parse_origins(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

