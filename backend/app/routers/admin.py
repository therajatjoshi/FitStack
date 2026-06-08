from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.admin import (
    AdminLogin,
    AdminToken,
    AdminUserSummary,
    CleanupResult,
)
from app.models.db_models import Admin
from app.services import admin_service
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])
auth_service = AuthService()


@router.post("/auth/login", response_model=AdminToken)
async def admin_login(
    payload: AdminLogin,
    db: AsyncSession = Depends(get_db),
) -> AdminToken:
    admin = await admin_service.authenticate_admin(db, payload.email, payload.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token(
        subject=str(admin.id), extra_claims={"type": "admin"}
    )
    return AdminToken(access_token=token)


@router.get("/users", response_model=list[AdminUserSummary])
async def list_users(
    _admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserSummary]:
    return await admin_service.list_user_summaries(db)


@router.get("/users/stale", response_model=list[AdminUserSummary])
async def list_stale_users(
    _admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserSummary]:
    return await admin_service.find_stale_users(db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    _admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await admin_service.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


@router.post("/users/cleanup", response_model=CleanupResult)
async def cleanup_stale_users(
    _admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> CleanupResult:
    return await admin_service.cleanup_stale(db)
