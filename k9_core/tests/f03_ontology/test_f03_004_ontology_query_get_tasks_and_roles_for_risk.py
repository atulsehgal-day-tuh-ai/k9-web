import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# FIX ROOT (patrón validado en F03_001 / F03_002 / F03_003)
# -----------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.ontology_query_node import OntologyQueryNode


def test_f03_004_ontology_query_get_tasks_and_roles_for_risk():
    """
    FASE 3 — OntologyQueryNode
    Test ID: F03_004

    Verifica:
    - Resolución ontológica de tareas asociadas a un riesgo
    - Derivación explícita de roles desde tareas
    - Sin uso de data sintética
    - Navegación ontológica directa y trazable
    """

    # ------------------------------------------------------------------
    # Given: comando canónico ONTOLOGY_QUERY
    # ------------------------------------------------------------------
    state = K9State(
        user_query="TEST_ONTOLOGY_TASKS_ROLES",
        intent="ontology_query_test",
        reasoning=[],
        context_bundle={
            "k9_command": {
                "intent": "ONTOLOGY_QUERY",
                "entity": "risk",
                "operation": "get_tasks_and_roles",
                "filters": {
                    "risk_id": "R01"
                },
                "output": "raw"
            }
        }
    )

    node = OntologyQueryNode(ontology_path="data/ontology")

    # ------------------------------------------------------------------
    # When: se ejecuta el nodo ontológico
    # ------------------------------------------------------------------
    state = node(state)
    result = state.context_bundle["ontology_result"]

    # ------------------------------------------------------------------
    # Then: estructura base canónica
    # ------------------------------------------------------------------
    assert result["type"] == "ontology_result"
    assert result["entity"] == "risk"
    assert result["operation"] == "get_tasks_and_roles"

    payload = result["payload"]

    assert payload["source_id"] == "R01"

    # ------------------------------------------------------------------
    # Then: tareas asociadas al riesgo
    # ------------------------------------------------------------------
    assert "tasks" in payload
    assert isinstance(payload["tasks"], list)
    assert len(payload["tasks"]) > 0

    # Las tareas se validan por ID (no por estructura)
    assert any(
        task_id.startswith("MRA_TA_")
        for task_id in payload["tasks"]
    )

    # ------------------------------------------------------------------
    # Then: roles derivados explícitamente desde tareas
    # ------------------------------------------------------------------
    assert "roles" in payload
    assert isinstance(payload["roles"], list)
    assert len(payload["roles"]) > 0

    assert any(
        role_id.startswith("MRA_ROL_")
        for role_id in payload["roles"]
    )

    # ------------------------------------------------------------------
    # Then: trazabilidad ontológica obligatoria
    # ------------------------------------------------------------------
    trace = result["traceability"]

    assert "source_files" in trace
    assert "12_catalogo_tareas_v1.yaml" in trace["source_files"]
    assert trace["filters_applied"]["risk_id"] == "R01"

    # ------------------------------------------------------------------
    # Then: huella de razonamiento
    # ------------------------------------------------------------------
    assert any(
        "OntologyQueryNode" in r or "get_tasks_and_roles" in r
        for r in state.reasoning
    )
