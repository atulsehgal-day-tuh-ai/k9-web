import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.ontology_query_node import OntologyQueryNode


def test_f03_002_ontology_query_retrieve_bowtie():
    """
    FASE 3 — OntologyQueryNode
    Test ID: F03_002

    Verifica:
    - Recuperación completa de un bowtie
    - Sin navegación parcial
    """

    # -----------------------------
    # Given: comando canónico ONTOLOGY_QUERY
    # -----------------------------
    state = K9State(
        user_query="TEST_ONTOLOGY_BOWTIE",
        intent="ontology_query_test",
        reasoning=[],
        context_bundle={
            "k9_command": {
                "intent": "ONTOLOGY_QUERY",
                "entity": "bowtie",
                "operation": "retrieve",
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
    # Then: estructura base
    # -----------------------------
    assert result["type"] == "ontology_result"
    assert result["entity"] == "bowtie"
    assert result["operation"] == "retrieve"

    payload = result["payload"]

    # -----------------------------
    # Then: bowtie completo (estructura real)
    # -----------------------------
    assert "bowtie" in payload
    bowtie = payload["bowtie"]

    # Identidad del bowtie
    assert "id_bowtie" in bowtie

    # Riesgo asociado
    assert "riesgo" in bowtie
    assert bowtie["riesgo"]["id"] == "R01"
    assert "nombre" in bowtie["riesgo"]

    # Lado izquierdo (causas)
    assert "causas" in bowtie
    assert isinstance(bowtie["causas"], list)

    # Controles
    assert "controles_criticos" in bowtie
    assert "controles_preventivos" in bowtie
    assert "controles_mitigacion" in bowtie

    # Consecuencias
    assert "consecuencias" in bowtie
    assert isinstance(bowtie["consecuencias"], list)

    # Factores y barreras
    assert "factores_degradacion" in bowtie
    assert "barreras_recuperacion" in bowtie

    # Relaciones explícitas (clave del bowtie)
    assert "relacion causa-control_critico_control_preventivo" in bowtie
    assert "relacion consecuencia-control_mitigacion" in bowtie
    assert "relacion factor_degradacion-control_critico_control_preventivo" in bowtie
    assert "relacion consecuencia-barrera_recuperacion" in bowtie

    # -----------------------------
    # Then: trazabilidad correcta
    # -----------------------------
    trace = result["traceability"]

    assert any(
        f.startswith("07_bowtie_")
        for f in trace["source_files"]
    )

    # -----------------------------
    # Then: huella de razonamiento
    # -----------------------------
    assert any(
        "OntologyQueryNode" in r or "ONTOLOGY_QUERY" in r
        for r in state.reasoning
    )
