from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

PrimaryGoal = Literal[
    "fat_loss",
    "muscle_gain",
    "strength",
    "recomp",
    "physique_pageant",
    "general_fitness",
]
ExperienceLevel = Literal["novice", "intermediate", "advanced"]
ActivityLevel = Literal["sedentary", "light", "moderate", "very_active", "extremely_active"]
Equipment = Literal["full_gym", "home_basic", "minimal", "bodyweight_only"]
Sex = Literal["male", "female", "other"]


# ── Profile ──────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    """All fields optional — enables partial updates."""

    height_cm: float | None = Field(None, ge=100, le=250)
    primary_goal: PrimaryGoal | None = None
    secondary_constraint: str | None = Field(None, max_length=255)
    experience_level: ExperienceLevel | None = None
    lift_competency: dict[str, Any] | None = None
    activity_level: ActivityLevel | None = None
    training_days_per_week: int | None = Field(None, ge=1, le=7)
    equipment: Equipment | None = None
    injuries_notes: str | None = None
    goal_targets: dict[str, Any] | None = None
    goal_timeline_weeks: int | None = Field(None, ge=1, le=520)


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    height_cm: float | None
    primary_goal: str | None
    secondary_constraint: str | None
    experience_level: str | None
    lift_competency: dict[str, Any] | None
    activity_level: str | None
    training_days_per_week: int | None
    equipment: str | None
    injuries_notes: str | None
    goal_targets: dict[str, Any] | None
    goal_timeline_weeks: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Medical flags ─────────────────────────────────────────────────────────────

class MedicalFlagsUpdate(BaseModel):
    heart_condition: bool = False
    diabetes: bool = False
    asthma: bool = False
    joint_or_back_issues: bool = False
    pregnant: bool = False
    other: bool = False
    other_notes: str | None = None
    none: bool = False


class MedicalFlagsResponse(BaseModel):
    id: str
    user_id: str
    heart_condition: bool
    diabetes: bool
    asthma: bool
    joint_or_back_issues: bool
    pregnant: bool
    other: bool
    other_notes: str | None
    none: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Body metrics ──────────────────────────────────────────────────────────────

class BodyMetricsCreate(BaseModel):
    weight_kg: float | None = Field(None, ge=20, le=300)
    body_fat_pct: float | None = Field(None, ge=3, le=60)
    waist_cm: float | None = Field(None, ge=30, le=250)
    hip_cm: float | None = Field(None, ge=30, le=250)


class BodyMetricsResponse(BaseModel):
    id: str
    user_id: str
    weight_kg: float | None
    body_fat_pct: float | None
    waist_cm: float | None
    hip_cm: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ── Consent ───────────────────────────────────────────────────────────────────

class ConsentRequest(BaseModel):
    consent_version: str = Field(..., max_length=20)


class ConsentResponse(BaseModel):
    consent_accepted_at: datetime
    consent_version: str


# ── Full merged profile view ──────────────────────────────────────────────────

class FullProfileResponse(BaseModel):
    # User identity
    id: str
    email: str
    name: str
    sex: str | None
    date_of_birth: date | None
    consent_accepted_at: datetime | None
    consent_version: str | None

    # Profile fields (None if no profile record yet)
    height_cm: float | None
    primary_goal: str | None
    secondary_constraint: str | None
    experience_level: str | None
    lift_competency: dict[str, Any] | None
    activity_level: str | None
    training_days_per_week: int | None
    equipment: str | None
    injuries_notes: str | None
    goal_targets: dict[str, Any] | None
    goal_timeline_weeks: int | None

    # Latest body snapshot (None if no metrics logged yet)
    latest_weight_kg: float | None
    latest_body_fat_pct: float | None
    latest_waist_cm: float | None
    latest_hip_cm: float | None

    # Safety/medical summary
    medical_flags: MedicalFlagsResponse | None

    # Computed
    profile_completeness: int  # 0-100
