# k9-web (K9 Mining Safety demo)

This repo contains:
- `k9_core/`: the K9 Mining Safety core (LangGraph pipeline + ontology + synthetic data)
- `k9_backend/`: FastAPI API server (Gemini hybrid: NL→K9 command → graph → NL synthesis)
- `k9_frontend/`: Next.js dashboard + chat UI (to be created)

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

