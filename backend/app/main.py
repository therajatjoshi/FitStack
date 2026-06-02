from fastapi import FastAPI

from app import __version__
from app.routers import exercises, health, workouts

app = FastAPI(
    title="FitStack API",
    description="AI-powered fitness programming platform",
    version=__version__,
)

app.include_router(health.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
