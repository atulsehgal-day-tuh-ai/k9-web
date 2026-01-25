import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics

def test_metrics_adapter_renders_plotly_from_fdo_trajectory_suggestion():
    """
    Test FDO Adapter 001

    Regla:
    - Dado un suggestion FDO de tipo trayectoria temporal
    - El adapter debe devolver un objeto plotly válido
    """

    analysis = {
        "fdo_trajectories": {
            "fatiga": {
                "weekly_values": [0.18, 0.22, 0.31, 0.29],
            },
            "produccion": {
                "weekly_values": [0.35, 0.38, 0.41, 0.44],
            },
        }
    }

    visual_suggestions = [
        {
            "type": "line_chart",
            "metric": "fdo_trajectories",
            "entities": ["fatiga", "produccion"],
            "question": "¿Quieres ver la evolución de los factores operacionales?",
        }
    ]

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    assert len(rendered) == 1

    chart = rendered[0]
    assert chart["type"] == "plotly"
    assert chart["figure"] is not None

    # Validación mínima de estructura plotly
    fig = chart["figure"]
    assert len(fig.data) == 2  # una línea por FDO
