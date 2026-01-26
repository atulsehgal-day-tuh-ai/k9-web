# k9-web (K9 Mining Safety Demo)

**K9 Mining Safety Demo** is a web application for mining safety risk analysis. Users ask natural language questions (in Spanish) about mining risks, and the system provides intelligent responses with visual dashboards.

## Architecture

The project has three main components:

| Component | Technology | Purpose |
|-----------|------------|---------|
| `k9_frontend/` | Next.js, React 19, TypeScript, Tailwind | Chat UI + KPI dashboard |
| `k9_backend/` | FastAPI, Python 3.11, Uvicorn | API server orchestrating the K9 pipeline |
| `k9_core/` | LangGraph, Pandas, Google Gemini | Core analysis engine + ontology |

## How It Works

The system uses a **3-phase hybrid approach**:

1. **Interpretation** - Gemini LLM translates Spanish questions into canonical K9 commands
2. **Deterministic Analysis** - LangGraph state machine processes data, computes metrics, and builds analysis (data engine → analyst → metrics → narrative)
3. **Synthesis** - Gemini converts structured analysis back into a Spanish natural language response

```
User Question (Spanish)
    ↓
[Frontend] POST /api/chat
    ↓
[Backend] K9Service.interpret()
    → Gemini: NL → K9 Command JSON
    ↓
[Backend] K9Service.run_graph()
    → LangGraph executes pipeline
    ↓
[Backend] K9Service.synthesize()
    → Gemini: K9 Analysis → Spanish NL response
    ↓
[Frontend] Display answer + metrics + reasoning trace
```

## Key Features

- **Chat interface** for natural language Q&A about mining risks
- **KPI dashboard** showing dominant risks, trends, and safety metrics
- **28 YAML ontology files** defining mining safety knowledge (risks, controls, causes, consequences, etc.)
- **Synthetic datasets** simulating realistic mining operations

## Why Separate Frontend and Backend?

- Browsers shouldn't hold secrets (like API keys) or run the full pipeline
- The backend centralizes the "smart" part and keeps keys/config secure (Azure App Settings)
- The frontend stays lightweight: collects user input and displays results

## Local dev (backend)

### 1) Set env vars
Set these (PowerShell example):

```powershell
$env:K9_PROVIDER = "gemini"
$env:K9_GEMINI_API_KEY = "<your_key>"
$env:K9_GEMINI_MODEL = "gemini-2.5-flash"
```

### 2) Install + run

```powershell
cd k9_backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Azure App Service (Docker)
- Backend and frontend are intended to run as separate Dockerized App Services.
- CI/CD is via GitHub Actions on push to `main`.

For the full end-to-end setup (Azure resources, ACR, App Service config, GitHub secrets, troubleshooting):
- See `docs/azure-appservice-cicd.md`

