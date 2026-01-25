import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))



import pytest

from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_node_skips_when_intent_is_not_operational():
    """
    F01_OPERATIONAL_001

    Regla:
    - Dado un K9 command con intent != OPERATIONAL_QUERY
    - El OperationalAnalysisNode debe:
        - NO generar analysis["operational_analysis"]
        - NO modificar state.answer
        - SOLO agregar trazabilidad en state.reasoning
        - Retornar el estado sin efectos laterales
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "ANALYTICAL_QUERY",
                "entity": "risks",
                "operation": "rank",
                "output": "analysis",
            }
        },
        analysis=None,
        reasoning=[],
    )

    result = operational_analysis_node(state)

    # 1️⃣ No debe crear salida operacional
    assert result.analysis is None or "operational_analysis" not in result.analysis, (
        "OperationalAnalysisNode no debe generar operational_analysis "
        "cuando el intent no es OPERATIONAL_QUERY."
    )

    # 2️⃣ No debe tocar answer
    assert result.answer is None, (
        "OperationalAnalysisNode no debe generar respuesta humana."
    )

    # 3️⃣ Debe dejar trazabilidad clara
    assert any(
        "skipped" in r.lower() and "intent" in r.lower()
        for r in result.reasoning
    ), "Debe registrar trazabilidad de skip por intent no operacional."
