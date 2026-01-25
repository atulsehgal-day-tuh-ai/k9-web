import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.narrative_node import narrative_node
from src.state.state import K9State


def test_narrative_node_f06_001_reads_preventive_decision():
    """
    F06_001

    Regla:
    - NarrativeNode NO decide ni prioriza
    - Solo comunica preventive_decision y proactive_comparison
    - Fallback contextual por áreas se conserva
    """

    state = K9State(
        analysis={
            "risk_summary": {
                "dominant_risk": "R01",
                "relevant_risk": "R02",
            },
            "proactive_comparison": {
                "R01": {
                    "alignment_status": "underestimated_by_proactive"
                }
            },
            "preventive_decision": {
                "scenario": "proactive_underestimation",
                "prioritized_risks": ["R01", "R03"],
                "decision_basis": {
                    "sources": ["operational_analysis", "proactive_comparison"]
                },
                "recommendation": "Priorizar vigilancia preventiva"
            },
            "areas_analizadas": ["Mina", "Planta"],
        },
        user_query="¿Qué pasaría si el modelo se equivoca?",
        intent="proactive_model_contrafactual",
        reasoning=[]
    )

    result = narrative_node(state)

    # -------------------------------------------------
    # Validación básica de respuesta
    # -------------------------------------------------
    assert result.answer is not None
    assert isinstance(result.answer, str)

    # Debe comunicar riesgos priorizados
    assert "R01" in result.answer
    assert "R03" in result.answer

    # -------------------------------------------------
    # Validación de rol: NO hay decisión nueva
    # -------------------------------------------------
    # Narrative no debe inventar campos
    assert "prioritization" not in result.answer.lower()
    assert "rank" not in result.answer.lower()

    # -------------------------------------------------
    # Reasoning registrado
    # -------------------------------------------------
    assert any(
        "preventive_decision" in r or "NarrativeNode" in r
        for r in result.reasoning
    )


def test_narrative_node_f06_002_fallback_keeps_areas():
    """
    F06_002

    Regla:
    - Si no hay preventive_decision ni proactive_comparison,
      Narrative debe usar fallback con áreas_analizadas
    """

    state = K9State(
        analysis={
            "areas_analizadas": ["Rajo Abierto", "Chancado"]
        },
        user_query="Dame un resumen",
        intent="general",
        reasoning=[]
    )


    result = narrative_node(state)

    assert result.answer is not None
    assert "Rajo Abierto" in result.answer
    assert "Chancado" in result.answer
    assert "no se dispone de información suficiente" in result.answer.lower()
