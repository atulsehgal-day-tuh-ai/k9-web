from pathlib import Path
import pandas as pd
import numpy as np


def test_f01_005_r03_estable():
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / "data" / "synthetic"

    path = data_path / "stde_trayectorias_semanales.csv"
    df = pd.read_csv(path)

    r03 = df["criticidad_R03_media"].values
    std_dev = float(np.std(r03))

    # R03 está diseñado para ser estable
    assert std_dev < 0.05, (
        f"R03 muestra variabilidad inesperada (std={std_dev:.4f})"
    )
