import sys
import os

# -----------------------------------------------------
# Ajuste de path (mismo patrón que F02_009–011)
# -----------------------------------------------------
ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(ROOT)

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_f03_001_respects_contract_and_preserves_engine():
    """
    F03_001
    El AnalystNode debe:
    - Preservar state.analysis["engine"]
    - Exponer todas las claves definidas en el contrato v3.2
    - No generar narrativa
    """

    # -------------------------------------------------
    # Arrange
    # -------------------------------------------------
    state = K9State()
    state.reasoning = []
    state.analysis = {
        "engine": {
            "period": {},
            "risk_trends": {},
            "weekly_signals": {},
            "observations": {},
            "audits": {},
            "proactivo": {},
            "fdo": {},
        }
    }

    # -------------------------------------------------
    # Act
    # -------------------------------------------------
    state = analyst_node(state)

    # -------------------------------------------------
    # Assert — engine sigue existiendo
    # -------------------------------------------------
    assert "engine" in state.analysis
    assert isinstance(state.analysis["engine"], dict)

    # -------------------------------------------------
    # Assert — bloques contractuales del Analyst
    # -------------------------------------------------
    required_blocks = [
        "period",
        "risk_trajectories",
        "risk_summary",
        "observations_summary",
        "operational_evidence",
        "proactive_comparison",
        "thresholds",
    ]

    for block in required_blocks:
        assert block in state.analysis
        assert isinstance(state.analysis[block], dict)

    # -------------------------------------------------
    # Assert — no narrativa generada
    # -------------------------------------------------
    assert isinstance(state.reasoning, list)
    assert all(isinstance(r, str) for r in state.reasoning)
