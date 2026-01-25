#from panel import state
from src.state.state import K9State

def semantic_retrieval_node(state: K9State) -> K9State:
    """
    Semantic Retrieval v0.1 (sin Redis)
    Responde consultas simples usando únicamente el context cargado en memoria.
    """

    query = state.user_query.lower()
    #ctx = state.context or {}
    ctx = state.context_bundle or {}

    # --------------------------
    # 1. ÁREAS OPERACIONALES
    # --------------------------
    if "área" in query or "areas" in query or "operacionales" in query:
        areas = ctx.get("areas_operacionales", [])
        state.answer = (
            "Las áreas operacionales consideradas son: " +
            ", ".join(areas)
        )
        state.reasoning.append("SemanticRetrieval: área operacional detectada.")
        return state

    # --------------------------
    # 2. TIPOS DE EVENTO
    # --------------------------
    if "tipo de evento" in query or "eventos" in query or "nm" in query or "opg" in query or "occ" in query:
        tipos = ctx.get("tipos_eventos", {})
        formatted = "\n".join([f"- {k}: {v}" for k, v in tipos.items()])
        state.answer = "Tipos de eventos registrados:\n" + formatted
        state.reasoning.append("SemanticRetrieval: tipos de eventos detectados.")
        return state

    # --------------------------
    # 3. TOP RIESGOS
    # --------------------------
    if "top riesgos" in query or "principales riesgos" in query:
        riesgos = ctx.get("top_riesgos_escondida", [])
        state.answer = (
            "Los riesgos principales considerados actualmente son: " +
            ", ".join(riesgos)
        )
        state.reasoning.append("SemanticRetrieval: top riesgos detectado.")
        return state

    # --------------------------
    # 4. MODELO PROACTIVO (fallback conceptual)
    # --------------------------
    if "modelo proactivo" in query or "proactivo" in query:
        defin = ctx.get("modelo_proactivo_definicion", "")
        state.answer = defin
        state.reasoning.append("SemanticRetrieval: definición de modelo proactivo.")
        return state

    # --------------------------
    # 5. NINGUNA COINCIDENCIA → devolver None y dejar que fallback decida
    # --------------------------
    state.reasoning.append("SemanticRetrieval: sin coincidencias, se delega al fallback.")
    return state
