import sys
import os

# -------------------------------------------------
# FIX IMPORT PATH (MISMO ESTÁNDAR DEL REPO)
# -------------------------------------------------
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_f05_002_exposes_audit_metrics():
    """
    F05_002

    Regla:
    - MetricsNode debe exponer auditorías como métricas deterministas
    - Sin interpretación ni narrativa
    - Auditorías deben ser consultables por:
        - total
        - riesgo
        - tipo
        - período
    """

    # -------------------------------------------------
    # Arrange
    # -------------------------------------------------
    state = K9State()
    state.reasoning = []
    state.intent = "auditorias"
    state.user_query = "muéstrame cuántas auditorías se hicieron el mes pasado"

    state.analysis = {
        "audits": [
            {
                "audit_id": "A01",
                "risk_id": "R01",
                "audit_type": "SEGURIDAD",
                "period": "2024-01",
            },
            {
                "audit_id": "A02",
                "risk_id": "R01",
                "audit_type": "SEGURIDAD",
                "period": "2024-01",
            },
            {
                "audit_id": "A03",
                "risk_id": "R02",
                "audit_type": "OPERACIONAL",
                "period": "2024-01",
            },
            {
                "audit_id": "A04",
                "risk_id": "R02",
                "audit_type": "OPERACIONAL",
                "period": "2024-02",
            },
        ]
    }

    # -------------------------------------------------
    # Act
    # -------------------------------------------------
    state = metrics_node(state)

    # -------------------------------------------------
    # Assert — metrics existe
    # -------------------------------------------------
    assert "metrics" in state.analysis
    metrics = state.analysis["metrics"]

    tables = metrics["tables"]

    # -------------------------------------------------
    # Assert — auditorías totales
    # -------------------------------------------------
    assert tables["audits_total"] == 4

    # -------------------------------------------------
    # Assert — auditorías por riesgo
    # -------------------------------------------------
    assert tables["audits_by_risk"]["R01"] == 2
    assert tables["audits_by_risk"]["R02"] == 2

    # -------------------------------------------------
    # Assert — auditorías por tipo
    # -------------------------------------------------
    assert tables["audits_by_type"]["SEGURIDAD"] == 2
    assert tables["audits_by_type"]["OPERACIONAL"] == 2

    # -------------------------------------------------
    # Assert — auditorías por período
    # -------------------------------------------------
    assert tables["audits_by_period"]["2024-01"] == 3
    assert tables["audits_by_period"]["2024-02"] == 1

    # -------------------------------------------------
    # Assert — NO interpretación
    # -------------------------------------------------
    forbidden_keys = (
        "interpretation",
        "decision",
        "conclusion",
        "narrative",
    )

    for key in forbidden_keys:
        assert key not in metrics

    # -------------------------------------------------
    # Assert — reasoning actualizado
    # -------------------------------------------------
    assert any("MetricsNode" in r for r in state.reasoning)
