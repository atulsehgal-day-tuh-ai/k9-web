import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.nodes.router import router_node
from src.state.state import K9State


def test_router_requires_k9_command():
    """
    El router no debe operar sin un K9 command explícito.
    """

    state = K9State(
        user_query="dummy",
        context_bundle={},  # ❌ sin k9_command
        reasoning=[]
    )

    with pytest.raises(ValueError) as exc:
        router_node(state)

    assert "k9_command" in str(exc.value)
