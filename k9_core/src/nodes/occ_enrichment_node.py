from typing import Dict, Any
import pandas as pd
from src.state.state import K9State
from src.data.data_manager import DataManager


def occ_enrichment_node(state: K9State) -> K9State:
    """
    OCC Enrichment Node — FASE 2

    Rol:
    - Leer observaciones (baseline + STDE)
    - Filtrar solo OCC
    - Asociar OCC → riesgo → control crítico
    - Registrar evidencia operacional
    - NO recalibrar
    - NO razonar
    """

    # Inicialización correcta del DataManager
    # Se asume que el base_path ya está definido en el proyecto
    dm = DataManager(base_path="data/synthetic")


    try:
        df = dm.get_observaciones_all()
    except Exception as e:
        state.reasoning.append(
            f"OCC Enrichment Node: error cargando observaciones: {e}"
        )
        return state

    # Columnas contractuales FASE 2 (solo presentes en baseline)
    REQUIRED_COLUMNS = {
        "semana",
        "tipo_observacion",
        "riesgo_id",           # columna J
        "is_control_critico",  # columna K
        "control_critico_id"   # columna L
    }

    # Nos quedamos solo con filas que tengan esas columnas (baseline)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        state.reasoning.append(
            "OCC Enrichment Node: columnas J/K/L no presentes en todas las filas "
            "(esperado para STDE 12s). Se filtrarán automáticamente."
        )

    # Filtrar solo OCC
    df_occ = df[df["tipo_observacion"] == "OCC"]

    # Mantener solo filas con riesgo_id válido (baseline)
    df_occ = df_occ[df_occ["riesgo_id"].notna()]

    risk_map: Dict[str, Dict[str, Any]] = {}
    total_occ = 0
    occ_with_critical_control = 0

    for _, row in df_occ.iterrows():
        total_occ += 1

        riesgo_id = row["riesgo_id"]
        semana = int(row["semana"])
        is_control_critico = bool(row.get("is_control_critico", False))

        control_id = None
        if is_control_critico:
            control_id = row.get("control_critico_id")
            if pd.notna(control_id):
                occ_with_critical_control += 1

        if riesgo_id not in risk_map:
            risk_map[riesgo_id] = {"occ_events": []}

        risk_map[riesgo_id]["occ_events"].append(
            {
                "week": semana,
                "is_control_critico": is_control_critico,
                "control_critico_id": control_id
            }
        )

    # Persistencia en el estado (FASE 2)
    state.risk_enrichment = {
        "by_risk": risk_map,
        "summary": {
            "total_occ": total_occ,
            "occ_with_critical_control": occ_with_critical_control,
            "risks_affected": sorted(risk_map.keys())
        }
    }

    state.reasoning.append(
        "OCC Enrichment Node: OCC enriquecidas con riesgo y control crítico (FASE 2)."
    )

    return state
