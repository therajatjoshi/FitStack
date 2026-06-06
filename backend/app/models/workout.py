from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WorkoutCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    workout_type: str = Field(..., min_length=1, max_length=100)


class WorkoutResponse(BaseModel):
    id: str
    user_id: str
    name: str
    workout_type: str
    created_at: datetime


class WorkoutLogCreate(BaseModel):
    exercise_id: UUID
    sets: int = Field(..., ge=1)
    reps: int = Field(..., ge=1)
    weight_kg: float = Field(..., ge=0)


class WorkoutLogResponse(BaseModel):
    id: str
    user_id: str
    exercise_id: str
    workout_id: str
    sets: int
    reps: int
    weight_kg: float
    logged_at: datetime
