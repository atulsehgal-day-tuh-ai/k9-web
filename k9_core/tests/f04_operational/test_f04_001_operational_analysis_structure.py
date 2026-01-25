import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.operational_analysis_node import operational_analysis_node


def test_f04_001_operational_analysis_structure_exists():
    """
    F04_001 — OperationalAnalysisNode expone estructura mínima y no decisional.
    """

    state = K9State(
        analysis={
            "engine": {
                "period": {},
                "risk_trends": {},
                "weekly_signals": {},
                "proactivo": {},
                "observations": {},
                "audits": {},
                "fdo": {},
            }
        },
        reasoning=[],
        user_query="",
        intent=""
    )

    result = operational_analysis_node(state)
    analysis = result.analysis

    assert "operational_analysis" in analysis, (
        "Debe existir analysis['operational_analysis']"
    )

    op = analysis["operational_analysis"]

    # Estructura mínima esperada
    for key in ("evidence_by_risk", "traceability", "meta"):
        assert key in op, (
            f"operational_analysis debe contener la clave '{key}'"
        )

    assert isinstance(op["evidence_by_risk"], dict)
    assert isinstance(op["traceability"], list)
    assert isinstance(op["meta"], dict)
