from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.db_models import User
from app.models.user import UserMeResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _to_me_response(user: User) -> UserMeResponse:
    return UserMeResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        sex=user.sex,
        date_of_birth=user.date_of_birth,
    )


@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserMeResponse:
    return _to_me_response(current_user)


@router.put("/me", response_model=UserMeResponse)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    # Only update fields that were explicitly provided.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return _to_me_response(current_user)
