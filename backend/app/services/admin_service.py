from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminUserSummary, CleanupResult
from app.models.db_models import Admin, BodyMetrics, User, Workout
from app.services.auth_service import AuthService

auth_service = AuthService()

# Stale thresholds (days). Tune here.
ABANDONED_DAYS = 30
INACTIVE_DAYS = 90


# ── Bootstrap ───────────────────────────────────────────────────────────────

async def ensure_seed_admin(db: AsyncSession, email: str, password: str) -> None:
    """Create the bootstrap admin if it doesn't already exist. Idempotent."""
    existing = await db.execute(select(Admin).where(Admin.email == email))
    if existing.scalar_one_or_none() is not None:
        return
    db.add(Admin(email=email, hashed_password=auth_service.hash_password(password)))
    await db.commit()


# ── Auth ────────────────────────────────────────────────────────────────────

async def authenticate_admin(
    db: AsyncSession, email: str, password: str
) -> Admin | None:
    result = await db.execute(select(Admin).where(Admin.email == email))
    admin = result.scalar_one_or_none()
    if admin is None or not auth_service.verify_password(
        password, admin.hashed_password
    ):
        return None
    return admin


# ── Stale logic ───────────────────────────────────────────────────────────────

def _stale_reason(
    created_at: datetime,
    consent_accepted_at: datetime | None,
    workout_count: int,
    body_metrics_count: int,
    now: datetime,
) -> str | None:
    """Return why an account is stale, or None if it is active/recent."""
    if consent_accepted_at is None and created_at < now - timedelta(days=ABANDONED_DAYS):
        return "abandoned"
    if (
        workout_count == 0
        and body_metrics_count == 0
        and created_at < now - timedelta(days=INACTIVE_DAYS)
    ):
        return "inactive"
    return None


async def _load_rows(db: AsyncSession) -> list[tuple[User, int, int]]:
    """One query: each user with their workout + body-metrics counts."""
    workout_count = (
        select(func.count(Workout.id))
        .where(Workout.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    metrics_count = (
        select(func.count(BodyMetrics.id))
        .where(BodyMetrics.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    stmt = select(
        User,
        workout_count.label("workout_count"),
        metrics_count.label("body_metrics_count"),
    ).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    return [(row[0], row[1], row[2]) for row in result.all()]


def _to_summary(
    user: User, workout_count: int, body_metrics_count: int, now: datetime
) -> AdminUserSummary:
    reason = _stale_reason(
        user.created_at, user.consent_accepted_at, workout_count, body_metrics_count, now
    )
    return AdminUserSummary(
        id=str(user.id),
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        consent_accepted_at=user.consent_accepted_at,
        workout_count=workout_count,
        body_metrics_count=body_metrics_count,
        is_stale=reason is not None,
        stale_reason=reason,
    )


async def list_user_summaries(db: AsyncSession) -> list[AdminUserSummary]:
    now = datetime.now(UTC)
    return [_to_summary(u, wc, mc, now) for (u, wc, mc) in await _load_rows(db)]


async def find_stale_users(db: AsyncSession) -> list[AdminUserSummary]:
    return [s for s in await list_user_summaries(db) if s.is_stale]


# ── Deletion ──────────────────────────────────────────────────────────────────

async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """Delete a user; dependent rows go via DB-level ON DELETE CASCADE.
    Returns False if the user does not exist."""
    result = await db.execute(select(User.id).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        return False
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return True


async def cleanup_stale(db: AsyncSession) -> CleanupResult:
    """Recompute stale accounts server-side and delete them."""
    now = datetime.now(UTC)
    stale = [
        u for (u, wc, mc) in await _load_rows(db)
        if _stale_reason(u.created_at, u.consent_accepted_at, wc, mc, now) is not None
    ]
    if not stale:
        return CleanupResult(deleted_count=0, deleted_emails=[])

    ids = [u.id for u in stale]
    emails = [u.email for u in stale]
    await db.execute(delete(User).where(User.id.in_(ids)))
    await db.commit()
    return CleanupResult(deleted_count=len(ids), deleted_emails=emails)
