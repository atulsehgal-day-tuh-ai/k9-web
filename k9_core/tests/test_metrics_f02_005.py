import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_suggests_comparative_chart_when_multiple_comparable_risks_exist():
    """
    Test F02.005 (final)

    Regla:
    - Si existen >=2 riesgos comparables del mismo nivel semántico
    - Y NO existen trayectorias temporales activables
    → se debe sugerir visualización comparativa (risk_comparison)
    """

    state = K9State(
        user_query="Dame un análisis general del estado de riesgos",
        intent="analyst",
        analysis={
            "operational_evidence": {
                "supported_risks": ["R01", "R02", "R03"]
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
    assert suggestion["metric"] == "risk_comparison"

    entities = suggestion.get("entities", [])
    assert set(entities) >= {"R01", "R02"}

    assert "compar" in suggestion["question"].lower()
