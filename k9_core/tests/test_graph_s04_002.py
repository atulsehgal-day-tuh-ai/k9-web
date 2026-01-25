# TEST_S04_002 — Integración del AnalystNode al grafo

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.graph.main_graph import build_k9_graph


def test_s04_002_graph_runs_analystnode():
    """
    TEST_S04_002
    Verifica que el AnalystNode se ejecuta dentro del grafo
    y escribe 'analysis' sin romper la respuesta final.
    """

    graph = build_k9_graph()

    result = graph.invoke({
        "user_query": "estado general de seguridad",
        "intent": "general_question"
    })

    # El sistema sigue respondiendo
    assert result.get("answer") is not None

    # AnalystNode debe haber escrito analysis
    assert result.get("analysis") is not None
    assert isinstance(result.get("analysis"), dict)

    # Reasoning debe reflejar la ejecución del AnalystNode
    reasoning = " ".join(result.get("reasoning", []))
    assert "AnalystNode" in reasoning
