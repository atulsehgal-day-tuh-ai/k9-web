import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

from src.data.data_manager import DataManager


def test_data_manager_f01_001_loads_all_datasets():
    """
    FASE 1 — DataManager
    Test ID: F01_001

    Verifica que todos los datasets base se cargan correctamente
    """
    dm = DataManager("data/synthetic")

    df_weekly = dm.get_weekly_signals()
    df_tray = dm.get_trayectorias_semanales()
    df_obs = dm.get_observaciones()
    df_pro = dm.get_proactivo_semanal()

    # Validaciones mínimas (no semánticas)
    assert not df_weekly.empty
    assert not df_tray.empty
    assert not df_obs.empty
    assert not df_pro.empty
