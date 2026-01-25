# TEST_S04_001 — Contrato mínimo del AnalystNode v0.1

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.state.state import K9State
from src.nodes.analyst_node import analyst_node


def test_s04_001_analystnode_populates_analysis():
    """
    TEST_S04_001
    Verifica que el AnalystNode v0.1:
    - escribe el campo 'analysis'
    - no modifica 'answer'
    - agrega reasoning
    - tolera signals=None
    """

    state = K9State(
        user_query="estado de riesgos",
        intent="general_question",
        context_bundle={
            "areas_operacionales": ["Mina Rajo"],
            "version_contexto": "0.2"
        },
        signals=None
    )

    updated_state = analyst_node(state)

    # El state debe seguir siendo el mismo objeto
    assert updated_state is state

    # analysis debe existir
    assert updated_state.analysis is not None
    assert isinstance(updated_state.analysis, dict)

    # analysis debe tener al menos una clave
    assert len(updated_state.analysis.keys()) >= 1

    # answer NO debe ser tocado aún
    assert updated_state.answer is None

    # reasoning debe registrar la acción
    assert any("Analyst" in r for r in updated_state.reasoning)
