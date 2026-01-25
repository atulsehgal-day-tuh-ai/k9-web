import sys
from pathlib import Path
import copy

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.operational_analysis_node import operational_analysis_node
from src.nodes.analyst_node import analyst_node
from src.nodes.metrics_node import metrics_node
from src.ui_adapters.metrics_adapter import render_metrics


def test_f05_root_metrics_node_and_adapter_do_not_affect_decision():
    """
    F05_ROOT_001 — MetricsNode + MetricsAdapter (render_metrics)
    materializan y renderizan resultados SIN alterar la decisión del Analyst.
    """

    # --------------------------------------------------
    # Estado base consistente (F03 + F04 cerradas)
    # --------------------------------------------------
    state = K9State(
        analysis={
            "engine": {
                "period": {},
                "risk_trends": {
                    "R01": {"trend_direction": "up"},
                    "R02": {"trend_direction": "flat"},
                },
                "weekly_signals": {
                    "R01": {"avg_criticidad": 0.8},
                    "R02": {"avg_criticidad": 0.3},
                },
                "proactivo": {
                    "R01": {"avg_rank": 2, "weeks": 12},
                    "R02": {"avg_rank": 1, "weeks": 12},
                },
                "observations": {},
                "audits": {
                    "summary": {
                        "total": 2,
                        "by_type": {
                            "reactive": 1,
                            "planned": 1,
                        },
                    }
                },
                "fdo": {},
            }
        },
        reasoning=[],
        user_query="",
        intent=""
    )

    # --------------------------------------------------
    # F04 — OperationalAnalysisNode
    # --------------------------------------------------
    state = operational_analysis_node(state)
    state.analysis["operational_analysis"]["evidence_by_risk"] = {
        "R01": {
            "occ_count": 2,
            "opg_count": 0,
            "critical_controls_affected": ["C01"],
        }
    }

    # --------------------------------------------------
    # F03 — AnalystNode (decisión)
    # --------------------------------------------------
    state = analyst_node(state)
    decision_before = copy.deepcopy(state.analysis["preventive_decision"])

    # --------------------------------------------------
    # F05 — MetricsNode
    # --------------------------------------------------
    state = metrics_node(state)

    metrics = state.analysis.get("metrics")
    assert metrics is not None, "MetricsNode debe exponer analysis['metrics']"

    visual_suggestions = metrics.get("visual_suggestions", [])
    assert isinstance(visual_suggestions, list)

    # --------------------------------------------------
    # MetricsAdapter — render_metrics
    # --------------------------------------------------
    rendered = render_metrics(
        analysis=state.analysis,
        visual_suggestions=visual_suggestions,
    )

    assert isinstance(rendered, list), (
        "render_metrics debe retornar una lista de artefactos renderizables"
    )

    # --------------------------------------------------
    # ROOT CRÍTICO: decisión NO cambia
    # --------------------------------------------------
    assert state.analysis["preventive_decision"] == decision_before, (
        "MetricsNode / MetricsAdapter no deben alterar preventive_decision"
    )
