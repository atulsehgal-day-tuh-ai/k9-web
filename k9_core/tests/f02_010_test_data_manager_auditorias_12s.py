import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import pandas as pd
from src.data.data_manager import DataManager


def test_data_manager_f02_010_loads_auditorias_12s(tmp_path):
    """
    F02_010
    DataManager debe cargar stde_auditorias_12s.csv correctamente.
    """

    # Arrange
    data_path = tmp_path
    sample_csv = data_path / "stde_auditorias_12s.csv"

    sample_csv.write_text(
        "id_auditoria,fecha,semana,dia_semana,turno,id_area,tipo_auditoria,resultado,hallazgos_clave\n"
        "AUD_001,2025-01-01,1,Lunes,Dia,AREA_01,SEGURIDAD,APROBADA,Sin hallazgos\n",
        encoding="utf-8"
    )

    dm = DataManager(base_path=data_path)

    # Act
    df = dm.get_auditorias_12s()

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df.columns) > 0
