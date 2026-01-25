from __future__ import annotations

from typing import Any, Dict, List, Tuple
from src.state.state import K9State


def _extract_occ_records(state: K9State) -> List[Dict[str, Any]]:
    """
    Extrae registros OCC/OPG enriquecidos desde el estado.

    Este nodo asume que OCCEnrichmentNode ya corrió y dejó evidencia en:
      - state.risk_enrichment (preferido)
    y/o que DataEngine / otros nodos puedan haber expuesto estructuras equivalentes.

    La función es robusta: soporta múltiples formas sin romper.
    """
    occ_records: List[Dict[str, Any]] = []

    # 1) Preferido: salida estructurada del OCCEnrichmentNode
    risk_enrichment = getattr(state, "risk_enrichment", None)
    if isinstance(risk_enrichment, dict):
        # Caso A: risk_enrichment trae una lista directa
        direct = risk_enrichment.get("occ_records") or risk_enrichment.get("records")
        if isinstance(direct, list):
            for x in direct:
                if isinstance(x, dict):
                    occ_records.append(x)

        # Caso B: risk_enrichment por riesgo
        by_risk = risk_enrichment.get("by_risk")
        if isinstance(by_risk, dict):
            for _, payload in by_risk.items():
                if not isinstance(payload, dict):
                    continue

                # Puede venir como lista unificada
                for key in ("occ_records", "records", "items", "occ", "observations"):
                    lst = payload.get(key)
                    if isinstance(lst, list):
                        for x in lst:
                            if isinstance(x, dict):
                                occ_records.append(x)

                # Puede venir separado OCC vs OPG
                for key in ("occ", "occ_list", "occ_items"):
                    lst = payload.get(key)
                    if isinstance(lst, list):
                        for x in lst:
                            if isinstance(x, dict):
                                x = dict(x)
                                x.setdefault("type", "OCC")
                                occ_records.append(x)

                for key in ("opg", "opg_list", "opg_items"):
                    lst = payload.get(key)
                    if isinstance(lst, list):
                        for x in lst:
                            if isinstance(x, dict):
                                x = dict(x)
                                x.setdefault("type", "OPG")
                                occ_records.append(x)

    # 2) Fallback: algunos flujos pueden dejarlo en analysis.engine u otros bloques
    analysis = state.analysis or {}
    engine = analysis.get("engine", {})
    if isinstance(engine, dict):
        for key in ("occ_enrichment", "occ_records", "observations_enriched"):
            candidate = engine.get(key)
            if isinstance(candidate, list):
                for x in candidate:
                    if isinstance(x, dict):
                        occ_records.append(x)
            elif isinstance(candidate, dict):
                # Si viene por riesgo
                by_risk = candidate.get("by_risk")
                if isinstance(by_risk, dict):
                    for _, payload in by_risk.items():
                        if isinstance(payload, dict):
                            lst = payload.get("records") or payload.get("occ_records")
                            if isinstance(lst, list):
                                for x in lst:
                                    if isinstance(x, dict):
                                        occ_records.append(x)

    # Normalización mínima: asegurar campos mínimos esperados por el nodo operacional
    normalized: List[Dict[str, Any]] = []
    for r in occ_records:
        if not isinstance(r, dict):
            continue
        rr = dict(r)

        # Campos mínimos
        rr.setdefault("id", rr.get("occ_id") or rr.get("id_observacion") or rr.get("id_obs"))
        rr.setdefault("risk_id", rr.get("id_riesgo") or rr.get("riesgo_id") or rr.get("risk"))
        rr.setdefault("type", rr.get("tipo") or rr.get("observation_type") or rr.get("class"))

        # Si aún no hay type, inferir por presencia de "OCC" en texto
        if rr.get("type") is None:
            rr["type"] = "OCC"

        # Normalizar type a {"OCC","OPG"} si venía diferente
        t = str(rr.get("type")).upper()
        rr["type"] = "OCC" if "OCC" in t else "OPG" if "OPG" in t else t

        # control / criticidad
        rr.setdefault("control_id", rr.get("id_control") or rr.get("control"))
        rr.setdefault("is_critical_control", rr.get("control_critico") or rr.get("is_critical") or False)
        rr.setdefault("audit_id", rr.get("id_auditoria") or rr.get("auditoria_id"))

        # Filtrar registros que no tengan risk_id (no se pueden agrupar)
        if rr.get("risk_id") is None:
            continue
        # Filtrar registros sin id, pero mantener si el resto está OK (para conteos)
        if rr.get("id") is None:
            rr["id"] = "UNKNOWN_OCC"

        normalized.append(rr)

    return normalized


def operational_analysis_node(state: K9State) -> K9State:
    """
    OperationalAnalysisNode — K9 v3.2

    Ejecuta SOLO cuando el K9 Command indica una consulta operacional.

    Rol:
      - Construir evidencia operacional rica (detallada) para drill-down,
        sin juicios cognitivos, sin umbrales, sin narrativa.
      - Esta evidencia es consumida por Metrics/Adapter/Streamlit/Proactive.

    Salida:
      state.analysis["operational_analysis"] = {
        "evidence_by_risk": { ... },
        "traceability": [ ... ],
        "meta": { ... }
      }
    """

    context = state.context_bundle or {}
    command = context.get("k9_command")

    if not command:
        state.reasoning.append(
            "OperationalAnalysisNode: skipped (no K9 command present)."
        )
        return state

    if command.get("intent") != "OPERATIONAL_QUERY":
        state.reasoning.append(
            f"OperationalAnalysisNode: skipped "
            f"(intent={command.get('intent')})."
        )
        return state

    analysis: Dict[str, Any] = state.analysis or {}
    occ_records = _extract_occ_records(state)

    # --------------------------------------------------
    # 4) Evidencia operacional detallada por riesgo
    # --------------------------------------------------
    evidence_by_risk: Dict[str, Dict[str, Any]] = {}

    for occ in occ_records:
        risk_id = occ["risk_id"]

        if risk_id not in evidence_by_risk:
            evidence_by_risk[risk_id] = {
                "occ_count": 0,
                "opg_count": 0,
                "occ_records": [],
                "opg_records": [],
                "controls_affected": set(),
                "critical_controls_affected": set(),
            }

        if occ.get("type") == "OCC":
            evidence_by_risk[risk_id]["occ_count"] += 1
            evidence_by_risk[risk_id]["occ_records"].append(occ)
        else:
            evidence_by_risk[risk_id]["opg_count"] += 1
            evidence_by_risk[risk_id]["opg_records"].append(occ)

        control_id = occ.get("control_id")
        if control_id:
            evidence_by_risk[risk_id]["controls_affected"].add(control_id)
            if bool(occ.get("is_critical_control")):
                evidence_by_risk[risk_id]["critical_controls_affected"].add(control_id)

    # --------------------------------------------------
    # 5) Normalización de estructuras para consumo externo
    # --------------------------------------------------
    for risk_id, data in evidence_by_risk.items():
        data["controls_affected"] = list(data["controls_affected"])
        data["critical_controls_affected"] = list(data["critical_controls_affected"])

    # --------------------------------------------------
    # 6) Trazabilidad OCC → control → auditoría
    # --------------------------------------------------
    traceability: List[Dict[str, Any]] = []
    for occ in occ_records:
        traceability.append(
            {
                "occ_id": occ.get("id"),
                "risk_id": occ.get("risk_id"),
                "control_id": occ.get("control_id"),
                "audit_id": occ.get("audit_id"),
            }
        )

    # --------------------------------------------------
    # 7) Salida final
    # --------------------------------------------------
    analysis["operational_analysis"] = {
        "evidence_by_risk": evidence_by_risk,
        "traceability": traceability,
        "meta": {
            "source": "OCC enrichment + STDE",
            "semantic_level": "operational",
            "records_total": int(len(occ_records)),
            "risks_total": int(len(evidence_by_risk)),
        },
    }

    state.analysis = analysis
    state.reasoning.append(
        "OperationalAnalysisNode: evidencia operacional detallada construida (sin juicios, sin umbrales, sin narrativa)."
    )
    return state
