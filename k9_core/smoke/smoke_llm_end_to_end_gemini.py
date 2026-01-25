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

from src.llm.factory import create_llm_client
from src.llm.payload import LLMKnowledgeScaffold
from src.llm.config import LLMSettings


def test_smoke_llm_end_to_end_gemini():
    """
    Smoke test — END TO END con Gemini real (fail-closed aware)

    Valida:
    - Interpretación NL vía Gemini
    - Respeto estricto de fail-closed
    - Ejecución completa SOLO si hay comando canónico
    - Síntesis final controlada
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — lenguaje natural
    # =====================================================
    state = K9State(
        user_query="Muéstrame el estado actual de los riesgos críticos"
    )

    # =====================================================
    # 2. Config LLM — Gemini
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
    # 3. Fase 1 — Interpretación NL → K9
    # =====================================================
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"

    state = llm_node(state)

    # -----------------------------------------------------
    # Outcome A — FAIL-CLOSED correcto
    # -----------------------------------------------------
    if "k9_command" not in state.context_bundle:
        assert state.context_bundle == {}
        assert state.answer is not None
        assert len(state.answer.strip()) > 0

        elapsed = time.time() - start
        assert elapsed < 15.0
        return  # ✅ test PASA aquí

    # -----------------------------------------------------
    # Outcome B — Comando canónico válido
    # -----------------------------------------------------
    assert state.context_bundle is not None
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
    # 5. Fase 3 — Síntesis Gemini
    # =====================================================
    session.active_phase = "synthesis"
    state = llm_node(state)

    # =====================================================
    # 6. Asserts finales
    # =====================================================
    assert state.answer is not None
    assert len(state.answer.strip()) > 0

    elapsed = time.time() - start
    assert elapsed < 15.0
