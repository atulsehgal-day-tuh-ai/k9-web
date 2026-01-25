# smoke/smoke_llm_conversational_context.py
import sys
import os
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.state.state import K9State
from src.nodes.llm_node import LLMNode
from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_conversational_context():
    """
    Smoke test — Conversational Context Carryover

    Valida:
    - Persistencia de sesión LLM
    - Uso de contexto entre turnos
    - Resolución de referencia anafórica
    - No reset de intención ni entidad
    """

    # =====================================================
    # Setup común
    # =====================================================
    mock_client = MockLLMClient()

    knowledge = LLMKnowledgeScaffold(
        canonical_language={},
        domain_semantics={},
        canonical_schema={},
        examples=[],
    )

    llm_node = LLMNode(
        llm_client=mock_client,
        knowledge_scaffold=knowledge,
    )

    # =====================================================
    # Turno 1 — Pregunta inicial
    # =====================================================
    state = K9State(
        user_query="Muéstrame el estado actual de los riesgos críticos"
    )

    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    assert state.context_bundle is not None
    assert "k9_command" in state.context_bundle

    cmd_1 = state.context_bundle["k9_command"]

    assert cmd_1.get("intent") == "ANALYTICAL_QUERY"
    assert cmd_1.get("entity") == "risk"

    # =====================================================
    # Turno 2 — Pregunta dependiente
    # =====================================================
    state.user_query = "¿Y cómo han evolucionado desde entonces?"

    # NO se reinicia sesión
    state = llm_node(state)

    session.active_phase = "interpretation"
    state = llm_node(state)

    assert state.context_bundle is not None
    assert "k9_command" in state.context_bundle

    cmd_2 = state.context_bundle["k9_command"]

    # =====================================================
    # Asserts clave de contexto
    # =====================================================
    assert session.turn_index == 2
    assert len(session.user_questions) == 2

    assert cmd_2.get("intent") == "ANALYTICAL_QUERY"
    assert cmd_2.get("entity") == "risk"
    assert cmd_2.get("operation") in ("trend", "evolution", "status_trend")

    # No se responde aún (interpretation)
    assert state.answer is None
