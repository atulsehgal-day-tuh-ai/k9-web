# TEST_S02_001 — Load context básico v3.2

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.load_context import load_context


def test_s02_001_load_context_populates_context_bundle():
    """
    TEST_S02_001
    Verifica que load_context pobla correctamente context_bundle
    sin afectar otros campos del state.
    """

    state = K9State(user_query="test")

    updated_state = load_context(state)

    # El state sigue siendo el mismo objeto
    assert updated_state is state

    # context_bundle debe existir
    assert updated_state.context_bundle is not None
    assert isinstance(updated_state.context_bundle, dict)

    # reasoning debe tener al menos una entrada
    assert len(updated_state.reasoning) >= 1
    assert "Load Context" in updated_state.reasoning[-1]

    # Campos que NO deben tocarse
    assert updated_state.signals is None
    assert updated_state.analysis is None
    assert updated_state.active_event is None
