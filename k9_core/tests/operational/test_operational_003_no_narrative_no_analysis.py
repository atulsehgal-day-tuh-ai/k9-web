import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_node_does_not_generate_narrative_or_analysis_reasoning():
    """
    F01_OPERATIONAL_003

    Regla:
    - El OperationalAnalysisNode:
        - NO debe generar narrativa
        - NO debe generar razonamiento analítico
        - NO debe interpretar resultados
        - SOLO debe dejar reasoning técnico de ejecución
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "OPERATIONAL_QUERY",
                "entity": "risks",
                "operation": "expose_evidence",
                "output": "analysis",
            }
        },
        analysis=None,
        reasoning=[],
        risk_enrichment={},
    )

    result = operational_analysis_node(state)

    # 1️⃣ No debe existir narrative_context
    assert not hasattr(result, "narrative_context") or result.narrative_context is None, (
        "OperationalAnalysisNode no debe generar narrative_context"
    )

    # 2️⃣ Reasoning debe ser técnico, no interpretativo
    forbidden_keywords = [
        "significa",
        "implica",
        "riesgo alto",
        "riesgo bajo",
        "crítico",
        "priorizar",
        "recomienda",
        "debería",
        "sugiere",
    ]

    for r in result.reasoning:
        r_lower = r.lower()
        for kw in forbidden_keywords:
            assert kw not in r_lower, (
                f"OperationalAnalysisNode contiene lenguaje interpretativo prohibido: '{kw}'"
            )

    # 3️⃣ No debe escribir respuesta humana
    assert result.answer is None, (
        "OperationalAnalysisNode no debe generar respuesta humana"
    )
