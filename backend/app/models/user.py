from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    name: str = Field(..., min_length=1, max_length=255)


class UserUpdate(BaseModel):
    """Editable user-level fields (sex, date of birth). All optional —
    only provided fields are updated."""

    sex: Literal["male", "female", "other"] | None = None
    date_of_birth: date | None = None

    @field_validator("date_of_birth")
    @classmethod
    def _dob_is_reasonable(cls, value: date | None) -> date | None:
        if value is None:
            return value
        today = date.today()
        if value > today:
            raise ValueError("date_of_birth cannot be in the future")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age > 120:
            raise ValueError("date_of_birth is not within a reasonable range")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    training_years: int
    goal: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMeResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    sex: str | None = None
    date_of_birth: date | None = None

    model_config = {"from_attributes": True}
