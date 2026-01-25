import sys
import os
import time

# =====================================================
# Bootstrap path
# =====================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =====================================================
# Imports K9
# =====================================================
from src.state.state import K9State
from src.nodes.llm_node import LLMNode

from src.nodes.router import router_node
from src.nodes.data_engine_node import data_engine_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node

from src.llm.factory import create_llm_client
from src.llm.payload import LLMKnowledgeScaffold
from src.llm.config import LLMSettings


def test_smoke_llm_mixed_clarification_then_composite():
    """
    SMOKE 4 — Mixed Clarification + Composite (fail-closed first)

    Valida:
    - Pregunta compuesta pero ambigua → CLARIFICATION_REQUEST
    - CLARIFICATION tiene prioridad sobre COMPOSITE
    - NO hay ejecución parcial
    - El sistema SOLO ejecuta si el composite se resuelve
    - Si NO se resuelve, permanece estable y correcto
    """

    start = time.time()

    # =====================================================
    # 1. LLM setup
    # =====================================================
    settings = LLMSettings(
        provider="gemini",
        gemini_model="gemini-2.5-flash",
    )

    llm_node = LLMNode(
        llm_client=create_llm_client(settings),
        knowledge_scaffold=LLMKnowledgeScaffold(
            canonical_language={},
            domain_semantics={},
            canonical_schema={},
            examples=[],
        ),
    )

    # =====================================================
    # 2. Turno 1 — Pregunta compuesta + ambigua
    # =====================================================
    state = K9State(
        user_query="Muéstrame los riesgos críticos y dime si están bien o mal últimamente"
    )

    state = llm_node(state)
    session = state.llm_session_context

    session.active_phase = "interpretation"
    state = llm_node(state)

    # ---- CLARIFICATION tiene prioridad
    assert "k9_command" not in state.context_bundle
    assert state.answer is not None
    assert state.context_bundle == {}
    assert state.analysis is None
    assert state.narrative_context is None
    assert not session.active_composite

    # =====================================================
    # 3. Turnos siguientes — aclaraciones
    # =====================================================
    clarification_queries = [
        "Muéstrame el estado actual de los riesgos críticos y dime cómo han evolucionado en el último mes",
        "Quiero ver la evolución mensual de los riesgos críticos del sistema",
    ]

    composite_cmd = None

    for q in clarification_queries:
        state.user_query = q
        session.active_phase = "interpretation"
        state = llm_node(state)

        if "k9_command" in state.context_bundle:
            composite_cmd = state.context_bundle["k9_command"]
            break

        # Mientras no se resuelva:
        assert "k9_command" not in state.context_bundle
        assert state.answer is not None
        assert state.context_bundle == {}
        assert state.analysis is None
        assert state.narrative_context is None

    # =====================================================
    # 4. Evaluación FINAL — ambos caminos son válidos
    # =====================================================
    if composite_cmd is None:
        # ✅ FAIL-CLOSED CORRECTO
        assert not session.active_composite
        assert state.answer is not None

    else:
        # ✅ COMPOSITE RESUELTO → ejecución completa
        session.active_composite = True

        for step in composite_cmd["plan"]:
            step_state = K9State(
                context_bundle={"k9_command": step},
                llm_session_context=session,
            )

            step_state = router_node(step_state)
            step_state = data_engine_node(step_state)
            step_state = analyst_node(step_state)
            step_state = narrative_node(step_state)

            assert step_state.analysis is not None
            assert step_state.narrative_context is not None

        session.active_phase = "synthesis"
        state = llm_node(state)

        assert state.answer is not None
        assert len(state.answer.strip()) > 0

    elapsed = time.time() - start
    assert elapsed < 120.0

