import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.operational_analysis_node import operational_analysis_node
from src.nodes.analyst_node import analyst_node


def test_f04_003_operational_enables_analyst_decision():
    """
    F04_003 — La evidencia operacional producida por F04
    habilita priorización en el Analyst (F03).
    """

    # Estado base con engine mínimo pero consistente
    state = K9State(
        analysis={
            "engine": {
                "period": {},
                "risk_trends": {
                    "R01": {"trend_direction": "up"},
                    "R02": {"trend_direction": "flat"},
                },
                "weekly_signals": {
                    "R01": {"avg_criticidad": 0.8},
                    "R02": {"avg_criticidad": 0.3},
                },
                "proactivo": {
                    "R01": {"avg_rank": 2, "weeks": 12},
                    "R02": {"avg_rank": 1, "weeks": 12},
                },
                "observations": {},
                "audits": {},
                "fdo": {},
            }
        },
        reasoning=[],
        user_query="",
        intent=""
    )

    # Ejecutar F04 — OperationalAnalysisNode
    state = operational_analysis_node(state)

    # Inyectar evidencia operacional mínima (simula output real del nodo)
    state.analysis["operational_analysis"]["evidence_by_risk"] = {
        "R01": {
            "occ_count": 1,
            "opg_count": 0,
            "critical_controls_affected": ["C01"],
        }
    }

    # Ejecutar F03 — AnalystNode
    state = analyst_node(state)

    decision = state.analysis["preventive_decision"]

    assert decision["prioritized_risks"], (
        "Con evidencia operacional, el Analyst debe priorizar riesgos"
    )

    assert "R01" in decision["prioritized_risks"], (
        "R01 debe ser priorizado cuando tiene evidencia operacional"
    )
