import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.narrative_node import narrative_node
from src.state.state import K9State


def test_narrative_node_no_reasoning_no_language():
    """
    F03_NARRATIVE_003

    Regla:
    - NarrativeNode NO debe:
        - razonar
        - recomendar
        - generar narrativa humana
    - Solo prepara contexto semántico
    """

    analysis_snapshot = {
        "period": {"window": "last_4_weeks"},
        "risk_summary": {"dominant_risk": "R01"},
    }

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "ANALYTICAL_QUERY",
                "entity": "risks",
                "operation": "analyze",
                "output": "narrative",
            }
        },
        analysis=analysis_snapshot.copy(),
        reasoning=[],
    )

    result = narrative_node(state)

    # 1️⃣ No debe generar respuesta humana
    assert result.answer is None

    # 2️⃣ No debe modificar analysis
    assert result.analysis == analysis_snapshot, (
        "NarrativeNode no debe modificar analysis."
    )

    # 3️⃣ Reasoning debe ser técnico (sin lenguaje humano)
    forbidden_keywords = [
        "debería",
        "recomienda",
        "sugiere",
        "es importante",
        "acción",
        "priorizar",
        "urgente",
        "implica",
        "significa",
    ]

    for r in result.reasoning:
        r_lower = r.lower()
        for kw in forbidden_keywords:
            assert kw not in r_lower, (
                f"NarrativeNode contiene lenguaje humano prohibido: '{kw}'"
            )
