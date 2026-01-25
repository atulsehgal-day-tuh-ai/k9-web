import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_suggests_ranking_chart_when_priority_exists():
    """
    Test F02.003
    Regla #3: ranking / prioridad ⇒ sugerir barras o tabla
    """

    state = K9State(
        user_query="Muéstrame el ranking de riesgos",
        intent="riesgos",
        analysis={
            "risk_summary": {
                "dominant_risk": "R02",
                "relevant_risk": "R01",
            },
            # Sin trayectorias → no Regla #1
            # Sin caso comparativo explícito → no Regla #2
        },
        reasoning=[],
        answer=None,
    )

    state = metrics_node(state)

    metrics = state.analysis["metrics"]
    suggestions = metrics["visual_suggestions"]

    assert len(suggestions) == 1

    suggestion = suggestions[0]
    assert suggestion["type"] == "bar_chart"
    assert suggestion["metric"] == "risk_priority"
    assert set(suggestion["entities"]) == {"R01", "R02"}
    assert "ranking" in suggestion["question"].lower()
