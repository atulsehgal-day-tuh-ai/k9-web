import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_renders_plotly_from_trajectory_suggestion():
    analysis = {
        "risk_trajectories": {
            "R01": {
                "weekly_values": [0.2, 0.3, 0.4],
            },
            "R02": {
                "weekly_values": [0.4, 0.5, 0.6],
            },
        }
    }

    visual_suggestions = [
        {
            "type": "line_chart",
            "metric": "risk_trajectories",
            "entities": ["R01", "R02"],
            "question": "¿Quieres ver la evolución temporal de los riesgos?",
        }
    ]

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    assert len(rendered) == 1
    assert rendered[0]["type"] == "plotly"
    assert rendered[0]["figure"] is not None
