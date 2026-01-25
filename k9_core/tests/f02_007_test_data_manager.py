import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.data.data_manager import DataManager


def test_data_manager_f02_007_loads_fdo_datasets():
    """
    FASE 2 — DataManager
    Test ID: F02_007

    Verifica:
    - Carga correcta de FDO diario
    - Carga correcta de FDO acumulado 12s
    - Separación semántica entre ambos
    """

    dm = DataManager("data/synthetic")

    df_fdo_daily = dm.get_fdo_diario()
    df_fdo_12s = dm.get_fdo_diario_12s()

    # Existencia
    assert df_fdo_daily is not None
    assert df_fdo_12s is not None

    # No vacíos
    assert not df_fdo_daily.empty
    assert not df_fdo_12s.empty

    # Columnas mínimas esperadas
    assert "fecha" in df_fdo_daily.columns
    assert "semana" in df_fdo_daily.columns

    assert "fecha" in df_fdo_12s.columns
    assert "semana" in df_fdo_12s.columns

    # Escalas distintas (no iguales)
    daily_sample = df_fdo_daily.select_dtypes(include="number").iloc[0]
    acc_sample = df_fdo_12s.select_dtypes(include="number").iloc[0]

    assert daily_sample.max() <= 1.0
    assert acc_sample.max() > 1.0
