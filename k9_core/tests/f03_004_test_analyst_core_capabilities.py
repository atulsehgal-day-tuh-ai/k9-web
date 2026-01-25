import sys
import os

# -----------------------------------------------------
# Ajuste de path (mismo patrón que F03_001–003)
# -----------------------------------------------------
ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.append(ROOT)

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_f03_004_core_capabilities_before_audits_and_fdo():
    """
    F03_004
    Valida las capacidades base del AnalystNode (1–5),
    asegurando coherencia estructural y semántica,
    independiente de Auditorías (Cap.6) y FDO (Cap.7).
    """

    # -------------------------------------------------
    # Arrange
    # -------------------------------------------------
    state = K9State()
    state.reasoning = []
    state.analysis = {
        "engine": {
            "period": {
                "start_week": 1,
                "end_week": 12
            },
            "risk_trends": {
                "R01": {"trend_direction": "up"},
                "R02": {"trend_direction": "flat"},
                "R03": {"trend_direction": "down"},
            },
            "weekly_signals": {
                "R01": {"avg_criticidad": 82},
                "R02": {"avg_criticidad": 40},
                "R03": {"avg_criticidad": 30},
            },
            "observations": {
                "summary": {
                    "total": 5,
                    "by_type": {
                        "OPG": 3,
                        "OCC": 2
                    }
                }
            },
            "proactivo": {
                "R01": {"avg_rank": 3, "weeks": 12},
                "R02": {"avg_rank": 5, "weeks": 12},
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
    # Assert — bloques base existen
    # -------------------------------------------------
    expected_blocks = [
        "period",
        "risk_trajectories",
        "risk_summary",
        "observations_summary",
        "operational_evidence",
        "proactive_comparison",
        "thresholds",
    ]

    for block in expected_blocks:
        assert block in state.analysis
        assert isinstance(state.analysis[block], dict)

    # -------------------------------------------------
    # Assert — Capacidad 2: trayectorias
    # -------------------------------------------------
    trajectories = state.analysis["risk_trajectories"]
    assert trajectories["R01"]["temporal_state"] == "degrading"
    assert trajectories["R02"]["temporal_state"] == "stable"
    assert trajectories["R03"]["temporal_state"] == "improving"

    # -------------------------------------------------
    # Assert — Capacidad 3: riesgo dominante / relevante
    # -------------------------------------------------
    summary = state.analysis["risk_summary"]
    assert summary["dominant_risk"] == "R01"
    assert summary["relevant_risk"] == "R01"

    # -------------------------------------------------
    # Assert — Capacidad 4: evidencia observacional
    # -------------------------------------------------
    obs_summary = state.analysis["observations_summary"]
    for risk_id in ["R01", "R02", "R03"]:
        assert "opg_count" in obs_summary[risk_id]
        assert "occ_count" in obs_summary[risk_id]
        assert obs_summary[risk_id]["support_level"] in {"none", "partial"}

    # -------------------------------------------------
    # Assert — Capacidad 5: evidencia operacional
    # -------------------------------------------------
    op_evidence = state.analysis["operational_evidence"]
    assert isinstance(op_evidence["has_operational_support"], bool)
    assert isinstance(op_evidence["supported_risks"], list)

    # -------------------------------------------------
    # Assert — Proactivo vs K9 (estructura)
    # -------------------------------------------------
    proactive = state.analysis["proactive_comparison"]
    assert "R01" in proactive
    assert "avg_rank_proactivo" in proactive["R01"]
    assert "alignment_status" in proactive["R01"]

    # -------------------------------------------------
    # Assert — Umbrales cognitivos
    # -------------------------------------------------
    thresholds = state.analysis["thresholds"]["by_risk"]
    for risk_id, data in thresholds.items():
        assert data["threshold_state"] in {
            "approaching_threshold",
            "below_threshold"
        }

    # -------------------------------------------------
    # Assert — NO depende de Auditorías ni FDO
    # -------------------------------------------------
    assert "audit_evidence" in state.analysis
    assert "fdo_context" in state.analysis
