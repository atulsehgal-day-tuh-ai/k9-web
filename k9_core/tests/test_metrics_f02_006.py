import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_suggests_ranking_when_no_time_series_and_no_comparison():
    """
    Test F02.006

    Regla:
    - Si NO existen trayectorias temporales
    - y NO existen condiciones de comparación multi-entidad
    - pero SÍ existe risk_summary
    → se debe sugerir ranking/prioridad (risk_priority) como fallback visual.
    """

    state = K9State(
        user_query="¿Qué riesgo debería priorizarse preventivamente?",
        intent="analyst",  # Intent irrelevante
        analysis={
            "risk_summary": {
                "dominant_risk": "R02",
                "relevant_risk": "R01",
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

    assert suggestion["type"] == "bar_chart"
    assert suggestion["metric"] == "risk_priority"

    entities = suggestion.get("entities", [])
    assert set(entities) == {"R01", "R02"}

    assert "ranking" in suggestion["question"].lower()
