# TEST_S01_002 — Serialización segura del K9State

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State


def test_s01_002_k9state_serialization():
    """
    TEST_S01_002
    Verifica que el K9State v3.2 se serializa correctamente a dict
    y conserva todos los campos esperados.
    """

    state = K9State(
        user_query="test query",
        intent="test_intent",
        reasoning=["step1", "step2"],
        demo_mode=True
    )

    data = state.model_dump()

    assert isinstance(data, dict)

    expected_keys = {
        "user_query",
        "intent",
        "reasoning",
        "demo_mode",
        "context_bundle",
        "signals",
        "active_event",
        "analysis",
        "answer",
    }

    assert expected_keys.issubset(set(data.keys()))
