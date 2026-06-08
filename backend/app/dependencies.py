from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Admin, User
from app.services.auth_service import AuthService

security = HTTPBearer()
auth_service = AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = auth_service.get_user_id_from_token(credentials.credentials)
    except JWTError as exc:
        raise credentials_exception from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    """Authorize an admin token. Requires the `type: "admin"` claim, so ordinary
    user tokens are rejected here, and admin tokens are rejected by
    `get_current_user` (their subject matches no user row)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = auth_service.decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise credentials_exception from exc

    if payload.get("type") != "admin":
        raise credentials_exception

    admin_id = payload.get("sub")
    if not admin_id:
        raise credentials_exception

    try:
        admin_uuid = UUID(admin_id)
    except ValueError as exc:
        raise credentials_exception from exc

    result = await db.execute(select(Admin).where(Admin.id == admin_uuid))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise credentials_exception

    return admin
