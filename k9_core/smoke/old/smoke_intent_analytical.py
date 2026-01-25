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


def test_analytical_query_structural_cognitive_path():
    """
    Smoke test — ANALYTICAL_QUERY (estructural)

    Valida:
    - Ejecución cognitiva real
    - Uso directo del engine
    - Independencia de OperationalAnalysisNode
    """

    start = time.time()

    # =====================================================
    # 1. Estado inicial — comando canónico
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
    # 2. Flujo cognitivo REAL (sin operacional)
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)     # ← engine obligatorio
    state = analyst_node(state)
    state = narrative_node(state)

    # =====================================================
    # 3. Performance
    # =====================================================
    assert (time.time() - start) < 1.5, "Analytical smoke test exceeded time budget"

    # =====================================================
    # 4. Invariantes cognitivas
    # =====================================================
    assert state.analysis is not None
    assert isinstance(state.analysis, dict)
    assert len(state.analysis) > 0, "ANALYTICAL_QUERY must produce analysis"

    # Engine debe existir
    assert "engine" in state.analysis, "Engine output must be present in analysis"

    # Razonamiento trazable
    assert isinstance(state.reasoning, list)
    assert any("AnalystNode" in r for r in state.reasoning)

    # =====================================================
    # 5. Invariantes narrativas
    # =====================================================
    assert state.narrative_context is not None
    nc = state.narrative_context

    assert nc.get("narrative_type") == "analytical"
    assert nc.get("narrative_intent") is not None
    assert isinstance(nc.get("conceptual_axes"), list)

    # =====================================================
    # 6. Invariantes negativas
    # =====================================================
    assert state.answer is None, "Smoke test must not generate human answer"
