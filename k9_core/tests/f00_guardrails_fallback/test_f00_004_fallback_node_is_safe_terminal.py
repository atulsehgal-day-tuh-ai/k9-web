import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.fallback_node import fallback_node


def test_f00_004_fallback_node_is_safe_terminal():
    """
    F00_004 — FallbackNode:
    - Responde con mensaje seguro
    - NO toca analysis
    - NO introduce decisiones
    """

    state = K9State(
        user_query="Tell me a joke",
        intent="out_of_domain",
        analysis={
            "engine": {"dummy": True}
        },
        reasoning=[]
    )

    result = fallback_node(state)

    # Answer existe
    assert result.answer is not None
    assert isinstance(result.answer, str)

    # Analysis intacto
    assert result.analysis == state.analysis

    # No decisiones nuevas
    assert "preventive_decision" not in result.analysis
