import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.data_engine_node import data_engine_node


def test_data_engine_f01_005_proactivo_vs_k9():
    """
    FASE 1 — DataEngineNode
    Test ID: F01_005

    Verifica:
    - Carga correcta del modelo proactivo semanal
    - Cálculo de ranking promedio por riesgo
    - Comparación determinista Proactivo vs K9
    """

    state = K9State(
        user_query="test",
        intent="analysis",
        context_bundle={},
        signals={},
        analysis={},
        reasoning=[],
    )

    state = data_engine_node(state)

    engine = state.analysis["engine"]

    # Proactivo base
    assert "proactivo" in engine
    assert isinstance(engine["proactivo"], dict)
    assert len(engine["proactivo"]) > 0

    # Estructura por riesgo
    for riesgo_id, data in engine["proactivo"].items():
        assert "avg_score_proactivo" in data
        assert "avg_rank_proactivo" in data
        assert "weeks_considered" in data

        assert isinstance(data["avg_score_proactivo"], float)
        assert isinstance(data["avg_rank_proactivo"], float)
        assert data["weeks_considered"] > 0

    # Comparación Proactivo vs K9 (si existe)
    if "proactivo_vs_k9" in engine:
        for riesgo_id, comp in engine["proactivo_vs_k9"].items():
            assert "avg_rank_k9" in comp
            assert "avg_rank_proactivo" in comp
            assert "rank_delta" in comp

            assert isinstance(comp["rank_delta"], float)
