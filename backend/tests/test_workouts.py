import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from app.models.db_models import Workout, WorkoutLog


def test_create_workout_requires_auth(client) -> None:
    response = client.post(
        "/workouts",
        json={"name": "Push Day", "workout_type": "strength"},
    )
    assert response.status_code == 401


def test_create_workout_returns_201(auth_client, db_session, auth_user) -> None:
    workout_id = uuid.uuid4()
    created_at = datetime.now(UTC)

    async def refresh_side_effect(obj: Workout) -> None:
        obj.id = workout_id
        obj.created_at = created_at

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.post(
        "/workouts",
        json={"name": "Push Day", "workout_type": "strength"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(workout_id)
    assert body["user_id"] == str(auth_user.id)
    assert body["name"] == "Push Day"
    assert body["workout_type"] == "strength"
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()


def test_list_workouts_returns_user_workouts(auth_client, db_session, auth_user) -> None:
    workout = Workout(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        name="Pull Day",
        workout_type="hypertrophy",
        created_at=datetime.now(UTC),
    )
    db_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[workout])))
    )

    response = auth_client.get("/workouts")

    assert response.status_code == 200
    workouts = response.json()
    assert len(workouts) == 1
    assert workouts[0]["name"] == "Pull Day"


def test_save_generated_workout_creates_ai_plan(
    auth_client, db_session, auth_user
) -> None:
    workout_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    captured: dict = {}

    def capture_add(obj) -> None:
        captured["workout"] = obj

    db_session.add.side_effect = capture_add

    async def refresh_side_effect(obj: Workout) -> None:
        obj.id = workout_id
        obj.created_at = created_at

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.post(
        "/workouts/generated",
        json={
            "workout_name": "AI Push Day",
            "workout_type": "hypertrophy",
            "progression_note": "First session — baseline.",
            "exercises": [
                {"name": "Bench Press", "sets": 3, "reps": 8, "weight_kg": 60.0,
                 "notes": "Control the descent"},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(workout_id)
    assert body["source"] == "ai"
    assert body["plan"]["exercises"][0]["name"] == "Bench Press"
    assert body["plan"]["progression_note"] == "First session — baseline."
    # Persisted as a single AI workout — no exercise rows, no logs.
    assert captured["workout"].source == "ai"
    db_session.commit.assert_awaited_once()


def test_complete_workout_sets_difficulty(auth_client, db_session, auth_user) -> None:
    workout_id = uuid.uuid4()
    workout = Workout(
        id=workout_id,
        user_id=auth_user.id,
        name="AI Push Day",
        workout_type="hypertrophy",
        source="ai",
        created_at=datetime.now(UTC),
    )
    db_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=workout))
    )

    response = auth_client.post(
        f"/workouts/{workout_id}/complete",
        json={"difficulty": "hard"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["difficulty"] == "hard"
    assert body["completed_at"] is not None
    assert workout.difficulty == "hard"
    db_session.commit.assert_awaited_once()


def test_complete_workout_rejects_bad_difficulty(auth_client) -> None:
    response = auth_client.post(
        f"/workouts/{uuid.uuid4()}/complete",
        json={"difficulty": "brutal"},
    )
    assert response.status_code == 422


def test_log_exercise_set_returns_201(auth_client, db_session, auth_user) -> None:
    workout_id = uuid.uuid4()
    exercise_id = uuid.uuid4()
    log_id = uuid.uuid4()
    logged_at = datetime.now(UTC)

    workout = Workout(
        id=workout_id,
        user_id=auth_user.id,
        name="Leg Day",
        workout_type="strength",
        created_at=logged_at,
    )

    async def execute_side_effect(statement):
        sql = str(statement)
        if "workouts" in sql:
            return MagicMock(scalar_one_or_none=MagicMock(return_value=workout))
        if "exercises" in sql:
            return MagicMock(scalar_one_or_none=MagicMock(return_value=object()))
        return MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        )

    db_session.execute = AsyncMock(side_effect=execute_side_effect)

    async def refresh_side_effect(obj: WorkoutLog) -> None:
        obj.id = log_id
        obj.logged_at = logged_at

    db_session.refresh.side_effect = refresh_side_effect

    response = auth_client.post(
        f"/workouts/{workout_id}/log",
        json={
            "exercise_id": str(exercise_id),
            "sets": 3,
            "reps": 10,
            "weight_kg": 60.0,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(log_id)
    assert body["workout_id"] == str(workout_id)
    assert body["exercise_id"] == str(exercise_id)
    assert body["sets"] == 3
    assert body["reps"] == 10
    assert body["weight_kg"] == 60.0


def test_list_workout_logs_returns_logs(auth_client, db_session, auth_user) -> None:
    workout_id = uuid.uuid4()
    exercise_id = uuid.uuid4()
    logged_at = datetime.now(UTC)

    workout = Workout(
        id=workout_id,
        user_id=auth_user.id,
        name="Leg Day",
        workout_type="strength",
        created_at=logged_at,
    )
    log = WorkoutLog(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        exercise_id=exercise_id,
        workout_id=workout_id,
        sets=3,
        reps=8,
        weight_kg=100.0,
        logged_at=logged_at,
    )

    call_count = {"n": 0}

    async def execute_side_effect(statement):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(scalar_one_or_none=MagicMock(return_value=workout))
        return MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[log])))
        )

    db_session.execute = AsyncMock(side_effect=execute_side_effect)

    response = auth_client.get(f"/workouts/{workout_id}/logs")

    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["exercise_id"] == str(exercise_id)
    assert logs[0]["weight_kg"] == 100.0
