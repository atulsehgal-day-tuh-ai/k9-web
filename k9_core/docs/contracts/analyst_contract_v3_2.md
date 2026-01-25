1. Propósito del AnalystNode

El AnalystNode es el componente cognitivo responsable de:

Interpretar los hechos estructurados producidos por DataEngineNode

Detectar patrones de degradación, estabilidad o mejora

Priorizar riesgos según dominancia y relevancia temporal

Producir análisis explicables y auditables

NO generar narrativa

NO usar LLM

NO ejecutar acciones

El Analyst razona, pero no comunica.

2. Entradas (Input Contract)

El Analyst consume exclusivamente información desde:

state.analysis["engine"]

2.1 Señales obligatorias (FASE 2 cerrada)

El Analyst asume siempre presentes los siguientes bloques:

engine.period

engine.risk_trends

engine.trajectories.weekly

engine.weekly_signals

engine.observations

engine.audits

engine.proactivo

engine.fdo

Si alguna señal está vacía, debe ser interpretada como ausencia de evidencia, no como error.

2.2 Contexto adicional (opcional)

El Analyst puede usar, si existe:

state.context_bundle

state.risk_enrichment

Nunca debe fallar si estos no están presentes.

3. Capacidades Cognitivas del Analyst

El Analyst implementa capacidades explícitas, cada una con propósito y límites claros.

Capacidad 1 — Riesgo dominante vs relevante

Objetivo
Identificar:

Riesgo dominante: mayor criticidad promedio

Riesgo relevante: no dominante, pero con tendencia a degradarse

Fuente principal

engine.weekly_signals

engine.risk_trends

Salida

risk_summary: {
  dominant_risk,
  relevant_risk
}

Capacidad 2 — Evolución temporal por riesgo

Objetivo
Clasificar el estado temporal de cada riesgo:

degrading

improving

stable

Fuente

engine.risk_trends

Salida

risk_trajectories[risk_id]: {
  trend_direction,
  temporal_state
}

Capacidad 3 — Evidencia observacional

Objetivo
Evaluar soporte operacional vía observaciones (OPG / OCC).

Fuente

engine.observations

state.risk_enrichment (si existe)

Salida

observations_summary[risk_id]: {
  opg_count,
  occ_count,
  support_level
}

Capacidad 4 — Evidencia operacional consolidada

Objetivo
Determinar si existen fallas operacionales relevantes que respalden la degradación.

Fuente

observations_summary

risk_enrichment

Salida

operational_evidence: {
  has_operational_support,
  supported_risks,
  evidence_by_risk
}

Capacidad 5 — Desalineación Proactivo vs K9

Objetivo
Detectar discrepancias entre modelos predictivos.

Fuente

engine.proactivo

Salida

proactive_comparison[risk_id]: {
  alignment_status
}


Estados posibles:

aligned

underestimated_by_proactive

overestimated_by_proactive

inconclusive

Capacidad 6 — Auditorías (FASE 3)

Objetivo
Incorporar evidencia de cumplimiento y degradación de barreras.

Fuente

engine.audits

Estados esperados

auditorías reactivas abiertas

hallazgos críticos

recurrencia por riesgo/control

⚠️ En v3.2 esta capacidad se define, pero puede estar parcialmente implementada.

Capacidad 7 — FDO y presión operacional

Objetivo
Contextualizar riesgos bajo presión operacional.

Fuente

engine.fdo.daily_summary

engine.fdo.accumulated_12s

Uso

No define riesgo

Modula interpretación

Capacidad 8 — Umbrales cognitivos

Objetivo
Determinar proximidad a estados críticos.

Fuente

combinación de:

tendencia

ranking

recurrencia

Salida

thresholds.by_risk[risk_id]: {
  threshold_state
}


Estados:

below_threshold

approaching_threshold

4. Salida (Output Contract)

El Analyst escribe exclusivamente en:

state.analysis


Estructura mínima obligatoria:

{
  period,
  risk_trajectories,
  observations_summary,
  operational_evidence,
  risk_summary,
  proactive_comparison,
  thresholds
}


⚠️ El Analyst NO debe eliminar state.analysis["engine"]
⚠️ El Analyst NO debe generar texto narrativo

5. Límites explícitos del Analyst

El Analyst NO:

genera recomendaciones

predice incidentes

ejecuta acciones

comunica al usuario final

decide mitigaciones

usa LLM

Es un componente de razonamiento intermedio, no un agente autónomo.

6. Compatibilidad y evolución

Este contrato corresponde a K9 v3.2

Nuevas capacidades:

se agregan como secciones nuevas

no rompen capacidades existentes

El contrato precede al código

7. Principio rector

El Analyst no inventa datos.
El Analyst no comunica conclusiones finales.
El Analyst razona sobre hechos.