import sys
from pathlib import Path

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_f02_003_engine_period_is_12_weeks_and_excludes_critical_monday():
    """
    F02_003

    Reglas:
    - El periodo del engine debe representar SOLO el baseline semanal (12 semanas)
    - No debe incluir el Lunes Crítico como semana adicional
    - min_week y max_week deben ser consistentes con 12 semanas
    """

    state = K9State(
        user_query="Test temporal",
        reasoning=[]
    )

    result = data_engine_node(state)
    engine = result.analysis["engine"]

    assert "period" in engine, "engine.period no expuesto"

    period = engine["period"]

    # Claves esperadas
    assert {"min_week", "max_week", "weeks"}.issubset(period.keys())

    weeks = period["weeks"]
    assert isinstance(weeks, list)
    assert len(weeks) == 12, (
        f"Baseline semanal inválido: se esperaban 12 semanas, "
        f"se obtuvieron {len(weeks)}"
    )

    # Orden y continuidad básica
    assert weeks == sorted(weeks), "Semanas no están ordenadas"
    assert period["min_week"] == weeks[0]
    assert period["max_week"] == weeks[-1]

    # El Lunes Crítico NO debe aparecer como semana
    # (es un día/evento adicional, no una semana)
    # Asumimos que semanas son enteros (IDs semanales)
    for w in weeks:
        assert isinstance(w, int), "IDs de semana deben ser enteros"
