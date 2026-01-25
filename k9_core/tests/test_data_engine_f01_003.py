# tests/test_data_engine_f01_003.py

import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_data_engine_f01_003_weekly_signals():
    """
    FASE 1 — DataEngineNode
    Test ID: F01_003

    Verifica:
    - Agregación correcta de señales semanales
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

    assert "weekly_signals" in engine
    assert "R01" in engine["weekly_signals"]
    assert "R02" in engine["weekly_signals"]

    r01 = engine["weekly_signals"]["R01"]

    assert r01["avg_criticidad"] > 0
    assert r01["avg_rank_pos"] > 0
    assert r01["top3_weeks"] >= 0
    assert 0.0 <= r01["is_top3_ratio"] <= 1.0

