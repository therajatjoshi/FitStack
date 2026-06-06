from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import BodyMetrics, MedicalFlags, Profile, User
from app.models.profile import (
    BodyMetricsCreate,
    BodyMetricsResponse,
    FullProfileResponse,
    MedicalFlagsResponse,
    MedicalFlagsUpdate,
    ProfileResponse,
    ProfileUpdate,
)

# ── Completeness score ────────────────────────────────────────────────────────
# 10 evenly-weighted fields.  Score = filled / 10 * 100 (rounded).

_COMPLETENESS_TOTAL = 10


def _compute_completeness(
    user: User,
    profile: Profile | None,
    medical: MedicalFlags | None,
    latest_metrics: BodyMetrics | None,
) -> int:
    score = 0
    # User fields (2)
    if user.sex:
        score += 1
    if user.date_of_birth:
        score += 1
    # Profile fields (6)
    if profile:
        if profile.height_cm:
            score += 1
        if profile.primary_goal:
            score += 1
        if profile.experience_level:
            score += 1
        if profile.activity_level:
            score += 1
        if profile.training_days_per_week is not None:
            score += 1
        if profile.equipment:
            score += 1
    # Medical acknowledged (1)
    if medical is not None:
        score += 1
    # At least one body metrics entry (1)
    if latest_metrics is not None:
        score += 1
    return round(score / _COMPLETENESS_TOTAL * 100)


# ── Profile ───────────────────────────────────────────────────────────────────

async def get_profile(db: AsyncSession, user_id: UUID) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def upsert_profile(
    db: AsyncSession, user_id: UUID, data: ProfileUpdate
) -> ProfileResponse:
    profile = await get_profile(db, user_id)

    if profile is None:
        profile = Profile(id=uuid.uuid4(), user_id=user_id)
        db.add(profile)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    profile.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(profile)
    return _profile_to_schema(profile)


def _profile_to_schema(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=str(profile.id),
        user_id=str(profile.user_id),
        height_cm=profile.height_cm,
        primary_goal=profile.primary_goal,
        secondary_constraint=profile.secondary_constraint,
        experience_level=profile.experience_level,
        lift_competency=profile.lift_competency,
        activity_level=profile.activity_level,
        training_days_per_week=profile.training_days_per_week,
        equipment=profile.equipment,
        injuries_notes=profile.injuries_notes,
        goal_targets=profile.goal_targets,
        goal_timeline_weeks=profile.goal_timeline_weeks,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


# ── Medical flags ─────────────────────────────────────────────────────────────

async def get_medical_flags(db: AsyncSession, user_id: UUID) -> MedicalFlags | None:
    result = await db.execute(
        select(MedicalFlags).where(MedicalFlags.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def upsert_medical_flags(
    db: AsyncSession, user_id: UUID, data: MedicalFlagsUpdate
) -> MedicalFlagsResponse:
    flags = await get_medical_flags(db, user_id)

    if flags is None:
        flags = MedicalFlags(id=uuid.uuid4(), user_id=user_id)
        db.add(flags)

    for field, value in data.model_dump().items():
        setattr(flags, field, value)

    flags.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(flags)
    return _flags_to_schema(flags)


def _flags_to_schema(flags: MedicalFlags) -> MedicalFlagsResponse:
    return MedicalFlagsResponse(
        id=str(flags.id),
        user_id=str(flags.user_id),
        heart_condition=flags.heart_condition,
        diabetes=flags.diabetes,
        asthma=flags.asthma,
        joint_or_back_issues=flags.joint_or_back_issues,
        pregnant=flags.pregnant,
        other=flags.other,
        other_notes=flags.other_notes,
        none=flags.none,
        updated_at=flags.updated_at,
    )


# ── Body metrics ──────────────────────────────────────────────────────────────

async def get_latest_body_metrics(
    db: AsyncSession, user_id: UUID
) -> BodyMetrics | None:
    result = await db.execute(
        select(BodyMetrics)
        .where(BodyMetrics.user_id == user_id)
        .order_by(desc(BodyMetrics.recorded_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def add_body_metrics(
    db: AsyncSession, user_id: UUID, data: BodyMetricsCreate
) -> BodyMetricsResponse:
    entry = BodyMetrics(id=uuid.uuid4(), user_id=user_id, **data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return _metrics_to_schema(entry)


async def list_body_metrics(
    db: AsyncSession,
    user_id: UUID,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> list[BodyMetricsResponse]:
    stmt = (
        select(BodyMetrics)
        .where(BodyMetrics.user_id == user_id)
        .order_by(desc(BodyMetrics.recorded_at))
    )
    if from_date:
        stmt = stmt.where(BodyMetrics.recorded_at >= from_date)
    if to_date:
        stmt = stmt.where(BodyMetrics.recorded_at <= to_date)

    result = await db.execute(stmt)
    return [_metrics_to_schema(m) for m in result.scalars().all()]


def _metrics_to_schema(m: BodyMetrics) -> BodyMetricsResponse:
    return BodyMetricsResponse(
        id=str(m.id),
        user_id=str(m.user_id),
        weight_kg=m.weight_kg,
        body_fat_pct=m.body_fat_pct,
        waist_cm=m.waist_cm,
        hip_cm=m.hip_cm,
        recorded_at=m.recorded_at,
    )


# ── Full merged view ──────────────────────────────────────────────────────────

async def get_full_profile(db: AsyncSession, user: User) -> FullProfileResponse:
    profile = await get_profile(db, user.id)
    medical = await get_medical_flags(db, user.id)
    latest_metrics = await get_latest_body_metrics(db, user.id)
    completeness = _compute_completeness(user, profile, medical, latest_metrics)

    return FullProfileResponse(
        # User
        id=str(user.id),
        email=user.email,
        name=user.name,
        sex=user.sex,
        date_of_birth=user.date_of_birth,
        consent_accepted_at=user.consent_accepted_at,
        consent_version=user.consent_version,
        # Profile (with None defaults if no record)
        height_cm=profile.height_cm if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        secondary_constraint=profile.secondary_constraint if profile else None,
        experience_level=profile.experience_level if profile else None,
        lift_competency=profile.lift_competency if profile else None,
        activity_level=profile.activity_level if profile else None,
        training_days_per_week=profile.training_days_per_week if profile else None,
        equipment=profile.equipment if profile else None,
        injuries_notes=profile.injuries_notes if profile else None,
        goal_targets=profile.goal_targets if profile else None,
        goal_timeline_weeks=profile.goal_timeline_weeks if profile else None,
        # Latest body metrics
        latest_weight_kg=latest_metrics.weight_kg if latest_metrics else None,
        latest_body_fat_pct=latest_metrics.body_fat_pct if latest_metrics else None,
        latest_waist_cm=latest_metrics.waist_cm if latest_metrics else None,
        latest_hip_cm=latest_metrics.hip_cm if latest_metrics else None,
        # Medical
        medical_flags=_flags_to_schema(medical) if medical else None,
        # Computed
        profile_completeness=completeness,
    )
