from typing import Any
from src.state.state import K9State

def riesgos_node(state: K9State) -> K9State:
    state.reasoning.append("Riesgos Node: explicando riesgos operacionales.")

    riesgos_top = state.context.get("top_riesgos_escondida", [])
    areas = state.context.get("areas_operacionales", [])

    respuesta = (
        f"Riesgos Operacionales — Información Base\n\n"
        f"Los principales riesgos priorizados en faena son:\n"
        f"• " + "\n• ".join(riesgos_top) + "\n\n"
        f"Áreas operacionales consideradas:\n"
        f"• " + "\n• ".join(areas) + "\n\n"
        f"Cada riesgo se evalúa en función de su potencial de consecuencia, "
        f"frecuencia observada, condiciones del entorno y criticidad operacional."
    )

    state.answer = respuesta
    return state
