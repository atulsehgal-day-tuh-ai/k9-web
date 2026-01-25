import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.narrative_node import narrative_node
from src.state.state import K9State


def test_narrative_node_skips_when_output_is_not_narrative():
    """
    F03_NARRATIVE_001

    Regla:
    - Dado un K9 command con output != "narrative"
    - El NarrativeNode debe:
        - NO crear state.narrative_context
        - NO modificar analysis
        - NO modificar answer
        - SOLO agregar trazabilidad en reasoning
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "ANALYTICAL_QUERY",
                "entity": "risks",
                "operation": "analyze",
                "output": "analysis",  # <-- clave
            }
        },
        analysis={"dummy": True},
        reasoning=[],
    )

    result = narrative_node(state)

    # 1️⃣ No debe crear contexto narrativo
    assert not hasattr(result, "narrative_context"), (
        "NarrativeNode no debe crear narrative_context si output != narrative."
    )

    # 2️⃣ No debe modificar analysis
    assert result.analysis == {"dummy": True}, (
        "NarrativeNode no debe modificar analysis."
    )

    # 3️⃣ No debe generar respuesta humana
    assert result.answer is None, (
        "NarrativeNode no debe generar respuesta humana."
    )

    # 4️⃣ Debe dejar trazabilidad clara
    assert any(
        "skipped" in r.lower() and "output" in r.lower()
        for r in result.reasoning
    ), (
        "NarrativeNode debe registrar que fue omitido por output."
    )
