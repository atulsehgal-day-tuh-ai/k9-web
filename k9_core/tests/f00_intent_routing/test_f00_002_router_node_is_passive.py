import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.router import router_node


def test_f00_002_router_node_is_passive():
    """
    F00_002 — RouterNode:
    - NO muta analysis
    - NO borra decisiones
    - Solo enruta por intent
    """

    state = K9State(
        user_query="Show me the risk summary",
        intent="risk_summary",
        analysis={
            "preventive_decision": {
                "prioritized_risks": ["R01"]
            }
        },
        reasoning=[]
    )

    result = router_node(state)

    # Analysis intacto
    assert result.analysis == state.analysis

    # Decision intacta
    assert result.analysis["preventive_decision"]["prioritized_risks"] == ["R01"]

    # Router solo deja huella en reasoning
    assert len(result.reasoning) >= 1
