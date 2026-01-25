import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_data_engine_f02_011_exposes_audits_analysis():
    """
    F02_011
    DataEngineNode debe exponer correctamente el bloque de auditorías
    dentro de state.analysis["engine"].
    """

    state = K9State()
    state.analysis = {}
    state.reasoning = []

    state = data_engine_node(state)

    engine = state.analysis.get("engine")
    assert engine is not None
    assert isinstance(engine, dict)

    assert "audits" in engine
    audits = engine["audits"]

    assert "daily" in audits
    assert "accumulated_12s" in audits
    assert "meta" in audits

    daily = audits["daily"]
    assert isinstance(daily["count"], int)
    assert isinstance(daily["by_tipo"], dict)
    assert isinstance(daily["by_origen"], dict)

    acc = audits["accumulated_12s"]
    assert isinstance(acc["records"], dict)

    meta = audits["meta"]
    assert "semantic_level" in meta
    assert "source" in meta