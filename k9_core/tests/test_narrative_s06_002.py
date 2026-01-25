# TEST_S06_002 — Narrative fallback explícito

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.narrative_node import narrative_node


def test_s06_002_narrative_fallback_when_no_signals():
    analysis_stub = {
        "areas_analizadas": ["Mina Rajo"]
        # sin signals_window, sin conteos
    }

    state = K9State(
        user_query="resumen semanal",
        intent="general_question",
        analysis=analysis_stub,
        answer=None,
    )

    updated = narrative_node(state)

    answer = updated.answer.lower()

    # Mensaje honesto de falta de información
    assert "no se dispone de información suficiente" in answer or "aún no hay información suficiente" in answer

    # Sugerencia de próximos pasos
    assert "observaciones" in answer or "señales" in answer

    # analysis intacto
    assert updated.analysis == analysis_stub

    # reasoning registra fallback
    assert any("fallback" in r.lower() for r in updated.reasoning)
