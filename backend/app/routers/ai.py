import json
import os
import re
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import CONSENT_TEXT
from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import BodyMetrics, MedicalFlags, Profile, User
from app.services import profile_service
from app.services.safety_service import build_safety_constraints

router = APIRouter(prefix="/ai", tags=["ai"])

_JSON_SHAPE = (
    '{"workout_name": string, "workout_type": string, '
    '"exercises": [{"name": string, "sets": number, "reps": number, '
    '"weight_kg": number, "notes": string}]}'
)
_BASE_SYSTEM_PROMPT = (
    "You are an expert fitness coach. Generate a structured workout plan. "
    f"Respond in JSON only with this shape: {_JSON_SHAPE}"
)


# ── Request / response schemas ────────────────────────────────────────────────

class GenerateWorkoutRequest(BaseModel):
    prompt: str | None = None


class GeneratedExercise(BaseModel):
    name: str
    sets: int = Field(..., ge=1)
    reps: int = Field(..., ge=1)
    weight_kg: float = Field(..., ge=0)
    notes: str


class _GeneratedWorkoutCore(BaseModel):
    """Internal shape — exactly what the LLM returns."""
    workout_name: str
    workout_type: str
    exercises: list[GeneratedExercise]


class GeneratedWorkoutResponse(BaseModel):
    workout_name: str
    workout_type: str
    exercises: list[GeneratedExercise]
    disclaimer: str = ""
    consult_recommended: bool = False


# ── Prompt building ───────────────────────────────────────────────────────────

def _compute_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _build_rich_system_prompt(
    user: User,
    profile: Profile | None,
    latest_metrics: BodyMetrics | None,
    constraint_text: str,
) -> str:
    lines: list[str] = [_BASE_SYSTEM_PROMPT, "", "User profile:"]

    if user.sex:
        lines.append(f"- Sex: {user.sex}")
    if user.date_of_birth:
        lines.append(f"- Age: {_compute_age(user.date_of_birth)} years")

    if profile:
        if profile.height_cm:
            lines.append(f"- Height: {profile.height_cm} cm")
        if profile.primary_goal:
            lines.append(f"- Primary goal: {profile.primary_goal}")
        elif user.goal and user.goal != "general":
            lines.append(f"- Goal: {user.goal}")
        if profile.secondary_constraint:
            lines.append(f"- Secondary constraint: {profile.secondary_constraint}")
        if profile.experience_level:
            lines.append(f"- Experience level: {profile.experience_level}")
        elif user.training_years:
            lines.append(f"- Training experience: {user.training_years} years")
        if profile.lift_competency:
            lines.append(f"- Lift competency: {json.dumps(profile.lift_competency)}")
        if profile.activity_level:
            lines.append(f"- Activity level: {profile.activity_level}")
        if profile.training_days_per_week is not None:
            lines.append(f"- Training frequency: {profile.training_days_per_week} days/week")
        if profile.equipment:
            lines.append(f"- Equipment available: {profile.equipment}")
        if profile.injuries_notes:
            lines.append(f"- Injuries/notes: {profile.injuries_notes}")
        if profile.goal_targets:
            lines.append(f"- Goal targets: {json.dumps(profile.goal_targets)}")
        if profile.goal_timeline_weeks:
            lines.append(f"- Goal timeline: {profile.goal_timeline_weeks} weeks")
    else:
        # Fallback to legacy user fields
        if user.goal:
            lines.append(f"- Goal: {user.goal}")
        if user.training_years:
            lines.append(f"- Training experience: {user.training_years} years")

    if latest_metrics:
        if latest_metrics.weight_kg:
            lines.append(f"- Current weight: {latest_metrics.weight_kg} kg")
        if latest_metrics.body_fat_pct:
            lines.append(f"- Body fat: {latest_metrics.body_fat_pct}%")

    if constraint_text:
        lines.extend(["", constraint_text])

    return "\n".join(lines)


# ── OpenAI helpers ────────────────────────────────────────────────────────────

def _get_openai_client() -> AsyncAzureOpenAI:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured",
        )
    return AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-08-01-preview",
    )


def _parse_workout_json(content: str) -> _GeneratedWorkoutCore:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()
    try:
        payload = json.loads(stripped)
        return _GeneratedWorkoutCore.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an invalid workout plan",
        ) from exc


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/generate-workout", response_model=GeneratedWorkoutResponse)
async def generate_workout(
    payload: GenerateWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GeneratedWorkoutResponse:
    # Load profile context (graceful: all can be None)
    user_profile = await profile_service.get_profile(db, current_user.id)
    medical_flags = await profile_service.get_medical_flags(db, current_user.id)
    latest_metrics = await profile_service.get_latest_body_metrics(db, current_user.id)

    safety = build_safety_constraints(current_user, medical_flags)
    system_prompt = _build_rich_system_prompt(
        current_user, user_profile, latest_metrics, safety.constraint_text
    )

    client = _get_openai_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    user_message = payload.prompt or "Generate a personalized workout plan for me."

    try:
        completion = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate workout plan",
        ) from exc

    content = completion.choices[0].message.content
    if not content:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an empty response",
        )

    core = _parse_workout_json(content)
    return GeneratedWorkoutResponse(
        workout_name=core.workout_name,
        workout_type=core.workout_type,
        exercises=core.exercises,
        disclaimer=safety.disclaimer or CONSENT_TEXT,
        consult_recommended=safety.requires_consult,
    )
