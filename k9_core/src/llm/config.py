# src/llm/config.py

from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    """
    Configuración de infraestructura LLM para K9.

    - NO conoce nodos
    - NO conoce estado
    - SOLO define proveedores y credenciales
    """

    # -------------------------------------------------
    # Proveedor activo
    # -------------------------------------------------
    provider: Literal["mock", "gemini"] = Field(
        default="mock",
        description="Proveedor LLM activo"
    )

    # -------------------------------------------------
    # Gemini
    # -------------------------------------------------
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="API Key para Google Gemini"
    )

    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Modelo Gemini a utilizar"
    )

    # -------------------------------------------------
    # BaseSettings config
    # -------------------------------------------------
    model_config = {
        "env_prefix": "K9_",
        "case_sensitive": False,
    }
