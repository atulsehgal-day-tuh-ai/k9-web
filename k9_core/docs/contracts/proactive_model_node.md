ProactiveModelNode — Contrato Cognitivo (FASE 2 · PRE lunes crítico)
1. Rol cognitivo

El ProactiveModelNode tiene como rol interpretar y explicar la relación entre:

el ranking y comportamiento del modelo proactivo,

el razonamiento cognitivo de K9,

y la evidencia operacional disponible (OCC),

con el objetivo de hacer explícita la alineación o desalineación entre ambos enfoques.

Este nodo no predice, no recalibra y no decide eventos.
Su función es explicativa y comparativa, no prescriptiva.

2. Alcance funcional (qué hace)

El nodo puede:

Explicar por qué un riesgo aparece:

alineado,

subestimado,

o sobreestimado
por el modelo proactivo, en relación con K9.

Incorporar evidencia operacional (OCC) como factor de refuerzo explicativo.

Generar razonamiento defendible del tipo:

“El modelo proactivo no prioriza R01 pese a la evidencia operacional, porque…”

El nodo no modifica el estado del sistema más allá de agregar una explicación estructurada.

3. Fuera de alcance (prohibiciones explícitas)

El ProactiveModelNode NO está autorizado a:

Recalibrar scores del modelo proactivo

Alterar rankings existentes

Declarar eventos críticos

Detectar lunes crítico

Ejecutar inferencia causal

Proponer acciones correctivas

Escribir directamente en state.answer

Usar LLMs como fuente de verdad

Cualquier violación de estas reglas se considera ruptura del contrato cognitivo.

4. Fase válida

FASE 2 — PRE lunes crítico

El nodo no debe ejecutarse en:

FASE 1

POST lunes crítico

escenarios con active_event activo

La activación del nodo es condicional a routing explícito, no automática.

5. Dependencias de estado (lectura)

El nodo lee exclusivamente los siguientes campos del K9State:

state.analysis["risk_summary"]

dominant_risk

relevant_risk

state.analysis["proactive_comparison"]

state.analysis["operational_evidence"] (si existe)

state.context_bundle (definición y supuestos del modelo proactivo)

No debe leer directamente datasets ni señales crudas.

6. Escritura en el estado (salida permitida)

El nodo escribe únicamente en:

state.analysis["proactive_explanation"]


Con una estructura esperada como:

{
  "alignment_status": "aligned | underestimated | overestimated | inconclusive",
  "explained_risks": ["R01", "R02"],
  "explanation": {
    "R01": {
      "proactive_rank": int,
      "k9_rank": int,
      "operational_evidence": True,
      "explanation_text": str
    }
  }
}


El nodo no debe modificar ningún otro bloque del análisis.

7. Supuestos cognitivos válidos

El nodo opera bajo los siguientes supuestos explícitos:

La desalineación no implica error del modelo proactivo.

La evidencia operacional refuerza, pero no invalida, modelos predictivos.

Un riesgo puede ser relevante cognitivamente antes de ser crítico predictivamente.

La explicación debe ser contextual y no reactiva.

8. Relación con otros nodos

DataEngineNode
→ fuente de hechos deterministas (no se toca)

OCC Enrichment Node
→ fuente de evidencia operacional (no se reinterpreta)

AnalystNode
→ consolida razonamiento previo (no se contradice)

NarrativeNode
→ traduce la explicación proactiva a lenguaje humano
(el ProactiveModelNode no genera narrativa)

9. Criterio de aceptación funcional

El nodo se considera correctamente implementado si:

Puede responder coherentemente a preguntas como:

“¿Por qué el modelo proactivo no está priorizando R01 pese a la evidencia operacional?”

La explicación es:

consistente con los datos

trazable

no sensacionalista

El sistema no declara eventos ni activa lunes crítico

10. Principio rector

El ProactiveModelNode no busca tener razón,
busca explicar por qué distintas formas de razonamiento
pueden coexistir antes de un evento crítico.

✅ Estado del contrato

Este contrato es activo, válido y obligatorio para toda implementación del proactive_model_node en K9 Mining Safety v3.2.