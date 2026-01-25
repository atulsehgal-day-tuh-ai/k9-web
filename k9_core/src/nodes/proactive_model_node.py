from typing import Dict, Any, List
from src.state.state import K9State


def proactive_model_node(state: K9State) -> K9State:
    """
    ProactiveModelNode — K9 v3.2

    Rol:
    - Explicar alineación o desalineación entre modelo proactivo y razonamiento K9
    - Usar evidencia operacional PURA (OperationalAnalysisNode) como refuerzo explicativo
    - NO recalibrar
    - NO declarar eventos
    - NO generar narrativa
    """

    analysis = state.analysis or {}

    # ------------------------------------------------------------
    # Entradas cognitivas (decisiones)
    # ------------------------------------------------------------
    risk_summary = analysis.get("risk_summary", {})
    proactive_comparison = analysis.get("proactive_comparison", {})

    dominant_risk = risk_summary.get("dominant_risk")
    relevant_risk = risk_summary.get("relevant_risk")

    # ------------------------------------------------------------
    # Evidencia operacional (FUENTE CORRECTA v3.2)
    # ------------------------------------------------------------
    operational_analysis = analysis.get("operational_analysis", {})
    evidence_by_risk = operational_analysis.get("evidence_by_risk", {})

    explanation_by_risk: Dict[str, Dict[str, Any]] = {}
    explained_risks: List[str] = []

    # ------------------------------------------------------------
    # Análisis explicativo por riesgo
    # ------------------------------------------------------------
    for risk, comp in proactive_comparison.items():
        alignment_status = comp.get("alignment_status", "inconclusive")
        avg_rank_k9 = comp.get("avg_rank_k9")
        avg_rank_proactivo = comp.get("avg_rank_proactivo")

        # Solo explicamos riesgos cognitivamente relevantes
        if risk not in {dominant_risk, relevant_risk}:
            continue

        # Evidencia operacional factual (sin juicio)
        evidence_info = evidence_by_risk.get(risk, {})
        has_operational_support = evidence_info.get("occ_count", 0) > 0

        # --------------------------------------------------------
        # Construcción explicativa (determinista)
        # --------------------------------------------------------
        if alignment_status == "aligned":
            explanation_text = (
                "El modelo proactivo y el razonamiento K9 muestran una priorización consistente "
                "para este riesgo en el periodo analizado."
            )

            if has_operational_support:
                explanation_text += (
                    " La evidencia operacional disponible refuerza esta lectura sin indicar "
                    "la ocurrencia de un evento crítico."
                )

        elif alignment_status == "underestimated_by_proactive":
            explanation_text = (
                "El modelo proactivo tiende a subestimar este riesgo en relación con el "
                "razonamiento K9, que considera su evolución temporal como relevante."
            )

            if has_operational_support:
                explanation_text += (
                    " Esta desalineación se ve reforzada por evidencia operacional reciente, "
                    "aunque aún no se configura un evento crítico."
                )

        elif alignment_status == "overestimated_by_proactive":
            explanation_text = (
                "El modelo proactivo asigna una mayor prioridad a este riesgo que el razonamiento "
                "K9, el cual observa una evolución menos preocupante en el periodo analizado."
            )

            if has_operational_support:
                explanation_text += (
                    " La evidencia operacional disponible no contradice esta lectura, pero "
                    "tampoco sugiere una degradación acelerada."
                )

        else:
            explanation_text = (
                "No existe información suficiente para establecer una alineación clara entre "
                "el modelo proactivo y el razonamiento K9 para este riesgo."
            )

        explanation_by_risk[risk] = {
            "proactive_rank": avg_rank_proactivo,
            "k9_rank": avg_rank_k9,
            "operational_evidence": has_operational_support,
            "explanation_text": explanation_text,
        }

        explained_risks.append(risk)

    # ------------------------------------------------------------
    # Resultado estructurado (contrato)
    # ------------------------------------------------------------
    if explained_risks:
        overall_alignment = "aligned"

        if any(
            proactive_comparison.get(r, {}).get("alignment_status")
            == "underestimated_by_proactive"
            for r in explained_risks
        ):
            overall_alignment = "underestimated"

        elif any(
            proactive_comparison.get(r, {}).get("alignment_status")
            == "overestimated_by_proactive"
            for r in explained_risks
        ):
            overall_alignment = "overestimated"
    else:
        overall_alignment = "inconclusive"

    analysis["proactive_explanation"] = {
        "alignment_status": overall_alignment,
        "explained_risks": explained_risks,
        "explanation": explanation_by_risk,
    }

    state.analysis = analysis

    state.reasoning.append(
        "ProactiveModelNode v3.2: explicación de alineación proactivo vs K9 generada "
        "usando evidencia operacional factual (OperationalAnalysisNode)."
    )

    return state
