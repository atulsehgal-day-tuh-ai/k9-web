import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.ontology_query_node import OntologyQueryNode


def test_f03_001_ontology_query_get_controls_for_risk():
    """
    FASE 3 — OntologyQueryNode
    Test ID: F03_001

    Verifica:
    - Resolución ontológica de controles asociados a un riesgo
    - No uso de data sintética
    - Estructura de salida canónica
    """

    # -----------------------------
    # Given: comando canónico ONTOLOGY_QUERY
    # -----------------------------
    state = K9State(
        user_query="TEST_ONTOLOGY_QUERY",
        intent="ontology_query_test",
        reasoning=[],
        context_bundle={
            "k9_command": {
                "intent": "ONTOLOGY_QUERY",
                "entity": "risk",
                "operation": "get_controls",
                "filters": {
                    "risk_id": "R01"
                },
                "output": "raw"
            }
        }
    )


    node = OntologyQueryNode(ontology_path="data/ontology")

    # -----------------------------
    # When: se ejecuta el nodo ontológico
    # -----------------------------
    state = node(state)

    result = state.context_bundle["ontology_result"]


    # -----------------------------
    # Then: estructura base correcta
    # -----------------------------
    assert result["type"] == "ontology_result"
    assert result["entity"] == "risk"
    assert result["operation"] == "get_controls"

    # -----------------------------
    # Then: payload contiene entidades relacionadas
    # -----------------------------
    payload = result["payload"]

    assert "source_id" in payload
    assert payload["source_id"] == "R01"
    assert "related_entities" in payload
    assert isinstance(payload["related_entities"], list)
    assert len(payload["related_entities"]) > 0

    # -----------------------------
    # Then: trazabilidad obligatoria
    # -----------------------------
    trace = result["traceability"]

    assert "source_files" in trace
    assert "01_catalogo_riesgos_v8.yaml" in trace["source_files"]
    assert trace["filters_applied"]["risk_id"] == "R01"

    # -----------------------------
    # Then: reasoning deja huella
    # -----------------------------
    assert any(
        "OntologyQueryNode" in r or "ONTOLOGY_QUERY" in r
        for r in state.reasoning
    )
