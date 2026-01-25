from typing import Dict, List
import pandas as pd

from src.data.data_manager import DataManager
from src.state.state import K9State

# 🔒 Contrato operativo (el único que el core conoce)
from src.time.data_slice import DataSlice

# 🔒 Resolución temporal determinista
from src.time.time_resolution import TimeResolutionLayer
from src.time.dataset_metadata import DatasetTimeMetadata


# =====================================================
# Helpers
# =====================================================

def _trend_direction(values: List[float]) -> str:
    if not values or len(values) < 2:
        return "flat"
    if values[-1] > values[0]:
        return "up"
    if values[-1] < values[0]:
        return "down"
    return "flat"


# =====================================================
# DataEngineNode
# =====================================================

def data_engine_node(state: K9State) -> K9State:
    """
    DataEngineNode — FASE 2 (infraestructura cerrada)

    Rol:
    - Convertir data sintética STDE en hechos analíticos estructurados
    - NO narrativa
    - NO decisiones cognitivas finales
    - Consume DataSlice si existe
    """

    dm = DataManager("data/synthetic")
    engine_analysis: Dict = {}

    # =====================================================
    # 🔑 BLOQUE 0 — Resolución temporal CANÓNICA (ÚNICO PUNTO)
    # =====================================================

    if state.data_slice is None and state.time_context is not None:
        df_meta = dm.get_trayectorias_semanales()

        if "semana" not in df_meta.columns:
            raise KeyError(
                "DataEngineNode: 'semana' column required to resolve temporal metadata."
            )

        total_periods = int(df_meta["semana"].nunique())

        metadata = DatasetTimeMetadata(
            min_date=str(df_meta["semana"].min()),
            max_date=str(df_meta["semana"].max()),
            granularity="week",
            total_periods=total_periods,
        )

        resolver = TimeResolutionLayer()
        state.data_slice = resolver.resolve(
            time_ctx=state.time_context,
            metadata=metadata,
        )

        state.reasoning.append(
            f"DataEngineNode: DataSlice resolved from TimeContext → {state.data_slice}"
        )

    # =====================================================
    # Bloque 1 — Periodo + Trayectorias semanales
    # =====================================================

    df_tray = dm.get_trayectorias_semanales()
    weeks = sorted(df_tray["semana"].unique().tolist())

    engine_analysis["period"] = {
        "min_week": weeks[0],
        "max_week": weeks[-1],
        "weeks": weeks,
    }

    engine_analysis["trajectories"] = {
        "weekly": {},
        "meta": {
            "semantic_level": "cognitive",
            "source": "stde_trayectorias_semanales.csv",
        },
    }

    weekly_trends = {}

    risk_columns = [
        c for c in df_tray.columns
        if c.startswith("criticidad_")
        and c.endswith("_media")
        and c != "criticidad_global_media"
    ]

    for col in risk_columns:
        risk_id = col.replace("criticidad_", "").replace("_media", "")
        values = df_tray.sort_values("semana")[col].tolist()

        weekly_trends[risk_id] = {
            "values": values,
            "trend_direction": _trend_direction(values),
        }

        engine_analysis["trajectories"]["weekly"][risk_id] = weekly_trends[risk_id]

    engine_analysis["risk_trends"] = {
        **weekly_trends,
        "_meta": {
            "semantic_level": "cognitive",
            "source": "stde_trayectorias_semanales.csv",
        },
    }

    # =====================================================
    # Bloque 2 — Señales semanales K9
    # =====================================================

    df_signals = dm.get_weekly_signals()
    engine_analysis["weekly_signals"] = {}

    for riesgo_id in engine_analysis["trajectories"]["weekly"].keys():
        df_r = df_signals[df_signals["riesgo_id"] == riesgo_id]
        if df_r.empty:
            continue

        engine_analysis["weekly_signals"][riesgo_id] = {
            "avg_criticidad": float(df_r["criticidad_media"].mean()),
            "avg_rank_pos": float(df_r["rank_pos"].mean()),
            "top3_weeks": int(df_r["is_top3"].sum()),
            "weeks_considered": int(df_r["semana"].nunique()),
        }

    # =====================================================
    # Bloque 3 — Observaciones (OPG / OCC)
    # =====================================================

    df_obs = dm.get_observaciones_all()

    if "semana" not in df_obs.columns:
        raise KeyError(
            "DataEngineNode: 'semana' column required for temporal slicing."
        )

    # 🔒 ORDEN CANÓNICO OBLIGATORIO
    df_obs = df_obs.sort_values("semana").reset_index(drop=True)

    data_slice: DataSlice | None = state.data_slice

    if data_slice and data_slice.is_index_slice():
        # DataSlice indices refer to PERIOD indices (weeks), not dataframe rows
        weeks_all = sorted(df_obs["semana"].unique().tolist())

        # Guardrails estrictos (sin defaults silenciosos)
        if data_slice.start is None or data_slice.end is None:
            raise ValueError(
                "DataEngineNode: INDEX DataSlice requires start and end."
            )

        if (
            data_slice.start < 0
            or data_slice.end > len(weeks_all)
            or data_slice.start >= data_slice.end
        ):
            raise ValueError(
                f"DataEngineNode: invalid DataSlice range "
                f"{data_slice.start}:{data_slice.end} "
                f"for total_weeks={len(weeks_all)}."
            )

        weeks_selected = weeks_all[data_slice.start : data_slice.end]

        df_obs = (
            df_obs[df_obs["semana"].isin(weeks_selected)]
            .reset_index(drop=True)
        )

        state.reasoning.append(
            "DataEngineNode: observaciones filtradas por semana "
            f"(weeks={weeks_selected}, slice={data_slice.start}:{data_slice.end})."
        )
    else:
        state.reasoning.append(
            "DataEngineNode: observaciones sin restricción (FULL DataSlice)."
        )


    engine_analysis["observations"] = {
        "summary": {
            "total": int(len(df_obs)),
            "by_type": {
                t: int(len(df_obs[df_obs["tipo_observacion"] == t]))
                for t in ["OPG", "OCC"]
            },
        }
    }

    # =====================================================
    # Bloques restantes — SIN CAMBIOS
    # =====================================================

    df_aud = dm.get_auditorias()
    df_aud_12s = dm.get_auditorias_12s()

    engine_analysis["audits"] = {
        "daily": {
            "count": int(len(df_aud)),
            "by_tipo": (
                df_aud["tipo_auditoria"].value_counts().to_dict()
                if "tipo_auditoria" in df_aud.columns else {}
            ),
            "by_origen": (
                df_aud["origen"].value_counts().to_dict()
                if "origen" in df_aud.columns else {}
            ),
        },
        "accumulated_12s": {
            "records": df_aud_12s.to_dict(orient="list"),
        },
        "meta": {
            "semantic_level": "operational+cognitive",
            "source": [
                "stde_auditorias.csv",
                "stde_auditorias_12s.csv",
            ],
        },
    }

    # =====================================================
    # Persistencia en estado
    # =====================================================

    state.analysis = state.analysis or {}
    state.analysis["engine"] = engine_analysis

    state.reasoning.append(
        "DataEngineNode: análisis STDE generado respetando DataSlice."
    )

    return state
