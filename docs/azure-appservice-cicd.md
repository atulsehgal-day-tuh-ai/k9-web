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

## Troubleshooting

### Deploy step fails: `Failed to get app runtime OS`
This almost always means **the Web App name and publish profile do not belong to the same Azure Web App**, or the app you’re targeting isn’t a **Linux Web App (Container)**.

Checklist:
- **App name secret is literal**:
  - `AZURE_WEBAPP_NAME_API` must be exactly `app-k9web-api-...` (no `$API_APP`, no URL, no quotes)
  - `AZURE_WEBAPP_NAME_FE` must be exactly `app-k9web-fe-...`
- **Publish profile is for the same app**:
  - Re-download the publish profile from the Azure Portal for that exact Web App and overwrite the GitHub secret.
  - If you export with CLI, the publish profile should contain a `publishUrl` like:
    - `app-k9web-<...>.scm.azurewebsites.net:443`
- **Web App is Linux**:
  - In CLI, `az webapp show -g <rg> -n <app> --query reserved` should return `true`

### Deploy step fails with `Unauthorized (CODE: 401)` to `*.scm.azurewebsites.net`
If the logs show a 401 when calling:
- `https://<app>.scm.azurewebsites.net:443/diagnostics/runtime`

then **SCM basic-auth publishing credentials are disabled** for the app, or the credentials were rotated after you saved the secret.

Check the policy (repeat for API and FE apps):
- Show current policy:
  - `az resource show -g <rg> --resource-type Microsoft.Web/sites/basicPublishingCredentialsPolicies -n <app>/scm --query properties.allow -o tsv`
- Enable it (if it prints `false`):
  - `az resource update -g <rg> --resource-type Microsoft.Web/sites/basicPublishingCredentialsPolicies -n <app>/scm --set properties.allow=true`

Notes:
- If you still see `Not Found`, double-check you’re using the **Web App name** (e.g. `app-k9web-api-demo`) and the correct resource group/subscription.

#### If `az resource ...` returns `Not Found` (use ARM directly)
Sometimes `az resource` struggles to resolve this child resource even though it exists. This `az rest` approach is deterministic.

PowerShell example:
- Check current value:
  - `az rest --method get --uri "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app>/basicPublishingCredentialsPolicies/scm?api-version=2022-03-01" --query properties.allow -o tsv`
- Enable:
  - `az rest --method put --uri "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/resourceGroups/<rg>/providers/Microsoft.Web/sites/<app>/basicPublishingCredentialsPolicies/scm?api-version=2022-03-01" --body "{""properties"":{""allow"":true}}" -o none`

After enabling, **re-download the publish profile** and update the GitHub secret, then rerun the workflow.

### Quick ACR sanity checks
- Confirm images/tags exist:
  - `az acr repository list -n <acrName> -o table`
  - `az acr repository show-tags -n <acrName> --repository k9-api -o table`
  - `az acr repository show-tags -n <acrName> --repository k9-frontend -o table`
