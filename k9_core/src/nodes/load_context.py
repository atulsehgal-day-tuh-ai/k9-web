from src.state.state import K9State

def load_context(state: K9State) -> K9State:
    """
    Nodo 3 del grafo K9 Mining Safety.
    Carga el contexto operativo mínimo que el agente necesita para razonar.
    Versión 0.2: alineado con K9State v3.2.
    """

    context = {
        "areas_operacionales": [
            "Mina Rajo",
            "Planta Concentradora",
            "Chancado",
            "Taller de Mantención",
            "Campamento",
        ],
        "top_riesgos_escondida": [
            "Caída de altura",
            "Caída de objetos",
            "Contacto con energía"
        ],
        "modelo_proactivo_definicion": (
            "El Modelo Proactivo es una metodología predictiva usada en minería "
            "para anticipar riesgos operacionales en ventanas de corto plazo."
        ),
        "tipos_eventos": {
            "NM": "Near Miss (evento sin lesión pero con potencial)",
            "OPG": "Oportunidad de mejora",
            "OCC": "Observación de conducta crítica",
            "INC": "Incidente",
            "HZD": "Peligro detectado"
        },
        "version_contexto": "0.2"
    }

    # ------------------------------------------------------------
    # Merge (NO clobber):
    # - `state.k9_command` is the source of truth for the graph.
    # - `state.context_bundle["k9_command"]` is kept for backward-compatible nodes.
    # ------------------------------------------------------------
    existing = state.context_bundle or {}
    merged = {**existing, **context}

    if state.k9_command and "k9_command" not in merged:
        merged["k9_command"] = state.k9_command
    elif state.k9_command and merged.get("k9_command") != state.k9_command:
        # Prefer canonical command
        merged["k9_command"] = state.k9_command

    state.context_bundle = merged
    state.reasoning.append("Load Context: contexto estructural cargado (v0.2).")

    return state
