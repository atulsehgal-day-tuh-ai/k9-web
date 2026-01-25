import sys
import os

# --------------------------------------------------
# Ajuste de path (mismo patrón que FASE 1)
# --------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import copy
from src.state.state import K9State
from src.nodes.metrics_node import metrics_node


def test_metrics_node_creates_metrics_block_without_cognitive_side_effects():
    """
    Test F02.001
    Verifica que MetricsNode:
    - materializa métricas deterministas
    - NO modifica análisis cognitivo
    - escribe exclusivamente en analysis["metrics"]
    """

    # -----------------------------
    # Given: estado base con analysis consolidado
    # -----------------------------
    initial_analysis = {
        "risk_summary": {
            "dominant_risk": "R02",
            "relevant_risk": "R01",
        },
        "risk_trajectories": {
            "R01": [0.2, 0.25, 0.3],
            "R02": [0.5, 0.5, 0.5],
        },
        "operational_evidence": {
            "occ_enriched": [
                {"risk_id": "R01", "is_control_critico": True},
                {"risk_id": "R01", "is_control_critico": False},
                {"risk_id": "R02", "is_control_critico": True},
            ]
        },
    }

    state = K9State(
        user_query="¿Cómo evolucionaron los riesgos?",
        intent="riesgos",
        analysis=copy.deepcopy(initial_analysis),
        reasoning=[],
        answer=None,
    )

    analysis_before = copy.deepcopy(state.analysis)

    # -----------------------------
    # When: se ejecuta MetricsNode
    # -----------------------------
    state = metrics_node(state)

    # -----------------------------
    # Then: existe bloque metrics
    # -----------------------------
    assert "metrics" in state.analysis, "MetricsNode no creó analysis['metrics']"

    metrics = state.analysis["metrics"]

    # -----------------------------
    # Then: estructura mínima correcta
    # -----------------------------
    assert "rankings" in metrics
    assert "time_series" in metrics
    assert "tables" in metrics
    assert "visual_suggestions" in metrics

    # -----------------------------
    # Then: no se modificó análisis cognitivo
    # -----------------------------
    analysis_after = copy.deepcopy(state.analysis)
    analysis_after.pop("metrics")

    assert analysis_after == analysis_before, (
        "MetricsNode modificó análisis cognitivo, lo cual está prohibido"
    )

    # -----------------------------
    # Then: rankings básicos correctos
    # -----------------------------
    rankings = metrics["rankings"]["risks_by_role"]
    assert rankings["dominant_risk"] == "R02"
    assert rankings["relevant_risk"] == "R01"

    # -----------------------------
    # Then: conteo OCC por riesgo
    # -----------------------------
    occ_table = metrics["tables"]["occ_by_risk"]
    assert occ_table["R01"] == 2
    assert occ_table["R02"] == 1

    # -----------------------------
    # Then: regla 7 — solo una sugerencia visual
    # -----------------------------
    suggestions = metrics["visual_suggestions"]
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 1

    # -----------------------------
    # Then: reasoning traza el paso del nodo
    # -----------------------------
    assert any(
        "MetricsNode" in r for r in state.reasoning
    ), "MetricsNode no dejó traza en reasoning"
