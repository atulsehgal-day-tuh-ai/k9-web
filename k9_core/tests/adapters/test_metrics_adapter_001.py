import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_renders_plotly_from_comparison_suggestion():
    analysis = {
        "risk_summary": {
            "dominant_risk": "R02",
            "relevant_risk": "R01",
        }
    }

    visual_suggestions = [
        {
            "type": "bar_chart",
            "metric": "risk_comparison",
            "entities": ["R01", "R02"],
            "question": "¿Quieres comparar los riesgos R01 y R02?",
        }
    ]

    rendered = render_metrics(analysis, visual_suggestions)

    assert len(rendered) == 1
    assert rendered[0]["type"] == "plotly"
    assert rendered[0]["figure"] is not None
