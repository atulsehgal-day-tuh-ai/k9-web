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

from src.nodes.router import router_node
from src.nodes.data_engine_node import data_engine_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node
from src.nodes.llm_node import LLMNode

from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_synthesis_basic():
    """
    Smoke test — LLM synthesis (mock)

    Valida:
    - Integración LLMNode sin romper core
    - Uso correcto de LLMPayload
    - Escritura controlada de state.answer
    - No regresión de invariantes cognitivas
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — comando canónico (determinista)
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "ANALYTICAL_QUERY",
                "operation": "status",
                "entity": "risk",
                "output": "narrative",
            }
        }
    )

    # =====================================================
    # 2. Flujo cognitivo sellado (SIN LLM)
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)
    state = analyst_node(state)
    state = narrative_node(state)

    # =====================================================
    # 3. Preparar LLMNode (mock)
    # =====================================================
    mock_client = MockLLMClient()

    # Knowledge scaffold vacío es válido para synthesis mock
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

    # Forzamos fase synthesis (primer smoke)
    state.llm_session_context = None  # asegurar inicialización limpia
    state = llm_node(state)

    # =====================================================
    # 4. Performance
    # =====================================================
    assert (time.time() - start) < 1.5, "LLM synthesis smoke test exceeded time budget"

    # =====================================================
    # 5. Invariantes cognitivas (NO deben romperse)
    # =====================================================
    assert state.analysis is not None
    assert isinstance(state.analysis, dict)
    assert "engine" in state.analysis

    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # =====================================================
    # 6. Invariantes narrativas
    # =====================================================
    assert state.narrative_context is not None

    # =====================================================
    # 7. Invariantes LLM
    # =====================================================
    assert state.answer is not None, "LLMNode must produce answer in synthesis phase"
    assert "[MOCK_SYNTHESIS]" in state.answer

    # No debe modificar intención
    assert state.intent in (None, "ANALYTICAL_QUERY")

    # =====================================================
    # 8. Invariantes negativas
    # =====================================================
    # LLM no debe tocar analysis ni reasoning
    assert "LLMNode" not in " ".join(state.reasoning), "LLMNode must not add cognitive reasoning"
