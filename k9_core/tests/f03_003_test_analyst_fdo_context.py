import sys
import os

# -----------------------------------------------------
# Ajuste de path (mismo patrón que F03_001 / F03_002)
# -----------------------------------------------------
ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(ROOT)

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_f03_003_exposes_fdo_context_as_modulator():
    """
    F03_003
    El AnalystNode debe exponer el bloque fdo_context
    como modulador cognitivo (NO predictivo).
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
            "proactivo": {},
            "audits": {},
            "fdo": {
                "daily_summary": {},
                "accumulated_12s": {
                    "criticidad_global": 82,
                    "fdo_fatiga": 88,
                    "fdo_backlog": 76,
                    "fdo_congestion": 64,
                    "fdo_dotacion": 55,
                },
            },
        }
    }

    # -------------------------------------------------
    # Act
    # -------------------------------------------------
    state = analyst_node(state)

    # -------------------------------------------------
    # Assert — engine preservado
    # -------------------------------------------------
    assert "engine" in state.analysis
    assert isinstance(state.analysis["engine"], dict)

    # -------------------------------------------------
    # Assert — fdo_context existe
    # -------------------------------------------------
    assert "fdo_context" in state.analysis
    fdo_context = state.analysis["fdo_context"]

    assert isinstance(fdo_context, dict)

    # -------------------------------------------------
    # Assert — estructura obligatoria
    # -------------------------------------------------
    required_keys = [
        "pressure_level",
        "dominant_factors",
        "role",
        "interpretation",
    ]

    for key in required_keys:
        assert key in fdo_context

    # -------------------------------------------------
    # Assert — semántica FDO correcta
    # -------------------------------------------------
    assert fdo_context["pressure_level"] in {"low", "medium", "high", "unknown"}
    assert isinstance(fdo_context["dominant_factors"], list)
    assert len(fdo_context["dominant_factors"]) <= 2

    assert fdo_context["role"] == "operational_context_modulator"

    # -------------------------------------------------
    # Assert — NO predictor / NO narrativa
    # -------------------------------------------------
    interpretation = fdo_context["interpretation"].lower()
    forbidden_terms = ["predict", "forecast", "alert", "risk increase"]

    for term in forbidden_terms:
        assert term not in interpretation
