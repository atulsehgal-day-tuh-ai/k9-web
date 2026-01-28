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


def _apply_critical_monday_overlay(df_tray: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the synthetic 'Critical Monday' scenario by appending/updating a new week row
    using `stde_riesgos_evento_lunes_critico.csv`.

    Notes:
    - Scenario file expresses criticidad on a 0–100 scale; we normalize to 0–1.
    - We keep other risks unchanged for the injected week unless explicitly provided.
    """
    event_path = Path("data/synthetic/stde_riesgos_evento_lunes_critico.csv")
    if not event_path.exists():
        return df_tray

    df_evt = pd.read_csv(event_path)
    if df_evt.empty:
        return df_tray

    required = {"semana", "id_riesgo", "criticidad_real_lunes_critico"}
    if not required.issubset(set(df_evt.columns)):
        return df_tray

    # Build / update one injected week row at a time (small dataset, deterministic)
    out = df_tray.copy()
    risk_cols = [c for c in out.columns if c.startswith("criticidad_") and c.endswith("_media") and c != "criticidad_global_media"]

    for _, row in df_evt.iterrows():
        try:
            week = int(row["semana"])
        except Exception:
            continue
        risk_id = str(row["id_riesgo"]).strip()
        if not risk_id:
            continue
        target_col = f"criticidad_{risk_id}_media"
        if target_col not in out.columns:
            continue

        try:
            criticidad_01 = float(row["criticidad_real_lunes_critico"]) / 100.0
        except Exception:
            continue

        if (out["semana"] == week).any():
            out.loc[out["semana"] == week, target_col] = criticidad_01
        else:
            # start from last known week row (keeps other risks stable)
            base = out.sort_values("semana").iloc[-1].to_dict()
            base["semana"] = week
            base[target_col] = criticidad_01

            # recompute global media if present
            if "criticidad_global_media" in out.columns and risk_cols:
                base["criticidad_global_media"] = float(
                    sum(float(base.get(c, 0) or 0) for c in risk_cols) / float(len(risk_cols))
                )

            out = pd.concat([out, pd.DataFrame([base])], ignore_index=True)

    return out.sort_values("semana").reset_index(drop=True)


def _compute_weekly_signals_from_trajectories(df_tray: pd.DataFrame) -> Dict[str, Dict]:
    """
    Recompute weekly_signals from `stde_trayectorias_semanales.csv` style data.
    Used for scenario overlay so injected week participates in dominance ranking.
    """
    risk_cols = [c for c in df_tray.columns if c.startswith("criticidad_") and c.endswith("_media") and c != "criticidad_global_media"]
    risks = [c.replace("criticidad_", "").replace("_media", "") for c in risk_cols]

    # rank per week (1 = highest criticidad)
    df_sorted = df_tray.sort_values("semana").reset_index(drop=True)
    ranks_by_risk: Dict[str, List[int]] = {rid: [] for rid in risks}

    for _, row in df_sorted.iterrows():
        vals = []
        for rid in risks:
            col = f"criticidad_{rid}_media"
            vals.append((rid, float(row.get(col, 0) or 0)))
        vals.sort(key=lambda x: x[1], reverse=True)
        for pos, (rid, _) in enumerate(vals, start=1):
            ranks_by_risk[rid].append(pos)

    signals: Dict[str, Dict] = {}
    for rid in risks:
        col = f"criticidad_{rid}_media"
        values = [float(v) for v in df_sorted[col].tolist()]
        if not values:
            continue
        rp = ranks_by_risk.get(rid, [])
        signals[rid] = {
            "avg_criticidad": float(sum(values) / len(values)),
            "avg_rank_pos": float(sum(rp) / len(rp)) if rp else None,
            "top3_weeks": int(sum(1 for x in rp if x <= 3)),
            "weeks_considered": int(len(values)),
        }
    return signals


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
    if isinstance(state.active_event, dict) and state.active_event.get("type") == "CRITICAL_MONDAY":
        df_tray = _apply_critical_monday_overlay(df_tray)
        state.reasoning.append("DataEngineNode: applied CRITICAL_MONDAY overlay to weekly trajectories.")
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

    if isinstance(state.active_event, dict) and state.active_event.get("type") == "CRITICAL_MONDAY":
        engine_analysis["weekly_signals"] = _compute_weekly_signals_from_trajectories(df_tray)
        state.reasoning.append("DataEngineNode: weekly_signals recomputed from trajectories for CRITICAL_MONDAY.")
    else:
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
