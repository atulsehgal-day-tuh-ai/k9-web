import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def test_f03_002_no_operational_evidence_no_prioritization():
    """
    F03_002 — Sin evidencia operacional, el Analyst NO prioriza riesgos.
    """

    state = K9State(
        analysis={
            "engine": {
                "period": {},
                "risk_trends": {},
                "weekly_signals": {},
                "proactivo": {
                    "R01": {"avg_rank": 1, "weeks": 12},
                    "R02": {"avg_rank": 2, "weeks": 12},
                },
                "observations": {},
                "audits": {},
                "fdo": {},
            },
            "operational_analysis": {
                "evidence_by_risk": {},
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

    assert decision["prioritized_risks"] == [], (
        "Sin evidencia operacional, el Analyst no debe priorizar riesgos"
    )
