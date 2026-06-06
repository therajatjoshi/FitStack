# FitStack — Setup Steps

Simple log of what has been built so far and how to run it. Use this to walk your team through the project.

---

## What we have today

- FastAPI backend with JWT auth, PostgreSQL persistence, and Azure OpenAI workout generation
- User profile system — onboarding fields, body metrics time-series, medical safety flags
- React frontend (Vite + TypeScript) with onboarding, profile, metrics, and workout logging
- Docker container for the backend (local + Azure)
- GitHub Actions — **CI** (tests on every push/PR) + **Deploy** (backend + frontend on push to `main`)
- Terraform config for Azure infrastructure (`infra/`) including PostgreSQL Flexible Server
- **Live site** — https://rajatjoshi.fit (Cloudflare → Azure Static Web Apps + App Service API)
- **Backend direct URL** — https://fitstack-tn26-api.azurewebsites.net
- API version **0.2.0** — auto-deploy pipeline verified end-to-end

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

**Goal:** Automatically test on every push and pull request to `main`.

**What was created:**

- `.github/workflows/ci.yml` — tests + Docker build smoke test
- `.github/workflows/deploy.yml` — auto-deploy backend + frontend on push to `main` (see Step 8)

**What CI does on each push/PR to `main`:**

1. Checks out the code
2. Sets up Python 3.12
3. Installs backend dependencies from `requirements-dev.txt`
4. Runs `pytest` (health, exercises, workouts, profile tests)
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
| Frontend | `npm run dev` (from `frontend/`) |

**Live site:** https://rajatjoshi.fit

**Test the health endpoint:**

```powershell
Invoke-RestMethod https://rajatjoshi.fit/health
```

**Register and login:**

```powershell
Invoke-RestMethod -Method Post -Uri https://rajatjoshi.fit/auth/register `
  -ContentType "application/json" `
  -Body '{"email":"you@example.com","password":"Test1234!","name":"Your Name"}'

$login = Invoke-RestMethod -Method Post -Uri https://rajatjoshi.fit/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"you@example.com","password":"Test1234!"}'
$token = $login.access_token
```

**Get profile (authenticated):**

```powershell
Invoke-RestMethod -Uri https://rajatjoshi.fit/profile/me `
  -Headers @{Authorization="Bearer $token"}
```

**Generate an AI workout (authenticated):**

```powershell
Invoke-RestMethod -Method Post -Uri https://rajatjoshi.fit/ai/generate-workout `
  -ContentType "application/json" `
  -Headers @{Authorization="Bearer $token"} `
  -Body '{"prompt":"a workout for me"}'
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

**Status:** All secrets configured. Auto-deploy verified (June 2026).

**Additional secret for frontend deploy:**

| Secret name | Source |
|-------------|--------|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Azure Portal → Static Web App **fitstack-frontend** → Manage deployment token |

---

### Security rules for the team

1. **Never** paste secrets into `SETUP-STEPS.md`, code, or commit messages
2. **Never** commit `terraform.tfstate` — it contains ACR passwords and App Insights keys (already in `.gitignore`)
3. If a secret is exposed, **rotate it immediately**:
   - ACR: `az acr credential renew --name fitstacktn26acr --password-name password`
   - Service principal: create a new SP and update `AZURE_CREDENTIALS` in GitHub
4. GitHub secrets are **write-only** — you cannot view them again after saving; keep a local secure copy (e.g. password manager) if needed

---

## Step 8 — CI/CD auto-deploy + custom domain

**Goal:** Push to `main` automatically deploys backend and frontend — no manual Docker push.

**What was created:**

- `.github/workflows/deploy.yml` — backend deploy (ACR push + App Service restart) + frontend deploy (Static Web Apps)
- `.github/workflows/ci.yml` — tests only (runs on push + PR to `main`; deploy moved to `deploy.yml`)

**Deploy flow on push to `main`:**

1. **Backend job** — login to Azure → login to ACR → build Docker image → push to ACR → restart Web App
2. **Frontend job** — `npm install` + `npm run build` (with `VITE_API_URL=https://rajatjoshi.fit`) → upload `frontend/dist/` to Azure Static Web Apps

**Verified:** Bumped API version to `0.2.0` in `/health`, pushed to `main`, and confirmed live at https://rajatjoshi.fit/health.

**Custom domain:** `rajatjoshi.fit` routes through Cloudflare to the Azure Static Web App (frontend) and App Service (API).

---

## Step 9 — PostgreSQL Flexible Server (Terraform)

**Goal:** Persistent database for users, workouts, profiles, and body metrics.

**Resources added to `infra/main.tf`:**

| Resource | Details |
|----------|---------|
| PostgreSQL Flexible Server | Burstable **B_Standard_B1ms**, PostgreSQL **16**, Central India |
| Database | **`fitstack_db`** |
| Firewall: AllowAzureServices | Azure services (App Service) |
| Firewall: AllowDeveloperIp | Your public IP for local dev |

**New variables (`infra/variables.tf`):**

| Variable | Default | Notes |
|----------|---------|-------|
| `admin_username` | `fitstackadmin` | Server admin login |
| `admin_password` | *(none)* | **Sensitive** — set in `terraform.tfvars` |
| `developer_ip` | *(none)* | Your public IP for dev access |

**Live outputs:**

| Output | Value |
|--------|-------|
| Server hostname | `fitstack-pg-tn26.postgres.database.azure.com` |
| Database name | `fitstack_db` |

**Important:** `infra/terraform.tfvars` is gitignored — never commit passwords.

**Status:** Applied to Azure successfully (June 2026).

---

## Step 10 — Database layer + ORM models

**Goal:** Async SQLAlchemy connection to PostgreSQL with typed models.

**What was created:**

```
backend/app/
├── database.py          # async engine, session factory, get_db()
├── dependencies.py      # get_current_user (JWT)
└── models/
    └── db_models.py     # SQLAlchemy ORM models
```

**Tables (initial set):**

| Model | Table | Purpose |
|-------|-------|---------|
| User | `users` | Auth + basic account info |
| Exercise | `exercises` | Exercise catalog |
| Workout | `workouts` | User workout sessions |
| WorkoutLog | `workout_logs` | Sets/reps/weight per exercise |

**Connection:** Set `DATABASE_URL` env var (asyncpg format):

```
postgresql+asyncpg://fitstackadmin:<password>@fitstack-pg-tn26.postgres.database.azure.com:5432/fitstack_db
```

**Startup:** `main.py` runs `Base.metadata.create_all` on startup (skipped when `SKIP_DB_INIT=1` for tests).

---

## Step 11 — JWT authentication

**Goal:** Register and login with email/password; protect workout and profile routes.

**Endpoints:**

| Method | Path | What it does |
|--------|------|--------------|
| POST | `/auth/register` | Create account (email, password, name) |
| POST | `/auth/login` | Returns JWT `access_token` |

**Stack:** passlib (bcrypt) for password hashing, python-jose for JWT tokens.

**Protected routes** use `get_current_user` dependency — pass `Authorization: Bearer <token>` header.

---

## Step 12 — Database-backed exercises & workouts

**Goal:** Replace stub data with real PostgreSQL CRUD.

**Endpoints:**

| Method | Path | Auth | What it does |
|--------|------|------|--------------|
| GET | `/exercises` | No | List exercises from DB |
| POST | `/exercises` | No | Seed a new exercise |
| POST | `/workouts` | Yes | Create a workout |
| GET | `/workouts` | Yes | List user's workouts |
| POST | `/workouts/{id}/log` | Yes | Log a set (exercise, sets, reps, weight) |
| GET | `/workouts/{id}/logs` | Yes | List logs for a workout |

**Tests:** Mocked DB session in `tests/conftest.py` so CI runs without PostgreSQL.

---

## Step 13 — Azure OpenAI workout generation

**Goal:** AI-generated workouts using user profile context and safety constraints.

**Endpoint:**

| Method | Path | Auth | What it does |
|--------|------|------|--------------|
| POST | `/ai/generate-workout` | Yes | Returns structured workout JSON from GPT-4o mini |

**Required App Service env vars:**

| Variable | Purpose |
|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | API key |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name (default: `gpt-4o-mini`) |

**Response includes:** `workout_name`, `workout_type`, `exercises[]`, `disclaimer`, `consult_recommended`.

**Status:** Verified live — generates personalized workouts with medical safety flags applied.

---

## Step 14 — React frontend (Vite + TypeScript)

**Goal:** Web UI for login, workout logging, and AI generation.

**What was created:**

```
frontend/
├── src/
│   ├── api.ts              # axios client, JWT in memory, VITE_API_URL
│   ├── App.tsx             # react-router routes
│   └── pages/
│       ├── LoginPage.tsx   # register + login
│       ├── DashboardPage.tsx
│       └── WorkoutPage.tsx
├── vite.config.ts          # VITE_API_URL defaults to https://rajatjoshi.fit
└── public/
    └── staticwebapp.config.json   # SPA fallback for React Router
```

**Run locally:**

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API calls go to `https://rajatjoshi.fit` by default (or set `VITE_API_URL=http://localhost:8000` for local backend).

**Deploy:** `deploy-frontend` job in `.github/workflows/deploy.yml` builds and uploads to Azure Static Web App **fitstack-frontend**.

---

## Step 15 — Profile, body metrics & medical safety (backend)

**Goal:** Rich user profiles for personalized AI workouts, with conservative safety when health flags are set.

**Design principles:**

- FitStack is a **fitness tool, not a medical app** — flags only make AI output more conservative
- Onboarding is fast: small mandatory set, everything else optional with defaults
- Body composition is a **time-series log** (never single overwrite fields)
- Workout generation is **never blocked** by optional profile fields

**New tables:**

| Model | Table | Purpose |
|-------|-------|---------|
| Profile | `profiles` | Goals, experience, equipment, injuries, etc. |
| MedicalFlags | `medical_flags` | Health considerations (heart, diabetes, joints, etc.) |
| BodyMetrics | `body_metrics` | Weight, body fat, waist, hip — logged over time |

**Extended `users` table:** `sex`, `date_of_birth`, `consent_accepted_at`, `consent_version`

**Endpoints:**

| Method | Path | Auth | What it does |
|--------|------|------|--------------|
| GET | `/consent-text` | No | Legal consent text + version |
| GET | `/profile/me` | Yes | Full profile + medical flags + latest metrics + completeness score (0–100) |
| PUT | `/profile/me` | Yes | Partial upsert of profile fields |
| PUT | `/profile/me/medical` | Yes | Upsert medical flags |
| POST | `/profile/me/consent` | Yes | Record consent acceptance |
| POST | `/body-metrics` | Yes | Log a new body metric entry |
| GET | `/body-metrics` | Yes | List metrics (optional date filters) |

**Safety service (`safety_service.py`):** When medical flags are active, AI prompts get conservative constraints and `consult_recommended: true`.

**AI upgrade:** `/ai/generate-workout` now injects profile, latest body metrics, and safety constraints into the system prompt.

**Tests:** `tests/test_profile.py` — 20+ tests covering profile, medical flags, body metrics, consent, and AI safety.

---

## Step 16 — Onboarding & profile UI (frontend)

**Goal:** Guided onboarding flow, profile editing, weigh-in tracking, and consult-recommended banner.

**New pages:**

| Page | Route | Purpose |
|------|-------|---------|
| OnboardingPage | `/onboarding` | 4-step flow: About You → Health → Consent → Optional extras |
| ProfilePage | `/profile` | Completeness bar + 4 saveable card sections |
| MetricsPage | `/metrics` | Weigh-in form + history list |

**New component:** `ConsultBanner.tsx` — amber warning when AI returns `consult_recommended: true`

**Routing logic:**

- Register → `/onboarding`
- Login with `profile_completeness === 0` → `/onboarding`
- Login with profile started → `/` (dashboard)

**Design system:** Glassmorphism — near-black `#080808` background, glass cards, electric indigo `#6366f1` accent, fully responsive (430px → desktop).

**Status:** Built, tested against live API, pushed to `main` (June 7, 2026).

---

## What's next (not done yet)

- [ ] Azure AI Search RAG pipeline (exercise science knowledge base)
- [ ] Entra ID B2C authentication (replace email/password JWT)
- [ ] Progressive overload tracking engine
- [ ] Periodization logic (linear → undulating → block)
- [ ] Coach mode (multi-tenant)
- [ ] Alembic migrations (currently using `create_all` on startup)

---

## Notes for explaining to the team

1. **Routers vs services:** Routes only handle HTTP. Services hold the logic. This makes it easy to change database or AI behavior without changing the API contract.
2. **Docker:** Same backend image runs locally and in Azure. No "works on my machine" surprises.
3. **CI vs Deploy:** `ci.yml` runs tests on every push/PR. `deploy.yml` deploys backend + frontend only on push to `main`.
4. **Auth:** JWT tokens stored in browser memory (not localStorage). Entra ID B2C is planned to replace email/password auth.
5. **Profile completeness:** A 0–100 score encourages onboarding but never blocks workout generation. Optional fields have sane defaults.
6. **Medical flags:** Not diagnosis — they only tell the AI to be conservative and show a "consult a professional" banner when appropriate.
7. **Body metrics:** Always append-only time-series. Users log new entries; history is preserved for trend tracking.
8. **Terraform:** All Azure resources are defined in `infra/`. A 4-character random suffix keeps globally unique names from colliding.
9. **GitHub Secrets:** Azure credentials live in GitHub repo settings, not in code. Never commit `.env`, `terraform.tfvars`, or `terraform.tfstate`.
10. **Frontend API URL:** Set via `VITE_API_URL` at build time. Production builds point to `https://rajatjoshi.fit`; local dev can override to `http://localhost:8000`.

---

*Last updated: June 7, 2026*
