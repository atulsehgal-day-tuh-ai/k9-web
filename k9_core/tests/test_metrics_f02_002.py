import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_suggests_comparative_chart_when_multiple_risks_present():
    """
    Test F02.002
    Regla #2: comparación multi-entidad → sugerir gráfico comparativo
    """

    state = K9State(
        user_query="Compara los riesgos",
        intent="riesgos",
        analysis={
            "risk_summary": {
                "dominant_risk": "R02",
                "relevant_risk": "R01",
            },
            # OJO: sin risk_trajectories → no se activa regla #1
            "operational_evidence": {},
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
    assert set(suggestion["entities"]) == {"R01", "R02"}
    assert "comparar" in suggestion["question"].lower()
