import sys
from pathlib import Path
import pandas as pd
import pytest

# --------------------------------------------------
# ROOT CORRECTO DEL REPO
# --------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.data.data_manager import DataManager


@pytest.fixture
def data_manager():
    data_path = REPO_ROOT / "data" / "synthetic"
    return DataManager(data_path)


def test_f02_001_data_manager_loads_all_core_datasets(data_manager):
    """
    F02_001
    Regla:
    - DataManager debe cargar todos los datasets reales sin error
    - Cada método debe devolver un DataFrame no vacío
    """

    dm = data_manager  # ✅ fixture inyectada, NO llamada

    loaders = [
        dm.get_trayectorias_semanales,
        dm.get_trayectorias_diarias,
        dm.get_weekly_signals,
        dm.get_observaciones,
        dm.get_observaciones_all,
        dm.get_proactivo_semanal,
        dm.get_fdo_diario,
        dm.get_fdo_diario_12s,
        dm.get_fdo_catalogo,
        dm.get_auditorias,
        dm.get_auditorias_12s,
    ]

    for loader in loaders:
        df = loader()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty, f"{loader.__name__} devolvió DataFrame vacío"
