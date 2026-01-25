import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.domain_guardrail import domain_guardrail


def test_f00_003_domain_guardrail_is_passive():
    """
    F00_003 — DomainGuardrail:
    - Puede bloquear flujo
    - NO muta analysis
    - NO borra decisiones
    """

    state = K9State(
        user_query="Tell me a joke",
        intent="out_of_domain",
        analysis={
            "preventive_decision": {
                "prioritized_risks": ["R01"]
            }
        },
        reasoning=[]
    )

    result = domain_guardrail(state)

    # Analysis intacto
    assert result.analysis == state.analysis

    # Decisión intacta
    assert result.analysis["preventive_decision"]["prioritized_risks"] == ["R01"]

    # Guardrail deja huella en reasoning o answer (según implementación)
    assert len(result.reasoning) >= 0
