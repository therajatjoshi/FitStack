# FitStack — Setup Steps

Simple log of what has been built so far and how to run it. Use this to walk your team through the project.

---

## What we have today

- FastAPI backend with 3 endpoints (health, exercises, workout generation)
- Docker container for the backend (local + Azure)
- GitHub Actions CI pipeline (tests + Docker build)
- Local tests with pytest
- Terraform config for Azure infrastructure (`infra/`)
- **Live Azure deployment** — https://fitstack-tn26-api.azurewebsites.net
- GitHub Actions secrets being configured for automated deploy to ACR

---

## Step 1 — FastAPI backend

**Goal:** Create the API skeleton with a clean folder structure.

**What was created:**

```
backend/
├── requirements.txt          # fastapi, uvicorn, pydantic
├── pytest.ini                # so tests can import the app
├── tests/
│   └── test_health.py        # checks /health returns 200
└── app/
    ├── main.py               # FastAPI app entry point
    ├── routers/              # API routes
    │   ├── health.py
    │   ├── exercises.py
    │   └── workouts.py
    ├── models/               # Pydantic request/response models
    │   ├── exercise.py
    │   └── workout.py
    └── services/             # business logic (stubs for now)
        ├── exercise_service.py
        └── workout_service.py
```

**Endpoints:**

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/exercises` | Returns a stub list of 3 exercises |
| POST | `/workouts/generate` | Returns a stub workout based on your input |

**Run locally (without Docker):**

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the API docs.

**Run tests:**

```powershell
cd backend
.\venv\Scripts\activate
pip install pytest httpx
pytest
```

---

## Step 2 — Docker container

**Goal:** Package the backend so it runs the same way on any machine.

**What was created:**

- `backend/Dockerfile` — uses `python:3.12-slim`, installs deps, runs uvicorn on port 8000
- `backend/.dockerignore` — keeps venv, cache, and `.env` out of the image
- `docker-compose.yml` (project root) — builds and runs the backend on port 8000

**Run with Docker:**

```powershell
cd "C:\My Repo\FitStack"
docker compose up --build
```

**Run in the background:**

```powershell
docker compose up -d
```

**Stop the container:**

```powershell
docker compose down
```

**Verify it works:**

- Health: http://localhost:8000/health
- API docs: http://localhost:8000/docs

**Status:** Built and tested successfully. All 3 endpoints respond correctly inside the container.

---

## Step 3 — GitHub Actions CI

**Goal:** Automatically test and build on every push to `main`.

**What was created:**

- `.github/workflows/ci.yml`

**What CI does on each push to `main`:**

1. Checks out the code
2. Sets up Python 3.12
3. Installs backend dependencies + pytest + httpx
4. Runs `pytest` (health endpoint test)
5. Builds the Docker image (`docker build -t fitstack-backend ./backend`)

**Known issue — push blocked by GitHub token:**

If `git push` fails with:

```
refusing to allow a Personal Access Token to create or update workflow
without `workflow` scope
```

Fix: update your GitHub Personal Access Token to include the **`workflow`** scope (classic token) or **Actions read/write** (fine-grained token), then push again.

---

## Step 4 — Docker verified on Windows

**Goal:** Confirm Docker Desktop works after installation.

**What we did:**

1. Refreshed the shell PATH so `docker` is found
2. Ran `docker compose build` — image built successfully
3. Ran `docker compose up -d` — container started
4. Hit all 3 endpoints — all returned expected results
5. Ran `pytest` locally — 1 test passed

---

## Quick reference for your team

**Start the app (pick one):**

| Method | Command |
|--------|---------|
| Python directly | `uvicorn app.main:app --reload` (from `backend/`) |
| Docker | `docker compose up --build` (from project root) |

**Test the health endpoint:**

```powershell
Invoke-RestMethod http://localhost:8000/health
```

**Generate a stub workout:**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/workouts/generate `
  -ContentType "application/json" `
  -Body '{"goal":"strength","experience_level":"beginner","days_per_week":3}'
```

---

## Step 5 — Terraform (Azure infrastructure)

**Goal:** Define all Azure resources as code so the team can deploy consistently.

**What was created:**

```
infra/
├── versions.tf      # Terraform + provider versions (azurerm, random)
├── providers.tf     # azurerm provider with subscription ID
├── variables.tf     # subscription_id, project_name, location, docker_image_name
├── main.tf          # all Azure resources
└── outputs.tf       # web app URL, ACR login server, resource group name
```

**Resources provisioned by Terraform:**

| Resource | Details |
|----------|---------|
| Resource group | Central India (`centralindia`) |
| Log Analytics workspace | For monitoring logs |
| Application Insights | Linked to Log Analytics, wired into Web App |
| Container Registry (ACR) | Basic SKU, admin enabled for initial Docker pulls |
| App Service Plan | B1, Linux |
| Linux Web App | Runs Docker image from ACR on port 8000 |

**Default variables:**

| Variable | Default |
|----------|---------|
| `subscription_id` | `7ec7c4d6-8b6b-4bf2-ab4c-9086a21a8a0c` |
| `project_name` | `fitstack` |
| `location` | `centralindia` |
| `docker_image_name` | `fitstack-backend:latest` |

**Deploy (after `az login`):**

```powershell
cd infra
terraform init
terraform plan
terraform apply
```

**After apply — push your Docker image to ACR:**

```powershell
# Use outputs from terraform apply
$ACR = "<acr_login_server from output>"
az acr login --name $ACR.Split(".")[0]
docker tag fitstack-backend:latest "$ACR/fitstack-backend:latest"
docker push "$ACR/fitstack-backend:latest"
```

Then restart the Web App so it pulls the new image.

**Status:** Applied to Azure successfully (May 31, 2026).

**Live outputs:**

| Output | Value |
|--------|-------|
| Resource group | `fitstack-rg` |
| ACR login server | `fitstacktn26acr.azurecr.io` |
| Web app URL | https://fitstack-tn26-api.azurewebsites.net |

---

## Step 6 — Azure deployment (Docker image to ACR + Web App)

**Goal:** Push the same Docker image used locally to Azure and run it on App Service.

**Commands you ran (in order):**

```powershell
# 1. Deploy infrastructure
cd infra
terraform plan
terraform apply          # 7 resources created in ~3 min

# 2. Log in to ACR
az acr login --name fitstacktn26acr

# 3. Rebuild image locally
cd ..
docker compose build

# 4. Tag and push to ACR
docker tag fitstack-backend:latest fitstacktn26acr.azurecr.io/fitstack-backend:latest
docker push fitstacktn26acr.azurecr.io/fitstack-backend:latest

# 5. Ensure App Service uses port 8000, then restart
az webapp config appsettings set --name fitstack-tn26-api --resource-group fitstack-rg --settings WEBSITES_PORT=8000
az webapp restart --name fitstack-tn26-api --resource-group fitstack-rg
```

**Tip:** After `docker compose build`, the image name is `fitstack-backend:latest` — not `fitstack-fitstack-backend:latest` (that typo caused a failed tag attempt in the terminal).

**Verified live endpoints:**

| Endpoint | Local (Docker) | Azure |
|----------|------------------|-------|
| `GET /health` | ✅ `{"status":"ok"}` | ✅ `{"status":"ok"}` |
| `GET /exercises` | ✅ 3 exercises | ✅ 3 exercises |
| `POST /workouts/generate` | ✅ stub workout | ✅ stub workout |
| `/docs` | http://localhost:8000/docs | https://fitstack-tn26-api.azurewebsites.net/docs |

**Status:** Backend is live on Azure in Central India.

---

## Step 7 — GitHub Secrets (for CI/CD deploy to Azure)

**Goal:** Store Azure credentials in GitHub so Actions can push Docker images to ACR and restart the Web App — without putting secrets in code.

**Why:** GitHub Actions runs in the cloud. To talk to Azure (login, push to ACR, restart App Service), it needs credentials stored as **encrypted secrets** in the repo settings.

**Where to paste in GitHub:**

1. Open your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** for each row below
3. Paste the value from the matching command output — **never commit these to git**

---

### Command 1 — Get ACR login credentials

Used so GitHub Actions can `docker push` to your registry.

```powershell
az acr credential show --name fitstacktn26acr
```

**From the output, create these GitHub secrets:**

| GitHub secret name | Where to get the value |
|--------------------|------------------------|
| `ACR_LOGIN_SERVER` | `fitstacktn26acr.azurecr.io` (or `terraform output acr_login_server`) |
| `ACR_USERNAME` | `"username"` field from the command output |
| `ACR_PASSWORD` | `"passwords"[0].value` from the command output (either password works) |

---

### Command 2 — Create a service principal for GitHub Actions

Used so GitHub Actions can log in to Azure (restart Web App, etc.). Scoped only to the `fitstack-rg` resource group.

```powershell
az ad sp create-for-rbac `
  --name "fitstack-github" `
  --role contributor `
  --scopes /subscriptions/7ec7c4d6-8b6b-4bf2-ab4c-9086a21a8a0c/resourceGroups/fitstack-rg `
  --json-auth
```

> Note: `--json-auth` is the newer flag (replaces deprecated `--sdk-auth`). It prints one JSON blob.

**From the output, create this GitHub secret:**

| GitHub secret name | Where to get the value |
|--------------------|------------------------|
| `AZURE_CREDENTIALS` | Paste the **entire JSON block** from the command output |

The JSON contains `clientId`, `clientSecret`, `subscriptionId`, and `tenantId`. GitHub Actions uses this with `azure/login@v2`.

---

### Command 3 — Web App details (no secret — use repo variables or hardcode in workflow)

These are not sensitive; they identify which app to restart after deploy.

| GitHub secret / variable | Value |
|--------------------------|-------|
| `AZURE_WEBAPP_NAME` | `fitstack-tn26-api` |
| `AZURE_RESOURCE_GROUP` | `fitstack-rg` |

You can add these as **Repository variables** (Settings → Secrets and variables → Actions → Variables) since they are not passwords.

---

### Checklist — secrets to add in GitHub

| # | Secret name | Source |
|---|-------------|--------|
| 1 | `AZURE_CREDENTIALS` | Full JSON from `az ad sp create-for-rbac ... --json-auth` |
| 2 | `ACR_LOGIN_SERVER` | `fitstacktn26acr.azurecr.io` |
| 3 | `ACR_USERNAME` | From `az acr credential show` |
| 4 | `ACR_PASSWORD` | From `az acr credential show` |
| 5 | `AZURE_WEBAPP_NAME` | `fitstack-tn26-api` |
| 6 | `AZURE_RESOURCE_GROUP` | `fitstack-rg` |

**Status:** Service principal created (`fitstack-github`). ACR credentials retrieved. Paste values into GitHub Actions secrets (in progress).

---

### Security rules for the team

1. **Never** paste secrets into `SETUP-STEPS.md`, code, or commit messages
2. **Never** commit `terraform.tfstate` — it contains ACR passwords and App Insights keys (already in `.gitignore`)
3. If a secret is exposed, **rotate it immediately**:
   - ACR: `az acr credential renew --name fitstacktn26acr --password-name password`
   - Service principal: create a new SP and update `AZURE_CREDENTIALS` in GitHub
4. GitHub secrets are **write-only** — you cannot view them again after saving; keep a local secure copy (e.g. password manager) if needed

---

## What's next (not done yet)

- [ ] Finish pasting GitHub Actions secrets (Step 7 checklist)
- [ ] Extend `.github/workflows/ci.yml` to push to ACR and restart Web App on merge to `main`
- [ ] Push CI workflow to GitHub (needs PAT with `workflow` scope if not done yet)
- [ ] PostgreSQL database
- [ ] Azure OpenAI + RAG for real workout generation
- [ ] React frontend
- [ ] Authentication (Entra ID B2C)

---

## Notes for explaining to the team

1. **Routers vs services:** Routes only handle HTTP. Services hold the logic. This makes it easy to swap stub data for real AI/database calls later without changing the API.
2. **Docker:** Same image runs locally and in Azure. No "works on my machine" surprises.
3. **CI:** Every push to `main` runs tests and builds the Docker image automatically — catches breakages early.
4. **Stubs:** Exercises and workout generation return fake data for now. The API shape is ready; we plug in Azure OpenAI and PostgreSQL when those steps come.
5. **Terraform:** All Azure resources are defined in `infra/`. A 4-character random suffix keeps globally unique names (Web App, ACR) from colliding.
6. **GitHub Secrets:** Azure credentials live in GitHub repo settings, not in code. We create them with `az acr credential show` and `az ad sp create-for-rbac`, then paste once into GitHub Actions secrets.

---

*Last updated: May 31, 2026*
