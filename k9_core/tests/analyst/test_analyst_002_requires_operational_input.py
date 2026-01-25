import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_node_requires_operational_analysis_input():
    """
    F02_ANALYST_002

    Regla:
    - Dado un intent analítico válido
    - Pero SIN state.analysis["operational_analysis"]
    - El AnalystNode:
        - NO debe crear analysis["analyst"]
        - NO debe inventar razonamiento
        - NO debe lanzar excepción
        - Debe dejar trazabilidad clara
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "ANALYTICAL_QUERY",
                "entity": "risks",
                "operation": "analyze",
                "output": "analysis",
            }
        },
        analysis={},  # No hay operational_analysis
        reasoning=[],
    )

    result = analyst_node(state)

    # 1️⃣ No debe crear bloque analítico
    assert "analyst" not in result.analysis, (
        "AnalystNode no debe crear analysis['analyst'] "
        "si falta operational_analysis."
    )

    # 2️⃣ No debe tocar answer
    assert result.answer is None, (
        "AnalystNode no debe generar respuesta humana."
    )

    # 3️⃣ Debe dejar trazabilidad de por qué no ejecutó
    assert any(
        "operational" in r.lower() and ("missing" in r.lower() or "skip" in r.lower())
        for r in result.reasoning
    ), (
        "Debe registrar reasoning indicando falta de input operacional."
    )
