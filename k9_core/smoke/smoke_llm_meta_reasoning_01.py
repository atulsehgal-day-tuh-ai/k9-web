"""
SMOKE_META_01 — Meta Reasoning (Selection → Explanation)

Objetivo:
- Validar razonamiento implícito con binding secuencial
- Ranking → explicación causal
- SIN CLARIFICATION_REQUEST
- Con scaffold completo + meta-ejemplos
"""

import os
import sys
import time
from pathlib import Path

# -----------------------------------------------------
# Exponer ROOT del repo
# -----------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# -----------------------------------------------------
# Imports K9
# -----------------------------------------------------
from src.state.state import K9State

from src.nodes.router import router_node
from src.nodes.data_engine_node import data_engine_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node
from src.nodes.llm_node import LLMNode

from src.llm.factory import create_llm_client
from src.llm.payload import LLMKnowledgeScaffold
from src.llm.config import LLMSettings

# -----------------------------------------------------
# Helpers
# -----------------------------------------------------
from smoke.smoke_k9_full_with_llm import build_knowledge_scaffold


def test_smoke_meta_reasoning_01_selection_then_explanation():
    """
    SMOKE_META_01

    Caso:
    - Ranking implícito
    - Explicación causal dependiente del resultado
    """

    start = time.time()

    # -------------------------------------------------
    # LLM setup
    # -------------------------------------------------
    settings = LLMSettings(
        provider=os.getenv("K9_LLM_PROVIDER", "gemini"),
        gemini_model=os.getenv("K9_GEMINI_MODEL", "gemini-2.5-flash"),
    )

    llm_node = LLMNode(
        llm_client=create_llm_client(settings),
        knowledge_scaffold=build_knowledge_scaffold(),
    )

    # -------------------------------------------------
    # Pregunta meta (la que rompía SMOKE 5)
    # -------------------------------------------------
    question = (
        "Muéstrame cuál fue el riesgo con mayor nivel de criticidad "
        "durante la última semana y explica los factores causales asociados."
    )

    state = K9State(
        user_query=question,
        demo_mode=True,
    )

    # -------------------------------------------------
    # Interpretation
    # -------------------------------------------------
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    # -------------------------------------------------
    # ASSERTS — interpretación correcta
    # -------------------------------------------------
    assert "k9_command" in state.context_bundle, (
        "El LLM no generó k9_command para una pregunta resoluble.\n"
        f"Reasoning: {state.reasoning}\n"
        f"Answer: {state.answer}"
    )

    assert state.answer is None, "No debe responder aún en fase interpretation"

    k9_command = state.context_bundle["k9_command"]

    assert k9_command["type"] == "composite"
    assert len(k9_command["plan"]) == 2

    # -------------------------------------------------
    # Core determinista — ejecución del composite
    # -------------------------------------------------
    state = router_node(state)
    state = data_engine_node(state)
    state = analyst_node(state)
    state = narrative_node(state)

    assert state.analysis is not None
    assert state.narrative_context is not None

    # -------------------------------------------------
    # Synthesis
    # -------------------------------------------------
    session.active_phase = "synthesis"
    state = llm_node(state)

    assert state.answer is not None
    assert len(state.answer.strip()) > 0

    # Señal mínima esperada
    assert "R02" in state.answer or "riesgo" in state.answer.lower()

    # -------------------------------------------------
    # Performance
    # -------------------------------------------------
    elapsed = time.time() - start
    assert elapsed < float(os.getenv("K9_SMOKE_TIMEOUT_S", "60.0"))
