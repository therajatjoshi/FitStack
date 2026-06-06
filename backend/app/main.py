import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.database import Base, engine
from app.routers import auth, exercises, health, workouts


async def create_tables() -> None:
    import app.models.db_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app = FastAPI(
    title="FitStack API",
    description="AI-powered fitness programming platform",
    version=__version__,
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


@app.on_event("startup")
async def on_startup() -> None:
    if os.getenv("SKIP_DB_INIT") == "1":
        return
    await create_tables()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
