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


def test_analytical_query_with_engine_evidence_full_path():
    """
    Smoke test — ANALYTICAL_QUERY con evidencia agregada (Modo 1 real)

    Flujo validado:
    engine → analyst → narrative

    Nota:
    - OperationalAnalysisNode puede NO ejecutarse
    - La evidencia proviene del engine (síntesis), no de drill-down
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
    # 2. Flujo cognitivo REAL
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)              # engine (obligatorio)
    state = operational_analysis_node(state)     # puede skippear
    state = analyst_node(state)                  # razonamiento
    state = narrative_node(state)                # curaduría narrativa

    # =====================================================
    # 3. Performance
    # =====================================================
    assert (time.time() - start) < 1.5, (
        "Analytical-with-evidence smoke test exceeded time budget"
    )

    # =====================================================
    # 4. Invariantes cognitivas
    # =====================================================
    assert state.analysis is not None
    assert isinstance(state.analysis, dict)
    assert len(state.analysis) > 0

    # Engine siempre presente
    assert "engine" in state.analysis

    # Evidencia DERIVADA presente (no drill-down)
    assert "operational_evidence" in state.analysis
    op = state.analysis["operational_evidence"]
    assert isinstance(op, dict)

    # Campos mínimos esperados
    assert "has_operational_support" in op
    assert "supported_risks" in op

    # El analyst realmente ejecutó
    assert any(
        "AnalystNode: deterministic reasoning executed" in r
        for r in state.reasoning
    )

    # =====================================================
    # 5. Invariantes narrativas
    # =====================================================
    assert state.narrative_context is not None
    nc = state.narrative_context

    assert nc.get("narrative_type") == "analytical"
    assert nc.get("narrative_intent") is not None

    # El foco es analítico, no operacional
    assert "analytical_results" in nc.get("semantic_focus", [])

    # =====================================================
    # 6. Invariantes negativas
    # =====================================================
    assert state.answer is None, (
        "Smoke test must not generate human answer"
    )
