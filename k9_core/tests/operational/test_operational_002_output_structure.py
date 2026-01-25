import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_node_creates_minimal_operational_output():
    """
    F01_OPERATIONAL_002

    Regla:
    - Dado un K9 command con intent OPERATIONAL_QUERY
    - El OperationalAnalysisNode debe:
        - Crear state.analysis["operational_analysis"]
        - Incluir las claves obligatorias:
            * evidence_by_risk
            * traceability
            * meta
        - NO generar state.answer
        - NO generar narrativa
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "OPERATIONAL_QUERY",
                "entity": "risks",
                "operation": "expose_evidence",
                "output": "analysis",
            }
        },
        analysis=None,
        reasoning=[],
        risk_enrichment={},  # sin evidencia, pero válido
    )

    result = operational_analysis_node(state)

    # 1️⃣ analysis debe existir
    assert result.analysis is not None, "analysis no debe ser None"

    assert "operational_analysis" in result.analysis, (
        "Debe existir analysis['operational_analysis']"
    )

    op = result.analysis["operational_analysis"]

    # 2️⃣ Claves obligatorias
    for key in ("evidence_by_risk", "traceability", "meta"):
        assert key in op, f"Falta clave obligatoria '{key}' en operational_analysis"

    # 3️⃣ Tipos mínimos esperados
    assert isinstance(op["evidence_by_risk"], dict)
    assert isinstance(op["traceability"], list)
    assert isinstance(op["meta"], dict)

    # 4️⃣ Meta mínima
    assert op["meta"].get("semantic_level") == "operational"

    # 5️⃣ No debe generar respuesta humana
    assert result.answer is None, "OperationalAnalysisNode no debe generar answer"

    # 6️⃣ Debe dejar trazabilidad en reasoning
    assert any(
        "operationalanalysisnode" in r.lower()
        for r in result.reasoning
    ), "Debe registrar reasoning del nodo operacional"
