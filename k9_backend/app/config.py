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

    # Neo4j (Knowledge Graph)
    # Leave uri empty to disable Neo4j integration (demo can still run without KG).
    neo4j_uri: str = Field(default="", description="Neo4j URI, e.g. bolt://localhost:7687 or neo4j+s://...")
    neo4j_username: str = Field(default="", description="Neo4j username")
    neo4j_password: str = Field(default="", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database name")

    model_config = {
        "env_prefix": "K9API_",
        "case_sensitive": False,
    }

    @property
    def neo4j_enabled(self) -> bool:
        return bool(self.neo4j_uri and self.neo4j_username and self.neo4j_password)


def parse_origins(raw: str) -> list[str]:
    raw = (raw or "").strip()
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

