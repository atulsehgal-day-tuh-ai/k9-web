from src.state.state import K9State

def bowtie_node(state: K9State) -> K9State:
    """
    BowTie Node v0.1 — versión mínima.
    Explica qué es un análisis BowTie sin usar ontología ni Redis.
    """

    state.reasoning.append("BowTie Node: explicación básica del análisis BowTie (v0.1).")

    explanation = """
El análisis BowTie es una metodología usada en minería para entender claramente:

1) El Evento Principal (Top Event)
2) Las Causas que pueden llevar a ese evento
3) Las Consecuencias potenciales si ocurre
4) Los Controles Preventivos (izquierda)
5) Los Controles Mitigadores (derecha)

La forma de 'corbatín' (BowTie) permite visualizar en una sola vista:
- qué energías están involucradas,
- cómo se puede liberar esa energía,
- qué controles deben existir para evitar el evento,
- y cómo mitigar sus consecuencias.

En K9 Mining Safety, la versión avanzada del BowTie permitirá:
- vincular riesgos reales,
- recuperar controles desde la ontología,
- detectar faltas de controles,
- y analizar patrones en ventanas temporales.

(Nota: Esta es la versión v0.1, sin ontología aún.)
    """.strip()

    state.answer = explanation
    return state
