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


def test_smoke_llm_interpretation_composite():
    """
    Smoke test — LLM interpretation COMPOSITE (mock)

    Valida:
    - NL → COMPOSITE_K9_COMMAND
    - Plan con múltiples K9_COMMAND
    - Validación de schema
    - NO ejecución del core
    - NO escritura de state.answer
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — pregunta compuesta
    # =====================================================
    state = K9State(
        user_query=(
            "Muéstrame el estado actual de los riesgos críticos "
            "y dime cómo han evolucionado en el último mes"
        )
    )

    # =====================================================
    # 2. Preparar LLMNode (mock)
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
    # 4. Asserts principales
    # =====================================================
    assert state.context_bundle is not None
    assert "k9_command" in state.context_bundle

    cmd = state.context_bundle["k9_command"]

    assert cmd.get("type") == "COMPOSITE_K9_COMMAND"
    assert isinstance(cmd.get("plan"), list)
    assert len(cmd["plan"]) >= 2

    for step in cmd["plan"]:
        assert step.get("type") == "K9_COMMAND"
        assert step.get("intent") == "ANALYTICAL_QUERY"
        assert step.get("entity") == "risk"
        assert step.get("operation") is not None
        assert step.get("output") is not None

    # =====================================================
    # 5. Invariantes cognitivas
    # =====================================================
    assert state.answer is None
    assert state.analysis is None
    assert state.narrative_context is None

    elapsed = time.time() - start
    assert elapsed < 2.0
