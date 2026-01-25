# tests/f04_004_test_proactive_model_node.py

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.proactive_model_node import proactive_model_node
from src.state.state import K9State


def test_proactive_model_node_f04_004_consumes_operational_analysis():
    """
    FASE 2 — ProactiveModelNode
    Test ID: F04_004

    Verifica:
    - El nodo expone analysis["proactive_explanation"]
    - Consume evidencia desde analysis["operational_analysis"]
    - NO depende de analysis["operational_evidence"] (legacy)
    - Preserva contrato estructural
    """

    # -----------------------------
    # Estado base mínimo válido
    # -----------------------------
    state = K9State(
        user_query="test",
        intent="analysis",
        context_bundle={},
        signals={},
        analysis={
            "risk_summary": {
                "dominant_risk": "R01",
                "relevant_risk": "R02",
            },
            "proactive_comparison": {
                "R01": {
                    "avg_rank_k9": 1,
                    "avg_rank_proactivo": 3,
                    "rank_delta": 2,
                    "alignment_status": "underestimated_by_proactive",
                },
                "R02": {
                    "avg_rank_k9": 2,
                    "avg_rank_proactivo": 2,
                    "rank_delta": 0,
                    "alignment_status": "aligned",
                },
            },
            # Fuente CORRECTA v3.2
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {
                        "occ_count": 2,
                        "opg_count": 1,
                        "controls_affected": ["C01"],
                        "critical_controls_affected": ["C01"],
                    },
                    "R02": {
                        "occ_count": 0,
                        "opg_count": 1,
                        "controls_affected": [],
                        "critical_controls_affected": [],
                    },
                }
            },
        },
        reasoning=[],
    )

    # -----------------------------
    # Ejecución
    # -----------------------------
    state = proactive_model_node(state)

    # -----------------------------
    # Verificaciones de contrato
    # -----------------------------
    assert "proactive_explanation" in state.analysis

    explanation = state.analysis["proactive_explanation"]

    # Estructura base
    assert "alignment_status" in explanation
    assert "explained_risks" in explanation
    assert "explanation" in explanation

    # Riesgos explicados deben ser solo dominant / relevant
    assert set(explanation["explained_risks"]).issubset({"R01", "R02"})

    # Evidencia operacional debe estar reflejada
    r01 = explanation["explanation"].get("R01")
    assert r01 is not None
    assert r01["operational_evidence"] is True

    # R02 no tiene OCC → evidencia falsa
    r02 = explanation["explanation"].get("R02")
    assert r02 is not None
    assert r02["operational_evidence"] is False

    # -----------------------------
    # Asegurar independencia de legacy
    # -----------------------------
    assert "operational_evidence" not in state.analysis
