import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_node_creates_structured_analytical_output():
    """
    F02_ANALYST_003

    Regla:
    - Dado un intent analítico válido
    - Con input operacional mínimo
    - El AnalystNode debe:
        - Crear bloques analíticos estructurados en state.analysis
        - Respetar las claves analíticas canónicas
        - NO generar respuesta humana
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
                        "occ_count": 2,
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

    # 1️⃣ Claves analíticas mínimas esperadas (flat)
    required_keys = {
        "period",
        "risk_trajectories",
        "risk_summary",
        "operational_evidence",
        "proactive_comparison",
    }

    missing = required_keys - set(result.analysis.keys())
    assert not missing, f"Faltan claves analíticas obligatorias: {missing}"

    # 2️⃣ No debe generar respuesta humana
    assert result.answer is None, (
        "AnalystNode no debe generar respuesta humana."
    )
