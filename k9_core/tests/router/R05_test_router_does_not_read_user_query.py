import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.router import router_node
from src.state.state import K9State


def test_router_does_not_use_user_query():
    """
    El router NO debe usar user_query para nada.
    Esta prueba asegura que valores absurdos no afectan el resultado.
    """

    state = K9State(
        user_query="¿qué crees tú que debería hacer la empresa?",
        context_bundle={
            "k9_command": {
                "intent": "SYSTEM_QUERY",
                "entity": "data_coverage",
                "operation": "summarize",
                "output": "summary",
            }
        },
        reasoning=[]
    )

    new_state = router_node(state)

    assert new_state.intent == "SYSTEM_QUERY"
