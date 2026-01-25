"""
K9 Mining Safety — Core Smoke Test (NO LLM)
"""

import sys
import time
from pathlib import Path

# -----------------------------------------------------
# Exponer ROOT del repo (no /src)
# -----------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.state.state import K9State
from src.nodes.router import router_node
from src.nodes.operational_analysis_node import operational_analysis_node
from src.nodes.analyst_node import analyst_node
from src.nodes.narrative_node import narrative_node


def test_k9_core_pipeline_without_llm():
    start_time = time.time()

    # =====================================================
    # Estado inicial canónico
    # =====================================================
    state = K9State(
        context_bundle={
            "k9_command": {
                "type": "K9_COMMAND",
                "intent": "OPERATIONAL_QUERY",
                "entity": "risk",
                "operation": "trend",
                "output": "narrative",
            }
        }
    )

    # =====================================================
    # Pipeline core
    # =====================================================
    state = router_node(state)
    state = operational_analysis_node(state)
    state = analyst_node(state)
    state = narrative_node(state)

    # =====================================================
    # Invariantes
    # =====================================================
    assert (time.time() - start_time) < 1.0

    assert isinstance(state.analysis, dict)
    assert "operational_analysis" in state.analysis

    assert isinstance(state.narrative_context, dict)
    assert state.answer is None

    assert isinstance(state.reasoning, list)
    assert len(state.reasoning) > 0
