"""
K9 Mining Safety — Smoke Test
Intent: TEMPORAL_RELATION_QUERY
Modo: Core cognitivo determinista (SIN LLM)

Valida:
- Routing correcto
- Soporte de análisis estructural (engine-only)
- No dependencia de evidencia operacional
- Narrative coherente con análisis temporal
- Sin texto humano
"""

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
from src.nodes.operational_analysis_node import operational_analysis_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node


def test_temporal_query_structural_path():
    start_time = time.time()

    # =====================================================
    # 1. Estado inicial — comando canónico temporal
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "TEMPORAL_RELATION_QUERY",
                "operation": "trend",
                "entity": "risk",
                "output": "narrative",
            }
        }
    )

    # =====================================================
    # 2. Flujo cognitivo completo (sin LLM)
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)                 # fuente estructural
    state = operational_analysis_node(state)        # esperado: skip
    state = analyst_node(state)                     # análisis estructural
    state = narrative_node(state)                   # contexto narrativo

    # =====================================================
    # 3. Invariante de performance
    # =====================================================
    assert (time.time() - start_time) < 1.5, (
        "TEMPORAL_RELATION_QUERY smoke test exceeded time budget"
    )

    # =====================================================
    # 4. Invariantes globales del estado
    # =====================================================
    assert state.answer is None, (
        "TEMPORAL_RELATION_QUERY must not generate final answer"
    )

    assert state.analysis is not None, (
        "TEMPORAL_RELATION_QUERY must produce analysis"
    )

    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # =====================================================
    # 5. Invariantes del análisis cognitivo
    # =====================================================
    assert state.analysis.get("analysis_mode") == "structural", (
        "TEMPORAL_RELATION_QUERY must support structural analysis mode"
    )

    # =====================================================
    # 6. Invariantes del contexto narrativo
    # =====================================================
    nc = state.narrative_context
    assert nc is not None, "Narrative context must exist"

    assert nc.get("narrative_type") == "analytical", (
        "TEMPORAL_RELATION_QUERY narrative_type must be 'analytical'"
    )

    # Foco semántico correcto (NO forzado)
    assert "structural_analysis" in nc.get("semantic_focus", []), (
        "Structural temporal analysis must expose 'structural_analysis' focus"
    )

    assert "analytical_results" not in nc.get("semantic_focus", []), (
        "Structural temporal analysis must not expose analytical_results"
    )

    assert "operational_evidence" not in nc.get("semantic_focus", []), (
        "Structural temporal analysis must not expose operational_evidence"
    )

    # Marcadores temporales — condicionales
    assert isinstance(nc.get("temporal_markers"), list), (
        "temporal_markers must exist as list (even if empty)"
    )
