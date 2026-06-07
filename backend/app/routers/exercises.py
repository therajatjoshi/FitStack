from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import Exercise as ExerciseORM
from app.models.db_models import User
from app.models.exercise import Exercise, ExerciseCreate

router = APIRouter(prefix="/exercises", tags=["exercises"])


def _to_schema(exercise: ExerciseORM) -> Exercise:
    return Exercise(
        id=str(exercise.id),
        name=exercise.name,
        muscle_group=exercise.muscle_group,
        equipment=exercise.equipment,
    )


@router.get("", response_model=list[Exercise])
async def list_exercises(db: AsyncSession = Depends(get_db)) -> list[Exercise]:
    result = await db.execute(select(ExerciseORM).order_by(ExerciseORM.name))
    exercises = result.scalars().all()
    return [_to_schema(exercise) for exercise in exercises]


@router.post("", response_model=Exercise, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    payload: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Exercise:
    exercise = ExerciseORM(**payload.model_dump())
    db.add(exercise)
    await db.commit()
    await db.refresh(exercise)
    return _to_schema(exercise)
