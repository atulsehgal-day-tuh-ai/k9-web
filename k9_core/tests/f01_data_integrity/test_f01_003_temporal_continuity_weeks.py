from pathlib import Path
import pandas as pd


def test_f01_003_continuidad_12_semanas():
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / "data" / "synthetic"

    path = data_path / "stde_trayectorias_semanales.csv"
    df = pd.read_csv(path)

    semanas = sorted(df["semana"].unique())

    assert len(semanas) == 12, (
        f"Se esperaban 12 semanas STDE, se encontraron {len(semanas)}"
    )

    diffs = [semanas[i + 1] - semanas[i] for i in range(len(semanas) - 1)]
    assert all(d == 1 for d in diffs), (
        f"Las semanas no son consecutivas: {semanas}"
    )

