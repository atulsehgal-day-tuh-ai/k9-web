import sys
from pathlib import Path

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import pytest

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def test_f03_001_analyst_always_emits_preventive_decision():
    """
    F03_001 — AnalystNode SIEMPRE emite preventive_decision.
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

    result = analyst_node(state)

    assert "preventive_decision" in result.analysis, (
        "AnalystNode debe emitir siempre 'preventive_decision'"
    )

    decision = result.analysis["preventive_decision"]

    assert isinstance(decision, dict), (
        "'preventive_decision' debe ser un dict"
    )

    for key in ("scenario", "prioritized_risks", "decision_basis", "recommendation"):
        assert key in decision, (
            f"'preventive_decision' debe contener la clave '{key}'"
        )
