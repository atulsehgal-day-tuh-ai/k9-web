import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.intent_classifier import intent_classifier


def test_f00_001_intent_classifier_sets_intent_only():
    """
    F00_001 — IntentClassifier:
    - Clasifica intención
    - NO modifica analysis
    - NO genera decisiones
    """

    state = K9State(
        user_query="What is the most critical risk right now?",
        analysis={
            "engine": {"dummy": True}
        },
        reasoning=[],
        intent=""   # ← contrato válido
    )

    result = intent_classifier(state)

    # Intent debe existir y ser string
    assert result.intent is not None
    assert isinstance(result.intent, str)
    assert result.intent != ""

    # Analysis NO debe mutar
    assert result.analysis == state.analysis

    # No debe crear decisiones
    assert "preventive_decision" not in result.analysis
