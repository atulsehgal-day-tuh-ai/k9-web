import sys
from pathlib import Path

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.nodes.data_engine_node import data_engine_node
from src.state.state import K9State


def test_f02_002_data_engine_exposes_structured_analysis():
    """
    F02_002

    Regla:
    - DataEngineNode debe poblar analysis["engine"]
    - No interpreta ni decide
    - Expone todos los dominios de datos esperados
    """

    # Estado inicial mínimo válido
    state = K9State(
        user_query="Pregunta de prueba",
        reasoning=[]
    )

    # Ejecución directa del nodo
    result = data_engine_node(state)

    # ---------------------------
    # Validaciones estructurales
    # ---------------------------
    analysis = result.analysis
    assert analysis is not None, "analysis no fue inicializado"
    assert "engine" in analysis, "analysis.engine no expuesto"

    engine = analysis["engine"]

    # ---------------------------
    # Claves contractuales mínimas
    # ---------------------------
    expected_keys = {
        "fdo",
        "risk_trends",
        "proactivo",
        "audits",
        "observations",
        "period",
    }

    assert expected_keys.issubset(engine.keys()), (
        f"analysis.engine incompleto. Esperado: {expected_keys}, "
        f"Encontrado: {engine.keys()}"
    )

    # ---------------------------
    # Validación de tipos (no lógica)
    # ---------------------------
    assert isinstance(engine["fdo"], dict)
    assert isinstance(engine["risk_trends"], dict)
    assert isinstance(engine["proactivo"], dict)
    assert isinstance(engine["audits"], dict)
    assert isinstance(engine["observations"], dict)
    assert isinstance(engine["period"], dict)

    # ---------------------------
    # Nada crítico debe venir vacío
    # ---------------------------
    for key in ["fdo", "risk_trends", "observations"]:
        assert engine[key], f"engine['{key}'] está vacío"
