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


def test_comparative_query_with_operational_evidence():
    start_time = time.time()

    # =====================================================
    # 1. Estado inicial — COMPARATIVE_QUERY canónico
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "COMPARATIVE_QUERY",
                "operation": "compare",
                "entity": "risk",
                "output": "narrative",
            }
        }
    )

    # =====================================================
    # 2. Flujo cognitivo completo (sin LLM)
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)               # base estructural
    state = operational_analysis_node(state)      # evidencia operacional
    state = analyst_node(state)                   # razonamiento determinista
    state = narrative_node(state)                 # contexto narrativo

    # =====================================================
    # 3. Invariante de performance
    # =====================================================
    assert (time.time() - start_time) < 1.5, (
        "COMPARATIVE_QUERY with evidence exceeded time budget"
    )

    # =====================================================
    # 4. Invariantes globales del estado
    # =====================================================
    assert state.answer is None, (
        "COMPARATIVE_QUERY must not produce final answer"
    )

    assert state.analysis is not None, (
        "COMPARATIVE_QUERY must produce analysis"
    )

    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # =====================================================
    # 5. Invariantes del análisis cognitivo
    # =====================================================
    # El modo sigue siendo estructural (comparative NO es un modo cognitivo)
    assert state.analysis.get("analysis_mode") == "structural", (
        "COMPARATIVE_QUERY analysis_mode must remain structural"
    )

    assert state.analysis.get("analysis_basis") in {
        "engine_only",
        "engine+operational",
        "operational+engine",
    }

    # Evidencia operacional presente
    assert "operational_evidence" in state.analysis
    assert isinstance(state.analysis["operational_evidence"], dict)

    # =====================================================
    # 6. Invariantes del narrative_context (aquí vive lo comparativo)
    # =====================================================
    nc = state.narrative_context
    assert nc is not None

    assert nc["narrative_type"] == "comparative"
    assert nc["narrative_intent"] == "comparative_explanation"

    # Foco semántico base
    assert "structural_analysis" in nc["semantic_focus"]

    # Evidencia operacional SOLO si existe soporte real
    if state.analysis["operational_evidence"].get("has_operational_support"):
        assert "operational_evidence" in nc["semantic_focus"]
    else:
        assert "operational_evidence" not in nc["semantic_focus"]

    # Comparaciones viven en narrativa
    assert "comparisons" in nc
    assert isinstance(nc["comparisons"], list)
