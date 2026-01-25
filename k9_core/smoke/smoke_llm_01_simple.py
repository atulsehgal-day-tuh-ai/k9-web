# smoke/smoke_llm_01_simple.py

"""
K9 Mining Safety — SMOKE 01 (LLM SIMPLE)

Objetivo:
- Validar que el LLM puede traducir una pregunta SIMPLE
- Generar un K9_COMMAND válido
- Ejecutar el core determinista
- Sintetizar una respuesta final DIRECTAMENTE desde `analysis`
- SIN composites
- SIN narrativa artificial
- SIN meta reasoning

NOTA CRÍTICA:
Este smoke valida el contrato de síntesis.
NO debe inyectar narrative_context manualmente.
Si este test falla, el contrato de síntesis está roto.
"""

import os
import sys
import time
import json
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
from src.llm.session_context import LLMSessionContext


# -----------------------------------------------------
# Helpers
# -----------------------------------------------------
def _load_json(filename: str) -> dict:
    path = REPO_ROOT / "src" / "language" / filename
    assert path.exists(), f"Missing language file: {filename}"
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(filename: str) -> str:
    path = REPO_ROOT / "src" / "language" / filename
    assert path.exists(), f"Missing language file: {filename}"
    return path.read_text(encoding="utf-8")


def build_knowledge_scaffold() -> LLMKnowledgeScaffold:
    """
    Scaffold mínimo para bootstrap LLM.
    """
    return LLMKnowledgeScaffold(
        canonical_language=_load_text("k9_language_v1_1.json"),
        domain_semantics=_load_json("k9_domain_semantics_es.json"),
        canonical_schema=_load_json("k9_canonical_schema_v1_2.json"),
        examples_basic=_load_text("k9_examples_basic.json"),
        examples_advanced=None,
        meta_reasoning_examples=None,
    )


# -----------------------------------------------------
# Smoke Test
# -----------------------------------------------------
def test_smoke_llm_01_simple():
    start = time.time()

    settings = LLMSettings(
        provider=os.getenv("K9_LLM_PROVIDER", "gemini"),
        gemini_model=os.getenv("K9_GEMINI_MODEL", "gemini-2.5-flash"),
    )

    llm_node = LLMNode(
        llm_client=create_llm_client(settings),
        knowledge_scaffold=build_knowledge_scaffold(),
    )

    state = K9State(
        user_query="¿Cuántas observaciones hubieron la última semana?",
        demo_mode=True,
    )

    # -------------------------
    # Interpretation
    # -------------------------
    state = llm_node(state)

    assert state.context_bundle is not None
    assert "k9_command" in state.context_bundle
    assert state.answer is None

    # -------------------------
    # Core determinista
    # -------------------------
    state = router_node(state)
    state = data_engine_node(state)
    state = analyst_node(state)
    state = narrative_node(state)

    # OPERATIONAL_QUERY → analysis obligatorio
    assert state.analysis is not None

    # -------------------------
    # Synthesis (LLM)
    # -------------------------
    state.llm_session_context = LLMSessionContext(
        session_id="smoke-01",
        active_phase="synthesis",
    )

    # -------------------------
    # DEBUG TRACE — SYNTHESIS INPUT
    # -------------------------
    payload = llm_node._build_payload(state, phase="synthesis")

    trace_path = REPO_ROOT / "smoke" / "llm_synthesis_prompt.txt"
    trace_path.write_text(payload.render(), encoding="utf-8")

    print(f"\n[TRACE] Prompt de síntesis guardado en: {trace_path}\n")

    state = llm_node(state)

    # -------------------------
    # Validaciones de contrato
    # -------------------------
    assert state.answer is not None
    assert isinstance(state.answer, str)

    # Debe ser síntesis humana, no JSON ni análisis crudo
    assert "{" not in state.answer
    assert "}" not in state.answer
    assert "observaciones" in state.answer.lower()

    print("\n=== SMOKE 01 FINAL ANSWER ===")
    print(state.answer)
    print("============================\n")

    assert (time.time() - start) < 60.0
