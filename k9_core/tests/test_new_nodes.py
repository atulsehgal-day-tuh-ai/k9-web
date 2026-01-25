import sys
import os

# Asegurar que /src esté en sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.graph.main_graph import build_k9_graph


def test_proactive_model_node():
    """Test: El intent proactive_model debe ejecutar el nodo 'proactive_model'."""
    graph = build_k9_graph()
    
    result = graph.invoke({"user_query": "explica el modelo proactivo"})
    
    assert "Modelo Proactivo" in result["answer"]
    assert any("Proactive Model Node" in step for step in result["reasoning"])


def test_riesgos_node():
    """Test: El intent riesgos debe ejecutar el nodo 'riesgos'."""
    graph = build_k9_graph()

    result = graph.invoke({"user_query": "cuáles son los riesgos principales"})
    
    assert "Riesgos Operacionales" in result["answer"]
    assert any("Riesgos Node" in step for step in result["reasoning"])


def test_fallback_node():
    """Test: Un intent desconocido debe ejecutar el nodo 'fallback'."""
    graph = build_k9_graph()

    result = graph.invoke({"user_query": "háblame de fútbol"})
    
    assert "no pertenece al dominio" in result["answer"]
    assert any("fallback" in step.lower() for step in result["reasoning"])


def test_routing_paths_exist():
    """Test: Validar que el router reconoce intents válidos."""
    graph = build_k9_graph()

    # Intent greeting → llm
    r1 = graph.invoke({"user_query": "hola"})
    assert r1["answer"] is not None

    # Intent proactive_model → nodo correcto
    r2 = graph.invoke({"user_query": "modelo proactivo"})
    assert "Modelo Proactivo" in r2["answer"]

    # Intent riesgos → nodo correcto
    r3 = graph.invoke({"user_query": "riesgos"})
    assert "Riesgos Operacionales" in r3["answer"]


def test_reasoning_chain_exists():
    """Test: El reasoning debe contener pasos del pipeline base + nodo final."""
    graph = build_k9_graph()

    result = graph.invoke({"user_query": "riesgos"})
    
    assert len(result["reasoning"]) >= 3
    assert "intent" or "Router" in result["reasoning"][0]
