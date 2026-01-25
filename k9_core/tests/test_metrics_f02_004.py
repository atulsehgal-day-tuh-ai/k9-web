import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_suggests_time_series_when_trajectories_exist():
    """
    Test F02.004

    Regla:
    - Si existen trayectorias temporales (>=2 puntos),
      se debe sugerir visualización temporal (line_chart),
      independientemente del intent o wording del user_query.
    """

    state = K9State(
        user_query="¿Cómo ha evolucionado el riesgo R01?",
        intent="analyst",  # Intent NO relevante para metrics
        analysis={
            "risk_trajectories": {
                "R01": {
                    "weekly_values": [0.21, 0.34, 0.48],
                    "trend_direction": "up",
                    "temporal_state": "degrading",
                }
            }
        },
        reasoning=[],
        answer=None,
    )

    state = metrics_node(state)

    metrics = state.analysis.get("metrics")
    assert metrics is not None

    suggestions = metrics.get("visual_suggestions", [])
    assert len(suggestions) == 1

    suggestion = suggestions[0]

    assert suggestion["type"] == "line_chart"
    assert suggestion["metric"] == "risk_trajectories"
    assert suggestion["entities"] == ["R01"]
    assert "evolución" in suggestion["question"].lower()
