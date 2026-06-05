from pydantic import BaseModel, Field


class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    muscle_group: str = Field(..., min_length=1, max_length=100)
    equipment: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(..., min_length=1, max_length=50)


class Exercise(BaseModel):
    id: str
    name: str
    muscle_group: str = Field(..., description="Primary muscle group targeted")
    equipment: str = Field(..., description="Required equipment (e.g. barbell, bodyweight)")
