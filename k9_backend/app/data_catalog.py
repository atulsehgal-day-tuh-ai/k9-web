from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class DatasetDescriptor:
    name: str
    granularity: str  # "day" | "week" | "mixed" | "n/a"
    primary_time_keys: List[str]
    description: str


DEFAULT_DATASETS: Dict[str, DatasetDescriptor] = {
    # Weekly / cognitive
    "stde_trayectorias_semanales.csv": DatasetDescriptor(
        name="stde_trayectorias_semanales.csv",
        granularity="week",
        primary_time_keys=["semana"],
        description="Weekly risk trajectories (main trends source)",
    ),
    "k9_weekly_signals.parquet": DatasetDescriptor(
        name="k9_weekly_signals.parquet",
        granularity="week",
        primary_time_keys=["week", "semana", "semana_id"],
        description="Weekly aggregated K9 signals by risk",
    ),
    "stde_proactivo_semanal_v4_4.csv": DatasetDescriptor(
        name="stde_proactivo_semanal_v4_4.csv",
        granularity="week",
        primary_time_keys=["semana_id", "semana"],
        description="Proactive model weekly scores/ranks",
    ),
    "stde_proactivo_semanal_v4_4_thresholds.csv": DatasetDescriptor(
        name="stde_proactivo_semanal_v4_4_thresholds.csv",
        granularity="week",
        primary_time_keys=["semana_id", "semana"],
        description="Proactive model thresholds (weekly)",
    ),
    "stde_ranking_proactivo_12s.csv": DatasetDescriptor(
        name="stde_ranking_proactivo_12s.csv",
        granularity="week",
        primary_time_keys=["semana_id", "semana"],
        description="12-week proactive ranking view",
    ),
    "stde_trayectorias_diarias.csv": DatasetDescriptor(
        name="stde_trayectorias_diarias.csv",
        granularity="day",
        primary_time_keys=["fecha", "id_dia"],
        description="Daily internal trajectories of criticidad by risk",
    ),
    # Daily / operational
    "stde_fdo_diario.csv": DatasetDescriptor(
        name="stde_fdo_diario.csv",
        granularity="day",
        primary_time_keys=["fecha", "id_dia"],
        description="Daily operational pressure factors (FDO, normalized 0–1)",
    ),
    "stde_fdo_diario_12s.csv": DatasetDescriptor(
        name="stde_fdo_diario_12s.csv",
        granularity="day",
        primary_time_keys=["fecha", "id_dia"],
        description="Daily FDO trend (12-week style)",
    ),
    "stde_observaciones.csv": DatasetDescriptor(
        name="stde_observaciones.csv",
        granularity="mixed",
        primary_time_keys=["fecha", "semana"],
        description="Operational observations (baseline)",
    ),
    "stde_observaciones_12s.csv": DatasetDescriptor(
        name="stde_observaciones_12s.csv",
        granularity="week",
        primary_time_keys=["semana"],
        description="12-week observations rollup (OPG/OCC by week)",
    ),
    "stde_auditorias.csv": DatasetDescriptor(
        name="stde_auditorias.csv",
        granularity="mixed",
        primary_time_keys=["fecha", "semana"],
        description="Operational audits (planned/reactive)",
    ),
    "stde_auditorias_12s.csv": DatasetDescriptor(
        name="stde_auditorias_12s.csv",
        granularity="week",
        primary_time_keys=["semana"],
        description="12-week audits rollup",
    ),
    "stde_eventos.csv": DatasetDescriptor(
        name="stde_eventos.csv",
        granularity="day",
        primary_time_keys=["fecha", "id_dia"],
        description="Operational events (hazard/near miss/minor incidents)",
    ),
    "stde_riesgos_evento_lunes_critico.csv": DatasetDescriptor(
        name="stde_riesgos_evento_lunes_critico.csv",
        granularity="day",
        primary_time_keys=["fecha", "id_dia"],
        description="Scenario injection dataset for 'Critical Monday'",
    ),
}


def collect_sources(obj: Any) -> Set[str]:
    """
    Recursively collect `_meta.source` occurrences from dict/list analysis payloads.
    """
    sources: Set[str] = set()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            meta = x.get("_meta")
            if isinstance(meta, dict) and "source" in meta:
                src = meta.get("source")
                if isinstance(src, str) and src.strip():
                    sources.add(src.strip())
                elif isinstance(src, list):
                    for s in src:
                        if isinstance(s, str) and s.strip():
                            sources.add(s.strip())
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(obj)
    return sources


def describe_sources(sources: Iterable[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in sorted(set(sources)):
        desc = DEFAULT_DATASETS.get(s)
        if desc is None:
            out.append({"source": s, "granularity": "unknown", "time_keys": [], "description": ""})
        else:
            out.append(
                {
                    "source": desc.name,
                    "granularity": desc.granularity,
                    "time_keys": desc.primary_time_keys,
                    "description": desc.description,
                }
            )
    return out

