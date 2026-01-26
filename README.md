# k9-web (K9 Mining Safety demo)

## What is this (plain English)?
This project is a **web demo** that lets a user ask questions (chat) and view a small dashboard about **mining safety risk**.

You’ll see two apps because they do different jobs:
- **Frontend (`k9_frontend/`)**: the website you open in a browser (UI + chat box + dashboard).
- **Backend (`k9_backend/`)**: an API server the frontend talks to. It runs the K9 pipeline and returns answers/results.

The **core logic/data** lives in `k9_core/` (ontology + pipeline + synthetic data). The backend imports and runs this.

### Why do we need both a frontend and backend?
- Browsers shouldn’t hold secrets (like API keys), and they shouldn’t run the full pipeline.
- The backend centralizes the “smart” part and keeps keys/config in one place (Azure App Settings).
- The frontend stays lightweight: it collects user input and shows results.

### High-level flow
1. User types a question in the frontend.
2. Frontend calls the backend endpoint `POST /api/chat`.
3. Backend runs the K9 pipeline (and optionally an LLM) and returns structured results.
4. Frontend renders the response (answer + “dominant risk”, etc.).

## Repo layout
This repo contains:
- `k9_core/`: the K9 Mining Safety core (LangGraph pipeline + ontology + synthetic data)
- `k9_backend/`: FastAPI API server (Gemini hybrid: NL→K9 command → graph → NL synthesis)
- `k9_frontend/`: Next.js dashboard + chat UI

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

