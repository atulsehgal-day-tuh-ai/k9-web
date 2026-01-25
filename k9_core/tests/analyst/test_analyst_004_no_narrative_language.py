import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_node_does_not_generate_narrative_language():
    """
    F02_ANALYST_004

    Regla:
    - El AnalystNode NO debe:
        - narrar
        - interpretar en lenguaje humano
        - recomendar acciones
    - Su reasoning debe ser técnico y declarativo
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
        analysis={
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {
                        "occ_count": 3,
                        "opg_count": 1,
                        "controls_affected": ["C01"],
                        "critical_controls_affected": [],
                    }
                }
            },
            "engine": {
                "weekly_signals": {}
            },
        },
        reasoning=[],
    )

    result = analyst_node(state)

    # 1️⃣ No debe generar respuesta humana
    assert result.answer is None, (
        "AnalystNode no debe generar respuesta humana."
    )

    # 2️⃣ Reasoning debe ser técnico (sin lenguaje humano)
    forbidden_keywords = [
        "debería",
        "recomienda",
        "sugiere",
        "es importante",
        "priorizar",
        "acción",
        "urgente",
        "riesgo alto",
        "riesgo bajo",
        "significa",
        "implica",
    ]

    for r in result.reasoning:
        r_lower = r.lower()
        for kw in forbidden_keywords:
            assert kw not in r_lower, (
                f"AnalystNode contiene lenguaje narrativo o interpretativo prohibido: '{kw}'"
            )
