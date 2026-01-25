import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)



from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_f04_002_builds_evidence_by_risk_correctly():
    """
    F04_002
    El nodo debe construir evidencia operacional detallada por riesgo.
    """

    state = K9State(
        analysis={},
        reasoning=[],
    )

    state.risk_enrichment = {
        "occ_records": [
            {
                "id": "OCC_001",
                "risk_id": "R01",
                "type": "OCC",
                "control_id": "CTRL_01",
                "is_critical_control": True,
            },
            {
                "id": "OPG_001",
                "risk_id": "R01",
                "type": "OPG",
                "control_id": "CTRL_02",
                "is_critical_control": False,
            },
        ]
    }

    state = operational_analysis_node(state)

    evidence = state.analysis["operational_analysis"]["evidence_by_risk"]

    assert "R01" in evidence

    r01 = evidence["R01"]

    assert r01["occ_count"] == 1
    assert r01["opg_count"] == 1

    assert "CTRL_01" in r01["controls_affected"]
    assert "CTRL_01" in r01["critical_controls_affected"]

    assert isinstance(r01["controls_affected"], list)
    assert isinstance(r01["critical_controls_affected"], list)
