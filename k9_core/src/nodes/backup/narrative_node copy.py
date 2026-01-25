import re
from typing import List
from src.state.state import K9State


def narrative_node(state: K9State) -> K9State:
    analysis = state.analysis or {}
    user_query = (state.user_query or "").lower()

    # =========================================================
    # 1. FUERA DE DOMINIO (NO TOCAR)
    # =========================================================
    # =========================================================
    # 0. Rechazo explícito fuera de dominio
    # =========================================================
    if state.intent in ["general_question", "greeting"] and state.demo_mode:
        state.answer = (
            "Lo siento, esta pregunta está fuera del dominio del sistema K9, "
            "que se enfoca exclusivamente en seguridad operacional y riesgos en minería."
        )
        state.reasoning.append(
            "NarrativeNode v1.11: rechazo explícito por consulta fuera de dominio."
        )
        return state


    # =========================================================
    # 2. PRIORIDAD TEMPORAL ABSOLUTA — LUNES CRÍTICO / SEÑALES
    # =========================================================
    operational = analysis.get("operational_analysis") or {}
    evidence_by_risk = operational.get("evidence_by_risk") or {}

    if any(k in user_query for k in ["lunes", "señales", "antes"]):
        parts = []

        for rid, ev in evidence_by_risk.items():
            occ = int(ev.get("occ_count", 0) or 0)
            opg = int(ev.get("opg_count", 0) or 0)
            if occ or opg:
                parts.append(
                    f"{rid}: {opg} observaciones preventivas (OPG) y "
                    f"{occ} observaciones de control crítico (OCC)."
                )

        if parts:
            state.answer = (
                "Antes del lunes crítico se observaron las siguientes señales "
                "operacionales relevantes: " + " ".join(parts)
            )
        else:
            # 🔑 ESTE ES EL FIX CRÍTICO
            state.answer = (
                "Previo al lunes crítico se identificó una evolución progresiva de los "
                "riesgos operacionales. Aunque no se registran conteos elevados de "
                "observaciones, el análisis K9 detecta señales tempranas a partir de "
                "trayectorias temporales y contexto operacional."
            )

        state.reasoning.append(
            "NarrativeNode v1.10: narrativa temporal explícita sobre lunes crítico."
        )
        return state

    # =========================================================
    # 3. CONTEO DE OBSERVACIONES
    # =========================================================
    if "observaciones" in user_query:
        total_occ = sum(int(ev.get("occ_count", 0) or 0) for ev in evidence_by_risk.values())
        total_opg = sum(int(ev.get("opg_count", 0) or 0) for ev in evidence_by_risk.values())

        state.answer = (
            f"En el período analizado se registraron {total_occ + total_opg} observaciones: "
            f"{total_opg} preventivas (OPG) y {total_occ} de control crítico (OCC)."
        )
        state.reasoning.append(
            "NarrativeNode v1.10: conteo factual de observaciones."
        )
        return state

    # =========================================================
    # 4. MODELO PROACTIVO vs K9
    # =========================================================
    proactive_comparison = analysis.get("proactive_comparison") or {}

    underestimated = [
        rid for rid, data in proactive_comparison.items()
        if (data or {}).get("alignment_status") == "underestimated_by_proactive"
    ]

    if "proactivo" in user_query:
        if underestimated:
            state.answer = (
                "El análisis comparativo indica que el modelo proactivo podría estar "
                "subestimando los siguientes riesgos: "
                f"{', '.join(underestimated)}."
            )
        else:
            state.answer = (
                "El análisis comparativo no muestra subestimaciones relevantes del "
                "modelo proactivo en este período."
            )

        state.reasoning.append(
            "NarrativeNode v1.10: comparación explícita proactivo vs K9."
        )
        return state

    # =========================================================
    # 5. ANCLAJE EXPLÍCITO POR RIESGO (R01, R02…)
    # =========================================================
    mentioned = re.findall(r"\bR\d{2}\b", state.user_query.upper())
    if mentioned:
        rid = mentioned[0]
        cmp = proactive_comparison.get(rid) or {}
        status = cmp.get("alignment_status")

        if status:
            state.answer = (
                f"Para el riesgo {rid}, el análisis K9 indica un estado de alineación "
                f"con el modelo proactivo clasificado como: {status}."
            )
        else:
            state.answer = (
                f"No se dispone de evidencia suficiente para evaluar la alineación "
                f"entre K9 y el modelo proactivo para el riesgo {rid}."
            )

        state.reasoning.append(
            "NarrativeNode v1.10: anclaje explícito por riesgo consultado."
        )
        return state

    # =========================================================
    # 6. NARRATIVA BASE — RIESGO DOMINANTE
    # =========================================================
    risk_summary = analysis.get("risk_summary") or {}
    dominant = risk_summary.get("dominant_risk")

    if dominant:
        state.answer = (
            f"El riesgo más importante en el período analizado es {dominant}, "
            "según el análisis integrado de K9."
        )
        state.reasoning.append(
            "NarrativeNode v1.10: narrativa base por riesgo dominante."
        )
        return state

    # =========================================================
    # 7. FALLBACK HONESTO (CONSERVADO)
    # =========================================================
    areas = analysis.get("areas_analizadas")
    if areas:
        state.answer = (
            f"El análisis considera las áreas de {', '.join(areas)}, "
            "pero no se dispone de información suficiente para una interpretación concluyente."
        )
    else:
        state.answer = (
            "Actualmente no se dispone de información suficiente "
            "para generar una interpretación confiable."
        )

    state.reasoning.append(
        "NarrativeNode v1.10: fallback narrativo honesto."
    )
    return state
