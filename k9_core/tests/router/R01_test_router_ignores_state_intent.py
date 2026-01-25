import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.nodes.router import router_node
from src.state.state import K9State


def test_router_ignores_state_intent_and_uses_k9_command():
    """
    R01 — El router ignora state.intent como input.
    Usa exclusivamente context_bundle["k9_command"]["intent"].
    """

    state = K9State(
        user_query="dummy",
        intent="ANALYTICAL_QUERY",  # ruido legacy
        context_bundle={
            "k9_command": {
                "intent": "OPERATIONAL_QUERY",
                "entity": "observations",
                "operation": "count",
                "time": {"type": "relative", "value": "last_week"},
                "output": "raw",
            }
        },
        reasoning=[]
    )

    new_state = router_node(state)

    # state.intent debe quedar DERIVADO del comando
    assert new_state.intent == "OPERATIONAL_QUERY"

    # Trazabilidad clara
    assert any(
        "OPERATIONAL_QUERY" in r for r in new_state.reasoning
    ), "Router did not log validated intent"
