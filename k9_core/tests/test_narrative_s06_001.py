# TEST_S06_001 — Ajuste de tono narrativo

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.narrative_node import narrative_node


def test_s06_001_narrative_tone_is_clear_and_demo_friendly():
    analysis_stub = {
        "areas_analizadas": ["Mina Rajo"],
        "signals_window": "últimos 7 días",
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

    updated = narrative_node(state)

    answer = updated.answer.lower()

    # checks de tono (heurísticos)
    assert "en los últimos 7 días" in answer
    assert "observaciones" in answer
    assert "near miss" in answer or "cuasi" in answer
    assert "riesgo" in answer

    # analysis intacto
    assert updated.analysis == analysis_stub

    # reasoning
    assert any("NarrativeNode" in r for r in updated.reasoning)
