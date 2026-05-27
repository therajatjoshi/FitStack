from fastapi import APIRouter

from app.models.workout import WorkoutGenerateRequest, WorkoutResponse
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/workouts", tags=["workouts"])
workout_service = WorkoutService()


@router.post("/generate", response_model=WorkoutResponse)
def generate_workout(request: WorkoutGenerateRequest) -> WorkoutResponse:
    return workout_service.generate_workout(request)
