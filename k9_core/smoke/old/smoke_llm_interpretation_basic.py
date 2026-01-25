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
from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_interpretation_basic():
    """
    Smoke test — LLM interpretation (mock)

    Valida:
    - Traducción NL → K9_COMMAND
    - Validación de schema canónico
    - Escritura controlada de context_bundle["k9_command"]
    - NO ejecución del core
    - NO escritura de state.answer
    - Fail-closed si el output no es válido
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — lenguaje natural
    # =====================================================
    state = K9State(
        user_query="Muéstrame el estado actual de los riesgos críticos"
    )

    # =====================================================
    # 2. Preparar LLMNode (mock)
    # =====================================================
    mock_client = MockLLMClient()

    knowledge = LLMKnowledgeScaffold(
        canonical_language={},   # no requerido para mock
        domain_semantics={},
        canonical_schema={},
        examples=[],
    )

    llm_node = LLMNode(
        llm_client=mock_client,
        knowledge_scaffold=knowledge,
    )

    # =====================================================
    # 3. Forzar fase de interpretación
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

    k9_command = state.context_bundle["k9_command"]

    assert isinstance(k9_command, dict)
    assert k9_command.get("intent") == "ANALYTICAL_QUERY"
    assert k9_command.get("entity") == "risk"
    assert k9_command.get("operation") is not None
    assert k9_command.get("output") is not None

    # =====================================================
    # 5. Invariantes cognitivas
    # =====================================================
    assert state.answer is None  # interpretación no responde
    assert state.analysis is None
    assert state.narrative_context is None

    # =====================================================
    # 6. Meta
    # =====================================================
    elapsed = time.time() - start
    assert elapsed < 1.0
