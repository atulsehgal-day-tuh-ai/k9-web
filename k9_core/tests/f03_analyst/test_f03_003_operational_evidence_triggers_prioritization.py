import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def test_f03_003_operational_evidence_triggers_prioritization():
    """
    F03_003 — Con evidencia operacional, el Analyst SÍ prioriza riesgos.
    """

    state = K9State(
        analysis={
            "engine": {
                "period": {},
                "risk_trends": {
                    "R01": {"trend_direction": "up"},
                    "R02": {"trend_direction": "flat"},
                },
                "weekly_signals": {
                    "R01": {"avg_criticidad": 0.75},
                    "R02": {"avg_criticidad": 0.30},
                },
                "proactivo": {
                    "R01": {"avg_rank": 2, "weeks": 12},
                    "R02": {"avg_rank": 1, "weeks": 12},
                },
                "observations": {},
                "audits": {},
                "fdo": {},
            },
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {
                        "occ_count": 2,
                        "opg_count": 0,
                        "critical_controls_affected": ["C01"]
                    }
                },
                "traceability": [],
                "meta": {}
            }
        },
        reasoning=[],
        user_query="",
        intent=""
    )

    result = analyst_node(state)
    decision = result.analysis["preventive_decision"]

    assert decision["prioritized_risks"], (
        "Con evidencia operacional, el Analyst debe priorizar al menos un riesgo"
    )

    assert "R01" in decision["prioritized_risks"], (
        "R01 debe aparecer priorizado cuando tiene evidencia operacional"
    )
