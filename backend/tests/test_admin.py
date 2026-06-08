import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.dependencies import get_current_admin
from app.main import app
from app.models.db_models import Admin, User
from app.services import admin_service
from app.services.admin_service import _stale_reason
from app.services.auth_service import AuthService

auth_service = AuthService()


# ── Helpers / fixtures ──────────────────────────────────────────────────────

def _scalar_obj(obj):
    return MagicMock(scalar_one_or_none=MagicMock(return_value=obj))


def _user(created_days_ago: int, *, consented: bool) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid.uuid4(),
        email=f"u{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="x",
        name="U",
        consent_accepted_at=now if consented else None,
        created_at=now - timedelta(days=created_days_ago),
    )


@pytest.fixture
def admin_client(client):
    async def override_admin() -> Admin:
        return Admin(
            id=uuid.uuid4(),
            email="admin@example.com",
            hashed_password="x",
            created_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_current_admin] = override_admin
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


# ── Pure stale logic ────────────────────────────────────────────────────────

def test_stale_reason_abandoned() -> None:
    now = datetime.now(UTC)
    created = now - timedelta(days=40)
    assert _stale_reason(created, None, 0, 0, now) == "abandoned"


def test_stale_reason_inactive() -> None:
    now = datetime.now(UTC)
    created = now - timedelta(days=120)
    # consented, but no activity for >90d
    assert _stale_reason(created, now, 0, 0, now) == "inactive"


def test_stale_reason_active_user_is_not_stale() -> None:
    now = datetime.now(UTC)
    created = now - timedelta(days=200)
    # consented and has workouts → active despite being old
    assert _stale_reason(created, now, 5, 0, now) is None


def test_stale_reason_recent_unconsented_not_yet_abandoned() -> None:
    now = datetime.now(UTC)
    created = now - timedelta(days=3)
    assert _stale_reason(created, None, 0, 0, now) is None


# ── Auth isolation ──────────────────────────────────────────────────────────

def test_admin_endpoint_requires_token(client) -> None:
    assert client.get("/admin/users").status_code == 401


def test_user_token_rejected_on_admin_endpoint(client) -> None:
    user_token = auth_service.create_access_token(subject=str(uuid.uuid4()))
    response = client.get(
        "/admin/users", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 401


def test_admin_token_rejected_on_user_endpoint(client, db_session) -> None:
    db_session.execute = AsyncMock(return_value=_scalar_obj(None))
    admin_token = auth_service.create_access_token(
        subject=str(uuid.uuid4()), extra_claims={"type": "admin"}
    )
    response = client.get(
        "/profile/me", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 401


# ── Admin login ─────────────────────────────────────────────────────────────

def test_admin_login_success(client, db_session) -> None:
    admin = Admin(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=auth_service.hash_password("s3cret-pass"),
        created_at=datetime.now(UTC),
    )
    db_session.execute = AsyncMock(return_value=_scalar_obj(admin))

    response = client.post(
        "/admin/auth/login",
        json={"email": "admin@example.com", "password": "s3cret-pass"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_admin_login_wrong_password(client, db_session) -> None:
    admin = Admin(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password=auth_service.hash_password("s3cret-pass"),
        created_at=datetime.now(UTC),
    )
    db_session.execute = AsyncMock(return_value=_scalar_obj(admin))

    response = client.post(
        "/admin/auth/login",
        json={"email": "admin@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


# ── User listing / deletion / cleanup ───────────────────────────────────────

def test_list_users_flags_stale(admin_client, db_session) -> None:
    abandoned = _user(40, consented=False)
    active = _user(5, consented=True)
    db_session.execute = AsyncMock(
        return_value=MagicMock(
            all=MagicMock(return_value=[(abandoned, 0, 0), (active, 2, 1)])
        )
    )

    response = admin_client.get("/admin/users")
    assert response.status_code == 200
    body = {row["email"]: row for row in response.json()}
    assert body[abandoned.email]["is_stale"] is True
    assert body[abandoned.email]["stale_reason"] == "abandoned"
    assert body[active.email]["is_stale"] is False


def test_delete_user_success(admin_client, db_session) -> None:
    user_id = uuid.uuid4()
    db_session.execute = AsyncMock(
        side_effect=[_scalar_obj(user_id), MagicMock()]
    )
    response = admin_client.delete(f"/admin/users/{user_id}")
    assert response.status_code == 204
    db_session.commit.assert_awaited_once()


def test_delete_user_not_found(admin_client, db_session) -> None:
    db_session.execute = AsyncMock(return_value=_scalar_obj(None))
    response = admin_client.delete(f"/admin/users/{uuid.uuid4()}")
    assert response.status_code == 404


def test_cleanup_deletes_only_stale(admin_client, db_session) -> None:
    abandoned = _user(40, consented=False)
    active = _user(5, consented=True)
    db_session.execute = AsyncMock(
        side_effect=[
            MagicMock(all=MagicMock(return_value=[(abandoned, 0, 0), (active, 2, 1)])),
            MagicMock(),  # the DELETE statement
        ]
    )

    response = admin_client.post("/admin/users/cleanup")
    assert response.status_code == 200
    body = response.json()
    assert body["deleted_count"] == 1
    assert body["deleted_emails"] == [abandoned.email]
    db_session.commit.assert_awaited_once()
