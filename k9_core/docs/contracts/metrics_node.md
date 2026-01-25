📐 CONTRATO OFICIAL — MetricsNode



K9 Mining Safety v3.2

FASE 1 cerrada / FASE 2 temprana (PRE lunes crítico)



1\. Rol del nodo (definición formal)



El MetricsNode es un nodo de materialización métrica, no cognitivo.



Su rol es transformar análisis ya consolidado en artefactos métricos estructurados (rankings, series temporales, tablas y conteos), sin interpretar, priorizar ni razonar sobre su significado.



El MetricsNode:



no decide,



no explica,



no persuade,



no genera narrativa.



2\. Principio rector



“MetricsNode no busca convencer; busca hacer visible.”



Toda salida del nodo debe ser:



determinista,



objetiva,



trazable al análisis existente,



reutilizable por capas superiores (UI, reportes, validaciones).



3\. Alcance funcional (qué SÍ hace)



El MetricsNode puede:



3.1 Materializar métricas



Rankings métricos



jerarquía dominante / relevante,



prioridad estructural (sin interpretación).



Series temporales



evolución semanal por riesgo,



valores ya calculados por nodos previos.



Tablas y conteos



OCC por riesgo,



conteos simples derivados de evidencia operacional.



3.2 Sugerir visualizaciones (no renderizarlas)



El MetricsNode puede sugerir visualizaciones potenciales, siempre bajo reglas deterministas explícitas, y nunca como decisión automática.



Las sugerencias:



son estructurales,



se expresan como preguntas,



no implican que la UI deba ejecutarlas.



4\. Fuera de alcance (prohibiciones explícitas)



El MetricsNode NO DEBE:



❌ Interpretar métricas (“esto es crítico”, “esto es preocupante”).



❌ Priorizar riesgos (eso es responsabilidad del AnalystNode).



❌ Generar narrativa o texto explicativo al usuario.



❌ Renderizar gráficos o ejecutar librerías de visualización.



❌ Decidir qué se muestra automáticamente en la UI.



❌ Modificar conclusiones cognitivas existentes.



❌ Recalcular scores del modelo proactivo.



❌ Introducir eventos, escenarios o análisis pre/post (lunes crítico).



5\. Fase válida de operación



El MetricsNode es válido únicamente en:



✅ FASE 1 — Baseline Cognitivo PRE lunes crítico.



✅ FASE 2 temprana — Proactivo + evidencia operacional.



No contiene lógica dependiente de:



eventos críticos,



comparaciones pre/post,



análisis de delta,



simulaciones contrafactuales.



6\. Dependencias de lectura (estado de entrada)



El MetricsNode solo puede leer desde analysis:



analysis\["risk\_summary"]



analysis\["risk\_trajectories"]



analysis\["operational\_evidence"]



analysis\["proactive\_explanation"] (si existe)



El MetricsNode NO accede directamente a:



data\_engine,



archivos CSV / Parquet,



modelos predictivos,



fuentes externas de datos.



7\. Escritura permitida en el estado (contrato de salida)



El MetricsNode solo puede escribir en un bloque aislado y no cognitivo del estado:



analysis\["metrics"]



Estructura esperada:

analysis\["metrics"] = {

&nbsp;   "rankings": {...},

&nbsp;   "time\_series": {...},

&nbsp;   "tables": {...},

&nbsp;   "visual\_suggestions": \[...]

}





El MetricsNode NO puede modificar:



risk\_summary,



análisis cognitivo previo,



reasoning,



answer.



8\. Reglas deterministas de sugerencia de visualización (cerradas)



El MetricsNode puede sugerir a lo más una visualización, y siempre como pregunta opcional.



Las reglas implementadas y garantizadas son:



Evolución temporal



Si existen trayectorias temporales válidas

→ sugerir line\_chart.



Comparación multi-riesgo



Si existen ≥2 riesgos comparables en el análisis



o si el usuario solicita explícitamente comparación

→ sugerir risk\_comparison.



Ranking / prioridad (fallback)



Si no existen trayectorias ni comparación



pero sí jerarquía estructural

→ sugerir risk\_priority.



Reglas adicionales no implementadas no deben inferirse ni simularse.



9\. Relación con otros nodos



Orden lógico del pipeline:



AnalystNode

&nbsp;  ↓

MetricsNode

&nbsp;  ↓

RouterNode

&nbsp;  ↓

NarrativeNode

&nbsp;  ↓

Streamlit





MetricsNode consume análisis cognitivo.



NarrativeNode consume análisis + métricas.



Streamlit consume métricas, nunca las genera.



10\. Criterios de aceptación funcional (testables)



El MetricsNode se considera correcto si:



No modifica análisis cognitivo.



Produce métricas deterministas y repetibles.



Cumple estrictamente las reglas de visualización definidas.



No rompe ningún test FASE 1 / FASE 2 temprana.



Validación mediante:



pytest (F02.001–F02.006),



smoke tests del grafo completo.



Cierre



Este contrato refleja exactamente el estado real del sistema hoy:

ni más, ni menos.



No introduce deuda.



No promete reglas futuras.



No contradice el código ni los tests.

