import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

# =====================================================
# PYTHON PATH (clave para smoke tests fuera de /tests)
# =====================================================
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SRC_PATH))


# =====================================================
# Imports reales del sistema
# =====================================================
from state.state import K9State
from nodes.narrative_node import narrative_node


def test_narrative_structural_analysis_mode():
    """
    Micro smoke — NarrativeNode con análisis estructural (engine-only)

    Valida:
    - No evidencia operacional
    - No inferencia analítica
    - Riesgo dominante abstracto
    """

    start = time.time()

    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "ANALYTICAL_QUERY",
                "operation": "status",
                "entity": "risk",
                "output": "narrative",
            }
        },
        analysis={
            "analysis_mode": "structural",
            "analysis_basis": "engine_only",
            "risk_summary": {
                "dominant_risk": "R02",
            },
        },
    )

    state = narrative_node(state)

    # Performance
    assert (time.time() - start) < 0.5

    nc = state.narrative_context
    assert nc["narrative_type"] == "analytical"

    # ✅ Invariantes semánticos CORRECTOS
    assert nc["semantic_focus"] == ["structural_analysis"]

    # ❌ No debe aparecer inferencia analítica
    assert "analytical_results" not in nc["semantic_focus"]
    assert "operational_evidence" not in nc["semantic_focus"]

    # Riesgo dominante abstracto
    assert "R02" in nc["key_risks"]



def test_narrative_evidence_based_analysis_mode():
    """
    Micro smoke — NarrativeNode con evidencia operacional REAL

    Valida:
    - Evidencia operacional presente
    - Riesgos soportados correctamente
    """

    start = time.time()

    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "ANALYTICAL_QUERY",
                "operation": "status",
                "entity": "risk",
                "output": "narrative",
            }
        },
        analysis={
            "analysis_mode": "evidence_based",
            "risk_summary": {
                "dominant_risk": "R01",
            },
            # 👇 Forma REAL consumida por NarrativeNode
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {
                        "occ_count": 3,
                        "opg_count": 1,
                        "critical_controls_affected": ["CC-01"],
                    }
                }
            },
        },
    )

    state = narrative_node(state)

    # =====================================================
    # Performance
    # =====================================================
    assert (time.time() - start) < 0.5

    nc = state.narrative_context

    assert nc["narrative_type"] == "analytical"

    # =====================================================
    # Invariantes semánticos
    # =====================================================
    assert "analytical_results" in nc["semantic_focus"]
    assert "operational_evidence" in nc["semantic_focus"]

    # =====================================================
    # Riesgo soportado por evidencia
    # =====================================================
    assert "R01" in nc["key_risks"]
