from datetime import datetime

from pydantic import BaseModel, EmailStr


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserSummary(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime
    consent_accepted_at: datetime | None = None
    workout_count: int
    body_metrics_count: int
    is_stale: bool
    stale_reason: str | None = None  # "abandoned" | "inactive" | None


class CleanupResult(BaseModel):
    deleted_count: int
    deleted_emails: list[str]
