# TEST_S01_001 — Inicialización segura del K9State

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State


def test_s01_001_k9state_default_initialization():
    """
    TEST_S01_001
    Verifica que el K9State v3.2 se inicializa correctamente
    sin requerir parámetros obligatorios.
    """

    state = K9State()

    # Campos base
    assert state.user_query == ""
    assert state.intent == ""
    assert state.reasoning == []
    assert state.demo_mode is False

    # Nuevos campos v3.2
    assert state.context_bundle is None
    assert state.signals is None
    assert state.active_event is None
    assert state.analysis is None
    assert state.answer is None
