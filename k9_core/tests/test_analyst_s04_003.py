# TEST_S04_003 — AnalystNode usa signals (STDE)

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def test_s04_003_analystnode_enriches_analysis_with_signals():
    """
    TEST_S04_003
    Verifica que el AnalystNode:
    - usa 'signals' cuando están presentes
    - enriquece 'analysis' con métricas simples
    - no modifica 'answer'
    """

    signals_stub = {
        "window": "last_7_days",
        "observations_count": 12,
        "near_miss_count": 4,
        "top_risk": "Caída de altura",
    }

    state = K9State(
        user_query="estado semanal",
        intent="general_question",
        context_bundle={
            "areas_operacionales": ["Mina Rajo"],
            "version_contexto": "0.2"
        },
        signals=signals_stub
    )

    updated_state = analyst_node(state)

    # analysis debe existir
    assert updated_state.analysis is not None
    assert isinstance(updated_state.analysis, dict)

    # Debe reflejar uso de signals
    assert updated_state.analysis.get("signals_window") == "last_7_days"
    assert updated_state.analysis.get("observations_count") == 12
    assert updated_state.analysis.get("near_miss_count") == 4
    assert updated_state.analysis.get("top_risk") == "Caída de altura"

    # answer no debe tocarse
    assert updated_state.answer is None

    # reasoning debe indicar uso de signals
    assert any("signals" in r.lower() for r in updated_state.reasoning)
