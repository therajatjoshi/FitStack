from fastapi import FastAPI

from app.routers import exercises, health, workouts

app = FastAPI(
    title="FitStack API",
    description="AI-powered fitness programming platform",
    version="0.2.0",
)

app.include_router(health.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
