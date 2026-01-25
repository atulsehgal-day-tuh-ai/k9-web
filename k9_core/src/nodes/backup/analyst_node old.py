from typing import Dict, Any, List, Tuple
from src.state.state import K9State


def _compute_k9_ranks_from_weekly_signals(weekly_signals: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """
    Deriva un ranking K9 (1 = mayor prioridad) a partir de avg_criticidad por riesgo.
    No interpreta: solo ordena un valor ya calculado por el engine.
    """
    items: List[Tuple[str, float]] = []
    for risk_id, data in weekly_signals.items():
        if risk_id.startswith("_"):
            continue
        avg_criticidad = float(data.get("avg_criticidad", 0) or 0)
        items.append((risk_id, avg_criticidad))

    # Mayor criticidad => mayor prioridad => rank más bajo (1)
    items.sort(key=lambda x: x[1], reverse=True)

    ranks: Dict[str, int] = {}
    for idx, (risk_id, _) in enumerate(items, start=1):
        ranks[risk_id] = idx
    return ranks


def analyst_node(state: K9State) -> K9State:
    """
    AnalystNode — K9 v3.2 (FINAL + refactor fino)

    Rol:
    - Interpretar hechos producidos por DataEngineNode (decisiones/juicios)
    - Razonamiento determinista
    - Juicios cognitivos (NO narrativa)
    - NO LLM
    - (v3.2) Centraliza priorización / recomendación / contrafactual => preventive_decision
    - (v3.2) Proporciona proactive_comparison completo para ProactiveModelNode
    """

    engine: Dict = state.analysis.get("engine", {})
    analysis: Dict[str, Any] = {}

    # =====================================================
    # 1. Periodo
    # =====================================================
    analysis["period"] = engine.get("period", {})

    # =====================================================
    # 2. Evolución temporal de riesgos
    # =====================================================
    risk_trajectories: Dict[str, Dict[str, Any]] = {}
    risk_trends = engine.get("risk_trends", {})

    for risk_id, data in risk_trends.items():
        if risk_id.startswith("_"):
            continue

        trend = data.get("trend_direction", "flat")
        temporal_state = (
            "degrading" if trend == "up"
            else "improving" if trend == "down"
            else "stable"
        )

        risk_trajectories[risk_id] = {
            "trend_direction": trend,
            "temporal_state": temporal_state
        }

    analysis["risk_trajectories"] = risk_trajectories

    # =====================================================
    # 3. Riesgo dominante vs relevante
    # =====================================================
    weekly_signals = engine.get("weekly_signals", {})

    dominant_risk = None
    relevant_risk = None
    max_criticidad = -1.0
    max_degradation_score = -1.0

    for risk_id, data in weekly_signals.items():
        if risk_id.startswith("_"):
            continue

        avg_criticidad = float(data.get("avg_criticidad", 0) or 0)

        if avg_criticidad > max_criticidad:
            max_criticidad = avg_criticidad
            dominant_risk = risk_id

        if risk_trajectories.get(risk_id, {}).get("temporal_state") == "degrading":
            if avg_criticidad > max_degradation_score:
                max_degradation_score = avg_criticidad
                relevant_risk = risk_id

    analysis["risk_summary"] = {
        "dominant_risk": dominant_risk,
        "relevant_risk": relevant_risk
    }

    # =====================================================
    # 4. Evidencia observacional (nivel alto)
    # =====================================================
    observations = engine.get("observations", {})
    obs_summary = observations.get("summary", {})
    total_obs = int(obs_summary.get("total", 0) or 0)
    by_type = obs_summary.get("by_type", {}) or {}

    observations_summary: Dict[str, Dict[str, Any]] = {}

    # Nota: esto replica tu comportamiento actual: no segmenta por riesgo.
    # Si luego quieres drill-down por riesgo, debe venir desde engine (no inventar aquí).
    for risk_id in risk_trajectories.keys():
        observations_summary[risk_id] = {
            "opg_count": int(by_type.get("OPG", 0) or 0),
            "occ_count": int(by_type.get("OCC", 0) or 0),
            "support_level": "none" if total_obs == 0 else "partial"
        }

    analysis["observations_summary"] = observations_summary

    # =====================================================
    # 5. Evidencia operacional — SÍNTESIS COGNITIVA
    # =====================================================
    # BUG FIX v3.2: antes leías desde `analysis` local (vacío). Aquí debe leerse desde state.analysis.
    operational_analysis = state.analysis.get("operational_analysis", {}) or {}
    evidence_by_risk = operational_analysis.get("evidence_by_risk", {}) or {}

    has_critical_control_failures = False
    supported_risks: List[str] = []

    for risk_id, evidence in evidence_by_risk.items():
        critical_controls = evidence.get("critical_controls_affected", []) or []
        occ_count = int(evidence.get("occ_count", 0) or 0)
        opg_count = int(evidence.get("opg_count", 0) or 0)

        if critical_controls:
            has_critical_control_failures = True

        if occ_count > 0 or opg_count > 1:
            supported_risks.append(risk_id)

    analysis["operational_evidence"] = {
        "has_critical_control_failures": has_critical_control_failures,
        "has_operational_support": len(supported_risks) > 0,
        "supported_risks": supported_risks,
        "summary": (
            "Operational evidence indicates control degradation."
            if has_critical_control_failures
            else "No critical control failures detected."
        )
    }

    # =====================================================
    # 6. Comparación Proactivo vs K9  (v3.2 — COMPLETA)
    # =====================================================
    # Fuente proactiva desde engine
    proactivo_engine = engine.get("proactivo", {}) or {}

    # Derivar ranking K9 desde weekly_signals (determinista, sin interpretación)
    k9_ranks = _compute_k9_ranks_from_weekly_signals(weekly_signals)

    proactive_comparison: Dict[str, Dict[str, Any]] = {}

    for risk_id, data in proactivo_engine.items():
        # esperamos avg_rank + weeks desde engine
        avg_rank_proactivo = data.get("avg_rank")
        weeks = data.get("weeks")

        # rank K9 (si no existe, queda None y alignment inconclusive)
        avg_rank_k9 = k9_ranks.get(risk_id)

        if avg_rank_proactivo is None or avg_rank_k9 is None:
            proactive_comparison[risk_id] = {
                "avg_rank_k9": avg_rank_k9,
                "avg_rank_proactivo": avg_rank_proactivo,
                "rank_delta": None,
                "weeks": weeks,
                "alignment_status": "inconclusive",
            }
            continue

        # Convención: rank más bajo = mayor prioridad
        # delta positivo => proactivo asigna menor prioridad (rank mayor) que K9 => subestima
        rank_delta = int(avg_rank_proactivo) - int(avg_rank_k9)

        if rank_delta >= 2:
            status = "underestimated_by_proactive"
        elif rank_delta <= -2:
            status = "overestimated_by_proactive"
        else:
            status = "aligned"

        proactive_comparison[risk_id] = {
            "avg_rank_k9": int(avg_rank_k9),
            "avg_rank_proactivo": int(avg_rank_proactivo),
            "rank_delta": int(rank_delta),
            "weeks": weeks,
            "alignment_status": status,
        }

    analysis["proactive_comparison"] = proactive_comparison

    # =====================================================
    # 7. Umbrales cognitivos
    # =====================================================
    thresholds = {}

    for risk_id, data in risk_trajectories.items():
        thresholds[risk_id] = {
            "threshold_state": (
                "approaching_threshold"
                if data["temporal_state"] == "degrading"
                else "below_threshold"
            )
        }

    analysis["thresholds"] = {
        "by_risk": thresholds
    }

    # =====================================================
    # 8. Evidencia de Auditorías (Capacidad 6)
    # =====================================================
    audits = engine.get("audits", {})
    daily_audits = audits.get("daily", {})

    total_audits = int(daily_audits.get("count", 0) or 0)
    by_tipo = daily_audits.get("by_tipo", {}) or {}
    by_origen = daily_audits.get("by_origen", {}) or {}

    if total_audits == 0:
        audit_pressure_level = "low"
    elif total_audits <= 3:
        audit_pressure_level = "medium"
    else:
        audit_pressure_level = "high"

    post_event_keywords = {"AUF", "REACTIVA", "POST_EVENTO"}
    has_post_event_audits = any(
        str(origen).upper() in post_event_keywords
        for origen in by_origen.keys()
    )

    analysis["audit_evidence"] = {
        "total_audits": total_audits,
        "audit_pressure_level": audit_pressure_level,
        "by_tipo": by_tipo,
        "by_origen": by_origen,
        "has_post_event_audits": has_post_event_audits,
        "role": "post_event_control_response",
        "interpretation": (
            "Post-event reactive audits indicating organizational response."
            if has_post_event_audits
            else "No post-event reactive audits detected."
        ),
    }

    # =====================================================
    # 9. Contexto FDO — Modulador cognitivo
    # =====================================================
    fdo = engine.get("fdo", {})
    fdo_12s = fdo.get("accumulated_12s", {})

    fdo_values = {
        k: v for k, v in fdo_12s.items()
        if isinstance(v, (int, float))
    }

    global_fdo_score = fdo_values.get("criticidad_global")

    if global_fdo_score is None:
        pressure_level = "unknown"
    elif global_fdo_score <= 30:
        pressure_level = "low"
    elif global_fdo_score <= 70:
        pressure_level = "medium"
    else:
        pressure_level = "high"

    dominant_factors = sorted(
        fdo_values.items(),
        key=lambda x: x[1],
        reverse=True
    )[:2]

    analysis["fdo_context"] = {
        "pressure_level": pressure_level,
        "dominant_factors": [f for f, _ in dominant_factors],
        "role": "operational_context_modulator",
        "interpretation": (
            "High operational pressure context modulating risk manifestation."
            if pressure_level == "high"
            else "Moderate operational pressure context."
            if pressure_level == "medium"
            else "Low operational pressure context."
        ),
    }

    # =====================================================
    # 10. Preventive Decision (v3.2) — PRIORIZACIÓN / RECOMENDACIÓN / CONTRAFACTUAL
    # =====================================================
    # Este bloque centraliza TODO lo que no debe vivir en Narrative:
    # - priorización
    # - recomendación preventiva
    # - escenarios contrafactuales
    preventive_decision = {
        "scenario": None,
        "prioritized_risks": [],
        "decision_basis": {},
        "recommendation": None,
    }

    # Universo base: dominant + relevant (sin límites artificiales; es "foco cognitivo", no filtro del sistema)
    allowed = set(filter(None, [dominant_risk, relevant_risk]))

    # Expansión contrafactual: si hay riesgos subestimados por proactivo, se agregan al universo de decisión
    underestimated = [
        r for r, info in proactive_comparison.items()
        if info.get("alignment_status") == "underestimated_by_proactive"
    ]
    for r in underestimated:
        allowed.add(r)

    candidates: List[Dict[str, Any]] = []
    for risk_id in allowed:
        ev = evidence_by_risk.get(risk_id, {}) or {}
        occ_count = int(ev.get("occ_count", 0) or 0)
        critical_controls = ev.get("critical_controls_affected", []) or []

        if occ_count > 0:
            candidates.append({
                "risk": risk_id,
                "occ_count": occ_count,
                "has_critical_controls": bool(critical_controls),
            })

    if candidates:
        # Priorización determinista: primero controles críticos, luego OCC
        candidates.sort(
            key=lambda x: (x["has_critical_controls"], x["occ_count"]),
            reverse=True,
        )
        prioritized = [c["risk"] for c in candidates]

        scenario = "preventive_watch"
        if any(r in underestimated for r in prioritized):
            scenario = "proactive_underestimation"

        preventive_decision.update({
            "scenario": scenario,
            "prioritized_risks": prioritized,
            "decision_basis": {
                "sources": ["operational_analysis", "proactive_comparison"],
                "criteria": ["critical_controls_affected", "occ_count", "alignment_status"],
                "universe": sorted(list(allowed)),
            },
            "recommendation": (
                "Priorizar vigilancia preventiva sobre los riesgos priorizados, "
                "dado soporte operacional activo y potencial desalineación del modelo proactivo."
                if scenario == "proactive_underestimation"
                else
                "Priorizar vigilancia preventiva sobre los riesgos con evidencia operacional activa."
            ),
        })

    analysis["preventive_decision"] = preventive_decision

    # =====================================================
    # Persistencia en estado
    # =====================================================
    state.analysis = {
        **state.analysis,
        **analysis
    }

    state.reasoning.append(
        "AnalystNode: razonamiento determinista aplicado sobre universo STDE completo "
        "(incluye proactive_comparison completo y preventive_decision decisional)."
    )

    return state
