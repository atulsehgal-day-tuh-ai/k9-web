from pathlib import Path


def test_f01_001_required_files_exist():
    # Root real del repo: k9_mining_safety
    repo_root = Path(__file__).resolve().parents[2]

    # Path real de datos sintéticos
    data_path = repo_root / "data" / "synthetic"

    required_files = [
        "stde_trayectorias_semanales.csv",
        "stde_trayectorias_diarias.csv",
        "k9_weekly_signals.parquet",
        "stde_observaciones.csv",
        "stde_observaciones_12s.csv",
        "stde_eventos.csv",
        "stde_incidentes_12s.csv",
        "stde_auditorias.csv",
        "stde_auditorias_12s.csv",
    ]

    for fname in required_files:
        path = data_path / fname
        assert path.exists(), f"Dataset no encontrado: {path}"
