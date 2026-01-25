import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_node_skips_when_intent_is_not_analytical():
    """
    F02_ANALYST_001

    Regla:
    - Dado un K9 command con intent NO analítico
    - El AnalystNode debe:
        - NO ejecutar lógica analítica
        - NO crear analysis["analyst"]
        - NO modificar answer
        - SOLO agregar trazabilidad de skip
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "OPERATIONAL_QUERY",  # intent NO válido para Analyst
                "entity": "risks",
                "operation": "rank",
                "output": "analysis",
            }
        },
        analysis={
            # Simular que ya existe análisis previo (ej. operacional)
            "operational_analysis": {
                "dummy": True
            }
        },
        reasoning=[],
    )

    result = analyst_node(state)

    # 1️⃣ No debe crear bloque analítico nuevo
    assert "analyst" not in result.analysis, (
        "AnalystNode no debe crear analysis['analyst'] "
        "cuando el intent no es analítico."
    )

    # 2️⃣ No debe tocar answer
    assert result.answer is None, (
        "AnalystNode no debe generar respuesta humana."
    )

    # 3️⃣ Debe registrar trazabilidad clara de skip
    assert any(
        "skipped" in r.lower() and "intent" in r.lower()
        for r in result.reasoning
    ), "Debe registrar reasoning de skip por intent no analítico."
