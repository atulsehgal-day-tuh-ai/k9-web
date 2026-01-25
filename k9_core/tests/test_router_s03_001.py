# TEST_S03_001 — Router compatible con K9State v3.2

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.graph.main_graph import build_k9_graph


def test_s03_001_router_routes_valid_intent():
    """
    TEST_S03_001
    Verifica que el router enruta correctamente un intent válido
    usando K9State v3.2.
    """

    graph = build_k9_graph()

    state_input = {
        "user_query": "explica el bowtie",
        "intent": "bowtie"
    }

    result = graph.invoke(state_input)

    assert result["intent"] == "bowtie"
    assert result["answer"] is not None


def test_s03_001_router_fallback_on_invalid_intent():
    """
    TEST_S03_001
    Verifica que el router activa fallback
    cuando el intent no es reconocido o es fuera de dominio.
    """

    graph = build_k9_graph()

    state_input = {
        "user_query": "algo extraño",
        "intent": "intent_invalido"
    }

    result = graph.invoke(state_input)

    assert result["intent"] in ["out_of_domain", "fallback"]
    assert result["answer"] is not None
