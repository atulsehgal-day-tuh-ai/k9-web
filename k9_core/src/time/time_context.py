# src/time/time_context.py

from pydantic import BaseModel, Field, validator
from typing import Literal


class TimeContext(BaseModel):
    """
    TimeContext — Contrato temporal canónico de K9.

    Rol:
    - Representar explícitamente la intención temporal del usuario
    - Ser creado SOLO por el Router
    - NO resolver fechas
    - NO cortar datasets
    - NO conocer el calendario ni la STDE

    Este objeto es semántico, no operativo.
    """

    # Tipo de tiempo solicitado
    type: Literal[
        "RELATIVE",   # ej: LAST_WEEK, LAST_4_WEEKS
        "WINDOW",     # ej: PRE, POST, PRE_POST
        "ANCHOR",     # ej: CRITICAL_MONDAY
        "ABSOLUTE",   # ej: fechas explícitas (futuro)
    ]

    # Valor canónico asociado al tipo
    value: str = Field(
        ...,
        description="Valor temporal canónico validado por el Router",
    )

    # Nivel de certeza del tiempo
    confidence: Literal[
        "EXPLICIT",   # el usuario lo dijo
        "INFERRED",   # default aplicado por el sistema
    ] = "EXPLICIT"

    # -----------------------------
    # Validaciones mínimas
    # -----------------------------

    @validator("value")
    def value_must_not_be_empty(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("TimeContext.value must be a non-empty string")
        return v

    def is_explicit(self) -> bool:
        """Indica si el tiempo fue definido explícitamente por el usuario."""
        return self.confidence == "EXPLICIT"

    def is_inferred(self) -> bool:
        """Indica si el tiempo fue inferido por default del sistema."""
        return self.confidence == "INFERRED"

    def __repr__(self) -> str:
        return (
            f"TimeContext(type={self.type}, "
            f"value={self.value}, "
            f"confidence={self.confidence})"
        )
