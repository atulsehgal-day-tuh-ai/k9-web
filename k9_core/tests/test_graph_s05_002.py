# TEST_S05_002 — Integración del NarrativeNode al grafo

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.graph.main_graph import build_k9_graph


def test_s05_002_graph_runs_narrativenode():
    """
    TEST_S05_002
    Verifica que el NarrativeNode se ejecuta dentro del grafo
    y genera 'answer' a partir del 'analysis'.
    """

    graph = build_k9_graph()

    result = graph.invoke({
        "user_query": "resumen semanal",
        "intent": "general_question"
    })

    # answer debe existir (NarrativeNode)
    assert result.get("answer") is not None
    assert isinstance(result.get("answer"), str)
    assert len(result.get("answer")) > 20

    # analysis debe existir (AnalystNode)
    assert result.get("analysis") is not None
    assert isinstance(result.get("analysis"), dict)

    # reasoning debe incluir NarrativeNode
    reasoning = " ".join(result.get("reasoning", []))
    assert "NarrativeNode" in reasoning
