import sys
from pathlib import Path

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_f02_004_engine_separates_observations_and_audits():
    """
    F02_004

    Reglas:
    - Observaciones y auditorías deben existir como dominios separados
    - No deben mezclarse estructuras ni claves
    """

    state = K9State(
        user_query="Test separación de dominios",
        reasoning=[]
    )

    result = data_engine_node(state)
    engine = result.analysis["engine"]

    # ---------------------------
    # Dominios esperados
    # ---------------------------
    assert "observations" in engine, "Dominio observations no expuesto"
    assert "audits" in engine, "Dominio audits no expuesto"

    observations = engine["observations"]
    audits = engine["audits"]

    # ---------------------------
    # Observaciones
    # ---------------------------
    assert isinstance(observations, dict)
    assert "summary" in observations, "observations.summary no expuesto"

    obs_summary = observations["summary"]
    assert "total" in obs_summary
    assert "by_type" in obs_summary
    assert set(obs_summary["by_type"].keys()).issubset({"OPG", "OCC"})

    # ---------------------------
    # Auditorías
    # ---------------------------
    assert isinstance(audits, dict)
    assert "daily" in audits
    assert "accumulated_12s" in audits
    assert "meta" in audits

    # ---------------------------
    # NO colisión semántica
    # ---------------------------
    assert "audits" not in observations, "Auditorías mezcladas en observaciones"
    assert "observations" not in audits, "Observaciones mezcladas en auditorías"
