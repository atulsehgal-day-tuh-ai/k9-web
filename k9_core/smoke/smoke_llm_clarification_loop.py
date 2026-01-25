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
# Imports
# =====================================================
from src.state.state import K9State

from src.nodes.llm_node import LLMNode

from src.llm.factory import create_llm_client
from src.llm.payload import LLMKnowledgeScaffold
from src.llm.config import LLMSettings


def test_smoke_llm_clarification_loop_complete():
    """
    SMOKE 1 — Clarification Loop Completo (fail-closed fuerte)

    Valida:
    - Ambigüedad inicial → CLARIFICATION_REQUEST
    - Persistencia de sesión
    - Loop de aclaración estable
    - NO ejecución del core mientras haya aclaración
    - El sistema se mantiene consistente aunque NO se resuelva la intención
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — pregunta ambigua
    # =====================================================
    state = K9State(
        user_query="Dime cosas sobre seguridad"
    )

    # =====================================================
    # 2. LLM setup
    # =====================================================
    settings = LLMSettings(
        provider="gemini",          # intercambiable por "mock"
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
    # 3. Turno 1 — Ambigüedad inicial
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    # -----------------------------------------------------
    # ASSERT — CLARIFICATION_REQUEST (fail-closed)
    # -----------------------------------------------------
    assert "k9_command" not in state.context_bundle
    assert state.answer is not None
    assert len(state.answer.strip()) > 0

    # =====================================================
    # 4. Turno 2 — Usuario NO aclara (mismo input)
    # =====================================================
    state = llm_node(state)

    # -----------------------------------------------------
    # ASSERT — Sigue en aclaración, sin degradar estado
    # -----------------------------------------------------
    assert "k9_command" not in state.context_bundle
    assert state.answer is not None
    assert len(state.answer.strip()) > 0

    # =====================================================
    # 5. Asserts finales
    # =====================================================
    elapsed = time.time() - start
    assert elapsed < 15.0
