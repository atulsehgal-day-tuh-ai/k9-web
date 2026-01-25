import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.graph.main_graph import build_k9_graph


def test_bowtie_node():
    """Test: El intent bowtie debe ejecutar correctamente el nodo BowTie."""

    graph = build_k9_graph()

    # Caso de prueba principal
    result = graph.invoke({"user_query": "explica el bowtie"})

    # Verificaciones principales
    assert result["intent"] == "bowtie"
    assert "BowTie" in result["answer"]
    assert "causas" in result["answer"].lower()
    assert "consecuencias" in result["answer"].lower()

    # Verificación cognitiva (razonamiento)
    reasoning = " ".join(result["reasoning"]).lower()
    assert "intent detected" in reasoning
    assert "domain guardrail" in reasoning
    assert "router node" in reasoning
    assert "bowtie node" in reasoning


def test_bowtie_in_router_paths():
    """Test: El router debe conocer la ruta para 'bowtie'."""

    graph = build_k9_graph()

    r = graph.invoke({"user_query": "que es un bowtie en seguridad"})

    assert r["intent"] == "bowtie"
    assert "BowTie" in r["answer"]
