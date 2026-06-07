import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.constants import CONSENT_TEXT, CONSENT_VERSION
from app.database import Base, engine
from app.routers import ai, auth, exercises, health, profile, workouts


async def create_tables() -> None:
    import app.models.db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("SKIP_DB_INIT") != "1":
        await create_tables()
    yield


app = FastAPI(
    title="FitStack API",
    description="AI-powered fitness programming platform",
    version=__version__,
    lifespan=lifespan,
)

cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/consent-text", tags=["consent"])
async def get_consent_text() -> dict[str, str]:
    return {"version": CONSENT_VERSION, "text": CONSENT_TEXT}


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
app.include_router(ai.router)
app.include_router(profile.router)
