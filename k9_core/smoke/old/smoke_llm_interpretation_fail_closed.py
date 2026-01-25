import sys
import os
import time

# =====================================================
# Bootstrap path — permite importar src/*
# =====================================================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.state.state import K9State
from src.nodes.llm_node import LLMNode
from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_interpretation_fail_closed():
    """
    Smoke test — LLM interpretation FAIL-CLOSED (mock)

    Valida:
    - Output NO canónico del LLM
    - Activación determinista de fail-closed
    - NO escritura de k9_command
    - Intent = CLARIFICATION_REQUEST
    - Escritura controlada de state.answer
    - Core cognitivo intacto
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — lenguaje natural ambiguo
    # =====================================================
    state = K9State(user_query="Dime cosas sobre seguridad")

    # =====================================================
    # 2. LLMNode con mock (interpretation inválida)
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
    # 3. Ejecutar interpretación
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"

    state = llm_node(state)

    # =====================================================
    # 4. Asserts de fail-closed
    # =====================================================
    assert state.intent == "CLARIFICATION_REQUEST"

    assert state.context_bundle is not None
    assert "k9_command" not in state.context_bundle

    assert state.answer is not None
    assert "interpret" in state.answer.lower() or "canón" in state.answer.lower()

    # =====================================================
    # 5. Invariantes cognitivas
    # =====================================================
    assert state.analysis is None
    assert state.narrative_context is None
    assert not session.active_composite
    assert len(state.reasoning) > 0

    elapsed = time.time() - start
    assert elapsed < 2.0
