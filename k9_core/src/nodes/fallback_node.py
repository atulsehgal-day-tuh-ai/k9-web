from typing import Any
from src.state.state import K9State

def fallback_node(state: K9State) -> K9State:
    state.reasoning.append("Fallback Node: consulta fuera de alcance del dominio minero.")

    state.answer = (
        "La consulta realizada no pertenece al dominio de seguridad operacional en minería. "
        "Puedo ayudarte con: riesgos, modelo proactivo, incidentes, contexto operativo, "
        "factores de exposición, BowTie o ICAM.\n\n"
        "Por favor reformula tu pregunta dentro de estos ámbitos."
    )

    return state
