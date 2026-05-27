from pydantic import BaseModel, Field


class WorkoutGenerateRequest(BaseModel):
    goal: str = Field(..., examples=["strength", "hypertrophy", "endurance"])
    experience_level: str = Field(..., examples=["beginner", "intermediate", "advanced"])
    days_per_week: int = Field(..., ge=1, le=7)
    equipment: list[str] = Field(default_factory=list)


class WorkoutExercise(BaseModel):
    exercise_id: str
    name: str
    sets: int
    reps: str
    notes: str | None = None


class WorkoutResponse(BaseModel):
    name: str
    description: str
    exercises: list[WorkoutExercise]
