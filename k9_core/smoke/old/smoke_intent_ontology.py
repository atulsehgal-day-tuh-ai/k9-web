"""
K9 Mining Safety — Smoke Test ONTOLOGY_QUERY (NO LLM)

Valida que el intent ONTOLOGY_QUERY:
- Sea aceptado por el Router
- NO ejecute OperationalAnalysisNode
- NO ejecute AnalystNode
- Ejecute NarrativeNode
- Construya narrative_context ontológico
- NO produzca texto humano
- NO dependa de LLM
"""

import sys
import time
from pathlib import Path

# -----------------------------------------------------
# Exponer ROOT del repo
# -----------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.router import router_node
from src.nodes.narrative_node import narrative_node


def test_ontology_query_routes_to_structural_narrative_only():
    start_time = time.time()

    # =====================================================
    # 1. Estado inicial: ONTOLOGY_QUERY canónico
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "ONTOLOGY_QUERY",
                "entity": "risk",
                "output": "narrative",
            }
        }
    )

    # =====================================================
    # 2. Routing + Narrative (sin otros nodos)
    # =====================================================
    state = router_node(state)
    state = narrative_node(state)

    # =====================================================
    # 3. Invariante de performance
    # =====================================================
    assert (time.time() - start_time) < 1.0, "Ontology smoke test exceeded time budget"

    # =====================================================
    # 4. Invariantes de estado global
    # =====================================================
    assert state.answer is None, "ONTOLOGY_QUERY must not produce final answer"
    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # No debe existir análisis cognitivo
    assert state.analysis is None or state.analysis == {}, (
        "ONTOLOGY_QUERY must not generate analysis"
    )

    # =====================================================
    # 5. Invariantes del narrative_context ontológico
    # =====================================================
    assert state.narrative_context is not None, (
        "ONTOLOGY_QUERY must produce narrative_context"
    )
    assert isinstance(state.narrative_context, dict)

    nc = state.narrative_context

    # Tipo narrativo correcto
    assert nc.get("narrative_type") == "ontology", (
        "ONTOLOGY_QUERY narrative_type must be 'ontology'"
    )

    # Intención explicativa correcta
    assert nc.get("narrative_intent") == "ontology_definition", (
        "ONTOLOGY_QUERY narrative_intent must be 'ontology_definition'"
    )

    # Debe existir foco semántico estructural
    assert "semantic_focus" in nc
    assert isinstance(nc["semantic_focus"], list)

    # Puede estar vacío o contener ontology_context,
    # pero NO debe contener foco cognitivo
    forbidden_focus = {
        "operational_evidence",
        "analytical_results",
        "risk_trends",
        "predictions",
    }

    for focus in nc["semantic_focus"]:
        assert focus not in forbidden_focus, (
            f"Forbidden semantic focus for ONTOLOGY_QUERY: {focus}"
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
        "te ayudo",
    ]

    for value in nc.values():
        if isinstance(value, str):
            lower = value.lower()
            for term in forbidden_terms:
                assert term not in lower, (
                    f"Human language detected in narrative_context: {value}"
                )
