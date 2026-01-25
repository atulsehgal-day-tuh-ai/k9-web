# tests/test_data_engine_f01_002.py

import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_data_engine_f01_002_period_and_trends():
    """
    FASE 1 — DataEngineNode
    Test ID: F01_002

    Verifica:
    - Extracción correcta del periodo
    - Cálculo de trayectorias por riesgo
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

    # Periodo
    assert "period" in engine
    assert engine["period"]["min_week"] >= 1
    assert engine["period"]["max_week"] >= engine["period"]["min_week"]
    assert len(engine["period"]["weeks"]) >= 3

    # Trayectorias
    assert "risk_trends" in engine
    assert "R01" in engine["risk_trends"]
    assert "R02" in engine["risk_trends"]

    r01 = engine["risk_trends"]["R01"]
    r02 = engine["risk_trends"]["R02"]

    assert isinstance(r01["weekly_values"], list)
    assert isinstance(r02["weekly_values"], list)

    assert r01["trend_direction"] in ["up", "down", "flat"]
    assert r02["trend_direction"] in ["up", "down", "flat"]
