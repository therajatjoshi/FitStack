import os

from fastapi import FastAPI

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


@app.on_event("startup")
async def on_startup() -> None:
    if os.getenv("SKIP_DB_INIT") == "1":
        return
    await create_tables()


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
