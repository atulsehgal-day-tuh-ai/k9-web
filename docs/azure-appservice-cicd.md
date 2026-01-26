# Azure App Service (Docker) + GitHub Actions (CI/CD)

This repo is set up so you **don’t need local Docker**:
- GitHub Actions builds Docker images on pushes to `main` (or manual runs)
- Images are pushed to **Azure Container Registry (ACR)**
- **Azure App Service (Linux, container)** pulls images and runs:
  - Backend: `k9_backend/` (FastAPI on port **8000**)
  - Frontend: `k9_frontend/` (Next.js on port **8080**)

## What this doc covers
- Creating Azure resources (RG, ACR, App Service Plan, Web Apps)
- Configuring App Service to pull private images from ACR
- Setting app settings (env vars) for backend + frontend
- Setting GitHub Actions secrets (ACR creds + publish profiles)
- How the workflows work and how to re-run them
- Troubleshooting the common Azure deploy errors we hit (runtime OS / SCM 401)
- Granting access to another user (e.g. `eduardo@day-tuh.ai`)

## Prereqs
- Azure CLI installed (`az`) and logged in: `az login`
- Correct subscription selected (if you have multiple): `az account set -s <subscriptionId>`
- Permissions to create resources / assign roles in the target subscription
- A GitHub repo with Actions enabled (this repo)

## 0) Choose names (example)
PowerShell:

```powershell
$SUFFIX = "demo"
$LOCATION = "eastus"

$RG   = "rg-k9web-$SUFFIX"
$ACR  = "acrk9web$SUFFIX"          # must be globally unique, lowercase, 5-50 chars
$PLAN = "asp-k9web-$SUFFIX"

$API_APP = "app-k9web-api-$SUFFIX"
$FE_APP  = "app-k9web-fe-$SUFFIX"
```

## 1) Create Azure resources (CLI)
Create resource group:

```powershell
az group create -n $RG -l $LOCATION
```

Create ACR (Standard is a good default):

```powershell
az acr create -g $RG -n $ACR --sku Standard
```

Enable ACR admin user (simplest for demo CI/CD):

```powershell
az acr update -n $ACR --admin-enabled true
```

Create Linux App Service Plan:

```powershell
az appservice plan create -g $RG -n $PLAN --is-linux --sku B1
```

Create Web Apps (Linux container). We create them with a placeholder image first; CI/CD will overwrite the image later:

```powershell
az webapp create -g $RG -p $PLAN -n $API_APP --deployment-container-image-name "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
az webapp create -g $RG -p $PLAN -n $FE_APP  --deployment-container-image-name "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
```

## 2) Configure App Service to pull images from ACR (private)
Get ACR login server + creds:

```powershell
$ACR_LOGIN_SERVER = az acr show -n $ACR --query loginServer -o tsv
$ACR_USERNAME     = az acr credential show -n $ACR --query username -o tsv
$ACR_PASSWORD     = az acr credential show -n $ACR --query "passwords[0].value" -o tsv
```

Point each Web App at the correct image **(this matches what the workflows push)**:
- Backend image: `k9-api:main`
- Frontend image: `k9-frontend:main`

```powershell
az webapp config container set -g $RG -n $API_APP `
  --docker-custom-image-name "$ACR_LOGIN_SERVER/k9-api:main" `
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
  --docker-registry-server-user $ACR_USERNAME `
  --docker-registry-server-password $ACR_PASSWORD

az webapp config container set -g $RG -n $FE_APP `
  --docker-custom-image-name "$ACR_LOGIN_SERVER/k9-frontend:main" `
  --docker-registry-server-url "https://$ACR_LOGIN_SERVER" `
  --docker-registry-server-user $ACR_USERNAME `
  --docker-registry-server-password $ACR_PASSWORD
```

## 3) App settings (environment variables)
These are configured **in Azure App Service**, not committed to git.

Azure Portal path:
- App Service → your app → **Settings → Environment variables**

### Backend app settings (`$API_APP`)
Required ports:
- `WEBSITES_PORT=8000`

CORS:
- `K9API_ALLOWED_ORIGINS=https://<frontend-hostname>`
  - Multiple origins: comma-separated, e.g. `https://a,https://b`
  - Use `*` only for quick testing (not recommended for production)

LLM configuration (optional; if not set you may see mock/demo responses):
- `K9_PROVIDER=gemini`
- `K9_GEMINI_API_KEY=<your key>`
- `K9_GEMINI_MODEL=gemini-2.5-flash`

### Frontend app settings (`$FE_APP`)
Required ports:
- `WEBSITES_PORT=8080`

Backend target for the Next.js server-side proxy:
- `K9_API_BASE_URL=https://<backend-hostname>`

## 4) GitHub repo secrets
GitHub path:
- Repo → **Settings → Secrets and variables → Actions**

### ACR push secrets (used by both workflows)
- `ACR_LOGIN_SERVER` (example: `acrk9webdemo.azurecr.io`)
- `ACR_USERNAME`
- `ACR_PASSWORD`

### Azure Web App deploy secrets (publish profiles)
- `AZURE_WEBAPP_NAME_API` = your backend Web App name (example: `app-k9web-api-demo`)
- `AZURE_WEBAPP_PUBLISH_PROFILE_API` = backend publish profile XML
- `AZURE_WEBAPP_NAME_FE` = your frontend Web App name (example: `app-k9web-fe-demo`)
- `AZURE_WEBAPP_PUBLISH_PROFILE_FE` = frontend publish profile XML

#### How to export publish profiles (CLI)
FTPS can be disabled and this still works (publish profiles are not “FTP credentials”).

```powershell
az webapp deployment list-publishing-profiles -g $RG -n $API_APP --xml | Out-File -Encoding utf8 publish-profile-api.xml
az webapp deployment list-publishing-profiles -g $RG -n $FE_APP  --xml | Out-File -Encoding utf8 publish-profile-fe.xml
```

Copy/paste the entire XML content into the corresponding GitHub secret values.

Notes:
- Keep `K9_GEMINI_API_KEY` **in Azure App Settings**, not GitHub secrets.
- Publish profiles are easiest for demo CI/CD; for production, prefer OIDC + managed identity/service principal.

## 5) Workflows (how CI/CD works)
Workflows live in:
- Backend: `.github/workflows/deploy-backend.yml`
- Frontend: `.github/workflows/deploy-frontend.yml`

Key behavior:
- Triggers on push to `main` with path filters (backend ignores frontend changes and vice-versa)
- Also supports **manual runs** via `workflow_dispatch`
- Builds and pushes:
  - `${ACR_LOGIN_SERVER}/k9-api:main`
  - `${ACR_LOGIN_SERVER}/k9-frontend:main`
- Deploys the container image to the Web App using `azure/webapps-deploy@v3`
- Includes a safe “publish profile matches app-name” validation step to catch secret mismatches early

## 6) Verify the deployment
ACR:

```powershell
az acr repository list -n $ACR -o table
az acr repository show-tags -n $ACR --repository k9-api -o table
az acr repository show-tags -n $ACR --repository k9-frontend -o table
```

Backend health:
- `https://<backend-hostname>/health` should return `{"ok":true}`

Frontend:
- `https://<frontend-hostname>/` should load the K9 UI

## 7) Troubleshooting

### Deploy step fails: `Failed to get app runtime OS`
Common causes:
- **Publish profile secret doesn’t belong to the same app** as `AZURE_WEBAPP_NAME_*`
- The target app is not Linux/container (should be `reserved:true`)
- SCM/Kudu rejects auth (often shows up as 401 in logs)

Sanity check Linux container:

```powershell
az webapp show -g $RG -n $API_APP --query "{name:name,reserved:reserved,kind:kind}" -o json
az webapp show -g $RG -n $FE_APP  --query "{name:name,reserved:reserved,kind:kind}" -o json
```

### Deploy step shows `Unauthorized (CODE: 401)` calling `*.scm.azurewebsites.net`
If GitHub Actions logs show a 401 on a URL like:
- `https://<app>.scm.azurewebsites.net:443/diagnostics/runtime`

Then SCM basic auth publishing credentials are disabled, or the credentials were rotated.

Fix (ARM via `az rest`, deterministic):

```powershell
$SUB = az account show --query id -o tsv
$URI = "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Web/sites/$API_APP/basicPublishingCredentialsPolicies/scm?api-version=2022-03-01"

az rest --method get --uri $URI --query properties.allow -o tsv
az rest --method put --uri $URI --body '{\"properties\":{\"allow\":true}}' -o none
az rest --method get --uri $URI --query properties.allow -o tsv
```

Repeat with `$FE_APP` by updating `$URI` accordingly.

After enabling:
- Re-download the publish profile(s)
- Update GitHub secrets
- Re-run the workflow(s)

### Portal notes: “FTP authentication has been disabled…“
That message is about **FTPS**. It does not prevent:
- exporting publish profiles
- using publish profiles for GitHub Actions deploys

### “Application Error” on the site
Start with:
- App Service → **Logs** (container logs)
- Check `WEBSITES_PORT` matches the container port:
  - backend: **8000**
  - frontend: **8080**

## 8) Give someone (e.g. `eduardo@day-tuh.ai`) access
There are two common meanings of “access”:

### A) Let them use/view the app
The site is public by default. Share the URL:
- `https://<frontend-hostname>`

### B) Let them manage the App Service in Azure (Portal access)
1. (If needed) add them to your tenant:
   - Azure Portal → **Microsoft Entra ID** → **Users** → **New guest user** → invite `eduardo@day-tuh.ai`
2. Assign a role on the frontend app:
   - App Service (`$FE_APP`) → **Access control (IAM)** → **Add role assignment**
   - Suggested roles:
     - **Reader**: can view settings/logs
     - **Contributor**: can change settings, restart, etc.

### C) Lock the app down (only authenticated users can open it)
App Service (`$FE_APP`) → **Authentication** → add an identity provider (Microsoft) → **Require authentication** → allow only specific users/groups.
