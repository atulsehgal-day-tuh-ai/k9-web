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


def test_comparative_query_structural_path():
    start_time = time.time()

    # =====================================================
    # 1. Estado inicial — comando comparativo canónico
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
    # 2. Flujo cognitivo completo
    # =====================================================
    state = router_node(state)
    state = data_engine_node(state)
    state = operational_analysis_node(state)   # esperado: skip
    state = analyst_node(state)
    state = narrative_node(state)

    # =====================================================
    # 3. Performance
    # =====================================================
    assert (time.time() - start_time) < 1.5

    # =====================================================
    # 4. Invariantes globales
    # =====================================================
    assert state.answer is None
    assert state.analysis is not None
    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0

    # =====================================================
    # 5. Invariantes del análisis
    # =====================================================
    assert state.analysis.get("analysis_mode") == "structural"
    assert state.analysis.get("analysis_basis") == "engine_only"

    # NO debe haber análisis operacional
    assert not state.analysis.get("operational_evidence", {}).get(
        "has_operational_support", True
    )

    # =====================================================
    # 6. Invariantes narrativos (AQUÍ vive la comparación)
    # =====================================================
    nc = state.narrative_context
    assert nc is not None

    assert nc["narrative_type"] == "comparative"
    assert "structural_analysis" in nc["semantic_focus"]

    # Comparación expresada SEMÁNTICAMENTE
    assert "comparisons" in nc
    assert isinstance(nc["comparisons"], list)
    assert len(nc["comparisons"]) > 0

    # No forzar resultados analíticos
    assert "analytical_results" not in nc["semantic_focus"]
    assert "operational_evidence" not in nc["semantic_focus"]
