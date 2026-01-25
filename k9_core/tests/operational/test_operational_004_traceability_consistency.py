import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.operational_analysis_node import operational_analysis_node
from src.state.state import K9State


def test_operational_node_traceability_is_consistent_with_occ_records():
    """
    F01_OPERATIONAL_004

    Regla:
    - traceability debe existir siempre
    - traceability debe ser una lista
    - Su largo debe coincidir con la cantidad de OCC/OPG procesados
    - Cada entrada debe contener claves mínimas:
        * occ_id
        * risk_id
        * control_id
        * audit_id
    """

    # Simular evidencia OCC mínima
    risk_enrichment = {
        "occ_records": [
            {
                "id": "OCC_001",
                "risk_id": "R01",
                "control_id": "C01",
                "audit_id": "A01",
                "type": "OCC",
            },
            {
                "id": "OCC_002",
                "risk_id": "R02",
                "control_id": "C02",
                "audit_id": "A02",
                "type": "OPG",
            },
        ]
    }

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
        risk_enrichment=risk_enrichment,
    )

    result = operational_analysis_node(state)

    op = result.analysis["operational_analysis"]

    traceability = op.get("traceability")

    # 1️⃣ Traceability debe ser lista
    assert isinstance(traceability, list), "traceability debe ser una lista"

    # 2️⃣ Largo consistente
    assert len(traceability) == 2, (
        "traceability debe tener una entrada por cada OCC/OPG procesado"
    )

    # 3️⃣ Claves mínimas por entrada
    required_keys = {"occ_id", "risk_id", "control_id", "audit_id"}

    for t in traceability:
        assert isinstance(t, dict)
        missing = required_keys - set(t.keys())
        assert not missing, f"Entrada de trazabilidad incompleta: faltan {missing}"
