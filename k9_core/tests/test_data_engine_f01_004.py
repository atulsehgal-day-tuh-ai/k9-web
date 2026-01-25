import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.data_engine_node import data_engine_node


def test_data_engine_f01_004_observations_counts():
    """
    FASE 1 — DataEngineNode
    Test ID: F01_004

    Verifica:
    - Conteo operacional de observaciones
    - Desglose OPG / OCC
    - Conteo semanal coherente
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
    assert "observations" in engine

    obs = engine["observations"]["by_type"]

    assert "OPG" in obs
    assert "OCC" in obs

    for obs_type in ["OPG", "OCC"]:
        block = obs[obs_type]

        assert "total" in block
        assert isinstance(block["total"], int)
        assert block["total"] >= 0

        assert "weekly_counts" in block
        assert isinstance(block["weekly_counts"], dict)

        for week, count in block["weekly_counts"].items():
            assert isinstance(week, int)
            assert isinstance(count, int)
            assert count >= 0
