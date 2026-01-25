# tests/f04_003_test_operational_analysis_traceability.py
import sys
import os

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
sys.path.insert(0, PROJECT_ROOT)

from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_f04_003_exposes_traceability():
    """
    F04_003
    El nodo debe exponer trazabilidad OCC → riesgo → control → auditoría.
    """

    state = K9State(
        analysis={},
        reasoning=[],
    )

    state.risk_enrichment = {
        "occ_records": [
            {
                "id": "OCC_002",
                "risk_id": "R02",
                "type": "OCC",
                "control_id": "CTRL_05",
                "audit_id": "AUD_010",
            }
        ]
    }

    state = operational_analysis_node(state)

    trace = state.analysis["operational_analysis"]["traceability"]

    assert len(trace) == 1

    t = trace[0]

    assert t["occ_id"] == "OCC_002"
    assert t["risk_id"] == "R02"
    assert t["control_id"] == "CTRL_05"
    assert t["audit_id"] == "AUD_010"
