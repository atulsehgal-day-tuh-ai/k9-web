# tests/test_analyst_f01_007.py

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def _mock_engine_analysis():
    """
    Engine mock mínimo, coherente con FASE 1.
    No usa lunes crítico.
    """
    return {
        "risk_trends": {
            "R01": {
                "weekly_values": [0.4, 0.45, 0.5],
                "trend_direction": "up",
                "confidence": "high",
            },
            "R02": {
                "weekly_values": [0.7, 0.7, 0.69],
                "trend_direction": "flat",
                "confidence": "high",
            },
        },
        "weekly_signals": {
            "R01": {"avg_score": 0.48},
            "R02": {"avg_score": 0.70},
        },
        "observations": {
            "R01": {
                "weekly_counts": {"W1": 2, "W2": 3, "W3": 4},
                "total": 9,
                "support_level": "strong",
            },
            "R02": {
                "weekly_counts": {"W1": 1, "W2": 1, "W3": 1},
                "total": 3,
                "support_level": "moderate",
            },
        },
        "proactivo_vs_k9": {
            "R01": {
                "proactive_rank": 4,
                "k9_rank": 2,
                "rank_delta": 2,
                "alignment_status": "underestimated_by_proactive",
            },
            "R02": {
                "proactive_rank": 1,
                "k9_rank": 1,
                "rank_delta": 0,
                "alignment_status": "aligned",
            },
        },
        "threshold_definition": {
            "min_weeks_trend": 3,
            "obs_support_required": True,
        },
        "threshold_flags": {
            "R01": {
                "threshold_state": "approaching_threshold",
                "weeks_considered": 3,
                "rationale_flags": {
                    "trend_up": True,
                    "obs_support": True,
                },
            },
            "R02": {
                "threshold_state": "below_threshold",
                "weeks_considered": 3,
                "rationale_flags": {
                    "trend_up": False,
                    "obs_support": False,
                },
            },
        },
    }


def test_analyst_f01_007_consolidates_engine_analysis():
    """
    FASE 1 — AnalystNode consolidation
    Test ID: F01_007

    Verifica:
    - analysis["engine"] no se pierde
    - Se construyen las secciones cognitivas clave
    - No se usan signals
    """

    state = K9State(
        user_query="test analyst consolidation"
    )

    # Simulamos contexto mínimo
    state.context_bundle = {
        "version_contexto": "v3.1",
        "areas_operacionales": ["Mina", "Planta"],
    }

    # Simulamos salida del DataEngineNode
    state.analysis = {
        "engine": _mock_engine_analysis()
    }

    result = analyst_node(state)

    # -----------------------------
    # Asserts estructurales
    # -----------------------------
    assert "engine" in result.analysis
    assert "risk_summary" in result.analysis
    assert "risk_trajectories" in result.analysis
    assert "observations_summary" in result.analysis
    assert "proactive_comparison" in result.analysis
    assert "thresholds" in result.analysis

    # -----------------------------
    # Asserts cognitivos clave
    # -----------------------------
    assert result.analysis["risk_summary"]["dominant_risk"] == "R02"
    assert result.analysis["risk_summary"]["relevant_risk"] == "R01"

    assert (
        result.analysis["thresholds"]["risks"]["R01"]["threshold_state"]
        == "approaching_threshold"
    )

    # -----------------------------
    # Regla FASE 1: engine intacto
    # -----------------------------
    assert result.analysis["engine"]["risk_trends"]["R01"]["trend_direction"] == "up"

    # -----------------------------
    # Reasoning presente
    # -----------------------------
    assert any(
        "AnalystNode v1.0" in r for r in result.reasoning
    )
