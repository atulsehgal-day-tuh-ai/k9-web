from pathlib import Path
import pandas as pd


def test_f01_002_trayectorias_semanales_schema():
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / "data" / "synthetic"

    path = data_path / "stde_trayectorias_semanales.csv"
    df = pd.read_csv(path)

    expected_columns = {
        "semana",
        "criticidad_R01_media",
        "criticidad_R02_media",
        "criticidad_R03_media",
        "criticidad_global_media",
    }

    missing = expected_columns - set(df.columns)
    assert not missing, f"Columnas faltantes en trayectorias_semanales: {missing}"
