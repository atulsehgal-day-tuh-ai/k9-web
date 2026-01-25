import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_renders_plotly_from_priority_ranking():
    analysis = {
        "risk_summary": {
            "dominant_risk": "R02",
            "relevant_risk": "R01",
        }
    }

    visual_suggestions = [
        {
            "type": "bar_chart",
            "metric": "risk_priority",
            "entities": ["R02", "R01"],
            "question": "¿Quieres ver el ranking de riesgos?",
        }
    ]

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    assert len(rendered) == 1
    assert rendered[0]["type"] == "plotly"
    assert rendered[0]["figure"] is not None
