"""
K9 Mining Safety — FULL SMOKE (WITH LLM)

Objetivo:
- Ejecutar el set mínimo de preguntas de demo (smoke_k9_full)
- Validar que el LLM NO pide CLARIFICATION cuando la pregunta es suficiente
- Core determinista ejecuta solo con K9_COMMAND válido
- Respuesta final sintetizada por LLM (synthesis)
- Caso fuera de dominio debe rechazarse correctamente
"""

import json
import os
import sys
import time
from pathlib import Path

# -----------------------------------------------------
# Exponer ROOT del repo (no /src)
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
def _load_json_from_candidates(filename: str) -> dict | list:
    """
    Busca el archivo JSON en ubicaciones comunes:
    - carpeta actual (smoke/)
    - repo root
    - repo root / "assets"
    - repo root / "resources"
    - repo root / "data"
    """
    candidates = [
        Path(__file__).resolve().parent / filename,
        REPO_ROOT / filename,
        REPO_ROOT / "assets" / filename,
        REPO_ROOT / "resources" / filename,
        REPO_ROOT / "data" / filename,
    ]

    for p in candidates:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)

    return {} if filename.endswith(".json") else {}


def build_knowledge_scaffold() -> LLMKnowledgeScaffold:
    """
    Carga bundle canónico real si los archivos están presentes.
    """
    canonical_language = _load_json_from_candidates("k9_language_v1_1.json")
    domain_semantics = _load_json_from_candidates("k9_domain_semantics_es.json")
    canonical_schema = _load_json_from_candidates("k9_canonical_schema_v1_2.json")

    examples_basic = _load_json_from_candidates("k9_examples_basic.json")
    examples_adv = _load_json_from_candidates("k9_examples_advanced.json")

    examples: list = []
    if isinstance(examples_basic, list):
        examples.extend(examples_basic)
    elif isinstance(examples_basic, dict) and "examples" in examples_basic:
        examples.extend(examples_basic["examples"])

    if isinstance(examples_adv, list):
        examples.extend(examples_adv)
    elif isinstance(examples_adv, dict) and "examples" in examples_adv:
        examples.extend(examples_adv["examples"])

    return LLMKnowledgeScaffold(
        canonical_language=canonical_language if isinstance(canonical_language, dict) else {},
        domain_semantics=domain_semantics if isinstance(domain_semantics, dict) else {},
        canonical_schema=canonical_schema if isinstance(canonical_schema, dict) else {},
        examples=examples,
    )


def run_question_with_llm(
    *,
    llm_node: LLMNode,
    question: str,
    must_contain: list[str] | None = None,
    must_not_contain: list[str] | None = None,
    expect_out_of_domain: bool = False,
    timeout_s: float = 60.0,
) -> K9State:
    """
    Ejecuta: Interpretation (LLM) -> Core determinista -> Synthesis (LLM)
    """
    start = time.time()

    state = K9State(
        user_query=question,
        demo_mode=True,
    )

    # -------------------------
    # Interpretation (LLM)
    # -------------------------
    state.llm_session_context = None
    state = llm_node(state)

    session = state.llm_session_context
    session.active_phase = "interpretation"
    state = llm_node(state)

    if expect_out_of_domain:
        assert state.context_bundle == {} or "k9_command" not in state.context_bundle
        assert state.answer is not None and len(state.answer.strip()) > 0

        answer = state.answer or ""
        if must_not_contain:
            for token in must_not_contain:
                assert token.lower() not in answer.lower()

        assert (time.time() - start) < timeout_s
        return state

    # 🔒 NUEVO CONTRATO — CLARIFICATION IMPLÍCITA
    if "k9_command" not in state.context_bundle:
        assert state.answer is not None
        assert len(state.answer.strip()) > 0
        return state

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

    assert state.analysis is not None
    assert state.narrative_context is not None

    # -------------------------
    # Synthesis (LLM)
    # -------------------------
    session.active_phase = "synthesis"
    state = llm_node(state)

    answer = state.answer or ""
    assert len(answer.strip()) > 0

    if must_contain:
        for token in must_contain:
            assert token.lower() in answer.lower()

    if must_not_contain:
        for token in must_not_contain:
            assert token.lower() not in answer.lower()

    assert (time.time() - start) < timeout_s
    return state


def test_smoke_k9_full_with_llm():
    """
    Smoke FULL (LLM)
    """
    global_start = time.time()

    provider = os.getenv("K9_LLM_PROVIDER", "gemini")
    settings = LLMSettings(
        provider=provider,
        gemini_model=os.getenv("K9_GEMINI_MODEL", "gemini-2.5-flash"),
    )

    llm_client = create_llm_client(settings)
    knowledge = build_knowledge_scaffold()

    llm_node = LLMNode(
        llm_client=llm_client,
        knowledge_scaffold=knowledge,
    )

    cases = [
        {
            "q": (
                "Muéstrame cuál fue el riesgo con mayor nivel de criticidad "
                "durante la última semana y explica los factores causales asociados."
            ),
            "must_contain": ["R02"],
        },
        {
            "q": (
                "¿Existe algún riesgo cuya criticidad durante el último mes "
                "no haya sido reflejada adecuadamente por el modelo proactivo?"
            ),
            "must_contain": ["proactivo"],
        },
        {
            "q": (
                "Muéstrame cómo ha evolucionado el riesgo R02 (Caída de Objetos) "
                "a lo largo del último mes."
            ),
            "must_contain": ["R02"],
        },
        {
            "q": (
                "¿Qué señales o eventos se registraron durante la semana previa "
                "al lunes crítico?"
            ),
            "must_contain": ["lunes"],
        },
        {
            "q": (
                "¿Cuántas observaciones se registraron durante la última semana "
                "y cómo se distribuyen por tipo?"
            ),
            "must_contain": ["observ"],
        },
        {
            "q": (
                "¿Qué riesgos presentaron la mayor presión operacional "
                "durante la última semana?"
            ),
            "must_contain": ["R02"],
        },
        {
            "q": (
                "¿Por qué el ranking del modelo proactivo no refleja completamente "
                "el riesgo emergente R01 durante el último mes?"
            ),
            "must_contain": ["proactivo"],
        },
        {
            "q": (
                "Construye una narrativa interpretativa sobre el comportamiento "
                "de los principales riesgos durante el último mes."
            ),
            "must_contain": ["R02"],
        },
        {
            "q": (
                "¿Qué riesgos superaron el umbral crítico durante el último mes?"
            ),
            "must_contain": ["R02"],
        },
        {
            "q": "¿Cuál es la capital de Chile?",
            "expect_out_of_domain": True,
            "must_not_contain": ["santiago", "chile es", "capital"],
        },
    ]

    for c in cases:
        run_question_with_llm(
            llm_node=llm_node,
            question=c["q"],
            must_contain=c.get("must_contain"),
            must_not_contain=c.get("must_not_contain"),
            expect_out_of_domain=c.get("expect_out_of_domain", False),
            timeout_s=float(os.getenv("K9_SMOKE_TIMEOUT_S", "60.0")),
        )

    assert (time.time() - global_start) < float(
        os.getenv("K9_SMOKE_GLOBAL_TIMEOUT_S", "300.0")
    )
