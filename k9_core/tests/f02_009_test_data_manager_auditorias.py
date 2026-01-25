import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

import pandas as pd
from src.data.data_manager import DataManager


def test_data_manager_f02_009_loads_auditorias(tmp_path):
    """
    F02_009
    DataManager debe cargar stde_auditorias.csv correctamente.
    """

    # Arrange
    data_path = tmp_path
    sample_csv = data_path / "stde_auditorias.csv"

    sample_csv.write_text(
        "id_auditoria_final,fecha,semana,id_area,riesgo_focal,tipo_auditoria,origen,rol_auditor_id,id_evento_asociado\n"
        "AUD_001,2025-01-01,1,AREA_01,R01,SEGURIDAD,planificada,ROL_01,EV_001\n"
    )

    dm = DataManager(base_path=data_path)

    # Act
    df = dm.get_auditorias()

    # Assert
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df.columns) > 0
