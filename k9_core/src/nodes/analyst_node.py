# src/nodes/analyst_node.py

from typing import Dict, Any, List, Tuple
from src.state.state import K9State


def _compute_k9_ranks_from_weekly_signals(
    weekly_signals: Dict[str, Dict[str, Any]]
) -> Dict[str, int]:
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

    items.sort(key=lambda x: x[1], reverse=True)

    ranks: Dict[str, int] = {}
    for idx, (risk_id, _) in enumerate(items, start=1):
        ranks[risk_id] = idx
    return ranks


def analyst_node(state: K9State) -> K9State:
    """
    AnalystNode — K9 v3.2 (CANONICAL)

    Rol:
    - Razonamiento determinista sobre resultados ya calculados
    - Comparaciones explícitas
    - Priorización derivada
    - NO narrativa
    - NO lenguaje natural
    """

    # =====================================================
    # 0. GATING K9 — ejecución SOLO si corresponde
    # =====================================================
    # Prefer canonical K9 command
    command = state.k9_command or (state.context_bundle or {}).get("k9_command")

    if not command:
        state.reasoning.append(
            "AnalystNode: skipped (no K9 command present)."
        )
        return state

    intent = command.get("intent")

    if intent not in {
        "ANALYTICAL_QUERY",
        "COMPARATIVE_QUERY",
        "TEMPORAL_RELATION_QUERY",
    }:
        state.reasoning.append(
            f"AnalystNode: skipped (intent={intent})."
        )
        return state

    # =====================================================
    # 1. Fuentes de análisis
    # =====================================================
    if state.analysis is None:
        state.analysis = {}

    engine: Dict[str, Any] = state.analysis.get("engine", {})
    analysis: Dict[str, Any] = {}

    # -----------------------------------------------------
    # Guard: requiere engine como mínimo
    # -----------------------------------------------------
    if not engine:
        state.reasoning.append(
            "AnalystNode: skipped (missing engine input)."
        )
        return state

    has_operational = "operational_analysis" in state.analysis
    analysis_mode = "evidence_based" if has_operational else "structural"

    analysis["analysis_mode"] = analysis_mode
    analysis["analysis_basis"] = (
        "engine_plus_operational" if has_operational else "engine_only"
    )

    
    # =====================================================
    # 2. Periodo
    # =====================================================
    analysis["period"] = engine.get("period", {})

    # =====================================================
    # 3. Evolución temporal de riesgos
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
            "temporal_state": temporal_state,
        }

    analysis["risk_trajectories"] = risk_trajectories

    # =====================================================
    # 4. Riesgo dominante vs relevante
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
        "relevant_risk": relevant_risk,
    }

    # =====================================================
    # 5. Evidencia operacional (síntesis)
    # =====================================================
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
        "has_operational_support": bool(supported_risks),
        "supported_risks": supported_risks,
    }

    # =====================================================
    # 6. Comparación Proactivo vs K9
    # =====================================================
    proactivo_engine = engine.get("proactivo", {}) or {}
    k9_ranks = _compute_k9_ranks_from_weekly_signals(weekly_signals)

    proactive_comparison: Dict[str, Dict[str, Any]] = {}

    for risk_id, data in proactivo_engine.items():
        avg_rank_proactivo = data.get("avg_rank")
        weeks = data.get("weeks")
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
    # 7. Persistencia
    # =====================================================
    state.analysis = {
        **state.analysis,
        **analysis,
    }

    state.reasoning.append(
        "AnalystNode: deterministic reasoning executed (K9 canonical)."
    )

    return state
