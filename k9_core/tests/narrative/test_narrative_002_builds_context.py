import sys
from pathlib import Path

# =====================================================
# Explicit project root resolution
# =====================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.nodes.narrative_node import narrative_node
from src.state.state import K9State


def test_narrative_node_builds_structured_context():
    """
    F03_NARRATIVE_002

    Regla:
    - Con output == narrative
    - El NarrativeNode debe:
        - Crear state.narrative_context
        - Respetar la estructura semántica canónica
        - NO generar lenguaje humano
    """

    state = K9State(
        context_bundle={
            "k9_command": {
                "intent": "ANALYTICAL_QUERY",
                "entity": "risks",
                "operation": "analyze",
                "output": "narrative",
            }
        },
        analysis={
            "period": {"window": "last_4_weeks"},
            "risk_summary": {
                "dominant_risk": "R01",
                "relevant_risk": "R02",
            },
            "operational_evidence": {
                "has_critical_control_failures": True,
                "supported_risks": ["R01", "R02"],
            },
            "risk_trajectories": {
                "R01": {"trend": "up"},
                "R02": {"trend": "stable"},
            },
        },
        reasoning=[],
    )

    result = narrative_node(state)

    # 1️⃣ Debe crear narrative_context
    assert result.narrative_context is not None, (
        "NarrativeNode debe crear state.narrative_context."
    )

    ctx = result.narrative_context

    # 2️⃣ Claves semánticas canónicas esperadas
    required_keys = {
        "narrative_type",
        "narrative_intent",
        "conceptual_axes",
        "narrative_constraints",
        "semantic_focus",
        "key_entities",
        "key_risks",
        "signals",
        "comparisons",
        "temporal_markers",
        "notes_for_llm",
    }

    missing = required_keys - set(ctx.keys())
    assert not missing, f"Faltan claves en narrative_context: {missing}"

    # 3️⃣ No debe generar respuesta humana
    assert result.answer is None
