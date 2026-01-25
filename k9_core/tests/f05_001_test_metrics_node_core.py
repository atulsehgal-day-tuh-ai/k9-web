import sys
import os

# -------------------------------------------------
# FIX IMPORT PATH (ROBUSTO PARA ESTE REPO)
# -------------------------------------------------
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_f05_001_generates_metrics_with_rules_and_operational_input():
    """
    F05_001
    MetricsNode debe:
    - Generar métricas deterministas
    - Preservar reglas de visualización v0.3
    - Consumir evidencia desde OperationalAnalysisNode
    - NO interpretar ni narrar
    """

    # -------------------------------------------------
    # Arrange
    # -------------------------------------------------
    state = K9State()
    state.reasoning = []
    state.intent = "comparar riesgos"
    state.user_query = "quiero comparar los riesgos R01 y R02"

    state.analysis = {
        "risk_summary": {
            "dominant_risk": "R01",
            "relevant_risk": "R02",
        },
        "risk_trajectories": {
            "R01": {"weekly_values": [10, 20, 30]},
            "R02": {"weekly_values": [5, 15, 25]},
        },
        "operational_analysis": {
            "evidence_by_risk": {
                "R01": {
                    "occ_count": 2,
                    "opg_count": 1,
                    "controls_affected": ["C01"],
                    "critical_controls_affected": ["C01"],
                },
                "R02": {
                    "occ_count": 1,
                    "opg_count": 0,
                    "controls_affected": [],
                    "critical_controls_affected": [],
                },
            }
        },
    }

    # -------------------------------------------------
    # Act
    # -------------------------------------------------
    state = metrics_node(state)

    # -------------------------------------------------
    # Assert — metrics existe
    # -------------------------------------------------
    assert "metrics" in state.analysis
    metrics = state.analysis["metrics"]
    assert isinstance(metrics, dict)

    # -------------------------------------------------
    # Assert — estructura base preservada (v0.3)
    # -------------------------------------------------
    for key in ("rankings", "time_series", "tables", "visual_suggestions"):
        assert key in metrics

    # -------------------------------------------------
    # Assert — tablas operacionales desde OperationalAnalysis
    # -------------------------------------------------
    tables = metrics["tables"]

    assert tables["occ_by_risk"]["R01"] == 2
    assert tables["occ_by_risk"]["R02"] == 1

    assert tables["critical_controls_affected_by_risk"]["R01"] == 1
    assert tables["critical_controls_affected_by_risk"]["R02"] == 0

    # -------------------------------------------------
    # Assert — reglas de visualización activas
    # -------------------------------------------------
    visuals = metrics["visual_suggestions"]
    assert isinstance(visuals, list)
    assert len(visuals) == 1

    suggestion = visuals[0]
    assert suggestion["type"] in ("line_chart", "bar_chart")
    assert "question" in suggestion
    assert "why" in suggestion

    # -------------------------------------------------
    # Assert — Metrics NO interpreta
    # -------------------------------------------------
    forbidden_keys = (
        "interpretation",
        "decision",
        "conclusion",
        "narrative",
    )

    for key in forbidden_keys:
        assert key not in metrics

    # -------------------------------------------------
    # Assert — reasoning actualizado
    # -------------------------------------------------
    assert any("MetricsNode" in r for r in state.reasoning)
