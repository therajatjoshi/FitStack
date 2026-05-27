from fastapi import APIRouter

from app.models.exercise import Exercise
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/exercises", tags=["exercises"])
exercise_service = ExerciseService()


@router.get("", response_model=list[Exercise])
def list_exercises() -> list[Exercise]:
    return exercise_service.list_exercises()
