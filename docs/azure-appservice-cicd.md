# Azure App Service (Docker) + GitHub Actions (CI/CD)

This repo is set up for **CI builds** (no local Docker required):
- GitHub Actions builds Docker images on every push to `main`
- Images are pushed to **Azure Container Registry (ACR)**
- Azure App Service pulls the images and runs:
  - Backend: `k9_backend/` (FastAPI)
  - Frontend: `k9_frontend/` (Next.js)

## 1) Azure resources (DEV/demo)

Create:
- **Resource Group** (example): `rg-k9web-dev`
- **ACR** (example): `acrk9webdev<suffix>`
- **App Service Plan (Linux)** (example): `asp-k9web-dev`
- **Web App (backend)** (example): `app-k9web-api-dev-<suffix>`
- **Web App (frontend)** (example): `app-k9web-fe-dev-<suffix>`

## 2) Configure App Service to pull images

In each Web App (Container settings):
- Image source: **Azure Container Registry**
- Image:
  - backend: `k9-api:main`
  - frontend: `k9-frontend:main`

## 3) App settings (environment variables)

### Backend (`app-k9web-api-dev-...`)
- `K9_PROVIDER=gemini`
- `K9_GEMINI_API_KEY=<your key>`
- `K9_GEMINI_MODEL=gemini-2.5-flash`
- `K9API_ALLOWED_ORIGINS=https://<frontend-hostname>`

### Frontend (`app-k9web-fe-dev-...`)
- `K9_API_BASE_URL=https://<backend-hostname>`

## 4) GitHub repository secrets

These are required by the workflows:

### ACR push secrets
- `ACR_LOGIN_SERVER` (example: `acrk9webdev123.azurecr.io`)
- `ACR_USERNAME` (ACR admin username)
- `ACR_PASSWORD` (ACR admin password)

### Azure Web App deploy secrets (publish profiles)
- `AZURE_WEBAPP_NAME_API` (backend web app name)
- `AZURE_WEBAPP_PUBLISH_PROFILE_API` (backend publish profile XML)
- `AZURE_WEBAPP_NAME_FE` (frontend web app name)
- `AZURE_WEBAPP_PUBLISH_PROFILE_FE` (frontend publish profile XML)

Notes:
- We intentionally keep `K9_GEMINI_API_KEY` **in Azure App Settings**, not GitHub secrets.
- Publish profiles are easiest for demo CI/CD; for production, prefer OIDC + a service principal.

## 5) Workflows
- Backend workflow: `.github/workflows/deploy-backend.yml`
- Frontend workflow: `.github/workflows/deploy-frontend.yml`

