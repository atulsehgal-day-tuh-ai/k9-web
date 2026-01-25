import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.occ_enrichment_node import occ_enrichment_node


def test_f00_006_occ_enrichment_is_non_decisional():
    """
    F00_006 — OccEnrichmentNode:
    - Enriquecer OCC
    - NO tocar analysis
    - NO decidir
    """

    state = K9State(
        user_query="",
        intent="enrichment",
        analysis={
            "engine": {
                "observations": {"summary": {"total": 3}}
            }
        },
        reasoning=[]
    )

    result = occ_enrichment_node(state)

    # risk_enrichment debe existir
    assert result.risk_enrichment is not None
    assert isinstance(result.risk_enrichment, dict)

    # Analysis intacto
    assert result.analysis == state.analysis

    # No decisiones creadas
    assert "preventive_decision" not in result.analysis
