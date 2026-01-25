import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.semantic_retrieval_node import semantic_retrieval_node


def test_f00_005_semantic_retrieval_is_safe():
    """
    F00_005 — SemanticRetrievalNode:
    - Puede responder o delegar
    - NO muta analysis
    - NO pisa decisiones
    """

    state = K9State(
        user_query="Explain R01 controls",
        intent="semantic_lookup",
        analysis={
            "preventive_decision": {
                "prioritized_risks": ["R01"]
            }
        },
        reasoning=[],
        context_bundle={
            "matches": [
                {"content": "R01 control description", "score": 0.92}
            ]
        }
    )

    result = semantic_retrieval_node(state)

    # Puede responder o no, pero nunca debe mutar analysis
    assert result.analysis == state.analysis

    # Decisión intacta
    assert result.analysis["preventive_decision"]["prioritized_risks"] == ["R01"]

    # Si no responde, debe quedar trazado en reasoning
    if result.answer is None:
        assert any("SemanticRetrieval" in r for r in result.reasoning)
