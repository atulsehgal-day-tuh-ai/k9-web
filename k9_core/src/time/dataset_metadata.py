# src/time/dataset_metadata.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetTimeMetadata:
    """
    Describe el dominio temporal del dataset, sin exponer datos.

    Permite resolver rangos sin hardcodear semanas, fechas ni simulaciones.
    """

    min_date: str
    max_date: str
    granularity: str  # day | week | month
    total_periods: int
