# src/time/time_resolution.py
from __future__ import annotations

from src.time.time_context import TimeContext
from src.time.data_slice import DataSlice
from src.time.dataset_metadata import DatasetTimeMetadata


class TimeResolutionLayer:
    """
    Traduce TimeContext (semántico) → DataSlice (operativo).

    Responsabilidad ÚNICA:
    - Resolver rangos físicos (índices) a partir de un contexto temporal canónico.

    NO:
    - Analiza datos
    - Filtra DataFrames
    - Conoce nodos
    - Conoce LLM
    """

    def resolve(
        self,
        time_ctx: TimeContext | None,
        metadata: DatasetTimeMetadata,
    ) -> DataSlice:

        # ---------------------------------
        # Caso 0 — Sin contexto temporal
        # ---------------------------------
        if time_ctx is None:
            return DataSlice(resolution="FULL")

        # ---------------------------------
        # Casos RELATIVE
        # ---------------------------------
        if time_ctx.type == "RELATIVE":
            value = time_ctx.value
            total = metadata.total_periods

            if value == "CURRENT_WEEK":
                return DataSlice(
                    resolution="INDEX",
                    start=max(total - 1, 0),
                    end=total,
                )

            if value == "LAST_WEEK":
                return DataSlice(
                    resolution="INDEX",
                    start=max(total - 2, 0),
                    end=max(total - 1, 0),
                )

            if value == "LAST_2_WEEKS":
                return DataSlice(
                    resolution="INDEX",
                    start=max(total - 2, 0),
                    end=total,
                )

            if value == "LAST_4_WEEKS":
                return DataSlice(
                    resolution="INDEX",
                    start=max(total - 4, 0),
                    end=total,
                )

            if value == "LAST_MONTH":
                # Asumimos 4 semanas como contrato físico
                return DataSlice(
                    resolution="INDEX",
                    start=max(total - 4, 0),
                    end=total,
                )

        # ---------------------------------
        # Casos WINDOW (evento ancla)
        # ---------------------------------
        if time_ctx.type == "WINDOW":
            value = time_ctx.value

            # ⚠️ Este layer NO resuelve anchors
            raise NotImplementedError(
                f"WINDOW '{value}' requiere anchor resuelto previamente "
                f"(fuera de TimeResolutionLayer)."
            )

        # ---------------------------------
        # Casos ANCHOR (no resolubles aquí)
        # ---------------------------------
        if time_ctx.type == "ANCHOR":
            raise NotImplementedError(
                "ANCHOR TimeContext debe resolverse antes de TimeResolutionLayer."
            )

        # ---------------------------------
        # Fallback defensivo
        # ---------------------------------
        raise ValueError(
            f"TimeResolutionLayer: TimeContext no soportado: {time_ctx}"
        )
