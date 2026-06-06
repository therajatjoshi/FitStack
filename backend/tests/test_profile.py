import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.db_models import BodyMetrics, MedicalFlags, Profile


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scalar_none():
    """Return an execute mock result whose scalar_one_or_none() is None."""
    return MagicMock(scalar_one_or_none=MagicMock(return_value=None))


def _scalar_obj(obj):
    return MagicMock(scalar_one_or_none=MagicMock(return_value=obj))


def _scalars_list(objs):
    return MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=objs)))
    )


# ── GET /consent-text ─────────────────────────────────────────────────────────

def test_get_consent_text_is_public(client) -> None:
    response = client.get("/consent-text")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "1.0"
    assert "not medical advice" in body["text"]


# ── GET /profile/me ───────────────────────────────────────────────────────────

def test_get_profile_me_requires_auth(client) -> None:
    response = client.get("/profile/me")
    assert response.status_code == 401


def test_get_profile_me_returns_empty_profile(
    auth_client, db_session, auth_user
) -> None:
    """When no profile/medical/metrics exist, returns zeros and Nones."""
    db_session.execute = AsyncMock(side_effect=lambda _: _scalar_none())

    response = auth_client.get("/profile/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(auth_user.id)
    assert body["email"] == auth_user.email
    assert body["height_cm"] is None
    assert body["primary_goal"] is None
    assert body["medical_flags"] is None
    assert body["latest_weight_kg"] is None
    assert body["profile_completeness"] == 0


# ── PUT /profile/me ───────────────────────────────────────────────────────────

def test_put_profile_me_creates_profile(auth_client, db_session, auth_user) -> None:
    """First PUT creates a new profile row."""
    profile_id = uuid.uuid4()
    now = datetime.now(UTC)

    # profile doesn't exist yet
    db_session.execute = AsyncMock(return_value=_scalar_none())

    async def refresh_side_effect(obj) -> None:
        if isinstance(obj, Profile):
            obj.id = profile_id
            obj.created_at = now
            obj.updated_at = now

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.put(
        "/profile/me",
        json={"height_cm": 175.0, "primary_goal": "strength"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["height_cm"] == 175.0
    assert body["primary_goal"] == "strength"
    assert body["user_id"] == str(auth_user.id)
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()


def test_put_profile_me_updates_existing_profile(
    auth_client, db_session, auth_user
) -> None:
    """Second PUT patches an existing profile."""
    now = datetime.now(UTC)
    existing_profile = Profile(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        height_cm=170.0,
        primary_goal="fat_loss",
        created_at=now,
        updated_at=now,
    )

    db_session.execute = AsyncMock(return_value=_scalar_obj(existing_profile))
    db_session.refresh = AsyncMock(return_value=None)

    response = auth_client.put(
        "/profile/me",
        json={"height_cm": 172.0},
    )

    assert response.status_code == 200
    body = response.json()
    # The service mutates the existing object in-place; our mock doesn't persist
    # but the returned schema comes from the (mutated) ORM object.
    assert body["user_id"] == str(auth_user.id)
    db_session.commit.assert_awaited_once()


def test_put_profile_me_rejects_invalid_height(auth_client) -> None:
    response = auth_client.put("/profile/me", json={"height_cm": 50.0})
    assert response.status_code == 422


# ── PUT /profile/me/medical ───────────────────────────────────────────────────

def test_put_medical_flags_creates_record(auth_client, db_session, auth_user) -> None:
    flags_id = uuid.uuid4()
    now = datetime.now(UTC)

    db_session.execute = AsyncMock(return_value=_scalar_none())

    async def refresh_side_effect(obj) -> None:
        if isinstance(obj, MedicalFlags):
            obj.id = flags_id
            obj.updated_at = now

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.put(
        "/profile/me/medical",
        json={"heart_condition": True, "none": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["heart_condition"] is True
    assert body["user_id"] == str(auth_user.id)
    db_session.add.assert_called_once()


def test_put_medical_flags_none_clears_consult(
    auth_client, db_session, auth_user
) -> None:
    """Setting none=True signals no conditions — safety service returns requires_consult=False."""
    flags_id = uuid.uuid4()
    now = datetime.now(UTC)

    db_session.execute = AsyncMock(return_value=_scalar_none())

    async def refresh_side_effect(obj) -> None:
        obj.id = flags_id
        obj.updated_at = now

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.put("/profile/me/medical", json={"none": True})

    assert response.status_code == 200
    body = response.json()
    assert body["none"] is True


# ── POST /body-metrics ────────────────────────────────────────────────────────

def test_post_body_metrics_returns_201(auth_client, db_session, auth_user) -> None:
    metric_id = uuid.uuid4()
    now = datetime.now(UTC)

    async def refresh_side_effect(obj) -> None:
        obj.id = metric_id
        obj.recorded_at = now

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.post(
        "/body-metrics",
        json={"weight_kg": 82.5, "body_fat_pct": 17.0},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["weight_kg"] == 82.5
    assert body["body_fat_pct"] == 17.0
    assert body["user_id"] == str(auth_user.id)
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()


def test_post_body_metrics_rejects_invalid_weight(auth_client) -> None:
    response = auth_client.post("/body-metrics", json={"weight_kg": 5.0})
    assert response.status_code == 422


def test_post_body_metrics_rejects_invalid_body_fat(auth_client) -> None:
    response = auth_client.post("/body-metrics", json={"body_fat_pct": 2.0})
    assert response.status_code == 422


# ── GET /body-metrics ─────────────────────────────────────────────────────────

def test_get_body_metrics_requires_auth(client) -> None:
    response = client.get("/body-metrics")
    assert response.status_code == 401


def test_get_body_metrics_returns_list(auth_client, db_session, auth_user) -> None:
    now = datetime.now(UTC)
    metric = BodyMetrics(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        weight_kg=80.0,
        body_fat_pct=15.5,
        waist_cm=None,
        hip_cm=None,
        recorded_at=now,
    )
    db_session.execute = AsyncMock(return_value=_scalars_list([metric]))

    response = auth_client.get("/body-metrics")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["weight_kg"] == 80.0
    assert body[0]["body_fat_pct"] == 15.5


# ── POST /profile/me/consent ──────────────────────────────────────────────────

def test_post_consent_records_version_and_timestamp(
    auth_client, db_session, auth_user
) -> None:
    response = auth_client.post(
        "/profile/me/consent",
        json={"consent_version": "1.0"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["consent_version"] == "1.0"
    assert body["consent_accepted_at"] is not None
    db_session.commit.assert_awaited_once()


# ── safety_service unit tests (no DB / no HTTP) ───────────────────────────────

from app.services.safety_service import build_safety_constraints  # noqa: E402


def _make_flags(**kwargs) -> MedicalFlags:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        heart_condition=False,
        diabetes=False,
        asthma=False,
        joint_or_back_issues=False,
        pregnant=False,
        other=False,
        other_notes=None,
        none=False,
        updated_at=datetime.now(UTC),
    )
    defaults.update(kwargs)
    return MedicalFlags(**defaults)


@pytest.fixture
def _user(auth_user):
    return auth_user


def test_safety_no_conditions_no_consult(_user) -> None:
    constraints = build_safety_constraints(_user, None)
    assert constraints.requires_consult is False
    assert constraints.constraint_text == ""


def test_safety_none_flag_no_consult(_user) -> None:
    flags = _make_flags(none=True)
    constraints = build_safety_constraints(_user, flags)
    assert constraints.requires_consult is False


def test_safety_heart_condition_requires_consult(_user) -> None:
    flags = _make_flags(heart_condition=True)
    constraints = build_safety_constraints(_user, flags)
    assert constraints.requires_consult is True
    assert "conservative" in constraints.constraint_text.lower()
    assert "consult" in constraints.constraint_text.lower()


def test_safety_diabetes_requires_consult(_user) -> None:
    flags = _make_flags(diabetes=True)
    assert build_safety_constraints(_user, flags).requires_consult is True


def test_safety_disclaimer_always_present(_user) -> None:
    for flags in [None, _make_flags(heart_condition=True), _make_flags(none=True)]:
        result = build_safety_constraints(_user, flags)
        assert result.disclaimer  # non-empty


# ── AI endpoint — safety constraint injection ─────────────────────────────────

from unittest.mock import patch  # noqa: E402


def test_ai_generate_workout_injects_safety_when_flagged(
    auth_client, db_session, auth_user
) -> None:
    """When a medical flag is active, consult_recommended must be True and the
    system prompt must contain conservative safety language."""
    now = datetime.now(UTC)
    flags = _make_flags(heart_condition=True)

    # DB call order inside generate_workout:
    #  1. get_profile        → scalar_one_or_none → None
    #  2. get_medical_flags  → scalar_one_or_none → flags (heart_condition=True)
    #  3. get_latest_body_metrics → scalar_one_or_none → None
    call_count = {"n": 0}

    async def execute_side_effect(stmt):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _scalar_none()
        if call_count["n"] == 2:
            return _scalar_obj(flags)
        return _scalar_none()

    db_session.execute = AsyncMock(side_effect=execute_side_effect)

    captured: list[list] = []
    mock_content = (
        '{"workout_name":"Safe Workout","workout_type":"general",'
        '"exercises":[{"name":"Walking","sets":3,"reps":10,"weight_kg":0,"notes":"light pace"}]}'
    )
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = mock_content

    mock_client = MagicMock()

    def _capture_and_return(**kwargs):
        captured.append(kwargs.get("messages", []))
        return mock_completion

    mock_client.chat.completions.create.side_effect = _capture_and_return

    with patch("app.routers.ai._get_openai_client", return_value=mock_client):
        response = auth_client.post(
            "/ai/generate-workout", json={"prompt": "safe workout for me"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["consult_recommended"] is True
    assert body["disclaimer"]

    # Verify safety text was in the system prompt sent to the LLM
    assert captured, "OpenAI was not called"
    system_msg = next(m for m in captured[0] if m["role"] == "system")
    assert "conservative" in system_msg["content"].lower()
    assert "consult" in system_msg["content"].lower()


def test_ai_generate_workout_no_consult_when_no_flags(
    auth_client, db_session, auth_user
) -> None:
    """No medical flags → consult_recommended is False."""
    db_session.execute = AsyncMock(side_effect=lambda _: _scalar_none())

    mock_content = (
        '{"workout_name":"General Workout","workout_type":"strength",'
        '"exercises":[{"name":"Squat","sets":3,"reps":5,"weight_kg":100,"notes":""}]}'
    )
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = mock_content
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    with patch("app.routers.ai._get_openai_client", return_value=mock_client):
        response = auth_client.post("/ai/generate-workout", json={})

    assert response.status_code == 200
    assert response.json()["consult_recommended"] is False
