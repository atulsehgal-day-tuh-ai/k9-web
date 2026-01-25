import sys
import os

# -----------------------------------------------------
# Ajuste de path (mismo patrón que F02_009–011 / F03_001)
# -----------------------------------------------------
ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(ROOT)

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_f03_002_exposes_audit_evidence_block():
    """
    F03_002
    El AnalystNode debe exponer correctamente el bloque
    audit_evidence como contexto post-evento (NO predictivo).
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
            "fdo": {},
            "audits": {
                "daily": {
                    "count": 2,
                    "by_tipo": {
                        "AUF": 2
                    },
                    "by_origen": {
                        "AUF": 2
                    }
                },
                "accumulated_12s": {},
                "meta": {}
            }
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
    # Assert — audit_evidence existe
    # -------------------------------------------------
    assert "audit_evidence" in state.analysis
    audit_evidence = state.analysis["audit_evidence"]

    assert isinstance(audit_evidence, dict)

    # -------------------------------------------------
    # Assert — estructura obligatoria
    # -------------------------------------------------
    required_keys = [
        "total_audits",
        "audit_pressure_level",
        "by_tipo",
        "by_origen",
        "has_post_event_audits",
        "role",
        "interpretation",
    ]

    for key in required_keys:
        assert key in audit_evidence

    # -------------------------------------------------
    # Assert — semántica post-evento
    # -------------------------------------------------
    assert audit_evidence["total_audits"] == 2
    assert audit_evidence["audit_pressure_level"] in {"low", "medium", "high"}
    assert isinstance(audit_evidence["by_tipo"], dict)
    assert isinstance(audit_evidence["by_origen"], dict)

    assert audit_evidence["has_post_event_audits"] is True
    assert audit_evidence["role"] == "post_event_control_response"

    # -------------------------------------------------
    # Assert — NO narrativa / NO predicción
    # -------------------------------------------------
    assert isinstance(audit_evidence["interpretation"], str)
    assert "predict" not in audit_evidence["interpretation"].lower()
