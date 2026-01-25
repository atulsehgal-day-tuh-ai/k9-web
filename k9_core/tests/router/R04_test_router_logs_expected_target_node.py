import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.router import router_node
from src.state.state import K9State


def test_router_logs_expected_target_node():
    """
    R03 — El router debe dejar trazabilidad explícita:
    intent validado + nodo esperado.
    """

    state = K9State(
        user_query="dummy",
        context_bundle={
            "k9_command": {
                "intent": "ONTOLOGY_QUERY",
                "entity": "risk",
                "operation": "retrieve",
                "filters": {"risk_id": "R01"},
                "output": "raw",
            }
        },
        reasoning=[]
    )

    new_state = router_node(state)

    assert any(
        "ONTOLOGY_QUERY" in r and "OntologyQueryNode" in r
        for r in new_state.reasoning
    ), "Router did not log expected node for ONTOLOGY_QUERY"
