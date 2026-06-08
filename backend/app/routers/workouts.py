from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import User
from app.models.workout import (
    CompleteWorkoutRequest,
    SaveGeneratedWorkoutRequest,
    WorkoutCreate,
    WorkoutLogCreate,
    WorkoutLogResponse,
    WorkoutResponse,
)
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/workouts", tags=["workouts"])
workout_service = WorkoutService()


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    payload: WorkoutCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    return await workout_service.create_workout(db, current_user, payload)


@router.post(
    "/generated",
    response_model=WorkoutResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_generated_workout(
    payload: SaveGeneratedWorkoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    return await workout_service.save_generated_workout(db, current_user, payload)


@router.get("", response_model=list[WorkoutResponse])
async def list_workouts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkoutResponse]:
    return await workout_service.list_workouts(db, current_user)


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    workout = await workout_service.get_user_workout(db, current_user, workout_id)
    return workout_service.to_workout_response(workout)


@router.post("/{workout_id}/complete", response_model=WorkoutResponse)
async def complete_workout(
    workout_id: UUID,
    payload: CompleteWorkoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutResponse:
    return await workout_service.complete_workout(
        db, current_user, workout_id, payload
    )


@router.post(
    "/{workout_id}/log",
    response_model=WorkoutLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def log_exercise_set(
    workout_id: UUID,
    payload: WorkoutLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutLogResponse:
    return await workout_service.log_set(db, current_user, workout_id, payload)


@router.get("/{workout_id}/logs", response_model=list[WorkoutLogResponse])
async def list_workout_logs(
    workout_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkoutLogResponse]:
    return await workout_service.list_logs(db, current_user, workout_id)
