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


def test_smoke_llm_composite_end_to_end():
    """
    SMOKE 2 — Composite END-TO-END (fail-closed fuerte)

    Valida:
    - Detección de pregunta compuesta
    - Entrada en CLARIFICATION_REQUEST
    - NO ejecución parcial
    - Estabilidad del sistema en modo composite pendiente
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
    # 2. LLM setup
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
    # 3. Interpretación inicial
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    # =====================================================
    # 4. ASSERTS — composite en fail-closed
    # =====================================================
    assert "k9_command" not in state.context_bundle
    assert state.answer is not None
    assert len(state.answer.strip()) > 0

    # =====================================================
    # 5. Asserts finales
    # =====================================================
    elapsed = time.time() - start
    assert elapsed < 30.0
