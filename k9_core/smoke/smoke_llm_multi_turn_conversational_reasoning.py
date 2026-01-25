import sys
import os
import time

# =====================================================
# Bootstrap path — permite importar src/*
# =====================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =====================================================
# Imports K9
# =====================================================
from src.state.state import K9State
from src.nodes.llm_node import LLMNode

from src.llm.factory import create_llm_client
from src.llm.payload import LLMKnowledgeScaffold
from src.llm.config import LLMSettings


def test_smoke_llm_multi_turn_conversational_reasoning():
    """
    SMOKE 3 — Multi-turn Conversational Reasoning (fail-closed compatible)

    Valida:
    - Persistencia de sesión entre múltiples turnos
    - Manejo estable de referencias anafóricas
    - Incremento correcto de turn_index
    - NO ejecución de core bajo ambigüedad
    - NO reset de contexto ni activación de composite
    """

    start = time.time()

    # =====================================================
    # 1. Inicializar LLM
    # =====================================================
    settings = LLMSettings(
        provider="gemini",
        gemini_model="gemini-2.5-flash",
    )

    llm_client = create_llm_client(settings)

    knowledge = LLMKnowledgeScaffold(
        canonical_language={},
        domain_semantics={},
        canonical_schema={},
        examples=[],
    )

    llm_node = LLMNode(
        llm_client=llm_client,
        knowledge_scaffold=knowledge,
    )

    # =====================================================
    # TURNO 1 — Pregunta base
    # =====================================================
    state = K9State(
        user_query="Muéstrame los riesgos críticos actuales"
    )

    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    assert session is not None
    assert session.turn_index >= 1
    assert state.intent in {"CLARIFICATION_REQUEST", "ANALYTICAL_QUERY"}

    # Mientras haya aclaración, NO se ejecuta core
    if state.intent == "CLARIFICATION_REQUEST":
        assert state.analysis is None
        assert state.narrative_context is None

    # =====================================================
    # TURNO 2 — Referencia anafórica
    # =====================================================
    state.user_query = "¿Y cómo han evolucionado?"
    session.active_phase = "interpretation"
    state = llm_node(state)

    assert session.turn_index >= 2
    assert state.intent in {"CLARIFICATION_REQUEST", "ANALYTICAL_QUERY"}

    if state.intent == "CLARIFICATION_REQUEST":
        assert state.analysis is None
        assert state.narrative_context is None

    # =====================================================
    # TURNO 3 — Foco implícito
    # =====================================================
    state.user_query = "¿Cuál es el más preocupante ahora?"
    session.active_phase = "interpretation"
    state = llm_node(state)

    assert session.turn_index >= 3
    assert state.intent in {
        "CLARIFICATION_REQUEST",
        "ANALYTICAL_QUERY",
        "COMPARATIVE_QUERY",
    }

    if state.intent == "CLARIFICATION_REQUEST":
        assert state.analysis is None
        assert state.narrative_context is None

    # =====================================================
    # Invariantes finales del smoke
    # =====================================================
    assert not session.active_composite
    assert session.turn_index >= 3

    elapsed = time.time() - start
    assert elapsed < 30.0
