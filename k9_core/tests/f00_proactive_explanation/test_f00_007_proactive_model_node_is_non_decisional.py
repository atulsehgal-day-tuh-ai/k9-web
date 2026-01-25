import sys
from pathlib import Path
import copy

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.proactive_model_node import proactive_model_node


def test_f00_007_proactive_model_node_is_non_decisional():
    """
    F00_007 — ProactiveModelNode:
    - Genera proactive_explanation
    - NO altera preventive_decision
    - NO recalcula evidencia
    """

    state = K9State(
        user_query="Compare proactive vs K9",
        intent="proactive_explanation",
        analysis={
            "risk_summary": {
                "dominant_risk": "R01",
                "relevant_risk": "R02",
            },
            "proactive_comparison": {
                "R01": {"alignment_status": "underestimated_by_proactive"},
                "R02": {"alignment_status": "aligned"},
            },
            "preventive_decision": {
                "prioritized_risks": ["R01"],
                "scenario": "proactive_underestimation",
            },
            "operational_analysis": {
                "evidence_by_risk": {
                    "R01": {"occ_count": 2, "critical_controls_affected": ["C01"]},
                },
                "traceability": [],
                "meta": {},
            },
        },
        reasoning=[]
    )

    decision_before = copy.deepcopy(state.analysis["preventive_decision"])

    result = proactive_model_node(state)

    assert "proactive_explanation" in result.analysis, (
        "Debe exponer analysis['proactive_explanation']"
    )

    explanation = result.analysis["proactive_explanation"]
    assert isinstance(explanation, dict)

    # Root: decisión intacta
    assert result.analysis["preventive_decision"] == decision_before, (
        "ProactiveModelNode no debe alterar preventive_decision"
    )
