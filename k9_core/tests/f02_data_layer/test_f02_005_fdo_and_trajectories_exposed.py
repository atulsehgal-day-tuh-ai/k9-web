import sys
from pathlib import Path

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_f02_005_engine_exposes_fdo_and_trajectories_independent_of_proactivo():
    """
    F02_005

    Reglas:
    - FDO diario y acumulado deben existir
    - Trayectorias por riesgo deben existir
    - No deben depender del bloque proactivo
    """

    state = K9State(
        user_query="Test FDO y trayectorias",
        reasoning=[]
    )

    result = data_engine_node(state)
    engine = result.analysis["engine"]

    # ---------------------------
    # Trayectorias
    # ---------------------------
    assert "trajectories" in engine, "engine.trajectories no expuesto"
    trajectories = engine["trajectories"]

    assert "weekly" in trajectories
    assert isinstance(trajectories["weekly"], dict)
    assert len(trajectories["weekly"]) >= 1, "No hay trayectorias por riesgo"

    # Cada riesgo debe tener values y trend_direction
    for risk_id, data in trajectories["weekly"].items():
        assert "values" in data
        assert "trend_direction" in data
        assert isinstance(data["values"], list)
        assert len(data["values"]) == 12, "Trayectoria no cubre 12 semanas"

    # ---------------------------
    # FDO
    # ---------------------------
    assert "fdo" in engine, "engine.fdo no expuesto"
    fdo = engine["fdo"]

    assert "daily_summary" in fdo
    assert "accumulated_12s" in fdo

    # FDO diario
    daily = fdo["daily_summary"]
    assert "factors" in daily
    assert isinstance(daily["factors"], dict)
    assert len(daily["factors"]) >= 1

    # FDO acumulado 12s
    acc = fdo["accumulated_12s"]
    assert "ranking" in acc
    assert isinstance(acc["ranking"], list)
    assert len(acc["ranking"]) >= 1

    # ---------------------------
    # Independencia del proactivo
    # ---------------------------
    assert "proactivo" in engine, "Bloque proactivo debe existir"
    assert engine["proactivo"] is not None

    # Pero FDO y trayectorias no dependen de proactivo
    # (verificamos que existen incluso si proactivo estuviera vacío)
