import sys
import os

# --------------------------------------------------
# Ajuste de path (MISMO estándar que tests anteriores)
# --------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_renders_audits_by_period_table():
    """
    F05_ADAPTER_003

    Regla:
    - Dado un metrics.tables.audits_by_period generado desde MetricsNode
    - El adapter debe renderizar una tabla válida
    - SIN interpretación
    - SIN modificar datos
    """

    analysis = {
        "metrics": {
            "tables": {
                "audits_by_period": {
                    "2024-01": 3,
                    "2024-02": 1,
                }
            }
        }
    }

    visual_suggestions = [
        {
            "type": "table",
            "metric": "audits_by_period",
            "question": "¿Quieres ver la cantidad de auditorías por período?",
        }
    ]

    rendered = render_metrics(
        analysis=analysis,
        visual_suggestions=visual_suggestions,
    )

    # --------------------------------------------------
    # Assert básicos
    # --------------------------------------------------
    assert isinstance(rendered, list)
    assert len(rendered) == 1

    table = rendered[0]

    # --------------------------------------------------
    # Validación estructura render
    # --------------------------------------------------
    assert table["type"] == "table"
    assert table["metric"] == "audits_by_period"
    assert "data" in table

    data = table["data"]

    assert "columns" in data
    assert "rows" in data

    rows = data["rows"]

    # --------------------------------------------------
    # Validación contenido EXACTO (sin reinterpretar)
    # --------------------------------------------------
    assert {"key": "2024-01", "count": 3} in rows
    assert {"key": "2024-02", "count": 1} in rows
