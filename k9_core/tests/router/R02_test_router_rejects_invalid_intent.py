import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


import pytest
from src.nodes.router import router_node
from src.state.state import K9State


def test_router_rejects_invalid_intent():
    """
    R02 — El router debe rechazar intents fuera del set cerrado K9.
    """

    state = K9State(
        user_query="dummy",
        context_bundle={
            "k9_command": {
                "intent": "FREE_TEXT_QUERY",  # ❌ no permitido
                "entity": "observations",
                "operation": "count",
                "output": "raw",
            }
        },
        reasoning=[]
    )

    with pytest.raises(ValueError) as exc:
        router_node(state)

    assert "Invalid K9 intent" in str(exc.value)
