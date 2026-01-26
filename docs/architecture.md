# K9-Web Architecture

This document describes the architecture of the K9 Mining Safety Demo system at both high and low levels.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js / React)                     │
│         Chat UI + KPI Dashboard + JSON Visualization                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP POST /api/chat
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND API (FastAPI)                          │
│                                                                     │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
│   │ interpret() │ →  │ run_graph() │ →  │ synthesize()│            │
│   │  NL → K9    │    │  LangGraph  │    │  K9 → NL    │            │
│   └─────────────┘    └─────────────┘    └─────────────┘            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   K9 Core     │      │   Ontology    │      │   LLM Client  │
│  (LangGraph   │      │  (28 YAML     │      │   (Gemini)    │
│   Pipeline)   │      │   files)      │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
        │
        ▼
┌───────────────┐
│ Synthetic Data│
│ (CSV/Parquet) │
└───────────────┘
```

### Component Overview

| Layer | Component | Technology | Responsibility |
|-------|-----------|------------|----------------|
| Frontend | `k9_frontend/` | Next.js, React 19, TypeScript | User interface, chat, dashboard |
| Backend | `k9_backend/` | FastAPI, Python 3.11 | API orchestration, 3-phase pipeline |
| Core | `k9_core/` | LangGraph, Pandas | Deterministic analysis engine |
| Knowledge | `k9_core/data/ontology/` | YAML | Mining safety domain knowledge |
| Data | `k9_core/data/synthetic/` | CSV, Parquet | Simulated mining operations data |
| LLM | Gemini API | Google AI | Natural language translation |

---

## Request/Response Flow

```
User Question (Spanish)
        │
        ▼
┌───────────────────────────────────────┐
│  POST /api/chat { sessionId, message }│
└───────────────────┬───────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐    ┌──────────┐    ┌──────────┐
│INTERPRET│    │RUN GRAPH │    │SYNTHESIZE│
│        │    │          │    │          │
│NL→K9   │ →  │LangGraph │ →  │K9→NL     │
│Command │    │Pipeline  │    │Response  │
└────────┘    └──────────┘    └──────────┘
    │               │               │
    ▼               ▼               ▼
  Gemini      Deterministic      Gemini
   LLM          Analysis          LLM
                    │
                    ▼
┌───────────────────────────────────────┐
│  Response: { answer, analysis,        │
│              metrics, reasoning }     │
└───────────────────────────────────────┘
```

---

## Low-Level Architecture

### LangGraph Pipeline (14 Nodes)

The K9 Core uses a LangGraph state machine with conditional routing based on query intent.

```
                            START
                              │
                              ▼
                    ┌─────────────────┐
                    │   guardrail    │  Domain validation
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │    context     │  Load operational context
                    └────────┬────────┘
                              │
                    ┌─────────┴─────────┐
                    │  route_pre_data   │  Router decision
                    └─────────┬─────────┘
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
            ▼                                   ▼
   ONTOLOGY_QUERY                        FACTUAL_QUERY
            │                                   │
            ▼                                   ▼
   ┌─────────────────┐               ┌─────────────────┐
   │ ontology_query  │               │   data_engine   │
   └────────┬────────┘               └────────┬────────┘
            │                                   │
            │                                   ▼
            │                        ┌─────────────────┐
            │                        │ occ_enrichment  │
            │                        └────────┬────────┘
            │                                   │
            │                                   ▼
            │                        ┌─────────────────┐
            │                        │    analyst      │
            │                        └────────┬────────┘
            │                                   │
            │                                   ▼
            │                        ┌─────────────────┐
            │                        │    metrics      │
            │                        └────────┬────────┘
            │                                   │
            │                                   ▼
            │                        ┌─────────────────┐
            │                        │     router      │
            │                        └────────┬────────┘
            │                                   │
            │                    ┌──────────────┴──────────────┐
            │                    │      route_post_analysis    │
            │                    └──────────────┬──────────────┘
            │                                   │
            │         ┌────────────┬────────────┼────────────┬────────────┐
            │         │            │            │            │            │
            │         ▼            ▼            ▼            ▼            ▼
            │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
            │   │ semantic │ │proactive │ │  bowtie  │ │ fallback │ │ [other]  │
            │   │ retrieval│ │  model   │ │          │ │          │ │          │
            │   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
            │        │            │            │            │            │
            │        └────────────┴────────────┴────────────┴────────────┘
            │                                   │
            └───────────────────────────────────┤
                                                │
                                                ▼
                                      ┌─────────────────┐
                                      │    narrative    │
                                      └────────┬────────┘
                                                │
                                                ▼
                                               END
```

### Node Responsibilities

| Node | Purpose | Key Operations |
|------|---------|----------------|
| `guardrail` | Domain validation | Validates intent is mining safety related |
| `context` | Load context | Loads operational areas, top risks, event types |
| `ontology_query` | Knowledge retrieval | Queries 28 YAML ontology files |
| `data_engine` | Data loading | Loads synthetic data, computes trends |
| `occ_enrichment` | OCC analysis | Enriches with critical control observations |
| `analyst` | Risk analysis | Rankings, trajectories, comparisons |
| `metrics` | KPI computation | Dominant risk, relevant risk, visualizations |
| `router` | Intent routing | Parses time context, validates intent |
| `semantic_retrieval` | Context lookup | Pattern matching for operational queries |
| `proactive_model` | Prediction analysis | Compares proactive model vs K9 rankings |
| `bowtie` | Causal analysis | BowTie methodology explanation |
| `fallback` | Error handling | Out-of-domain responses |
| `narrative` | LLM preparation | Structures guidance for synthesis phase |

---

## K9State (Central Data Contract)

All nodes operate on a shared `K9State` dataclass:

```python
class K9State:
    # Inputs
    user_query: str                    # Original Spanish question
    k9_command: Dict[str, Any]         # Canonical K9 command (SOURCE OF TRUTH)

    # Execution
    reasoning: List[str]               # Step-by-step trace log
    demo_mode: bool                    # Out-of-domain flag

    # Context
    context_bundle: Dict[str, Any]     # Operational context + ontology results
    time_context: TimeContext          # Semantic time specification
    data_slice: DataSlice              # Physical data filter

    # Analysis
    intent: str                        # Canonical intent string
    analysis: Dict[str, Any]           # Engine + analyst + metrics results
    risk_enrichment: Dict[str, Any]    # OCC enrichment by risk

    # Output
    narrative_context: Dict[str, Any]  # Pre-LLM guidance for synthesis
    answer: str                        # Final Spanish narrative
```

### Analysis Structure

The `state.analysis` dictionary contains:

```
analysis/
├── engine/
│   ├── period (min_week, max_week)
│   ├── trajectories (risk trends by week)
│   ├── weekly_signals (avg_criticidad, rank, top3 weeks)
│   ├── observations (OPG/OCC counts)
│   └── audits (audit statistics)
├── risk_trajectories/
│   └── {risk_id: trend_direction, temporal_state}
├── risk_summary/
│   ├── dominant_risk (highest avg_criticidad)
│   └── relevant_risk (degrading trajectory)
├── proactive_comparison/
│   └── {risk_id: proactive_rank, k9_rank, delta}
├── operational_evidence/
│   └── {risk_id: occ_support, control_failures}
├── metrics/
│   ├── rankings
│   ├── time_series
│   ├── tables
│   └── visual_suggestions
└── proactive_explanation/
    └── {risk_id: alignment_status, explanation}
```

---

## Temporal Resolution Pipeline

```
User Intent (NL)
      │
      ▼
┌─────────────────┐
│  "last month"   │  User says temporal phrase
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TimeContext    │  Semantic representation
│  type: RELATIVE │
│  value: LAST_   │
│         MONTH   │
│  confidence:    │
│    EXPLICIT     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   DataSlice     │  Physical data filter
│  resolution:    │
│    INDEX        │
│  start: 8       │
│  end: 12        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Filtered Data  │  Actual rows from dataset
└─────────────────┘
```

### Time Context Types

| Type | Values | Example |
|------|--------|---------|
| RELATIVE | CURRENT_WEEK, LAST_WEEK, LAST_2_WEEKS, LAST_4_WEEKS, LAST_MONTH | "última semana" |
| WINDOW | PRE, POST, PRE_POST | "antes del evento" |
| ANCHOR | CRITICAL_MONDAY | "lunes crítico" |
| ABSOLUTE | Specific dates | "semana 10" |

---

## Ontology Structure

The knowledge base consists of 28 YAML files organized by entity type:

### Core Catalogs

| File | Entity | Description |
|------|--------|-------------|
| `01_catalogo_riesgos_v8.yaml` | Risk | 3 main risks with causes, consequences, controls |
| `02_catalogo_controles_v6.yaml` | Controls | Preventive & mitigative controls |
| `03_catalogo_causas_v4.yaml` | Causes | Root causes linked to risks |
| `04_catalogo_consecuencias_v6.yaml` | Consequences | Potential impacts |
| `05_catalogo_factores_degradacion_v3.yaml` | Degradation | Environmental factors |
| `06_catalogo_barreras_recuperacion_v3.yaml` | Barriers | Recovery/mitigation barriers |

### BowTie Analysis

| File | Risk | Description |
|------|------|-------------|
| `07_bowtie_caida_altura_v3.yaml` | R01 | Fall from height |
| `08_bowtie_caida_objetos_v3.yaml` | R02 | Object fall |
| `09_bowtie_contacto_energia_v3.yaml` | R03 | Energy contact |

### Operational Catalogs

| File | Entity |
|------|--------|
| `10_catalogo_roles_v3.yaml` | Job roles |
| `12_catalogo_tareas_v1.yaml` | Tasks |
| `13_catalogo_areas_operacionales_v1.yaml` | Operational areas |
| `14_catalogo_epp_v3.yaml` | PPE |
| `17_catalogo_peligros_detectados_v5.yaml` | Hazards |
| `19_catalogo_acciones_correctivas_v1.yaml` | Corrective actions |

### Schema & Structure

| File | Purpose |
|------|---------|
| `21_formatos_analisis_v4.yaml` | Analysis formats |
| `23_estructura_incidentes_v5.yaml` | Incident schema |
| `24_estructura_observaciones_v6.yaml` | Observation schema |
| `27_catalogo_niveles_severidad_v2.yaml` | Severity levels |
| `28_glosario_seguridad_v7.yaml` | Safety glossary |

---

## LLM Integration

### Architecture Pattern

```
┌────────────────────────────────────────────────────┐
│                   LLM Factory                      │
│  create_llm_client(settings) → BaseLLMClient      │
│     ├── "mock"   → MockLLMClient                  │
│     └── "gemini" → GeminiClient                   │
└────────────────────────────────────────────────────┘
```

### LLM Contract

The LLM is treated as a **stateless translator** with strict constraints:

- **No domain reasoning** - only linguistic translation
- **No flow control** - returns raw text only
- **No state** - each call is independent
- **No decision making** - follows K9 semantic schema

### Payload Structure

```
LLMPayload
├── LLMSystemContract
│   └── constraints: [do_not_reason, do_not_decide_flow, ...]
├── LLMUserContext
│   ├── original_question
│   └── language: "es"
├── LLMK9Context
│   ├── k9_command (SOURCE OF TRUTH)
│   ├── operational_analysis
│   └── narrative_context
└── LLMKnowledgeScaffold
    ├── canonical_schema
    ├── domain_semantics_es
    └── examples
```

### Phases

| Phase | Input | Output |
|-------|-------|--------|
| Interpretation | Spanish question | K9 command JSON |
| Synthesis | K9 analysis + narrative_context | Spanish response |

---

## Frontend Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        page.tsx                                 │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │      Chat Panel         │  │      Dashboard Panel        │  │
│  │  ┌───────────────────┐  │  │  ┌───────────────────────┐  │  │
│  │  │  Message Thread   │  │  │  │  KpiCard (dominant)   │  │  │
│  │  │  - user messages  │  │  │  └───────────────────────┘  │  │
│  │  │  - assistant msgs │  │  │  ┌───────────────────────┐  │  │
│  │  └───────────────────┘  │  │  │  KpiCard (relevant)   │  │  │
│  │  ┌───────────────────┐  │  │  └───────────────────────┘  │  │
│  │  │   Input Box       │  │  │  ┌───────────────────────┐  │  │
│  │  └───────────────────┘  │  │  │  JsonBlock (metrics)  │  │  │
│  └─────────────────────────┘  │  │  JsonBlock (reasoning)│  │  │
│                               │  └───────────────────────────┘  │
└───────────────────────────────┴─────────────────────────────────┘
```

### State Management

```typescript
// Main state in page.tsx
input: string              // Current message text
messages: Message[]        // Chat history
latestResult: ApiResponse  // Last API response (raw JSON)
loading: boolean           // Async state
error: string | null       // Error message
```

### API Route Proxy

The frontend proxies requests to the backend:

```
Frontend /api/chat → route.ts → Backend K9_API_BASE_URL/api/chat
```

---

## Key Architectural Principles

1. **Single Source of Truth**: `state.k9_command` drives all routing decisions
2. **Separation of Concerns**:
   - Semantic (TimeContext) vs Operational (DataSlice)
   - Deterministic cognition vs LLM interfaces
   - Data loading vs analysis
3. **Composability**: All nodes operate on immutable K9State
4. **Explicit Traceability**: `state.reasoning` logs all decisions
5. **Gating Pattern**: Nodes validate preconditions before execution
6. **Minimal LLM Contract**: LLM only translates, no domain logic
7. **Ontology-First**: Domain knowledge externalized to YAML

---

## Environment Configuration

### Backend

| Variable | Purpose | Default |
|----------|---------|---------|
| `K9_PROVIDER` | LLM provider | `gemini` |
| `K9_GEMINI_API_KEY` | Gemini API key | (required) |
| `K9_GEMINI_MODEL` | Model name | `gemini-2.5-flash` |
| `K9API_K9_CORE_DIR` | Path to k9_core | (auto-detected) |
| `K9API_ALLOWED_ORIGINS` | CORS origins | `*` |

### Frontend

| Variable | Purpose | Default |
|----------|---------|---------|
| `K9_API_BASE_URL` | Backend URL | `/api/chat` proxy |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Azure App Service                            │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │  Frontend Container │      │  Backend Container  │          │
│  │  (Node.js/Next.js)  │ ──── │  (Python/FastAPI)   │          │
│  │  Port: 3000         │      │  Port: 8000         │          │
│  └─────────────────────┘      └─────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure Container Registry (ACR)                     │
│   k9-frontend:latest    │    k9-backend:latest                 │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              GitHub Actions CI/CD                               │
│   deploy-frontend.yml   │    deploy-backend.yml                │
│   Trigger: push to main │    Trigger: push to main             │
└─────────────────────────────────────────────────────────────────┘
```

For detailed deployment instructions, see [azure-appservice-cicd.md](./azure-appservice-cicd.md).
