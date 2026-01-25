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
from src.nodes.router import router_node
from src.nodes.data_engine_node import data_engine_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node
from src.nodes.llm_node import LLMNode

from src.llm.mock_client import MockLLMClient
from src.llm.payload import LLMKnowledgeScaffold


def test_smoke_llm_composite_basic():
    """
    Smoke test — LLM COMPOSITE (mock)

    Valida:
    - Iteración controlada explanation_i → synthesis
    - Registro de partial_responses
    - Escritura final única de state.answer
    - No ruptura del core cognitivo
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — COMPOSITE_K9_COMMAND (determinista)
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "COMPOSITE_K9_COMMAND",
                "plan": [
                    {
                        "type": "K9_COMMAND",
                        "intent": "ANALYTICAL_QUERY",
                        "operation": "status",
                        "entity": "risk",
                        "output": "narrative",
                    },
                    {
                        "type": "K9_COMMAND",
                        "intent": "ANALYTICAL_QUERY",
                        "operation": "trend",
                        "entity": "risk",
                        "output": "narrative",
                    },
                ],
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
    # 4. Inicializar sesión y marcar COMPOSITE
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_composite = True

    session.meta["active_step_index"] = 0
    
    # =====================================================
    # 5. Fase explanation_i — sub-comando 1
    # =====================================================
    session.active_phase = "explanation_i"
    state = llm_node(state)

    assert len(session.partial_responses) == 1
    assert state.answer is None

    # =====================================================
    # 6. Fase explanation_i — sub-comando 2
    # =====================================================
    session.active_phase = "explanation_i"
    state = llm_node(state)

    assert len(session.partial_responses) == 2
    assert state.answer is None

    # =====================================================
    # 7. Fase synthesis — respuesta final
    # =====================================================
    session.active_phase = "synthesis"
    state = llm_node(state)

    assert state.answer is not None
    assert "MOCK" in state.answer.upper()

    # =====================================================
    # 8. Invariantes
    # =====================================================
    assert state.analysis is not None
    assert state.narrative_context is not None
    assert session.active_composite is False

    elapsed = time.time() - start
    assert elapsed < 2.0
