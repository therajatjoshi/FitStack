# FitStack — Setup Steps

Simple log of what has been built so far and how to run it. Use this to walk your team through the project.

---

## What we have today

- FastAPI backend with 3 endpoints (health, exercises, workout generation)
- Docker container for the backend
- GitHub Actions CI pipeline (tests + Docker build)
- Local tests with pytest

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

## What's next (not done yet)

- [ ] Push CI workflow to GitHub (needs PAT with `workflow` scope)
- [ ] Terraform for Azure infrastructure
- [ ] Deploy to Azure App Service + Container Registry
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

---

*Last updated: May 31, 2026*
