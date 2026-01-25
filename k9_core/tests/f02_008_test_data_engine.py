import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_data_engine_f02_008_exposes_fdo_analysis():
    """
    FASE 2 — DataEngineNode
    Test ID: F02_008

    Verifica:
    - Exposición explícita de FDO en analysis
    - Separación entre FDO y trayectorias de riesgo
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

    assert "engine" in state.analysis
    engine = state.analysis["engine"]

    # Bloque FDO existe
    assert "fdo" in engine

    fdo = engine["fdo"]

    # Sub-bloques esperados
    assert "daily_summary" in fdo
    assert "accumulated_12s" in fdo

    # Estructura mínima
    assert isinstance(fdo["daily_summary"], dict)
    assert isinstance(fdo["accumulated_12s"], dict)

    # No deben confundirse con trayectorias de riesgo
    assert "risk_trends" in engine
    assert "R01" in engine["risk_trends"]
