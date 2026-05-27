from pydantic import BaseModel, Field


class Exercise(BaseModel):
    id: str
    name: str
    muscle_group: str = Field(..., description="Primary muscle group targeted")
    equipment: str = Field(..., description="Required equipment (e.g. barbell, bodyweight)")
