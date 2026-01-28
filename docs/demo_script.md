# Demo script (curated questions)

Goal: run a reliable demo with **repeatable answers** and **traceability** (what data was used, which nodes ran, and what recommendations came from the knowledge graph).

## Acceptance criteria
- Same question + same dataset state → same answer (demo mode).
- Each response includes a **trace**:
  - intent / query type (operational vs analytic)
  - time window (e.g. last_7d / last_30d)
  - datasets used (file names)
  - graph queries invoked (names/IDs)
- “Critical Monday” button produces a visible **before/after** change in:
  - dominant risk ranking
  - trajectory panels / metrics deltas

## Recommended demo flow
1. Start with “What is the dominant risk today?”
2. Ask one “why” question (causal/exposure factors) to show prescriptive recommendations.
3. Trigger **Critical Monday** and re-ask the dominant risk question to show the change.
4. Show trace panels + raw metrics to prove the answer is reproducible and inspectable.

## The 10 questions
For each question, the UI should show:
- answer (Spanish is fine)
- dominant risk (e.g. R02)
- relevant risk(s)
- trace (datasets + time window + KG lookups)

### Q1 — Dominant risk (current)
**Question**: ¿Cuál es el riesgo dominante hoy?

**Expected output**:
- dominant risk populated (e.g. `R02`)
- time window = last_7d (or “today”)

### Q2 — Explain drivers (causal + factors)
**Question**: Explica por qué el riesgo dominante es el más crítico. ¿Qué factores causales y de exposición están asociados?

**Expected output**:
- explanation referencing factors/controls from ontology (KG)
- recommendations/controls list (prescriptive)

### Q3 — Trajectory for a specific risk
**Question**: Muéstrame la evolución del riesgo R02 en el último mes.

**Expected output**:
- trajectory metrics for last_30d
- any degradation flags

### Q4 — Compare risks (ranking)
**Question**: Compara R01 vs R02: ¿cuál está empeorando más en las últimas 4 semanas?

**Expected output**:
- relative trend comparison
- relevant risk = one that’s degrading

### Q5 — Operational query: observations
**Question**: ¿Cuántas observaciones tuvimos en la última semana y en qué áreas ocurrieron?

**Expected output**:
- counts by area
- trace includes observations dataset(s)

### Q6 — Operational query: audits
**Question**: ¿Qué auditorías reactivas ocurrieron después de eventos en los últimos 14 días?

**Expected output**:
- list/count of reactive audits
- link to event timing association (even if heuristic)

### Q7 — Proactive misalignment (weekly model)
**Question**: ¿Hay desalineación con el modelo proactivo esta semana? ¿Qué umbrales se cruzaron?

**Expected output**:
- proactive model threshold status
- signal that ranking/threshold changed

### Q8 — “Critical Monday” before/after
**Question**: Antes y después de “Lunes Crítico”: ¿cómo cambió el ranking de riesgos?

**Expected output**:
- explicit delta (before vs after)
- trace shows scenario toggle

### Q9 — Prescriptive controls/barriers
**Question**: Para el riesgo dominante, ¿cuáles son los controles críticos y barreras de recuperación recomendadas?

**Expected output**:
- controls + barriers from KG

### Q10 — What changed recently (temporal explanation)
**Question**: ¿Qué cambió en los últimos 7 días que explica el aumento del riesgo relevante?

**Expected output**:
- recent drivers from operational data (FDO/observations/audits)
- trace shows datasets used

