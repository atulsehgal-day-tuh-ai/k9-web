"""
K9 Mining Safety — Smoke Test GREETING_QUERY (NO LLM)

Valida que el intent GREETING_QUERY:
- Sea aceptado por el Router
- NO ejecute lógica cognitiva
- Ejecute SOLO NarrativeNode
- Construya narrative_context institucional
- NO produzca texto humano
"""

import sys
import time
from pathlib import Path

# -----------------------------------------------------
# Exponer ROOT del repo (no /src)
# -----------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.router import router_node
from src.nodes.narrative_node import narrative_node


def test_greeting_query_routes_to_institutional_narrative_only():
    start_time = time.time()

    # =====================================================
    # 1. Estado inicial: GREETING_QUERY canónico
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "GREETING_QUERY",
                "output": "narrative"
            }
        }
    )

    # =====================================================
    # 2. Routing + Narrative (sin otros nodos)
    # =====================================================
    state = router_node(state)
    state = narrative_node(state)

    # =====================================================
    # 3. Invariantes de performance
    # =====================================================
    assert (time.time() - start_time) < 1.0, "Greeting smoke test exceeded time budget"

    # =====================================================
    # 4. Invariantes de estado global
    # =====================================================
    assert state.answer is None, "GREETING_QUERY must not produce final answer"
    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # No debe existir análisis cognitivo
    assert state.analysis is None or state.analysis == {}, (
        "GREETING_QUERY must not generate analysis"
    )

    # =====================================================
    # 5. Invariantes del narrative_context institucional
    # =====================================================
    assert state.narrative_context is not None, (
        "GREETING_QUERY must produce narrative_context"
    )
    assert isinstance(state.narrative_context, dict)

    nc = state.narrative_context

    # Tipo narrativo correcto
    assert nc.get("narrative_type") == "institutional", (
        "GREETING_QUERY narrative_type must be 'institutional'"
    )

    # Debe tener foco semántico institucional
    assert "semantic_focus" in nc
    assert isinstance(nc["semantic_focus"], list)
    assert len(nc["semantic_focus"]) > 0

    # No debe contener elementos cognitivos
    forbidden_keys = {
        "operational_analysis",
        "analyst",
        "metrics",
        "risk_ranking",
        "recommendations"
    }

    for key in forbidden_keys:
        assert key not in nc, (
            f"Forbidden cognitive key found in narrative_context: {key}"
        )

    # =====================================================
    # 6. Invariante crítica: NO texto humano
    # =====================================================
    forbidden_terms = [
        "hola",
        "bienvenido",
        "recomienda",
        "debería",
        "puedes",
        "te ayudo"
    ]

    for value in nc.values():
        if isinstance(value, str):
            lower = value.lower()
            for term in forbidden_terms:
                assert term not in lower, (
                    f"Human language detected in narrative_context: {value}"
                )
