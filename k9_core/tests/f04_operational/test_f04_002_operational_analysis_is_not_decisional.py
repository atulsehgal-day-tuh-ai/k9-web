import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.operational_analysis_node import operational_analysis_node


def test_f04_002_operational_analysis_is_not_decisional():
    """
    F04_002 — OperationalAnalysisNode NO emite decisiones ni semántica cognitiva.
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
    op = result.analysis["operational_analysis"]

    forbidden_keys = {
        "prioritized_risks",
        "risk_level",
        "risk_priority",
        "recommendation",
        "decision",
        "alert",
        "critical",
    }

    def contains_forbidden(obj):
        if isinstance(obj, dict):
            return any(
                k in forbidden_keys or contains_forbidden(v)
                for k, v in obj.items()
            )
        if isinstance(obj, list):
            return any(contains_forbidden(v) for v in obj)
        return False

    assert not contains_forbidden(op), (
        "OperationalAnalysisNode no debe emitir decisiones ni semántica cognitiva"
    )
