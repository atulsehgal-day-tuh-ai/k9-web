# src/time/data_slice.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal


@dataclass(frozen=True)
class DataSlice:
    """
    DataSlice — Contrato operativo mínimo para el core.

    Define QUÉ subconjunto físico de datos debe consumirse.
    - NO interpreta tiempo
    - NO conoce fechas
    - NO conoce semántica
    - SOLO expresa un corte físico ejecutable

    El core SOLO opera sobre este objeto.
    """

    # Tipo de resolución física del corte
    resolution: Literal[
        "FULL",   # dataset completo
        "INDEX",  # corte por índice (Python slicing semantics)
    ] = "FULL"

    # Límites físicos del slice (semánticamente opacos)
    # Convención: start incluido, end excluido (igual que iloc)
    start: Optional[int] = None
    end: Optional[int] = None

    # -----------------------------
    # Predicados operativos
    # -----------------------------

    def is_full(self) -> bool:
        return self.resolution == "FULL"

    def is_index_slice(self) -> bool:
        return self.resolution == "INDEX"

    # -----------------------------
    # Validación defensiva mínima
    # -----------------------------

    def validate(self) -> None:
        if self.resolution == "INDEX":
            if self.start is None or self.end is None:
                raise ValueError(
                    "DataSlice INDEX requires both start and end indices."
                )
            if self.start < 0 or self.end < 0:
                raise ValueError(
                    "DataSlice indices must be non-negative."
                )
            if self.start >= self.end:
                raise ValueError(
                    "DataSlice start index must be < end index."
                )

    # -----------------------------
    # Representación estable
    # -----------------------------

    def __repr__(self) -> str:
        if self.is_full():
            return "DataSlice(FULL)"
        return f"DataSlice(INDEX, start={self.start}, end={self.end})"
