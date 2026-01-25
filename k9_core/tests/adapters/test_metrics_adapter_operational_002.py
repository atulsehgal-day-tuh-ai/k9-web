import sys
import os

# --------------------------------------------------
# Ajuste de path (MISMO estándar que tests anteriores)
# --------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT)

from src.ui_adapters.metrics_adapter import render_metrics


def test_metrics_adapter_renders_operational_occ_by_risk_table():
    """
    F05_ADAPTER_002

    Regla:
    - Dado un metrics.tables.occ_by_risk generado desde OperationalAnalysisNode
    - El adapter debe renderizar una tabla válida
    - SIN interpretación
    - SIN modificar datos
    """

    analysis = {
        "metrics": {
            "tables": {
                "occ_by_risk": {
                    "R01": 3,
                    "R02": 1,
                }
            }
        }
    }

    visual_suggestions = [
        {
            "type": "table",
            "metric": "occ_by_risk",
            "entities": ["R01", "R02"],
            "question": "¿Quieres ver la distribución de OCC por riesgo?",
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
    assert "data" in table

    data = table["data"]

    assert "columns" in data
    assert "rows" in data

    rows = data["rows"]

    assert {"risk_id": "R01", "occ_count": 3} in rows
    assert {"risk_id": "R02", "occ_count": 1} in rows

