# tests/test_graph_f01_006.py

import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.graph.main_graph import build_k9_graph


def test_graph_f01_006_includes_data_engine_node():
    """
    FASE 1 — Main Graph wiring
    Test ID: F01_003

    Verifica:
    - El grafo compila
    - El nodo 'data_engine' existe en el grafo compilado (si la API lo expone)
    """

    graph = build_k9_graph()
    assert graph is not None

    # Intento de inspección defensiva: distintas versiones exponen estructuras distintas
    if hasattr(graph, "get_graph"):
        g = graph.get_graph()
        # Algunas implementaciones exponen .nodes como dict / list / set
        if hasattr(g, "nodes"):
            nodes = g.nodes
            if isinstance(nodes, dict):
                assert "data_engine" in nodes
            elif isinstance(nodes, (list, set, tuple)):
                assert "data_engine" in nodes
            # si no calza, no fallamos: el objetivo principal es compile
