from typing import List, Dict, Any

import plotly.graph_objects as go
import pandas as pd


def render_metrics(
    analysis: Dict[str, Any],
    visual_suggestions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Metrics Adapter

    Rol:
    - Convertir visual_suggestions (definidas por MetricsNode)
      en artefactos renderizables por Streamlit.
    - NO decidir reglas.
    - NO acceder a data raw externa.
    - NO modificar analysis.

    Nota arquitectónica (v3.2):
    - El adapter consume preferentemente analysis["metrics"].
    - analysis directo solo se usa como fallback o compatibilidad.
    
    Retorna:
    - Lista de dicts con:
        {
            "type": "plotly" | "table",
            "figure" | "data": objeto renderizable
        }
    """

    rendered_outputs: List[Dict[str, Any]] = []

    metrics = analysis.get("metrics", {})
    metrics_tables = metrics.get("tables", {})
    metrics_series = metrics.get("time_series", {})

    for suggestion in visual_suggestions:
        metric = suggestion.get("metric")
        chart_type = suggestion.get("type")
        entities = suggestion.get("entities", [])

        # ============================================================
        # 1. Serie temporal de riesgos
        # ============================================================
        if chart_type == "line_chart" and metric == "risk_trajectories":
            trajectories = metrics_series.get(
                "risk_trajectories",
                analysis.get("risk_trajectories", {})  # fallback
            )

            fig = go.Figure()

            for risk_id in entities:
                values = trajectories.get(risk_id, {}).get("weekly_values", [])
                if not values:
                    continue

                weeks = list(range(1, len(values) + 1))

                fig.add_trace(
                    go.Scatter(
                        x=weeks,
                        y=values,
                        mode="lines+markers",
                        name=risk_id,
                    )
                )

            if fig.data:
                fig.update_layout(
                    title="Evolución temporal de riesgos",
                    xaxis_title="Semana",
                    yaxis_title="Índice de riesgo",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                )

                rendered_outputs.append(
                    {
                        "type": "plotly",
                        "figure": fig,
                    }
                )

        # ============================================================
        # 2. Comparación entre riesgos
        # ============================================================
        elif chart_type == "bar_chart" and metric == "risk_comparison":
            trajectories = metrics_series.get(
                "risk_trajectories",
                analysis.get("risk_trajectories", {})  # fallback
            )

            labels = []
            values = []

            for risk_id in entities:
                labels.append(risk_id)

                if risk_id in trajectories:
                    weekly = trajectories[risk_id].get("weekly_values", [])
                    values.append(weekly[-1] if weekly else 0)
                else:
                    values.append(0)  # fallback neutro explícito

            if labels:
                fig = go.Figure(
                    data=[go.Bar(x=labels, y=values)]
                )

                fig.update_layout(
                    title="Comparación entre riesgos",
                    xaxis_title="Riesgo",
                    yaxis_title="Valor relativo",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                )

                rendered_outputs.append(
                    {
                        "type": "plotly",
                        "figure": fig,
                    }
                )

        # ============================================================
        # 3. Ranking / prioridad de riesgos
        # ============================================================
        elif chart_type == "bar_chart" and metric == "risk_priority":
            risk_summary = analysis.get("risk_summary", {})

            labels = []
            values = []

            dominant = risk_summary.get("dominant_risk")
            relevant = risk_summary.get("relevant_risk")

            if dominant:
                labels.append(dominant)
                values.append(2)

            if relevant and relevant != dominant:
                labels.append(relevant)
                values.append(1)

            if labels:
                fig = go.Figure(
                    data=[go.Bar(x=labels, y=values)]
                )

                fig.update_layout(
                    title="Prioridad de riesgos",
                    xaxis_title="Riesgo",
                    yaxis_title="Nivel de prioridad",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                )

                rendered_outputs.append(
                    {
                        "type": "plotly",
                        "figure": fig,
                    }
                )

        # ============================================================
        # 4. FDO — Serie temporal
        # ============================================================
        elif chart_type == "line_chart" and metric == "fdo_trajectories":
            # En v3.2, FDO temporal debe venir desde metrics (si existe)
            fdo_series = metrics_series.get("fdo_trajectories", {})

            fig = go.Figure()

            for fdo_id in entities:
                values = fdo_series.get(fdo_id, {}).get("weekly_values", [])
                if not values:
                    continue

                weeks = list(range(1, len(values) + 1))

                fig.add_trace(
                    go.Scatter(
                        x=weeks,
                        y=values,
                        mode="lines+markers",
                        name=fdo_id,
                    )
                )

            if fig.data:
                fig.update_layout(
                    title="Evolución temporal de Factores de Degradación Operacional (FDO)",
                    xaxis_title="Semana",
                    yaxis_title="Índice FDO",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                )

                rendered_outputs.append(
                    {
                        "type": "plotly",
                        "figure": fig,
                    }
                )

        # ============================================================
        # 5. FDO — Comparación agregada
        # ============================================================
        elif chart_type == "bar_chart" and metric == "fdo_comparison":
            # FDO agregados deben venir desde métricas/tablas
            fdo_table = metrics_tables.get("fdo_summary", {})

            labels = []
            values = []

            for fdo_id in entities:
                value = fdo_table.get(fdo_id)
                if value is not None:
                    labels.append(fdo_id)
                    values.append(value)

            if labels:
                fig = go.Figure(
                    data=[go.Bar(x=labels, y=values)]
                )

                fig.update_layout(
                    title="Factores de Degradación Operacional (FDO)",
                    xaxis_title="Factor",
                    yaxis_title="Nivel",
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                )

                rendered_outputs.append(
                    {
                        "type": "plotly",
                        "figure": fig,
                    }
                )

        # ============================================================
        # 6. Tabla genérica (fallback)
        # ============================================================
        elif chart_type == "table":
            table_data = suggestion.get("data")

            if isinstance(table_data, list):
                df = pd.DataFrame(table_data)
                rendered_outputs.append(
                    {
                        "type": "table",
                        "data": df,
                    }
                )

        # --------------------------------------------------
        # Render tabla OCC por riesgo (operational evidence)
        # --------------------------------------------------
        if chart_type == "table" and metric == "occ_by_risk":

            table_data = metrics_tables.get("occ_by_risk", {})

            if isinstance(table_data, dict) and table_data:
                rows = [
                    {
                        "risk_id": risk_id,
                        "occ_count": count,
                    }
                    for risk_id, count in table_data.items()
                    if risk_id in entities
                ]

                rendered_outputs.append(
                    {
                        "type": "table",
                        "metric": "occ_by_risk",
                        "data": {
                            "columns": ["risk_id", "occ_count"],
                            "rows": rows,
                        },
                        "question": suggestion.get("question"),
                    }
                )

        # ============================================================
        # >>> NUEVO BLOQUE AUDITORÍAS — Tablas deterministas
        # ============================================================
        if chart_type == "table" and metric.startswith("audits_"):

            table_data = metrics_tables.get(metric, {})

            if isinstance(table_data, dict) and table_data:
                rows = [
                    {
                        "key": k,
                        "count": v,
                    }
                    for k, v in table_data.items()
                ]

                rendered_outputs.append(
                    {
                        "type": "table",
                        "metric": metric,
                        "data": {
                            "columns": ["key", "count"],
                            "rows": rows,
                        },
                        "question": suggestion.get("question"),
                    }
                )

    return rendered_outputs
