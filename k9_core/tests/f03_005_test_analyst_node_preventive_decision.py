import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.nodes.analyst_node import analyst_node
from src.state.state import K9State


def test_analyst_node_f03_005_produces_preventive_decision():
    """
    F03_005

    Regla:
    - El AnalystNode debe producir proactive_comparison y preventive_decision
    - Sin depender de proactive_explanation
    - Sin perder capacidades previas
    """

    state = K9State(
        analysis={
            "engine": {
                "period": {"start": "2024-01-01", "end": "2024-01-07"},
                "weekly_signals": {
                    "R01": {"avg_criticidad": 80},
                    "R02": {"avg_criticidad": 40},
                },
                "risk_trends": {
                    "R01": {"trend_direction": "up"},
                    "R02": {"trend_direction": "flat"},
                },
                "observations": {
                    "summary": {
                        "total": 3,
                        "by_type": {"OCC": 2, "OPG": 1}
                    }
                },
                "proactivo": {
                    "R01": {"avg_rank": 3, "weeks": 4},
                    "R02": {"avg_rank": 1, "weeks": 4},
                },
                "audits": {
                    "daily": {
                        "count": 1,
                        "by_tipo": {"SEGURIDAD": 1},
                        "by_origen": {"REACTIVA": 1},
                    }
                },
                "fdo": {
                    "accumulated_12s": {
                        "criticidad_global": 75,
                        "fatiga": 60,
                    }
                },
            },
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {
                        "occ_count": 2,
                        "opg_count": 1,
                        "critical_controls_affected": ["C01"]
                    },
                    "R02": {
                        "occ_count": 0,
                        "opg_count": 1,
                        "critical_controls_affected": []
                    }
                }
            }
        },
        reasoning=[]
    )

    result = analyst_node(state)
    analysis = result.analysis

    # -----------------------------------------
    # Contratos NUEVOS
    # -----------------------------------------
    assert "proactive_comparison" in analysis
    assert "preventive_decision" in analysis

    preventive = analysis["preventive_decision"]

    assert preventive["scenario"] in ("preventive_watch", "proactive_underestimation")
    assert isinstance(preventive["prioritized_risks"], list)

    # R01 debe aparecer porque tiene OCC y control crítico
    assert "R01" in preventive["prioritized_risks"]

    # -----------------------------------------
    # Contratos EXISTENTES (no regresión)
    # -----------------------------------------
    assert "risk_summary" in analysis
    assert "thresholds" in analysis
    assert "audit_evidence" in analysis
    assert "fdo_context" in analysis

    # -----------------------------------------
    # Regla clave: NO depende de proactive_explanation
    # -----------------------------------------
    assert "proactive_explanation" not in analysis
