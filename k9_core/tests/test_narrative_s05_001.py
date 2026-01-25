# TEST_S05_001 — Narrative Node v0.1

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.narrative_node import narrative_node


def test_s05_001_narrative_node_generates_answer_from_analysis():
    """
    TEST_S05_001
    Verifica que el NarrativeNode:
    - genera 'answer' a partir de 'analysis'
    - no modifica 'analysis'
    - agrega reasoning
    """

    analysis_stub = {
        "context_version": "0.2",
        "areas_analizadas": ["Mina Rajo"],
        "signals_window": "last_7_days",
        "observations_count": 12,
        "near_miss_count": 4,
        "top_risk": "Caída de altura",
    }

    state = K9State(
        user_query="resumen semanal",
        intent="general_question",
        analysis=analysis_stub,
        answer=None,
    )

    updated_state = narrative_node(state)

    # answer debe generarse
    assert updated_state.answer is not None
    assert isinstance(updated_state.answer, str)
    assert len(updated_state.answer) > 20

    # analysis NO debe tocarse
    assert updated_state.analysis == analysis_stub

    # reasoning debe registrar la acción
    assert any("Narrative" in r for r in updated_state.reasoning)
