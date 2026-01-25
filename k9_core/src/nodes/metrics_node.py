from typing import Dict, Any, List
from src.state.state import K9State


def metrics_node(state: K9State) -> K9State:
    """
    MetricsNode v0.4 (v0.3 PRESERVADA)

    Rol:
    - Materializar métricas deterministas a partir de analysis consolidado
    - Construir rankings, series temporales y tablas básicas
    - Sugerir visualizaciones SOLO bajo reglas explícitas
    - NO interpretar, NO priorizar, NO generar narrativa

    Principio rector:
    "MetricsNode no busca convencer; busca hacer visible."
    """

    # --------------------------------------------------
    # Guard clause
    # --------------------------------------------------
    if not state.analysis:
        state.reasoning.append(
            "MetricsNode: analysis no disponible, no se generan métricas."
        )
        return state

    analysis = state.analysis

    metrics: Dict[str, Any] = {
        "rankings": {},
        "time_series": {},
        "tables": {},
        "visual_suggestions": [],
    }

    # ==================================================
    # 1. Rankings métricos (sin interpretación)
    # ==================================================
    risk_summary = analysis.get("risk_summary")
    if risk_summary:
        metrics["rankings"]["risks_by_role"] = {
            "dominant_risk": risk_summary.get("dominant_risk"),
            "relevant_risk": risk_summary.get("relevant_risk"),
        }

    # ==================================================
    # 2. Series temporales
    # ==================================================
    risk_trajectories = analysis.get("risk_trajectories")
    if isinstance(risk_trajectories, dict) and risk_trajectories:
        metrics["time_series"]["risk_trajectories"] = risk_trajectories

    # ==================================================
    # 3. Tablas operacionales básicas
    # ==================================================
    # ⚠️ CAMBIO CLAVE:
    # La evidencia operacional YA NO viene del Analyst.
    # Viene del OperationalAnalysisNode.
    # ==================================================

    operational_analysis = analysis.get("operational_analysis")
    evidence_by_risk = {}

    if isinstance(operational_analysis, dict):
        evidence_by_risk = operational_analysis.get("evidence_by_risk", {})

    if isinstance(evidence_by_risk, dict) and evidence_by_risk:
        # OCC por riesgo
        metrics["tables"]["occ_by_risk"] = {
            risk_id: data.get("occ_count", 0)
            for risk_id, data in evidence_by_risk.items()
        }

        # OPG por riesgo
        metrics["tables"]["opg_by_risk"] = {
            risk_id: data.get("opg_count", 0)
            for risk_id, data in evidence_by_risk.items()
        }

        # Controles afectados
        metrics["tables"]["controls_affected_by_risk"] = {
            risk_id: len(data.get("controls_affected", []))
            for risk_id, data in evidence_by_risk.items()
        }

        # Controles críticos afectados
        metrics["tables"]["critical_controls_affected_by_risk"] = {
            risk_id: len(data.get("critical_controls_affected", []))
            for risk_id, data in evidence_by_risk.items()
        }

    # ==================================================
    # >>> NUEVO BLOQUE 3.B — Auditorías (métricas deterministas)
    # ==================================================
    audits = analysis.get("audits")

    if isinstance(audits, list) and audits:
        # Conteo total de auditorías
        metrics["tables"]["audits_total"] = len(audits)

        # Auditorías por riesgo
        metrics["tables"]["audits_by_risk"] = _count_by_key(
            audits, key="risk_id"
        )

        # Auditorías por tipo
        metrics["tables"]["audits_by_type"] = _count_by_key(
            audits, key="audit_type"
        )

        # Auditorías por período
        metrics["tables"]["audits_by_period"] = _count_by_key(
            audits, key="period"
        )

    # ==================================================
    # 4. Reglas deterministas de visualización
    # ==================================================
    visual_suggestions: List[Dict[str, Any]] = []

    # --------------------------------------------------
    # Regla 1 (PRIORIDAD ALTA)
    # Evolución temporal
    # --------------------------------------------------
    if isinstance(risk_trajectories, dict):
        risks_with_series = [
            r for r, v in risk_trajectories.items()
            if isinstance(v, dict) and len(v.get("weekly_values", [])) >= 2
        ]

        if risks_with_series:
            visual_suggestions.append(
                {
                    "type": "line_chart",
                    "metric": "risk_trajectories",
                    "entities": risks_with_series,
                    "why": "Existen trayectorias temporales por riesgo",
                    "question": (
                        "¿Quieres ver la evolución temporal de los riesgos?"
                    ),
                }
            )

    # --------------------------------------------------
    # Regla 2 (PRIORIDAD MEDIA)
    # Comparación multi-riesgo (analysis-driven)
    # --------------------------------------------------
    if not visual_suggestions:
        comparable_risks: set[str] = set()

        if isinstance(risk_trajectories, dict):
            comparable_risks.update(risk_trajectories.keys())

        # Soporte factual (OperationalAnalysisNode)
        if isinstance(evidence_by_risk, dict):
            comparable_risks.update(evidence_by_risk.keys())

        # Soporte cognitivo (AnalystNode) — preserva semántica v0.3
        operational_evidence = analysis.get("operational_evidence", {})
        if isinstance(operational_evidence, dict):
            supported = operational_evidence.get("supported_risks", [])
            if isinstance(supported, list):
                comparable_risks.update([r for r in supported if r])

        intent = state.intent or ""
        query = (state.user_query or "").lower()

        explicit_compare = any(
            token in query
            for token in (
                "compar",
                "versus",
                "vs",
                "comparación",
                "comparar",
            )
        )

        if explicit_compare and isinstance(risk_summary, dict):
            for k in ("dominant_risk", "relevant_risk"):
                r = risk_summary.get(k)
                if r:
                    comparable_risks.add(r)

        if len(comparable_risks) >= 2:
            entities = sorted(comparable_risks)
            visual_suggestions.append(
                {
                    "type": "bar_chart",
                    "metric": "risk_comparison",
                    "entities": entities,
                    "why": "Existen múltiples riesgos comparables en el análisis",
                    "question": (
                        f"¿Quieres comparar métricamente los riesgos {', '.join(entities)}?"
                    ),
                }
            )

    # --------------------------------------------------
    # Regla 3 (PRIORIDAD BAJA / fallback)
    # Ranking / prioridad
    # --------------------------------------------------
    if not visual_suggestions and risk_summary:
        entities = [
            r for r in (
                risk_summary.get("dominant_risk"),
                risk_summary.get("relevant_risk"),
            )
            if r
        ]

        if entities:
            visual_suggestions.append(
                {
                    "type": "bar_chart",
                    "metric": "risk_priority",
                    "entities": entities,
                    "why": "Existe jerarquía de riesgos (dominante vs relevante)",
                    "question": (
                        "¿Quieres ver el ranking de riesgos por prioridad?"
                    ),
                }
            )

    # --------------------------------------------------
    # Regla 7: UNA sola sugerencia
    # --------------------------------------------------
    if visual_suggestions:
        metrics["visual_suggestions"].append(visual_suggestions[0])

    # ==================================================
    # Persistencia
    # ==================================================
    state.analysis["metrics"] = metrics

    state.reasoning.append(
        "MetricsNode: métricas deterministas generadas "
        "a partir del analysis (reglas analysis-driven)."
    )

    return state


# --------------------------------------------------
# Helpers internos (NO cognitivos)
# --------------------------------------------------
def _count_by_key(items: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counter: Dict[str, int] = {}
    for item in items:
        value = item.get(key)
        if value is None:
            continue
        counter[value] = counter.get(value, 0) + 1
    return counter
