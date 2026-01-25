from pathlib import Path
import pandas as pd


LUNES_CRITICO_FECHA = "2025-02-03"


def test_f01_004_lunes_critico_es_evento_diario():
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / "data" / "synthetic"

    eventos_path = data_path / "stde_eventos.csv"
    trayectorias_path = data_path / "stde_trayectorias_semanales.csv"

    eventos = pd.read_csv(eventos_path, parse_dates=["fecha"])
    trayectorias = pd.read_csv(trayectorias_path)

    # El lunes crítico debe existir como evento
    fechas_eventos = eventos["fecha"].astype(str).tolist()
    assert any(f.startswith(LUNES_CRITICO_FECHA) for f in fechas_eventos), (
        "Lunes crítico no encontrado en stde_eventos.csv"
    )

    # El lunes crítico NO debe aparecer en trayectorias semanales
    trayectorias_str = trayectorias.astype(str)
    assert not trayectorias_str.apply(
        lambda col: col.str.contains(LUNES_CRITICO_FECHA, regex=False)
    ).any().any(), (
        "El lunes crítico aparece en trayectorias semanales y no debería"
    )
