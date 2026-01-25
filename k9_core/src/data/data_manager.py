# src/data/data_manager.py

from pathlib import Path
import pandas as pd


class DataManager:
    """
    DataManager — FASE 1 (Baseline PRE lunes crítico)

    Responsabilidad única:
    - Cargar datasets sintéticos base desde disco
    - Exponerlos como DataFrames limpios
    """

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    # ---------- Helpers internos ----------

    def _load_csv(self, filename: str) -> pd.DataFrame:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {path}")
        return pd.read_csv(path)

    def _load_parquet(self, filename: str) -> pd.DataFrame:
        path = self.base_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {path}")
        return pd.read_parquet(path)

    # ---------- Datasets final ----------

    def get_weekly_signals(self) -> pd.DataFrame:
        """
        k9_weekly_signals.parquet
        Señales semanales agregadas por riesgo
        """
        return self._load_parquet("k9_weekly_signals.parquet")

    def get_trayectorias_semanales(self) -> pd.DataFrame:
        """
        stde_trayectorias_semanales.csv
        Evolución temporal de riesgos (fuente principal de tendencias)
        """
        return self._load_csv("stde_trayectorias_semanales.csv")

    def get_observaciones(self) -> pd.DataFrame:
        """
        stde_observaciones_12s.csv
        Observaciones OPG / OCC por semana
        """
        return self._load_csv("stde_observaciones_12s.csv")
    
    def get_observaciones_all(self) -> pd.DataFrame:
        """
        Unifica observaciones baseline + STDE 12 semanas
        """
        df_base = self._load_csv("stde_observaciones.csv")
        df_12s = self._load_csv("stde_observaciones_12s.csv")
        df = pd.concat([df_base, df_12s], ignore_index=True)

        required_cols = {"semana", "tipo_observacion"}
        missing = required_cols - set(df.columns)
        if missing:
            raise KeyError(f"Observaciones missing columns: {missing}")

        return df

    def get_proactivo_semanal(self) -> pd.DataFrame:
        """
        stde_proactivo_semanal_v4_4.csv
        Salida semanal del modelo proactivo
        """
        return self._load_csv("stde_proactivo_semanal_v4_4.csv")
    
    def get_trayectorias_diarias(self) -> pd.DataFrame:
        """
        stde_trayectorias_diarias.csv
        Trayectorias internas diarias de criticidad por riesgo.
        Uso interno (no narrativa directa).
        """
        return self._load_csv("stde_trayectorias_diarias.csv")
    
    def get_fdo_diario(self) -> pd.DataFrame:
        """
        stde_fdo_diario.csv
        Estado diario normalizado (0–1) de factores operacionales.
        Representa presión operacional instantánea.
        """
        return self._load_csv("stde_fdo_diario.csv")
    
    def get_fdo_diario_12s(self) -> pd.DataFrame:
        """
        stde_fdo_diario_12s.csv
        Tendencia estratégica acumulada de FDO (índice 1–100).
        Incluye fecha para alineación temporal.
        """
        return self._load_csv("stde_fdo_diario_12s.csv")

    def get_fdo_catalogo(self) -> pd.DataFrame:
        """
        stde_fdo_catalogo.csv
        Catálogo semántico de factores operacionales (nombres, descripciones).
        """
        return self._load_csv("stde_fdo_catalogo.csv")

    def get_auditorias(self) -> pd.DataFrame:
        """
        stde_auditorias.csv
        Auditorías operativas (planificadas / reactivas).
        Nivel: operacional / factual.
        """
        return self._load_csv("stde_auditorias.csv")


    def get_auditorias_12s(self) -> pd.DataFrame:
        """
        stde_auditorias_12s.csv
        Auditorías agregadas / narrativas a 12 semanas.
        Nivel: cognitivo / longitudinal.
        """
        return self._load_csv("stde_auditorias_12s.csv")

    def get_observaciones_by_week_range(
        self,
        start_week: int,
        end_week: int
    ) -> pd.DataFrame:
        """
        Retorna observaciones dentro de un rango semanal [start_week, end_week).

        Infraestructura pura:
        - NO interpreta intención
        - NO valida semántica
        - NO aplica lógica cognitiva
        """

        df = self.get_observaciones_all()

        return df[
            (df["semana"] >= start_week) &
            (df["semana"] < end_week)
        ].reset_index(drop=True)
