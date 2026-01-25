# smoke/smoke_llm_end_to_end_basic.py
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

from src.nodes.router import router_node
from src.nodes.data_engine_node import data_engine_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node
from src.nodes.llm_node import LLMNode

from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_end_to_end_basic():
    """
    Smoke test — END TO END (NL → K9 → CORE → LLM)

    Valida:
    - Interpretación NL → K9_COMMAND
    - Ejecución completa del core cognitivo
    - Construcción de narrative_context
    - Síntesis final vía LLM
    - Escritura única y controlada de state.answer
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — lenguaje natural
    # =====================================================
    state = K9State(
        user_query="Muéstrame el estado actual de los riesgos críticos"
    )

    # =====================================================
    # 2. LLMNode (mock)
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
    # 3. Fase 1 — Interpretación NL → K9
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"

    state = llm_node(state)

    assert "k9_command" in state.context_bundle
    assert state.answer is None

    # =====================================================
    # 4. Fase 2 — Core cognitivo determinista
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)
    state = analyst_node(state)
    state = narrative_node(state)

    assert state.analysis is not None
    assert state.narrative_context is not None

    # =====================================================
    # 5. Fase 3 — Síntesis LLM
    # =====================================================
    session.active_phase = "synthesis"
    state = llm_node(state)

    # =====================================================
    # 6. Asserts finales
    # =====================================================
    assert state.answer is not None
    assert "MOCK" in state.answer.upper()

    elapsed = time.time() - start
    assert elapsed < 5.0
