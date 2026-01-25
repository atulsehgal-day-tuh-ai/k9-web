import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# FIX ROOT (patrón validado en F03_001 / F03_002)
# -----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.ontology_query_node import OntologyQueryNode


def test_f03_003_ontology_query_get_causes_for_risk():
    """
    FASE 3 — OntologyQueryNode
    Test ID: F03_003

    Verifica:
    - Resolución ontológica de causas asociadas a un riesgo
    - Uso explícito del campo 'riesgo_asociado'
    - No uso de data sintética
    - Estructura de salida canónica
    """

    # -------------------------------------------------------------------------
    # Given: comando canónico ONTOLOGY_QUERY
    # -------------------------------------------------------------------------
    state = K9State(
        user_query="TEST_ONTOLOGY_CAUSES",
        intent="ontology_query_test",
        reasoning=[],
        context_bundle={
            "k9_command": {
                "intent": "ONTOLOGY_QUERY",
                "entity": "risk",
                "operation": "get_causes",
                "filters": {
                    "risk_id": "R01"
                },
                "output": "raw"
            }
        }
    )

    node = OntologyQueryNode(ontology_path="data/ontology")

    # -------------------------------------------------------------------------
    # When: se ejecuta el nodo ontológico
    # -------------------------------------------------------------------------
    state = node(state)

    result = state.context_bundle["ontology_result"]

    # -------------------------------------------------------------------------
    # Then: estructura base canónica
    # -------------------------------------------------------------------------
    assert result["type"] == "ontology_result"
    assert result["entity"] == "risk"
    assert result["operation"] == "get_causes"

    # -------------------------------------------------------------------------
    # Then: payload correcto (semántica explícita)
    # -------------------------------------------------------------------------
    payload = result["payload"]

    assert payload["source_id"] == "R01"
    assert "related_entities" in payload
    assert isinstance(payload["related_entities"], list)
    assert len(payload["related_entities"]) > 0

    # Cada causa debe declarar explícitamente su riesgo asociado
    for cause in payload["related_entities"]:
        assert isinstance(cause, dict)
        assert cause.get("riesgo_asociado") == "R01"

    # -------------------------------------------------------------------------
    # Then: trazabilidad obligatoria
    # -------------------------------------------------------------------------
    trace = result["traceability"]

    assert "source_files" in trace
    assert "03_catalogo_causas_v4.yaml" in trace["source_files"]
    assert trace["filters_applied"]["risk_id"] == "R01"

    # -------------------------------------------------------------------------
    # Then: huella de razonamiento
    # -------------------------------------------------------------------------
    assert any(
        "OntologyQueryNode" in r or "get_causes" in r
        for r in state.reasoning
    )
