from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import User
from app.models.profile import (
    BodyMetricsCreate,
    BodyMetricsResponse,
    ConsentRequest,
    ConsentResponse,
    FullProfileResponse,
    MedicalFlagsResponse,
    MedicalFlagsUpdate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services import profile_service

router = APIRouter(tags=["profile"])


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get("/profile/me", response_model=FullProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FullProfileResponse:
    return await profile_service.get_full_profile(db, current_user)


@router.put("/profile/me", response_model=ProfileResponse)
async def update_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    return await profile_service.upsert_profile(db, current_user.id, payload)


@router.put("/profile/me/medical", response_model=MedicalFlagsResponse)
async def update_medical_flags(
    payload: MedicalFlagsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MedicalFlagsResponse:
    return await profile_service.upsert_medical_flags(db, current_user.id, payload)


@router.post("/profile/me/consent", response_model=ConsentResponse)
async def record_consent(
    payload: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    current_user.consent_accepted_at = datetime.now(UTC)
    current_user.consent_version = payload.consent_version
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return ConsentResponse(
        consent_accepted_at=current_user.consent_accepted_at,
        consent_version=current_user.consent_version,
    )


# ── Body metrics ──────────────────────────────────────────────────────────────

@router.post(
    "/body-metrics",
    response_model=BodyMetricsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_body_metrics(
    payload: BodyMetricsCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BodyMetricsResponse:
    return await profile_service.add_body_metrics(db, current_user.id, payload)


@router.get("/body-metrics", response_model=list[BodyMetricsResponse])
async def list_body_metrics(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[BodyMetricsResponse]:
    return await profile_service.list_body_metrics(
        db, current_user.id, from_date, to_date
    )
