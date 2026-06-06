import json
import os
import re

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AzureOpenAI
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.models.db_models import User

router = APIRouter(prefix="/ai", tags=["ai"])

SYSTEM_PROMPT = (
    "You are an expert fitness coach. Generate a structured workout plan. "
    'Respond in JSON only with this shape: {"workout_name": string, "workout_type": string, '
    '"exercises": [{"name": string, "sets": number, "reps": number, "weight_kg": number, "notes": string}]}'
)


class GenerateWorkoutRequest(BaseModel):
    prompt: str | None = None


class GeneratedExercise(BaseModel):
    name: str
    sets: int = Field(..., ge=1)
    reps: int = Field(..., ge=1)
    weight_kg: float = Field(..., ge=0)
    notes: str


class GeneratedWorkoutResponse(BaseModel):
    workout_name: str
    workout_type: str
    exercises: list[GeneratedExercise]


def _build_system_prompt(user: User) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"User goal: {user.goal}\n"
        f"Training experience: {user.training_years} years"
    )


def _get_openai_client() -> AzureOpenAI:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not endpoint or not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is not configured",
        )

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-08-01-preview",
    )


def _parse_workout_json(content: str) -> GeneratedWorkoutResponse:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()

    try:
        payload = json.loads(stripped)
        return GeneratedWorkoutResponse.model_validate(payload)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an invalid workout plan",
        ) from exc


@router.post("/generate-workout", response_model=GeneratedWorkoutResponse)
async def generate_workout(
    payload: GenerateWorkoutRequest,
    current_user: User = Depends(get_current_user),
) -> GeneratedWorkoutResponse:
    client = _get_openai_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    user_message = payload.prompt or "Generate a personalized workout plan for me."

    try:
        completion = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": _build_system_prompt(current_user)},
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

    return _parse_workout_json(content)
