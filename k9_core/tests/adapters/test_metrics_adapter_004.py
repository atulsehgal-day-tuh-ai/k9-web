import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_ignores_unknown_metric():
    analysis = {}

    visual_suggestions = [
        {
            "type": "bar_chart",
            "metric": "unknown_metric",
            "entities": ["X"],
            "question": "Esto no debería renderizarse",
        }
    ]

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    assert rendered == []
